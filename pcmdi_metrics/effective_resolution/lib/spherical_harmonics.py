#!/usr/bin/env python
"""Pluggable spherical-harmonic backends for kinetic energy spectra.

Klaver et al. (2020) build global kinetic energy (KE) spectra from the
spherical-harmonic (SH) coefficients of the vorticity (:math:`\\zeta_{l,m}`)
and divergence (:math:`d_{l,m}`) of the horizontal wind.  This module isolates
that transform behind a single function, `vrtdiv_spectral_coefficients`, so
that the science code in `pcmdi_metrics.effective_resolution.lib.ke_spectra`
never has to know which library performed the transform.

Backends
--------
``"windspharm"`` (default)
    Uses ``spharm`` (pyspharm), the Fortran SPHEREPACK wrapper that
    ``windspharm`` is built on.  Handles regular and Gaussian lat-lon grids
    and is the most widely available option in the climate Python stack.
``"shtns"``
    Uses ``shtns`` (Schaeffer, 2013), the package used by Klaver et al.
    themselves.  Fastest option; less commonly installed.
``"numpy"``
    Dependency-free fallback built on FFT-in-longitude plus Gauss-Legendre
    quadrature in latitude.  Vorticity and divergence are formed with
    spectral differencing in longitude and centred finite differences in
    latitude, which *damps the very wavenumbers the effective-resolution
    diagnostic is looking at*.  Use for testing and for reproducing the
    plumbing, not for publishing effective-resolution numbers.
``"auto"``
    Try ``windspharm`` then ``shtns`` then ``numpy``.

Notes
-----
All backends return **4-pi normalised, real-field** coefficients
:math:`c_{l,m}` for :math:`m \\ge 0`, defined so that

.. math::
    f(\\lambda,\\mu) = \\sum_{l}\\sum_{m=-l}^{l} c_{l,m}\\,
                       \\bar{P}_{l,m}(\\mu)\\,e^{im\\lambda},

with :math:`\\frac{1}{4\\pi}\\oint |f|^2 \\, d\\Omega =
\\sum_l \\left( |c_{l,0}|^2 + 2\\sum_{m>0} |c_{l,m}|^2 \\right)`.
`sum_over_m` applies exactly that :math:`m`-folding, so the normalisation is
consistent across backends.  `parseval_check` is provided to verify a new or
modified backend against the grid-space variance.

References
----------
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
Schaeffer, N. (2013). Efficient spherical harmonic transforms aimed at
    pseudospectral numerical simulations. *Geochemistry, Geophysics,
    Geosystems*, 14, 751-758. https://doi.org/10.1002/ggge.20071
"""

from __future__ import annotations

import warnings
from typing import Any, Literal

import numpy as np

__all__ = [
    "available_backends",
    "resolve_backend",
    "vrtdiv_spectral_coefficients",
    "sum_over_m",
    "normalized_legendre",
    "parseval_check",
]

BackendName = Literal["auto", "windspharm", "shtns", "numpy"]

#: Radius of the Earth in metres, matching the value used by Klaver et al.
EARTH_RADIUS = 6.371e6


# ---------------------------------------------------------------------------
# Backend discovery
# ---------------------------------------------------------------------------


def available_backends() -> list[str]:
    """List the SH backends importable in the current environment.

    Returns
    -------
    list of str
        Subset of ``["windspharm", "shtns", "numpy"]``, in order of
        preference.  ``"numpy"`` is always present.

    Examples
    --------
    >>> available_backends()  # doctest: +SKIP
    ['windspharm', 'numpy']
    """
    found = []
    for name, module in (("windspharm", "spharm"), ("shtns", "shtns")):
        try:
            __import__(module)
        except ImportError:
            continue
        found.append(name)
    found.append("numpy")
    return found


