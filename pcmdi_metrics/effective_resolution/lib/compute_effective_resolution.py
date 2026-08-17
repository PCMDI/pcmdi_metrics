#!/usr/bin/env python
"""Effective resolution metrics following Klaver et al. (2020).

Public API
----------
compute_effective_resolution(ds, uvar, vvar, ...)
    Pure computation -- accepts an already-opened xarray Dataset, performs no
    file I/O and produces no plots.

process_effective_resolution(params)
    File-path/driver-oriented entry point.  Loads input, calls
    `compute_effective_resolution`, and writes NetCDF/JSON/PNG output in the
    PMP layout.

Method summary
--------------
Three spectra are examined per model configuration:

============================  ===========================================
Spectrum                      Role
============================  ===========================================
divergent KE at 250 hPa       Steepens earliest and most sharply; the most
                              sensitive single indicator.
rotational KE at 250 hPa      Near-tropopause rotational component.
rotational KE at 500 hPa      Confirms that the resolution signal is not
                              confined to the tropopause.
============================  ===========================================

The divergent spectrum at 500 hPa is deliberately *excluded*: Klaver et al.
find it steepens at all scales and carries no usable signal.

The effective resolution is the wavenumber at which steepening is diagnosed
for at least two of the three spectra, which is equivalent to the median of
the three detection wavenumbers.  The range spanned by the three is reported
as an uncertainty interval (the error bars of the paper's Figure 2).
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

import numpy as np
import xarray as xr

from .grid_distance import grid_box_distance_from_dataset, ratio_to_dx_convention
from .ke_spectra import compute_ke_spectra_timeseries, eddy_scale
from .spectral_slope import detect_steepening, fit_spectral_slope
from .spherical_harmonics import EARTH_RADIUS, resolve_backend

__all__ = [
    "compute_effective_resolution",
    "process_effective_resolution",
    "SPECTRUM_KEYS",
]

#: The three spectra used for the two-out-of-three confirmation rule, as
#: ``(pressure level in hPa, KE component)`` pairs.
SPECTRUM_KEYS: tuple[tuple[int, str], ...] = (
    (250, "div"),
    (250, "rot"),
    (500, "rot"),
)


def compute_effective_resolution(
    ds: xr.Dataset,
    uvar: str = "ua",
    vvar: str = "va",
    levels: tuple[float, ...] = (250.0, 500.0),
    plev_units: Literal["Pa", "hPa"] = "Pa",
    ntrunc: int | None = None,
    backend: Literal["auto", "windspharm", "shtns", "numpy"] = "auto",
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    fit_window: int = 20,
    fit_anchor: Literal["center", "right", "left"] = "center",
    steepening_factor: float = 0.25,
    wavenumber_ratio: float = 2.0,
    min_wavenumber: int = 32,
    n_confirm: int = 2,
    rsphere: float = EARTH_RADIUS,
    lat_name: str = "lat",
    lon_name: str = "lon",
    plev_name: str = "plev",
    time_name: str = "time",
    grid_box_distance_km: float | None = None,
    model: str = "model",
    exp: str | None = None,
    member: str | None = None,
    debug: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute effective-resolution metrics from an already-opened Dataset.

    This is the pure-computation entry point: no file I/O, no output files,
    no plots.  Suitable for notebooks, pipelines and unit tests.  ``ds`` is
    assumed to be on the model's **native** grid -- regridding before this
    call destroys the very information the diagnostic measures.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset holding ``uvar`` and ``vvar`` on ``(time, plev, lat, lon)``,
        with ``levels`` present on the ``plev_name`` axis.  Klaver et al. use
        6-hourly instantaneous winds over four months (March, June,
        September, December) of a single year; sub-daily sampling matters
        because the diagnostic lives in the transient, small-scale part of
        the flow.
    uvar, vvar : str, optional
        Zonal and meridional wind variable names.  Defaults ``"ua"``, ``"va"``.
    levels : tuple of float, optional
        Pressure levels to analyse, in ``plev_units``.  Default
        ``(250.0, 500.0)``.
    plev_units : {"Pa", "hPa"}, optional
        Units of the ``plev_name`` coordinate.  Default ``"Pa"`` (CMIP).
        ``levels`` is interpreted in hPa regardless and converted internally.
    ntrunc : int or None, optional
        Triangular truncation.  Default ``None`` (``nlat - 1``).
    backend : {"auto", "windspharm", "shtns", "numpy"}, optional
        Spherical-harmonic backend.
    gridtype : {"auto", "regular", "gaussian"}, optional
        Latitude grid type.
    fit_window : int, optional
        Sliding-window width for the slope fit, in wavenumbers.  Default
        ``20``.
    fit_anchor : {"center", "right", "left"}, optional
        Window anchoring for the slope fit.  See
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
        Sphere radius in metres.
    lat_name, lon_name, plev_name, time_name : str, optional
        Coordinate and dimension names.
    grid_box_distance_km : float or None, optional
        Representative grid box diagonal :math:`\\tilde{L}_{box}` in km.  If
        ``None`` (default) it is derived from ``ds``'s own grid.  Pass an
        explicit value for reduced Gaussian or octahedral grids, where the
        Dataset's rectilinear coordinates would misrepresent the mesh; see
        `~pcmdi_metrics.effective_resolution.lib.grid_distance.representative_grid_box_distance`.
    model, exp, member : str or None, optional
        Labels used as keys in the returned ``metrics`` dict.
    debug : bool, optional
        Print intermediate diagnostics.  Default ``False``.

    Returns
    -------
    metrics : dict
        Nested ``{model: {member: {...}}}`` in PMP style.  The inner dict
        holds:

        - ``effective_wavenumber``: :math:`l_{eff}`, the ``n_confirm``-th
          smallest detection wavenumber (``None`` if fewer than ``n_confirm``
          spectra steepen)
        - ``effective_resolution_km``: :math:`L_{eff}`, the eddy scale of
          :math:`l_{eff}` (Eq. 3)
        - ``grid_box_distance_km``: :math:`\\tilde{L}_{box}`
        - ``resolution_ratio``: :math:`L_{eff}/\\tilde{L}_{box}` -- the
          grid-independent headline metric, 2.7-4.8 across the paper's models
        - ``resolution_ratio_dx_convention``: the same in the
          Skamarock/Abdalla :math:`\\Delta x` convention
        - ``is_upper_limit``: ``True`` when the diagnosis is bounded by
          ``min_wavenumber`` rather than resolved
        - ``steepening_wavenumber``: per-spectrum detections, keyed
          ``"div_250"``, ``"rot_250"``, ``"rot_500"``
        - ``steepening_wavenumber_range``: ``[min, max]`` over the three
          spectra, the error bar of the paper's Figure 2
    diagnostics : dict
        Intermediate objects for plotting and archiving:

        - ``spectra``: ``{level_hPa: Dataset}`` from
          `~pcmdi_metrics.effective_resolution.lib.ke_spectra.compute_ke_spectra_timeseries`
        - ``slopes``: ``{"<component>_<level>": DataArray}`` of fitted exponents
        - ``detections``: ``{"<component>_<level>": dict}`` from
          `~pcmdi_metrics.effective_resolution.lib.spectral_slope.detect_steepening`
        - ``dataset``: a single Dataset merging spectra and slopes, ready for
          ``to_netcdf``

    Notes
    -----
    Interpreting the result: scales *smaller* than :math:`L_{eff}` are
    dynamically unreliable and, per the authors, "should be disregarded in
    the context of interpretational climate studies".  The diagnostic says
    nothing about the fidelity of scales *larger* than :math:`L_{eff}` -- a
    model can have a good effective resolution and a poor spectrum in the
    resolved range.

    Because this uses a global, vertically sparse, time-mean spectrum, a
    single :math:`L_{eff}` may mask phenomenon-dependent behaviour
    (midlatitude storms versus equatorial updraughts), a caveat the authors
    raise explicitly.

    Examples
    --------
    >>> metrics, diags = compute_effective_resolution(  # doctest: +SKIP
    ...     ds, uvar="ua", vvar="va", model="HadGEM3-GC31-HM", member="r1i1p1f1"
    ... )
    >>> metrics["HadGEM3-GC31-HM"]["r1i1p1f1"]["effective_wavenumber"]  # doctest: +SKIP
    108.0
    """
    spectra: dict[float, xr.Dataset] = {}
    slopes: dict[str, xr.DataArray] = {}
    detections: dict[str, dict[str, Any]] = {}

    for level in levels:
        spectra[level] = compute_ke_spectra_timeseries(
            ds,
            uvar=uvar,
            vvar=vvar,
            plev=level,
            plev_units="hPa",
            time_mean=True,
            time_name=time_name,
            plev_name=plev_name,
            ntrunc=ntrunc,
            backend=backend,
            gridtype=gridtype,
            rsphere=rsphere,
            lat_name=lat_name,
            lon_name=lon_name,
        )
        if debug:
            print(f"[effective_resolution] computed spectra at {level} hPa")

    for level, component in SPECTRUM_KEYS:
        key = f"{component}_{int(level)}"
        if float(level) not in spectra:
            continue
        slope = fit_spectral_slope(
            spectra[float(level)][f"ke_{component}"],
            window=fit_window,
            anchor=fit_anchor,
        )
        slopes[key] = slope
        detections[key] = detect_steepening(
            slope,
            steepening_factor=steepening_factor,
            wavenumber_ratio=wavenumber_ratio,
            min_wavenumber=min_wavenumber,
        )
        if debug:
            print(f"[effective_resolution] {key}: {detections[key]['wavenumber']}")

    detected = sorted(
        d["wavenumber"] for d in detections.values() if d["wavenumber"] is not None
    )
    if len(detected) >= n_confirm:
        l_eff: float | None = float(detected[n_confirm - 1])
        l_eff_km: float | None = float(eddy_scale(l_eff, rsphere))
    else:
        l_eff = None
        l_eff_km = None

    is_upper_limit = bool(
        l_eff is not None
        and any(
            d.get("is_upper_limit")
            for d in detections.values()
            if d["wavenumber"] is not None and d["wavenumber"] <= l_eff
        )
    )

    if grid_box_distance_km is None:
        grid_box_distance_km = grid_box_distance_from_dataset(
            ds, lat_name=lat_name, lon_name=lon_name, rsphere=rsphere
        )

    ratio = None if l_eff_km is None else float(l_eff_km / grid_box_distance_km)

    inner: dict[str, Any] = {
        "effective_wavenumber": l_eff,
        "effective_resolution_km": l_eff_km,
        "grid_box_distance_km": float(grid_box_distance_km),
        "resolution_ratio": ratio,
        "resolution_ratio_dx_convention": (
            None if ratio is None else float(ratio_to_dx_convention(ratio))
        ),
        "is_upper_limit": is_upper_limit,
        "n_spectra_steepening": len(detected),
        "steepening_wavenumber": {
            key: det["wavenumber"] for key, det in detections.items()
        },
        "steepening_eddy_scale_km": {
            key: (None if det["wavenumber"] is None else float(eddy_scale(det["wavenumber"], rsphere)))
            for key, det in detections.items()
        },
        "steepening_wavenumber_range": (
            [float(detected[0]), float(detected[-1])] if detected else None
        ),
        "sh_backend": resolve_backend(backend),
        "criterion": {
            "fit_window": fit_window,
            "fit_anchor": fit_anchor,
            "steepening_factor": steepening_factor,
            "wavenumber_ratio": wavenumber_ratio,
            "min_wavenumber": min_wavenumber,
            "n_confirm": n_confirm,
        },
        "reference": "Klaver et al. (2020), doi:10.1002/asl.952",
    }
    if exp is not None:
        inner["exp"] = exp

    metrics = {model: {member if member is not None else "unspecified": inner}}

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
        "reference": "Klaver et al. (2020), doi:10.1002/asl.952",
    }

    diagnostics = {
        "spectra": spectra,
        "slopes": slopes,
        "detections": detections,
        "dataset": merged,
    }
    return metrics, diagnostics


