#!/usr/bin/env python
"""Spectral slope and steepening detection.

Klaver et al. (2020) diagnose the effective resolution from the *shape* of
the KE spectrum rather than from its amplitude.  The chain is:

1. Fit :math:`y = C\\,l^{-n}` in a sliding window of 20 wavenumbers to obtain
   the local slope exponent :math:`n(l)` (their Appendix S3).
2. Declare "steepening" at the smallest :math:`l \\ge l_{min}` where the
   exponent grows by at least 25% over a doubling of wavenumber, i.e.
   :math:`n(2l) \\ge 1.25\\, n(l)`.
3. Take :math:`l_{min} = 32` (:math:`\\Delta S = 625` km), the smallest
   wavenumber at which the method is meaningful, because the observed
   spectrum is shallower than :math:`k^{-3}` for :math:`l < 13`.

The 25% threshold is described in the paper as "ad hoc and somewhat
arbitrary"; it is exposed here as `steepening_factor` so that sensitivity
tests are one keyword away.  The paper's own sensitivity argument -- that the
two-out-of-three confirmation rule (see
`~pcmdi_metrics.effective_resolution.lib.compute_effective_resolution`) makes
the final answer only marginally sensitive to this value -- is worth
re-testing on any new model.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import xarray as xr

__all__ = [
    "fit_spectral_slope",
    "detect_steepening",
    "reference_steepening_line",
]


def fit_spectral_slope(
    spectrum: xr.DataArray,
    window: int = 20,
    anchor: Literal["center", "right", "left"] = "center",
    wavenumber_name: str = "wavenumber",
    min_valid: int | None = None,
) -> xr.DataArray:
    """Local spectral slope exponent from a sliding log-log fit.

    Fits :math:`\\log E = \\log C - n \\log l` by least squares over a moving
    window of ``window`` wavenumbers and returns the exponent :math:`n`, so
    that larger values mean a steeper spectrum.

    Parameters
    ----------
    spectrum : xarray.DataArray
        KE spectrum with a ``wavenumber_name`` dimension.  Must be positive;
        non-positive values are masked out of the fit.
    window : int, optional
        Number of wavenumbers in the fitting window.  Default is ``20``,
        following Appendix S3 of Klaver et al. (2020).
    anchor : {"center", "right", "left"}, optional
        Which wavenumber in the window the fitted exponent is assigned to.
        The paper's phrasing ("indicative of steepening at the largest
        wavenumber in the range") is ambiguous about whether the plotted
        :math:`n(l)` curve is centre- or right-anchored.  ``"center"``
        (default) is the conventional choice; ``"right"`` reproduces the
        literal reading.  Because the criterion compares :math:`n` at
        :math:`l` and :math:`2l`, a constant offset between the two
        conventions shifts the diagnosed wavenumber by roughly ``window/2``
        -- non-negligible at :math:`l \\sim 35`, small at :math:`l \\sim 110`.
        Report which convention was used.
    wavenumber_name : str, optional
        Name of the wavenumber dimension.
    min_valid : int or None, optional
        Minimum number of positive points required inside a window for the
        fit to be attempted.  Default (``None``) is ``window // 2``.

    Returns
    -------
    xarray.DataArray
        Exponent :math:`n` on the same ``wavenumber`` coordinate, ``NaN``
        where the window is incomplete or degenerate.

    Examples
    --------
    A pure power law returns its own exponent:

    >>> ell = np.arange(1, 200)
    >>> spec = xr.DataArray(
    ...     ell.astype(float) ** -3.0, coords={"wavenumber": ell}, dims="wavenumber"
    ... )
    >>> n = fit_spectral_slope(spec)
    >>> bool(abs(float(n.sel(wavenumber=100)) - 3.0) < 1e-8)
    True
    """
    if window < 3:
        raise ValueError(f"window must be >= 3, got {window}")
    if min_valid is None:
        min_valid = window // 2

    ell = np.asarray(spectrum[wavenumber_name].values, dtype=float)
    values = np.asarray(spectrum.values, dtype=float)
    n_points = ell.size

    offsets = {
        "center": window // 2,
        "right": window - 1,
        "left": 0,
    }
    if anchor not in offsets:
        raise ValueError(f"anchor must be one of {sorted(offsets)}, got {anchor!r}")
    offset = offsets[anchor]

    slope = np.full(n_points, np.nan)
    log_l = np.log(ell)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_e = np.log(values)

    for start in range(0, n_points - window + 1):
        stop = start + window
        x = log_l[start:stop]
        y = log_e[start:stop]
        good = np.isfinite(x) & np.isfinite(y)
        if good.sum() < min_valid:
            continue
        # np.polyfit returns [slope, intercept]; n = -slope
        fit = np.polyfit(x[good], y[good], 1)
        slope[start + offset] = -fit[0]

    out = xr.DataArray(
        slope,
        coords={wavenumber_name: spectrum[wavenumber_name]},
        dims=wavenumber_name,
        name="spectral_slope",
    )
    for coord in ("eddy_scale",):
        if coord in spectrum.coords:
            out = out.assign_coords({coord: spectrum[coord]})
    out.attrs = {
        "long_name": "Spectral slope exponent n of E ~ l**(-n)",
        "units": "1",
        "fit_window": window,
        "anchor": anchor,
        "description": "Klaver et al. (2020), Appendix S3",
    }
    return out


def detect_steepening(
    slope: xr.DataArray,
    steepening_factor: float = 0.25,
    wavenumber_ratio: float = 2.0,
    min_wavenumber: int = 32,
    max_wavenumber: int | None = None,
    require_all: bool = True,
    wavenumber_name: str = "wavenumber",
) -> dict[str, float | None]:
    """Locate the wavenumber where the spectral slope starts steepening.

    Implements the detection criterion of Klaver et al. (2020): steepening is
    declared at the smallest :math:`l \\ge` ``min_wavenumber`` such that the
    exponent has grown by ``steepening_factor`` (25%) by the time the
    wavenumber has grown by ``wavenumber_ratio`` (a factor 2).

    Formally, with :math:`r` = ``wavenumber_ratio`` and :math:`f` =
    ``steepening_factor``, the reference line through :math:`(l, n(l))` is

    .. math:: n_{ref}(l') = n(l)\\left(1 + f\\,\\frac{\\log(l'/l)}{\\log r}\\right),

    and steepening is declared where :math:`n(l') \\ge n_{ref}(l')`.

    Parameters
    ----------
    slope : xarray.DataArray
        Output of `fit_spectral_slope`.
    steepening_factor : float, optional
        Fractional increase of the exponent required over a
        ``wavenumber_ratio`` increase in wavenumber.  Default ``0.25``.
        Explicitly flagged as ad hoc by the authors -- vary it.
    wavenumber_ratio : float, optional
        Wavenumber ratio over which the increase must occur.  Default ``2.0``.
    min_wavenumber : int, optional
        Smallest wavenumber at which detection is attempted.  Default ``32``
        (:math:`\\Delta S \\approx 625` km).  A model that shows no steepening
        by this point gets an *upper limit*, not a value -- exactly the case
        of HadGEM3-GC31-LM and CNRM-CM6-0 in the paper.
    max_wavenumber : int or None, optional
        Largest candidate wavenumber.  Default (``None``) uses
        ``max(l) / wavenumber_ratio`` so that the comparison point
        :math:`r\\,l` stays inside the fitted range.
    require_all : bool, optional
        If ``True`` (default), every wavenumber in :math:`(l, r\\,l]` must lie
        on or above the reference line -- the paper's "progressive
        deterioration" requirement.  If ``False``, only :math:`l' = r\\,l` is
        tested.
    wavenumber_name : str, optional
        Name of the wavenumber dimension.

    Returns
    -------
    dict
        ``{"wavenumber": float or None, "slope_at_detection": float or None,
        "is_upper_limit": bool, "criterion": dict}``.  ``wavenumber`` is
        ``None`` when no steepening is found anywhere in range;
        ``is_upper_limit`` is ``True`` when steepening is already present at
        ``min_wavenumber``, meaning the true value is at or below it.

    Examples
    --------
    A clean :math:`l^{-3}` power law that rolls off past :math:`l = 60` is
    detected at :math:`l = 53`.  Detection precedes the roll-off because a
    centred 20-wavenumber window centred on 53 already reaches :math:`l = 63`
    -- an inherent lead of roughly ``window / 2`` that is common to any
    windowed slope estimate and applies equally to the published values.

    >>> ell = np.arange(1, 400)
    >>> e = ell.astype(float) ** -3.0 * np.exp(-np.maximum(ell - 60, 0) / 80)
    >>> spec = xr.DataArray(e, coords={"wavenumber": ell}, dims="wavenumber")
    >>> res = detect_steepening(fit_spectral_slope(spec))
    >>> res["wavenumber"]
    53.0

    Relaxing ``require_all`` tests only the endpoint :math:`l' = 2l`, which
    fires earlier and is more easily tripped by a local wobble:

    >>> detect_steepening(fit_spectral_slope(spec), require_all=False)["wavenumber"]
    34.0
    """
    if not 0 < steepening_factor:
        raise ValueError("steepening_factor must be positive")
    if wavenumber_ratio <= 1:
        raise ValueError("wavenumber_ratio must be > 1")

    ell = np.asarray(slope[wavenumber_name].values, dtype=float)
    n = np.asarray(slope.values, dtype=float)

    if max_wavenumber is None:
        max_wavenumber = ell.max() / wavenumber_ratio

    criterion = {
        "steepening_factor": steepening_factor,
        "wavenumber_ratio": wavenumber_ratio,
        "min_wavenumber": min_wavenumber,
        "require_all": require_all,
    }
    result: dict[str, float | None] = {
        "wavenumber": None,
        "slope_at_detection": None,
        "is_upper_limit": False,
        "criterion": criterion,
    }

    candidates = np.where((ell >= min_wavenumber) & (ell <= max_wavenumber) & np.isfinite(n))[0]
    for i in candidates:
        l0, n0 = ell[i], n[i]
        if n0 <= 0:
            continue
        window = np.where((ell > l0) & (ell <= wavenumber_ratio * l0))[0]
        window = window[np.isfinite(n[window])]
        if window.size == 0:
            continue

        n_ref = reference_steepening_line(
            ell[window], l0, n0, steepening_factor, wavenumber_ratio
        )
        hits = n[window] >= n_ref
        detected = hits.all() if require_all else hits[-1]

        if detected:
            result["wavenumber"] = float(l0)
            result["slope_at_detection"] = float(n0)
            result["is_upper_limit"] = bool(np.isclose(l0, ell[candidates[0]]))
            return result

    return result


def reference_steepening_line(
    ell: np.ndarray,
    l0: float,
    n0: float,
    steepening_factor: float = 0.25,
    wavenumber_ratio: float = 2.0,
) -> np.ndarray:
    """Reference line for the steepening criterion.

    These are the "straight skewed lines" of Figure 1 (panels d-f, j-l) in
    Klaver et al. (2020): straight on a log-wavenumber / linear-exponent axis,
    anchored at :math:`(l_0, n_0)`, rising by ``steepening_factor`` per
    ``wavenumber_ratio`` in wavenumber.  Useful both inside
    `detect_steepening` and for reproducing the figure.

    Parameters
    ----------
    ell : ndarray
        Wavenumbers at which to evaluate the line.
    l0, n0 : float
        Anchor point: wavenumber and slope exponent.
    steepening_factor : float, optional
        Fractional exponent increase per ``wavenumber_ratio``.
    wavenumber_ratio : float, optional
        Wavenumber ratio.

    Returns
    -------
    ndarray
        Reference exponent at each element of ``ell``.

    Examples
    --------
    >>> float(reference_steepening_line(np.array([64.0]), 32.0, 3.0)[0])
    3.75
    """
    return n0 * (
        1.0 + steepening_factor * np.log(ell / l0) / np.log(wavenumber_ratio)
    )