def resolve_backend(backend: BackendName = "auto") -> str:
    """Resolve ``"auto"`` to a concrete backend name and validate the choice.

    Parameters
    ----------
    backend : {"auto", "windspharm", "shtns", "numpy"}, optional
        Requested backend.  Default is ``"auto"``.

    Returns
    -------
    str
        Concrete backend name.

    Raises
    ------
    ValueError
        If ``backend`` is not a recognised name.
    ImportError
        If a specific backend was requested but is not installed.
    """
    valid = {"auto", "windspharm", "shtns", "numpy"}
    if backend not in valid:
        raise ValueError(f"Unknown SH backend {backend!r}; expected one of {sorted(valid)}")

    found = available_backends()
    if backend == "auto":
        chosen = found[0]
        if chosen == "numpy":
            warnings.warn(
                "Neither 'spharm' (pyspharm/windspharm) nor 'shtns' is installed; "
                "falling back to the 'numpy' backend. Its finite-difference "
                "vorticity/divergence damps high wavenumbers and will bias the "
                "diagnosed effective resolution. Install pyspharm or shtns for "
                "production use.",
                UserWarning,
                stacklevel=2,
            )
        return chosen

    if backend not in found:
        raise ImportError(
            f"SH backend {backend!r} requested but not importable. "
            f"Available backends: {found}"
        )
    return backend


# ---------------------------------------------------------------------------
# Public transform API
# ---------------------------------------------------------------------------


def vrtdiv_spectral_coefficients(
    u: np.ndarray,
    v: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    ntrunc: int | None = None,
    backend: BackendName = "auto",
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    rsphere: float = EARTH_RADIUS,
    backend_kwargs: dict[str, Any] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Spherical-harmonic coefficients of vorticity and divergence.

    Parameters
    ----------
    u, v : ndarray
        Zonal and meridional wind on a global lat-lon grid, shape
        ``(nlat, nlon)``.  Must be free of missing values.
    lat : ndarray
        Latitudes in degrees north, shape ``(nlat,)``.  May be increasing or
        decreasing; the backend handles the ordering.
    lon : ndarray
        Longitudes in degrees east, shape ``(nlon,)``, monotonically
        increasing and evenly spaced.
    ntrunc : int or None, optional
        Triangular truncation wavenumber.  Default (``None``) is
        ``nlat - 1``.
    backend : {"auto", "windspharm", "shtns", "numpy"}, optional
        SH transform backend.  Default is ``"auto"``.
    gridtype : {"auto", "regular", "gaussian"}, optional
        Latitude grid type.  ``"auto"`` inspects ``lat`` for even spacing and
        picks ``"regular"`` if evenly spaced, ``"gaussian"`` otherwise.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.
    backend_kwargs : dict or None, optional
        Extra keyword arguments forwarded to the backend constructor.

    Returns
    -------
    ell : ndarray
        Total wavenumbers, shape ``(ntrunc + 1,)``, ``[0, 1, ..., ntrunc]``.
    vrt : ndarray
        Complex vorticity coefficients, shape ``(ntrunc + 1, ntrunc + 1)``,
        indexed ``[l, m]`` for ``m <= l``; entries with ``m > l`` are zero.
        Units s\\ :sup:`-1`.
    div : ndarray
        Complex divergence coefficients, same shape and units as ``vrt``.

    Notes
    -----
    The returned arrays hold only ``m >= 0``.  Use `sum_over_m` to obtain the
    :math:`m`-summed power with the correct factor-of-two folding for the
    negative-:math:`m` half of the spectrum.

    Examples
    --------
    >>> ell, vrt, div = vrtdiv_spectral_coefficients(  # doctest: +SKIP
    ...     u, v, lat, lon, backend="windspharm"
    ... )
    >>> vrt.shape == (ell.size, ell.size)  # doctest: +SKIP
    True
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)

    if u.shape != v.shape:
        raise ValueError(f"u and v must have the same shape, got {u.shape} and {v.shape}")
    if u.ndim != 2:
        raise ValueError(f"u and v must be 2-D (nlat, nlon), got ndim={u.ndim}")
    if u.shape != (lat.size, lon.size):
        raise ValueError(
            f"u/v shape {u.shape} does not match (lat, lon) = ({lat.size}, {lon.size})"
        )
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        raise ValueError("u and v must not contain NaN/inf; fill missing values first")

    if ntrunc is None:
        ntrunc = lat.size - 1
    if gridtype == "auto":
        dlat = np.diff(lat)
        gridtype = "regular" if np.allclose(dlat, dlat[0], rtol=1e-4) else "gaussian"

    name = resolve_backend(backend)
    kwargs = dict(backend_kwargs or {})

    if name == "windspharm":
        vrt, div = _vrtdiv_windspharm(u, v, lat, lon, ntrunc, gridtype, rsphere, **kwargs)
    elif name == "shtns":
        vrt, div = _vrtdiv_shtns(u, v, lat, lon, ntrunc, gridtype, rsphere, **kwargs)
    else:
        vrt, div = _vrtdiv_numpy(u, v, lat, lon, ntrunc, gridtype, rsphere, **kwargs)

    ell = np.arange(ntrunc + 1)
    return ell, vrt, div


