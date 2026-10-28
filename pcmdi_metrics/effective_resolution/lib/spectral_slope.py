#!/usr/bin/env python
"""Spectral slope fitting and steepening detection.

Klaver et al. (2020) diagnose the effective resolution from the *shape* of the
kinetic energy spectrum rather than its amplitude:

1. Fit :math:`E = C\\,l^{-n}` in a sliding window of 20 wavenumbers to obtain
   the local slope exponent :math:`n(l)` (their Appendix S3).
2. Declare "steepening" at the smallest :math:`l \\ge l_{min}` where the
   exponent grows by at least 25% over a doubling of wavenumber.
3. Take :math:`l_{min} = 32` (:math:`\\Delta S \\approx 625` km), below which
   the method is not meaningful because the observed spectrum is shallower
   than :math:`k^{-3}` for :math:`l < 13`.

The 25% threshold is described in the paper as "ad hoc and somewhat
arbitrary"; it is exposed as ``steepening_factor`` so sensitivity tests are one
keyword away.

References
----------
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import xarray as xr

__all__ = ["detect_steepening", "fit_spectral_slope", "reference_steepening_line"]

#: Wavenumber offset within the fitting window that the exponent is assigned to.
_ANCHORS = {"center": lambda w: w // 2, "right": lambda w: w - 1, "left": lambda w: 0}


def fit_spectral_slope(
    spectrum: xr.DataArray,
    window: int = 20,
    anchor: Literal["center", "right", "left"] = "center",
    wavenumber_name: str = "wavenumber",
) -> xr.DataArray:
    """Local spectral slope exponent from a sliding log-log fit.

    Fits :math:`\\log E = \\log C - n \\log l` by least squares over a moving
    window of ``window`` wavenumbers and returns the exponent :math:`n`, so
    that larger values mean a steeper spectrum.

    Parameters
    ----------
    spectrum : xarray.DataArray
        KE spectrum with a ``wavenumber_name`` dimension.  Non-positive values
        are masked out of the fit.
    window : int, optional
        Number of wavenumbers in the fitting window.  Default ``20``,
        following Appendix S3 of Klaver et al. (2020).
    anchor : {"center", "right", "left"}, optional
        Which wavenumber in the window the fitted exponent is assigned to.
        The paper's phrasing -- steepening in a window being "indicative of
        steepening at the largest wavenumber in the range" -- is ambiguous
        about the anchoring of the plotted :math:`n(l)` curve.  ``"center"``
        (default) is the conventional choice; ``"right"`` is the literal
        reading.  The two shift the diagnosed wavenumber by roughly
        ``window / 2``: material at :math:`l \\sim 35`, minor at
        :math:`l \\sim 110`.  Report which convention was used.
    wavenumber_name : str, optional
        Name of the wavenumber dimension.

    Returns
    -------
    xarray.DataArray
        Exponent :math:`n` on the same wavenumber coordinate, ``NaN`` where
        the window is incomplete or degenerate.

    Examples
    --------
    A pure power law returns its own exponent:

    >>> ell = np.arange(1, 200)
    >>> spec = xr.DataArray(
    ...     ell.astype(float) ** -3.0, coords={"wavenumber": ell}, dims="wavenumber"
    ... )
    >>> bool(abs(float(fit_spectral_slope(spec).sel(wavenumber=100)) - 3.0) < 1e-8)
    True
    """
    if window < 3:
        raise ValueError(f"window must be >= 3, got {window}")
    if anchor not in _ANCHORS:
        raise ValueError(f"anchor must be one of {sorted(_ANCHORS)}, got {anchor!r}")
    offset = _ANCHORS[anchor](window)

    ell = np.asarray(spectrum[wavenumber_name].values, dtype=float)
    log_l = np.log(ell)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_e = np.log(np.asarray(spectrum.values, dtype=float))

    slope = np.full(ell.size, np.nan)
    min_points = window // 2
    for start in range(ell.size - window + 1):
        x, y = log_l[start : start + window], log_e[start : start + window]
        good = np.isfinite(x) & np.isfinite(y)
        if good.sum() >= min_points:
            slope[start + offset] = -np.polyfit(x[good], y[good], 1)[0]

    out = xr.DataArray(
        slope,
        coords={wavenumber_name: spectrum[wavenumber_name]},
        dims=wavenumber_name,
        name="spectral_slope",
    )
    if "eddy_scale" in spectrum.coords:
        out = out.assign_coords(eddy_scale=spectrum["eddy_scale"])
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
    wavenumber_name: str = "wavenumber",
) -> dict[str, Any]:
    """Locate the wavenumber at which the spectral slope starts steepening.

    Implements the detection criterion of Klaver et al. (2020): steepening is
    declared at the smallest :math:`l \\ge` ``min_wavenumber`` such that the
    exponent has grown by ``steepening_factor`` by the time the wavenumber has
    grown by ``wavenumber_ratio``, and stays at or above the reference line
    throughout -- the paper's "progressive deterioration" requirement.

    Parameters
    ----------
    slope : xarray.DataArray
        Output of `fit_spectral_slope`.
    steepening_factor : float, optional
        Fractional increase of the exponent required over a
        ``wavenumber_ratio`` increase in wavenumber.  Default ``0.25``,
        explicitly flagged as ad hoc by the authors.
    wavenumber_ratio : float, optional
        Wavenumber ratio over which the increase must occur.  Default ``2.0``.
    min_wavenumber : int, optional
        Smallest wavenumber at which detection is attempted.  Default ``32``
        (:math:`\\Delta S \\approx 625` km).  A model showing no steepening by
        this point gets an *upper limit*, not a value -- the case of
        HadGEM3-GC31-LM and CNRM-CM6-0 in the paper.
    max_wavenumber : int or None, optional
        Largest candidate wavenumber.  Default (``None``) uses
        ``max(l) / wavenumber_ratio``, keeping the comparison point inside the
        fitted range.
    wavenumber_name : str, optional
        Name of the wavenumber dimension.

    Returns
    -------
    dict
        Keys ``wavenumber`` (``None`` if no steepening is found),
        ``slope_at_detection``, ``is_upper_limit`` (``True`` when steepening
        is already present at the first candidate wavenumber, so the value
        bounds rather than resolves the answer) and ``criterion``.

    Examples
    --------
    A clean :math:`l^{-3}` power law rolling off past :math:`l = 60` is
    detected at :math:`l = 53`.  Detection precedes the roll-off because a
    centred 20-wavenumber window centred on 53 already reaches :math:`l = 63`;
    that lead is inherent to any windowed slope estimate and applies equally
    to the published values.

    >>> ell = np.arange(1, 400)
    >>> e = ell.astype(float) ** -3.0 * np.exp(-np.maximum(ell - 60, 0) / 80)
    >>> spec = xr.DataArray(e, coords={"wavenumber": ell}, dims="wavenumber")
    >>> detect_steepening(fit_spectral_slope(spec))["wavenumber"]
    53.0
    """
    if steepening_factor <= 0:
        raise ValueError("steepening_factor must be positive")
    if wavenumber_ratio <= 1:
        raise ValueError("wavenumber_ratio must be > 1")

    ell = np.asarray(slope[wavenumber_name].values, dtype=float)
    n = np.asarray(slope.values, dtype=float)
    if max_wavenumber is None:
        max_wavenumber = ell.max() / wavenumber_ratio

    result: dict[str, Any] = {
        "wavenumber": None,
        "slope_at_detection": None,
        "is_upper_limit": False,
        "criterion": {
            "steepening_factor": steepening_factor,
            "wavenumber_ratio": wavenumber_ratio,
            "min_wavenumber": min_wavenumber,
        },
    }

    mask = (ell >= min_wavenumber) & (ell <= max_wavenumber) & np.isfinite(n)
    candidates = np.flatnonzero(mask)
    for i in candidates:
        l0, n0 = ell[i], n[i]
        if n0 <= 0:
            continue
        ahead = np.where((ell > l0) & (ell <= wavenumber_ratio * l0))[0]
        ahead = ahead[np.isfinite(n[ahead])]
        if ahead.size == 0:
            continue

        reference = reference_steepening_line(
            ell[ahead], l0, n0, steepening_factor, wavenumber_ratio
        )
        if np.all(n[ahead] >= reference):
            result["wavenumber"] = float(l0)
            result["slope_at_detection"] = float(n0)
            result["is_upper_limit"] = bool(i == candidates[0])
            break

    return result


def reference_steepening_line(
    ell: np.ndarray,
    l0: float,
    n0: float,
    steepening_factor: float = 0.25,
    wavenumber_ratio: float = 2.0,
) -> np.ndarray:
    """Reference line for the steepening criterion.

    These are the "straight skewed lines" of Figure 1 in Klaver et al. (2020):
    straight on log-wavenumber / linear-exponent axes, anchored at
    :math:`(l_0, n_0)`, rising by ``steepening_factor`` per
    ``wavenumber_ratio`` in wavenumber,

    .. math::
        n_{ref}(l) = n_0\\left(1 + f\\,\\frac{\\log(l/l_0)}{\\log r}\\right).

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
    return n0 * (1.0 + steepening_factor * np.log(ell / l0) / np.log(wavenumber_ratio))