def process_effective_resolution(params: dict[str, Any]) -> dict[str, Any]:
    """Compute effective-resolution metrics from input file paths.

    File-path/driver-oriented entry point.  Opens the input, calls
    `compute_effective_resolution`, and writes the NetCDF, JSON and (if
    requested) PNG output.

    Parameters
    ----------
    params : dict
        User parameters.  Recognised keys:

        ``model``, ``exp``, ``member`` : str
            Labels for output naming and the metrics dict.
        ``input_file`` : str
            Path or glob for the wind data.  May contain both ``uvar`` and
            ``vvar``; use ``input_file_v`` if they live in separate files.
        ``input_file_v`` : str, optional
            Separate path for the meridional wind.
        ``uvar``, ``vvar`` : str
            Wind variable names.  Defaults ``"ua"``, ``"va"``.
        ``levels`` : sequence of float
            Pressure levels in hPa.  Default ``(250.0, 500.0)``.
        ``start``, ``end`` : str, optional
            Time subset bounds, ``"YYYY-MM"`` or ``"YYYY-MM-DD"``.
        ``backend``, ``gridtype``, ``ntrunc`` : optional
            Passed to the spectral computation.
        ``fit_window``, ``fit_anchor``, ``steepening_factor``,
        ``wavenumber_ratio``, ``min_wavenumber``, ``n_confirm`` : optional
            Passed to the detection criterion.
        ``grid_box_distance_km`` : float, optional
            Override for reduced/octahedral grids.
        ``output_dir`` : str
            Output directory.  Created if absent.  Default ``"./output"``.
        ``save_netcdf``, ``save_json``, ``plot`` : bool, optional
            Output switches.  Defaults ``True``, ``True``, ``False``.
        ``debug`` : bool, optional
            Default ``False``.

    Returns
    -------
    dict
        The same ``{model: {member: {...}}}`` metrics dict written to JSON.

    Examples
    --------
    >>> params = {  # doctest: +SKIP
    ...     "model": "HadGEM3-GC31-HM",
    ...     "exp": "highresSST-present",
    ...     "member": "r1i1p1f1",
    ...     "input_file": "/path/to/ua_6hrPlevPt_*.nc",
    ...     "input_file_v": "/path/to/va_6hrPlevPt_*.nc",
    ...     "levels": (250.0, 500.0),
    ...     "start": "2014-03-01",
    ...     "end": "2014-03-31",
    ...     "output_dir": "./output",
    ... }
    >>> metrics = process_effective_resolution(params)  # doctest: +SKIP
    """
    import xcdat as xc

    model = params.get("model", "model")
    exp = params.get("exp")
    member = params.get("member")
    input_file = params["input_file"]
    input_file_v = params.get("input_file_v")
    uvar = params.get("uvar", "ua")
    vvar = params.get("vvar", "va")
    levels = tuple(params.get("levels", (250.0, 500.0)))
    start = params.get("start")
    end = params.get("end")
    output_dir = params.get("output_dir", "./output")
    save_netcdf = params.get("save_netcdf", True)
    save_json = params.get("save_json", True)
    make_plot = params.get("plot", False)
    debug = params.get("debug", False)

    os.makedirs(output_dir, exist_ok=True)

    ds = xc.open_mfdataset(input_file, decode_times=True)
    if input_file_v is not None:
        ds = xr.merge([ds, xc.open_mfdataset(input_file_v, decode_times=True)])

    if start is not None or end is not None:
        ds = ds.sel(time=slice(start, end))

    tag = "_".join(
        str(part) for part in (model, exp, member) if part not in (None, "")
    )
    if start is not None and end is not None:
        tag += f"_{start}_{end}"

    metrics, diagnostics = compute_effective_resolution(
        ds,
        uvar=uvar,
        vvar=vvar,
        levels=levels,
        ntrunc=params.get("ntrunc"),
        backend=params.get("backend", "auto"),
        gridtype=params.get("gridtype", "auto"),
        fit_window=params.get("fit_window", 20),
        fit_anchor=params.get("fit_anchor", "center"),
        steepening_factor=params.get("steepening_factor", 0.25),
        wavenumber_ratio=params.get("wavenumber_ratio", 2.0),
        min_wavenumber=params.get("min_wavenumber", 32),
        n_confirm=params.get("n_confirm", 2),
        grid_box_distance_km=params.get("grid_box_distance_km"),
        model=model,
        exp=exp,
        member=member,
        debug=debug,
    )

    if save_netcdf:
        nc_path = os.path.join(output_dir, f"ke_spectra_{tag}.nc")
        diagnostics["dataset"].to_netcdf(nc_path)
        if debug:
            print(f"[effective_resolution] wrote {nc_path}")

    if save_json:
        json_path = os.path.join(output_dir, f"effective_resolution_{tag}.json")
        with open(json_path, "w") as handle:
            json.dump(
                {
                    "DIMENSIONS": {
                        "json_structure": ["model", "realization", "metric"],
                    },
                    "RESULTS": metrics,
                    "REFERENCE": "Klaver et al. (2020), doi:10.1002/asl.952",
                },
                handle,
                indent=2,
                sort_keys=True,
                default=_json_default,
            )
        if debug:
            print(f"[effective_resolution] wrote {json_path}")

    if make_plot:
        from .plot import plot_spectra_and_slope

        plot_spectra_and_slope(
            diagnostics,
            metrics[model][member if member is not None else "unspecified"],
            title=tag.replace("_", " "),
            output_file=os.path.join(output_dir, f"ke_spectra_{tag}.png"),
        )

    return metrics


def _json_default(obj: Any) -> Any:
    """Fallback JSON encoder for numpy scalars."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