def sum_over_m(coeffs: np.ndarray) -> np.ndarray:
    """Sum :math:`|c_{l,m}|^2` over all :math:`m` from :math:`-l` to :math:`l`.

    Implements the :math:`m`-summation of Equation (2) of Klaver et al. (2020)
    for real fields, where only :math:`m \\ge 0` is stored and the
    negative-:math:`m` half contributes an identical amount.

    Parameters
    ----------
    coeffs : ndarray
        Complex coefficients, shape ``(..., nl, nm)``, indexed ``[l, m]``
        with ``m >= 0``.

    Returns
    -------
    ndarray
        Real power per total wavenumber, shape ``(..., nl)``.

    Examples
    --------
    >>> c = np.zeros((3, 3), dtype=complex)
    >>> c[2, 0] = 1.0
    >>> c[2, 1] = 1.0
    >>> sum_over_m(c)
    array([0., 0., 3.])
    """
    power = np.abs(coeffs) ** 2
    return power[..., 0] + 2.0 * power[..., 1:].sum(axis=-1)


# ---------------------------------------------------------------------------
# Backend: windspharm / pyspharm
# ---------------------------------------------------------------------------


def _vrtdiv_windspharm(
    u: np.ndarray,
    v: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    ntrunc: int,
    gridtype: str,
    rsphere: float,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """Vorticity/divergence coefficients via ``spharm`` (SPHEREPACK).

    ``spharm`` expects latitude ordered north-to-south and returns triangular
    packed coefficients; this helper reorders the input and unpacks the result
    into the dense ``[l, m]`` layout used throughout this module.
    """
    import spharm

    nlat, nlon = u.shape
    flip = lat[0] < lat[-1]  # spharm wants north-to-south
    if flip:
        u = u[::-1, :]
        v = v[::-1, :]

    sht = spharm.Spharmt(nlon, nlat, rsphere=rsphere, gridtype=gridtype, **kwargs)
    vrtspec, divspec = sht.getvrtdivspec(u, v, ntrunc=ntrunc)

    return (
        _unpack_triangular(vrtspec, ntrunc),
        _unpack_triangular(divspec, ntrunc),
    )


def _unpack_triangular(spec: np.ndarray, ntrunc: int) -> np.ndarray:
    """Unpack SPHEREPACK triangular storage into a dense ``[l, m]`` array.

    ``spharm`` stores coefficients in the order ``(m, l)`` with ``l >= m``,
    running ``m`` outermost.  This routine reverses that packing and applies
    the ``sqrt(2)`` factor that converts SPHEREPACK's ``2*sqrt(2)``-style
    convention to the 4-pi normalisation documented at module level.

    Parameters
    ----------
    spec : ndarray
        Packed complex coefficients, shape ``((ntrunc+1)*(ntrunc+2)/2,)``.
    ntrunc : int
        Triangular truncation wavenumber.

    Returns
    -------
    ndarray
        Dense complex array of shape ``(ntrunc + 1, ntrunc + 1)``.

    Notes
    -----
    The scaling constant is checked, not assumed: call `parseval_check` after
    changing anything here.  SPHEREPACK conventions have historically shifted
    between releases.
    """
    spec = np.asarray(spec).ravel()
    dense = np.zeros((ntrunc + 1, ntrunc + 1), dtype=complex)
    idx = 0
    for m in range(ntrunc + 1):
        for ell in range(m, ntrunc + 1):
            dense[ell, m] = spec[idx]
            idx += 1
    # SPHEREPACK convention -> 4-pi normalised coefficients.
    return dense / np.sqrt(2.0)


# ---------------------------------------------------------------------------
# Backend: SHTns
# ---------------------------------------------------------------------------


def _vrtdiv_shtns(
    u: np.ndarray,
    v: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    ntrunc: int,
    gridtype: str,
    rsphere: float,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """Vorticity/divergence coefficients via ``shtns`` (Schaeffer, 2013).

    This is the backend used by Klaver et al. (2020).  ``shtns`` performs the
    vector (spheroidal/toroidal) analysis directly; vorticity and divergence
    follow from the toroidal and spheroidal coefficients as
    :math:`\\zeta_{l,m} = l(l+1)\\,T_{l,m}/a` and
    :math:`d_{l,m} = -l(l+1)\\,S_{l,m}/a`.
    """
    import shtns

    nlat, nlon = u.shape
    sh = shtns.sht(ntrunc, ntrunc, 1, shtns.sht_orthonormal, **kwargs)
    sh.set_grid(nlat, nlon, shtns.sht_reg_fast if gridtype == "regular" else shtns.sht_quick_init)

    if lat[0] < lat[-1]:
        u = u[::-1, :]
        v = v[::-1, :]

    slm = np.zeros(sh.nlm, dtype=complex)  # spheroidal (divergent) part
    tlm = np.zeros(sh.nlm, dtype=complex)  # toroidal (rotational) part
    # shtns' spat_to_SHsphtor takes (theta, phi) components: v_theta = -v
    sh.spat_to_SHsphtor(np.ascontiguousarray(-v), np.ascontiguousarray(u), slm, tlm)

    dense_s = _unpack_shtns(slm, sh, ntrunc)
    dense_t = _unpack_shtns(tlm, sh, ntrunc)

    ell = np.arange(ntrunc + 1)[:, None]
    lap = ell * (ell + 1) / rsphere
    return lap * dense_t, -lap * dense_s


def _unpack_shtns(coeffs: np.ndarray, sh: Any, ntrunc: int) -> np.ndarray:
    """Unpack ``shtns``' packed ``lm`` storage into a dense ``[l, m]`` array."""
    dense = np.zeros((ntrunc + 1, ntrunc + 1), dtype=complex)
    for m in range(ntrunc + 1):
        for ell in range(m, ntrunc + 1):
            dense[ell, m] = coeffs[sh.idx(ell, m)]
    return dense


# ---------------------------------------------------------------------------
# Backend: numpy fallback
# ---------------------------------------------------------------------------


def _vrtdiv_numpy(
    u: np.ndarray,
    v: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    ntrunc: int,
    gridtype: str,
    rsphere: float,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """Dependency-free vorticity/divergence coefficients.

    Vorticity and divergence are formed in grid space -- spectral (FFT)
    differentiation in longitude, centred finite differences in latitude --
    and then transformed with `scalar_sh_analysis`.

    Warnings
    --------
    Centred differences damp the smallest resolved scales, which is precisely
    where the effective-resolution steepening criterion operates.  Treat this
    backend as a plumbing/test path only.
    """
    nlat, nlon = u.shape
    ascending = lat[0] < lat[-1]
    if not ascending:
        lat = lat[::-1]
        u = u[::-1, :]
        v = v[::-1, :]

    phi = np.deg2rad(lat)[:, None]
    cosphi = np.cos(phi)
    cosphi = np.where(np.abs(cosphi) < 1e-8, 1e-8, cosphi)

    # d/dlambda via FFT (exact for the periodic longitude direction)
    k = np.fft.rfftfreq(nlon, d=1.0 / nlon)
    du_dlam = np.fft.irfft(1j * k * np.fft.rfft(u, axis=1), n=nlon, axis=1)
    dv_dlam = np.fft.irfft(1j * k * np.fft.rfft(v, axis=1), n=nlon, axis=1)

    # d/dphi of (u cos phi), (v cos phi) via centred differences
    ducos_dphi = np.gradient(u * cosphi, phi[:, 0], axis=0)
    dvcos_dphi = np.gradient(v * cosphi, phi[:, 0], axis=0)

    # zeta = (1 / (a cos(phi))) [ dv/dlam - d(u cos phi)/dphi ]
    # delta = (1 / (a cos(phi))) [ du/dlam + d(v cos phi)/dphi ]
    vrt = (dv_dlam - ducos_dphi) / (rsphere * cosphi)
    div = (du_dlam + dvcos_dphi) / (rsphere * cosphi)

    vrt_lm = scalar_sh_analysis(vrt, lat, ntrunc, gridtype=gridtype)
    div_lm = scalar_sh_analysis(div, lat, ntrunc, gridtype=gridtype)
    return vrt_lm, div_lm


def scalar_sh_analysis(
    field: np.ndarray,
    lat: np.ndarray,
    ntrunc: int,
    gridtype: str = "regular",
) -> np.ndarray:
    """Forward spherical-harmonic analysis of a scalar field.

    Longitude is handled by FFT; latitude by quadrature against fully
    normalised associated Legendre functions.

    Parameters
    ----------
    field : ndarray
        Scalar field on the global grid, shape ``(nlat, nlon)``, with latitude
        ascending.
    lat : ndarray
        Ascending latitudes in degrees north, shape ``(nlat,)``.
    ntrunc : int
        Triangular truncation wavenumber.
    gridtype : {"regular", "gaussian"}, optional
        Selects the quadrature weights: ``cos(phi) dphi`` for a regular grid,
        Gauss-Legendre weights for a Gaussian grid.

    Returns
    -------
    ndarray
        Complex coefficients of shape ``(ntrunc + 1, ntrunc + 1)`` indexed
        ``[l, m]`` for ``m >= 0``, 4-pi normalised.

    Examples
    --------
    >>> lat = np.linspace(-89.5, 89.5, 180)
    >>> lon = np.arange(0.0, 360.0, 2.0)
    >>> f = np.broadcast_to(np.sin(np.deg2rad(lat))[:, None], (180, 180))
    >>> c = scalar_sh_analysis(np.array(f), lat, 8)
    >>> bool(abs(c[1, 0].real - 1 / np.sqrt(3)) < 1e-3)
    True
    """
    nlat, nlon = field.shape
    mu = np.sin(np.deg2rad(lat))

    if gridtype == "gaussian":
        _, weights = np.polynomial.legendre.leggauss(nlat)
        weights = weights[np.argsort(np.argsort(mu))]
    else:
        dphi = np.gradient(np.deg2rad(lat))
        weights = np.cos(np.deg2rad(lat)) * dphi
        weights = weights * (2.0 / weights.sum())

    # F_m(mu): mean over longitude of field * exp(-i m lambda)
    fm = np.fft.rfft(field, axis=1) / nlon  # (nlat, nlon//2 + 1)
    nm = min(ntrunc + 1, fm.shape[1])

    coeffs = np.zeros((ntrunc + 1, ntrunc + 1), dtype=complex)
    for m in range(nm):
        pbar = normalized_legendre(m, ntrunc, mu)  # (ntrunc + 1 - m, nlat)
        coeffs[m:, m] = 0.5 * (pbar * (weights * fm[:, m])[None, :]).sum(axis=1)
    return coeffs


def normalized_legendre(m: int, ntrunc: int, mu: np.ndarray) -> np.ndarray:
    """Fully normalised associated Legendre functions for a fixed order.

    Uses the standard stable three-term recursion.  The normalisation is such
    that :math:`\\tfrac{1}{2}\\int_{-1}^{1} \\bar{P}_{l,m}^2 \\, d\\mu = 1`,
    i.e. :math:`\\bar{P}_{0,0} = 1`.

    Parameters
    ----------
    m : int
        Zonal wavenumber (order), ``0 <= m <= ntrunc``.
    ntrunc : int
        Maximum total wavenumber (degree).
    mu : ndarray
        ``sin(latitude)``, shape ``(nlat,)``.

    Returns
    -------
    ndarray
        Array of shape ``(ntrunc + 1 - m, nlat)`` holding
        :math:`\\bar{P}_{l,m}(\\mu)` for ``l = m, m+1, ..., ntrunc``.

    Examples
    --------
    >>> mu = np.linspace(-1, 1, 5)
    >>> p = normalized_legendre(0, 2, mu)
    >>> p.shape
    (3, 5)
    >>> bool(np.allclose(p[0], 1.0))
    True
    """
    mu = np.asarray(mu, dtype=float)
    nlat = mu.size
    out = np.zeros((ntrunc + 1 - m, nlat))
    if m > ntrunc:
        return out

    sin_theta = np.sqrt(np.clip(1.0 - mu**2, 0.0, None))

    # Sectoral term P_{m,m}
    pmm = np.ones(nlat)
    for i in range(1, m + 1):
        pmm = pmm * np.sqrt((2.0 * i + 1.0) / (2.0 * i)) * sin_theta
    out[0] = pmm
    if ntrunc == m:
        return out

    # First off-sectoral term P_{m+1,m}
    pmm1 = np.sqrt(2.0 * m + 3.0) * mu * pmm
    out[1] = pmm1

    for ell in range(m + 2, ntrunc + 1):
        a = np.sqrt((4.0 * ell**2 - 1.0) / (ell**2 - m**2))
        b = np.sqrt(((ell - 1.0) ** 2 - m**2) / (4.0 * (ell - 1.0) ** 2 - 1.0))
        out[ell - m] = a * (mu * out[ell - 1 - m] - b * out[ell - 2 - m])
    return out


# ---------------------------------------------------------------------------
# Verification helper
# ---------------------------------------------------------------------------


def parseval_check(
    field: np.ndarray,
    lat: np.ndarray,
    coeffs: np.ndarray,
    gridtype: str = "regular",
) -> tuple[float, float]:
    """Compare grid-space variance with spectral-space power.

    A backend whose normalisation is correct satisfies

    .. math:: \\frac{1}{4\\pi}\\oint |f|^2 d\\Omega = \\sum_{l,m} |c_{l,m}|^2 .

    Use this whenever a backend is added or a library version changes -- SH
    normalisation conventions differ between packages and releases.

    Parameters
    ----------
    field : ndarray
        Grid-space field, shape ``(nlat, nlon)``.
    lat : ndarray
        Latitudes in degrees north, shape ``(nlat,)``.
    coeffs : ndarray
        Dense ``[l, m]`` coefficients from a backend.
    gridtype : {"regular", "gaussian"}, optional
        Quadrature weight convention.

    Returns
    -------
    grid_variance : float
        Area-weighted mean of ``field ** 2``.
    spectral_power : float
        ``sum_over_m(coeffs).sum()``.

    Examples
    --------
    >>> lat = np.linspace(-89.5, 89.5, 180)
    >>> f = np.broadcast_to(np.sin(np.deg2rad(lat))[:, None], (180, 180)).copy()
    >>> g, s = parseval_check(f, lat, scalar_sh_analysis(f, lat, 60))
    >>> bool(abs(g - s) / g < 1e-3)
    True
    """
    w = np.cos(np.deg2rad(lat))
    grid_variance = float(np.average((field**2).mean(axis=1), weights=w))
    spectral_power = float(sum_over_m(coeffs).sum())
    return grid_variance, spectral_power
