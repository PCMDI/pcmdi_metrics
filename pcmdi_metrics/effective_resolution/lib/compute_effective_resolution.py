#!/usr/bin/env python
"""Effective resolution metrics following Klaver et al. (2020).

Public API
----------
`compute_effective_resolution`
    Pure computation: accepts an already-opened xarray Dataset, performs no
    file I/O and produces no plots.
`process_effective_resolution`
    File-path entry point for driver scripts: loads input, calls
    `compute_effective_resolution`, and writes NetCDF, JSON and PNG output in
    the PMP layout.

Method summary
--------------
Three spectra are examined per model configuration:

============================  ===========================================
Spectrum                      Role
============================  ===========================================
divergent KE at 250 hPa       Steepens earliest and most sharply; the most
                              sensitive single indicator.
rotational KE at 250 hPa      Near-tropopause rotational component.
rotational KE at 500 hPa      Confirms the signal is not confined to the
                              tropopause.
============================  ===========================================

The divergent spectrum at 500 hPa is deliberately *excluded*: Klaver et al.
find it steepens at all scales and carries no usable signal.

The effective resolution is the wavenumber at which steepening is diagnosed
for at least two of the three spectra, equivalent to the median of the three
detection wavenumbers.  The range spanned by the three is reported as an
uncertainty interval -- the error bars of the paper's Figure 2.

References
----------
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
"""

from __future__ import annotations

import os
from typing import Any, Literal

import xarray as xr

from pcmdi_metrics.io import xcdat_open
from pcmdi_metrics.io.base import Base

from .grid_distance import grid_box_distance_from_dataset, ratio_to_dx_convention
from .ke_spectra import EARTH_RADIUS, compute_ke_spectra_timeseries, eddy_scale
from .spectral_slope import detect_steepening, fit_spectral_slope

__all__ = [
    "SPECTRUM_KEYS",
    "compute_effective_resolution",
    "process_effective_resolution",
]

#: The three spectra used for the two-out-of-three confirmation rule, as
#: ``(pressure level in hPa, KE component)`` pairs.
SPECTRUM_KEYS: tuple[tuple[int, str], ...] = ((250, "div"), (250, "rot"), (500, "rot"))

REFERENCE = "Klaver et al. (2020), doi:10.1002/asl.952"


def compute_effective_resolution(
    ds: xr.Dataset,
    uvar: str = "ua",
    vvar: str = "va",
    levels: tuple[float, ...] = (250.0, 500.0),
    ntrunc: int | None = None,
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    fit_window: int = 20,
    fit_anchor: Literal["center", "right", "left"] = "center",
    steepening_factor: float = 0.25,
    wavenumber_ratio: float = 2.0,
    min_wavenumber: int = 32,
    n_confirm: int = 2,
    rsphere: float = EARTH_RADIUS,
    plev_name: str | None = None,
    grid_box_distance_km: float | None = None,
    model: str = "model",
    exp: str | None = None,
    member: str | None = None,
    debug: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute effective-resolution metrics from an already-opened Dataset.

    This is the pure-computation entry point: no file I/O, no output files, no
    plots.  Suitable for notebooks, pipelines and unit tests.  ``ds`` is
    assumed to be on the model's **native** grid; regridding beforehand
    destroys the very information the diagnostic measures.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset holding ``uvar`` and ``vvar`` on ``(time, plev, lat, lon)``.
        Coordinate names are resolved from the dataset's own axis metadata,
        and the vertical coordinate may be in Pa or hPa.  Klaver et al. use
        6-hourly instantaneous winds over four months of a single year;
        sub-daily sampling matters because the diagnostic lives in the
        transient, small-scale part of the flow.
    uvar, vvar : str, optional
        Zonal and meridional wind variable names.  Defaults ``"ua"``, ``"va"``.
    levels : tuple of float, optional
        Pressure levels to analyse, **in hPa**.  Default ``(250.0, 500.0)``.
    ntrunc : int or None, optional
        Triangular truncation.  Default ``None`` (``nlat - 1``).
    gridtype : {"auto", "regular", "gaussian"}, optional
        Latitude grid type.  Default ``"auto"``.
    fit_window : int, optional
        Sliding-window width for the slope fit, in wavenumbers.  Default 20.
    fit_anchor : {"center", "right", "left"}, optional
        Window anchoring for the slope fit; see
        `~pcmdi_metrics.effective_resolution.lib.spectral_slope.fit_spectral_slope`.
    steepening_factor : float, optional
        Fractional exponent increase defining steepening.  Default ``0.25``,
        described by the authors as ad hoc; vary it to test sensitivity.
    wavenumber_ratio : float, optional
        Wavenumber ratio over which the increase is measured.  Default ``2.0``.
    min_wavenumber : int, optional
        Smallest wavenumber at which detection is attempted.  Default ``32``.
    n_confirm : int, optional
        Number of spectra that must show steepening.  Default ``2`` (of 3).
    rsphere : float, optional
        Sphere radius in metres.  Default is
        `~pcmdi_metrics.effective_resolution.lib.ke_spectra.EARTH_RADIUS`.
    plev_name : str or None, optional
        Vertical coordinate name.  Default resolves it from ``ds``.
    grid_box_distance_km : float or None, optional
        Representative grid box diagonal :math:`\\tilde{L}_{box}` in km.  If
        ``None`` (default) it is derived from ``ds``'s own grid.  Pass an
        explicit value for reduced Gaussian or octahedral grids, where the
        Dataset's rectilinear coordinates misrepresent the mesh.
    model, exp, member : str or None, optional
        Labels used as keys in the returned ``metrics`` dict.
    debug : bool, optional
        Print intermediate diagnostics.  Default ``False``.

    Returns
    -------
    metrics : dict
        Nested ``{model: {member: {...}}}`` in PMP style.  The inner dict
        holds ``effective_wavenumber`` (:math:`l_{eff}`, ``None`` if fewer
        than ``n_confirm`` spectra steepen), ``effective_resolution_km``
        (:math:`L_{eff}`, Eq. 3), ``grid_box_distance_km``
        (:math:`\\tilde{L}_{box}`), ``resolution_ratio``
        (:math:`L_{eff}/\\tilde{L}_{box}`, the grid-independent headline
        metric, 2.7-4.8 across the paper's models),
        ``resolution_ratio_dx_convention``, ``is_upper_limit``,
        ``n_spectra_steepening``, ``steepening_wavenumber`` and
        ``steepening_eddy_scale_km`` per spectrum (keyed ``"div_250"``,
        ``"rot_250"``, ``"rot_500"``), and ``steepening_wavenumber_range``.
    diagnostics : dict
        ``spectra`` (``{level_hPa: Dataset}``), ``slopes``, ``detections`` and
        ``dataset`` -- a single Dataset merging spectra and slopes, ready for
        ``to_netcdf`` or for
        `~pcmdi_metrics.effective_resolution.lib.plot.plot_spectra_and_slope`.

    Notes
    -----
    Scales *smaller* than :math:`L_{eff}` are dynamically unreliable and, per
    the authors, "should be disregarded in the context of interpretational
    climate studies".  The diagnostic says nothing about the fidelity of
    scales *larger* than :math:`L_{eff}`: a model can have a good effective
    resolution and a poor spectrum in the resolved range.  Because this is a
    global, vertically sparse, time-mean spectrum, a single :math:`L_{eff}`
    may also mask phenomenon-dependent behaviour, a caveat the authors raise
    explicitly.

    Examples
    --------
    >>> metrics, diags = compute_effective_resolution(  # doctest: +SKIP
    ...     ds, model="HadGEM3-GC31-HM", member="r1i1p1f1"
    ... )
    >>> metrics["HadGEM3-GC31-HM"]["r1i1p1f1"]["effective_wavenumber"]  # doctest: +SKIP
    108.0
    """
    spectra: dict[float, xr.Dataset] = {}
    for level in levels:
        spectra[float(level)] = compute_ke_spectra_timeseries(
            ds,
            uvar=uvar,
            vvar=vvar,
            level_hpa=float(level),
            time_mean=True,
            plev_name=plev_name,
            ntrunc=ntrunc,
            gridtype=gridtype,
            rsphere=rsphere,
        )
        if debug:
            print(f"[effective_resolution] computed spectra at {level} hPa")

    slopes: dict[str, xr.DataArray] = {}
    detections: dict[str, dict[str, Any]] = {}
    for level, component in SPECTRUM_KEYS:
        if float(level) not in spectra:
            continue
        key = f"{component}_{int(level)}"
        slopes[key] = fit_spectral_slope(
            spectra[float(level)][f"ke_{component}"],
            window=fit_window,
            anchor=fit_anchor,
        )
        detections[key] = detect_steepening(
            slopes[key],
            steepening_factor=steepening_factor,
            wavenumber_ratio=wavenumber_ratio,
            min_wavenumber=min_wavenumber,
        )
        if debug:
            print(f"[effective_resolution] {key}: l = {detections[key]['wavenumber']}")

    detected = sorted(
        d["wavenumber"] for d in detections.values() if d["wavenumber"] is not None
    )
    if len(detected) >= n_confirm:
        l_eff: float | None = float(detected[n_confirm - 1])
        l_eff_km: float | None = float(eddy_scale(l_eff, rsphere))
    else:
        l_eff = l_eff_km = None

    if grid_box_distance_km is None:
        grid_box_distance_km = grid_box_distance_from_dataset(ds, rsphere=rsphere)
    ratio = None if l_eff_km is None else float(l_eff_km / grid_box_distance_km)

    inner: dict[str, Any] = {
        "effective_wavenumber": l_eff,
        "effective_resolution_km": l_eff_km,
        "grid_box_distance_km": float(grid_box_distance_km),
        "resolution_ratio": ratio,
        "resolution_ratio_dx_convention": (
            None if ratio is None else float(ratio_to_dx_convention(ratio))
        ),
        "is_upper_limit": bool(
            l_eff is not None
            and any(
                d["is_upper_limit"]
                for d in detections.values()
                if d["wavenumber"] is not None and d["wavenumber"] <= l_eff
            )
        ),
        "n_spectra_steepening": len(detected),
        "steepening_wavenumber": {k: d["wavenumber"] for k, d in detections.items()},
        "steepening_eddy_scale_km": {
            k: (
                None
                if d["wavenumber"] is None
                else float(eddy_scale(d["wavenumber"], rsphere))
            )
            for k, d in detections.items()
        },
        "steepening_wavenumber_range": (
            [float(detected[0]), float(detected[-1])] if detected else None
        ),
        "criterion": {
            "fit_window": fit_window,
            "fit_anchor": fit_anchor,
            "steepening_factor": steepening_factor,
            "wavenumber_ratio": wavenumber_ratio,
            "min_wavenumber": min_wavenumber,
            "n_confirm": n_confirm,
        },
        "reference": REFERENCE,
    }
    if exp is not None:
        inner["exp"] = exp

    merged = xr.Dataset()
    for level, spec in spectra.items():
        for var in ("ke_rot", "ke_div", "ke_total"):
            merged[f"{var}_{int(level)}"] = spec[var]
    for key, slope in slopes.items():
        merged[f"slope_{key}"] = slope
    merged.attrs = {
        "model": model,
        "experiment": exp or "",
        "member": member or "",
        "effective_wavenumber": "" if l_eff is None else l_eff,
        "grid_box_distance_km": float(grid_box_distance_km),
        "reference": REFERENCE,
    }

    metrics = {model: {member if member is not None else "unspecified": inner}}
    diagnostics = {
        "spectra": spectra,
        "slopes": slopes,
        "detections": detections,
        "dataset": merged,
    }
    return metrics, diagnostics


def process_effective_resolution(params: dict[str, Any]) -> dict[str, Any]:
    """Compute effective-resolution metrics from input file paths.

    Opens the input, calls `compute_effective_resolution`, and writes the
    NetCDF, JSON and, if requested, PNG output.  The JSON is written through
    `pcmdi_metrics.io.base.Base`, so it carries the standard PMP provenance
    block.

    Parameters
    ----------
    params : dict
        User parameters.  Recognised keys: ``model``, ``exp``, ``member``
        (labels); ``input_file`` (path, glob or list for the wind data) and
        optional ``input_file_v`` when the meridional wind lives in separate
        files; ``uvar``, ``vvar``; ``levels`` in hPa; ``start`` and ``end``
        time bounds; ``ntrunc``, ``gridtype``, ``plev_name``; the criterion
        keys ``fit_window``, ``fit_anchor``, ``steepening_factor``,
        ``wavenumber_ratio``, ``min_wavenumber``, ``n_confirm``;
        ``grid_box_distance_km`` to override the derived value;
        ``output_dir``; the switches ``save_netcdf``, ``save_json``, ``plot``;
        and ``debug``.

    Returns
    -------
    dict
        The same ``{model: {member: {...}}}`` metrics dict written to JSON.

    Examples
    --------
    >>> metrics = process_effective_resolution(  # doctest: +SKIP
    ...     {
    ...         "model": "HadGEM3-GC31-HM",
    ...         "exp": "highresSST-present",
    ...         "member": "r1i1p1f1",
    ...         "input_file": "/path/to/ua_6hrPlevPt_*.nc",
    ...         "input_file_v": "/path/to/va_6hrPlevPt_*.nc",
    ...         "start": "2014-03-01",
    ...         "end": "2014-03-31",
    ...         "output_dir": "./output",
    ...     }
    ... )
    """
    model = params.get("model", "model")
    exp = params.get("exp")
    member = params.get("member")
    start = params.get("start")
    end = params.get("end")
    output_dir = params.get("output_dir", "./output")
    debug = params.get("debug", False)

    os.makedirs(output_dir, exist_ok=True)

    ds = xcdat_open(params["input_file"], decode_times=True)
    if params.get("input_file_v") is not None:
        ds = xr.merge([ds, xcdat_open(params["input_file_v"], decode_times=True)])
    if start is not None or end is not None:
        ds = ds.sel(time=slice(start, end))

    tag = "_".join(str(p) for p in (model, exp, member) if p not in (None, ""))
    if start is not None and end is not None:
        tag += f"_{start}_{end}"

    metrics, diagnostics = compute_effective_resolution(
        ds,
        uvar=params.get("uvar", "ua"),
        vvar=params.get("vvar", "va"),
        levels=tuple(params.get("levels", (250.0, 500.0))),
        ntrunc=params.get("ntrunc"),
        gridtype=params.get("gridtype", "auto"),
        fit_window=params.get("fit_window", 20),
        fit_anchor=params.get("fit_anchor", "center"),
        steepening_factor=params.get("steepening_factor", 0.25),
        wavenumber_ratio=params.get("wavenumber_ratio", 2.0),
        min_wavenumber=params.get("min_wavenumber", 32),
        n_confirm=params.get("n_confirm", 2),
        plev_name=params.get("plev_name"),
        grid_box_distance_km=params.get("grid_box_distance_km"),
        model=model,
        exp=exp,
        member=member,
        debug=debug,
    )

    if params.get("save_netcdf", True):
        diagnostics["dataset"].to_netcdf(
            os.path.join(output_dir, f"ke_spectra_{tag}.nc")
        )

    if params.get("save_json", True):
        json_structure = ["model", "realization", "metric"]
        Base(output_dir, f"effective_resolution_{tag}.json").write(
            {
                "DIMENSIONS": {"json_structure": json_structure},
                "RESULTS": metrics,
                "REFERENCE": REFERENCE,
            },
            json_structure=json_structure,
            sort_keys=True,
            indent=4,
            separators=(",", ": "),
        )

    if params.get("plot", False):
        from .plot import plot_spectra_and_slope

        plot_spectra_and_slope(
            diagnostics,
            metrics[model][member if member is not None else "unspecified"],
            title=tag.replace("_", " "),
            output_file=os.path.join(output_dir, f"ke_spectra_{tag}.png"),
        )

    return metrics
