#!/usr/bin/env python
"""Global kinetic energy spectra of the rotational and divergent wind.

Implements Equations (1)-(3) of Klaver et al. (2020):

.. math::
    E_{l,m} = \\frac{a^2}{2 l (l+1)}
              \\left( |\\zeta_{l,m}|^2 + |d_{l,m}|^2 \\right)
    \\qquad
    E_l = \\sum_{m=-l}^{l} E_{l,m}
    \\qquad
    \\Delta S = \\pi \\sqrt{\\frac{a^2}{l(l+1)}} \\approx \\frac{20000\\,\\mathrm{km}}{l}

The rotational (vorticity) and divergent (divergence) parts are kept separate
throughout, because Klaver et al. show that the divergent spectrum steepens
earlier and more sharply and is therefore the more sensitive indicator of a
model's effective resolution.

The spherical-harmonic transform is done here in NumPy rather than through an
optional Fortran library, so the metric has no dependency outside the standard
PMP environment.  Vorticity and divergence coefficients are formed *exactly*
in spectral space, from the coefficients of :math:`U = u\\cos\\phi` and
:math:`V = v\\cos\\phi`,

.. math::
    \\zeta_{l,m} = \\frac{1}{a}\\left( i m\\, V^{c}_{l,m} + U^{H}_{l,m} \\right),
    \\qquad
    d_{l,m} = \\frac{1}{a}\\left( i m\\, U^{c}_{l,m} - V^{H}_{l,m} \\right),

where the two projections use :math:`\\bar{P}_{l,m}` and
:math:`\\bar{H}_{l,m} = (1-\\mu^2)\\,\\mathrm{d}\\bar{P}_{l,m}/\\mathrm{d}\\mu`
(Bourke, 1972).  This matters: forming vorticity and divergence by finite
differences on the grid damps precisely the high wavenumbers this diagnostic
inspects, and would manufacture the steepening it is meant to detect.

References
----------
Bourke, W. (1972). An efficient, one-level, primitive-equation spectral model.
    *Monthly Weather Review*, 100, 683-689.
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import xarray as xr

from pcmdi_metrics.io import get_latitude_key, get_longitude_key, get_time_key

__all__ = [
    "EARTH_RADIUS",
    "compute_ke_spectra",
    "compute_ke_spectra_timeseries",
    "eddy_scale",
    "select_pressure_level",
    "sum_over_m",
    "vrtdiv_spectral_coefficients",
    "wavenumber_from_eddy_scale",
]

#: Radius of the Earth in metres, matching the value used by Klaver et al.
EARTH_RADIUS = 6.371e6

#: Coordinate ``units`` strings recognised as pascals and as hectopascals.
_PA_UNITS = ("pa", "pascal", "pascals")
_HPA_UNITS = ("hpa", "mb", "mbar", "millibar", "millibars", "hectopascal")


def eddy_scale(
    ell: np.ndarray | float,
    rsphere: float = EARTH_RADIUS,
    formula: Literal["exact", "approx"] = "exact",
) -> np.ndarray:
    """Half-wavelength (eddy scale) corresponding to a total wavenumber.

    Equation (3) of Klaver et al. (2020),

    .. math::
        \\Delta S = \\pi \\sqrt{\\frac{a^2}{l(l+1)}}
                  \\approx \\frac{20000\\,\\mathrm{km}}{l}.

    Parameters
    ----------
    ell : array_like or float
        Total wavenumber :math:`l`.  ``l = 0`` maps to ``inf``.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.
    formula : {"exact", "approx"}, optional
        ``"exact"`` (default) evaluates the left-hand side of Equation (3).
        ``"approx"`` uses the ``20000 / l`` shorthand that the published
        Table 1 values were rounded from; use it when comparing directly
        against the paper's numbers.  The two differ by about 1% at
        :math:`l = 50` and less above that.

    Returns
    -------
    ndarray
        Eddy scale :math:`\\Delta S` in kilometres.

    Examples
    --------
    Reproduces the ``L_eff`` column of Table 1 to within that rounding:

    >>> float(np.round(eddy_scale(108), 0))  # Table 1: 185 km
    184.0
    >>> float(np.round(eddy_scale(55, formula="approx"), 0))  # Table 1: 364 km
    364.0
    """
    ell = np.asarray(ell, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        if formula == "approx":
            scale = 20000.0 / ell
        elif formula == "exact":
            scale = np.pi * np.sqrt(rsphere**2 / (ell * (ell + 1.0))) / 1000.0
        else:
            raise ValueError(f"formula must be 'exact' or 'approx', got {formula!r}")
    return np.where(ell > 0, scale, np.inf)


def wavenumber_from_eddy_scale(scale_km: float, rsphere: float = EARTH_RADIUS) -> float:
    """Invert `eddy_scale`: total wavenumber for a given half-wavelength.

    Parameters
    ----------
    scale_km : float
        Eddy scale in kilometres.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.

    Returns
    -------
    float
        Total wavenumber :math:`l`, not rounded to an integer.

    Examples
    --------
    >>> int(round(wavenumber_from_eddy_scale(625.0)))
    32
    """
    ratio = (np.pi * rsphere / 1000.0 / scale_km) ** 2
    return float((-1.0 + np.sqrt(1.0 + 4.0 * ratio)) / 2.0)


def _legendre(m: int, ntrunc: int, mu: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Normalised Legendre functions and their derivative combination.

    Returns :math:`\\bar{P}_{l,m}(\\mu)` and
    :math:`\\bar{H}_{l,m} = (1-\\mu^2)\\,\\mathrm{d}\\bar{P}_{l,m}/\\mathrm{d}\\mu`
    for ``l = m ... ntrunc``, using the standard stable three-term recursion.
    The normalisation is :math:`\\tfrac{1}{2}\\int_{-1}^{1}\\bar{P}_{l,m}^2
    \\,\\mathrm{d}\\mu = 1`, i.e. :math:`\\bar{P}_{0,0} = 1`.

    Parameters
    ----------
    m : int
        Zonal wavenumber (order).
    ntrunc : int
        Maximum total wavenumber (degree).
    mu : ndarray
        ``sin(latitude)``, shape ``(nlat,)``.

    Returns
    -------
    p, h : ndarray
        Both of shape ``(ntrunc + 1 - m, nlat)``.

    Examples
    --------
    >>> p, h = _legendre(0, 2, np.linspace(-1, 1, 5))
    >>> p.shape
    (3, 5)
    >>> bool(np.allclose(p[0], 1.0)) and bool(np.allclose(h[0], 0.0))
    True
    """
    mu = np.asarray(mu, dtype=float)
    nlat = mu.size
    # One extra degree is needed for the H recursion at l = ntrunc.
    p = np.zeros((ntrunc + 2 - m, nlat))
    sin_theta = np.sqrt(np.clip(1.0 - mu**2, 0.0, None))

    pmm = np.ones(nlat)
    for i in range(1, m + 1):
        pmm = pmm * np.sqrt((2.0 * i + 1.0) / (2.0 * i)) * sin_theta
    p[0] = pmm
    if p.shape[0] > 1:
        p[1] = np.sqrt(2.0 * m + 3.0) * mu * pmm
    for degree in range(m + 2, ntrunc + 2):
        a = np.sqrt((4.0 * degree**2 - 1.0) / (degree**2 - m**2))
        b = np.sqrt(((degree - 1.0) ** 2 - m**2) / (4.0 * (degree - 1.0) ** 2 - 1.0))
        p[degree - m] = a * (mu * p[degree - 1 - m] - b * p[degree - 2 - m])

    # (1 - mu^2) dP/dmu = -l * eps(l+1,m) * P_{l+1,m} + (l+1) * eps(l,m) * P_{l-1,m}
    ell = np.arange(m, ntrunc + 1, dtype=float)
    h = np.zeros((ntrunc + 1 - m, nlat))
    h -= (ell * _epsilon(ell + 1.0, m))[:, None] * p[1 : ntrunc + 2 - m]
    h[1:] += ((ell[1:] + 1.0) * _epsilon(ell[1:], m))[:, None] * p[: ntrunc - m]
    return p[: ntrunc + 1 - m], h


def _epsilon(ell: np.ndarray, m: int) -> np.ndarray:
    """Recursion coefficient :math:`\\sqrt{(l^2-m^2)/(4l^2-1)}`, zero for ``l <= |m|``."""
    ell = np.asarray(ell, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        value = np.sqrt(np.abs(ell**2 - m**2) / (4.0 * ell**2 - 1.0))
    return np.where(ell > abs(m), value, 0.0)


def _quadrature_weights(lat: np.ndarray, gridtype: str) -> np.ndarray:
    """Latitude quadrature weights normalised to sum to 2.

    ``cos(phi) dphi`` on a regular grid, Gauss-Legendre weights on a Gaussian
    grid.
    """
    if gridtype == "gaussian":
        _, weights = np.polynomial.legendre.leggauss(lat.size)
        mu = np.sin(np.deg2rad(lat))
        return weights[np.argsort(np.argsort(mu))]
    weights = np.cos(np.deg2rad(lat)) * np.abs(np.gradient(np.deg2rad(lat)))
    return weights * (2.0 / weights.sum())


def vrtdiv_spectral_coefficients(
    u: np.ndarray,
    v: np.ndarray,
    lat: np.ndarray,
    ntrunc: int | None = None,
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    rsphere: float = EARTH_RADIUS,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Spherical-harmonic coefficients of vorticity and divergence.

    Parameters
    ----------
    u, v : ndarray
        Zonal and meridional wind on a global lat-lon grid, shape
        ``(nlat, nlon)``, free of missing values.  Longitudes must be evenly
        spaced and span the globe.
    lat : ndarray
        Latitudes in degrees north, shape ``(nlat,)``, monotonic in either
        direction.
    ntrunc : int or None, optional
        Triangular truncation wavenumber.  Default (``None``) is ``nlat - 1``.
        Accuracy degrades within roughly 10% of the truncation limit, so
        detections above ``0.85 * ntrunc`` should be treated with caution.
    gridtype : {"auto", "regular", "gaussian"}, optional
        Latitude grid type.  ``"auto"`` (default) calls a grid regular when
        the latitudes are evenly spaced and Gaussian otherwise.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.

    Returns
    -------
    ell : ndarray
        Total wavenumbers ``[0, 1, ..., ntrunc]``, shape ``(ntrunc + 1,)``.
    vrt, div : ndarray
        Complex vorticity and divergence coefficients in s\\ :sup:`-1`, shape
        ``(ntrunc + 1, ntrunc + 1)`` indexed ``[l, m]``.  Only ``m >= 0`` is
        stored; entries with ``m > l`` are zero.  Use `sum_over_m` to obtain
        the power per total wavenumber with the correct folding of the
        negative-``m`` half.

    Notes
    -----
    Rows within a grid cell of the poles are dropped from the quadrature.
    They carry negligible area weight, and the :math:`1/\\cos^2\\phi` factor in
    the projection is singular there.
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    lat = np.asarray(lat, dtype=float)

    if u.shape != v.shape:
        raise ValueError(f"u and v must have the same shape, got {u.shape}, {v.shape}")
    if u.ndim != 2:
        raise ValueError(f"u and v must be 2-D (nlat, nlon), got ndim={u.ndim}")
    if u.shape[0] != lat.size:
        raise ValueError(f"u has {u.shape[0]} latitudes but lat has {lat.size}")
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        raise ValueError("u and v must not contain NaN/inf; fill missing values first")

    nlat, nlon = u.shape
    if ntrunc is None:
        ntrunc = nlat - 1
    if gridtype == "auto":
        dlat = np.diff(lat)
        gridtype = "regular" if np.allclose(dlat, dlat[0], rtol=1e-4) else "gaussian"

    mu = np.sin(np.deg2rad(lat))
    cosphi = np.cos(np.deg2rad(lat))
    weights = _quadrature_weights(lat, gridtype)

    # Project (u cos phi, v cos phi) with weight 1/(1 - mu^2); poles contribute
    # no area and would divide by zero.
    cos2 = cosphi**2
    weights = np.where(cos2 > 1e-12, weights / np.where(cos2 > 1e-12, cos2, 1.0), 0.0)

    u_fourier = np.fft.rfft(u * cosphi[:, None], axis=1) / nlon
    v_fourier = np.fft.rfft(v * cosphi[:, None], axis=1) / nlon

    vrt = np.zeros((ntrunc + 1, ntrunc + 1), dtype=complex)
    div = np.zeros_like(vrt)
    for m in range(min(ntrunc + 1, u_fourier.shape[1])):
        p, h = _legendre(m, ntrunc, mu)
        um = u_fourier[:, m] * weights
        vm = v_fourier[:, m] * weights
        vrt[m:, m] = (
            1j * m * (0.5 * (p * vm).sum(1)) + 0.5 * (h * um).sum(1)
        ) / rsphere
        div[m:, m] = (
            1j * m * (0.5 * (p * um).sum(1)) - 0.5 * (h * vm).sum(1)
        ) / rsphere

    return np.arange(ntrunc + 1), vrt, div


def sum_over_m(coeffs: np.ndarray) -> np.ndarray:
    """Sum :math:`|c_{l,m}|^2` over all :math:`m` from :math:`-l` to :math:`l`.

    Implements the :math:`m`-summation of Equation (2) of Klaver et al. (2020)
    for real fields, where only :math:`m \\ge 0` is stored and the
    negative-:math:`m` half contributes an identical amount.

    Parameters
    ----------
    coeffs : ndarray
        Complex coefficients of shape ``(..., nl, nm)`` indexed ``[l, m]``.

    Returns
    -------
    ndarray
        Real power per total wavenumber, shape ``(..., nl)``.

    Examples
    --------
    >>> c = np.zeros((3, 3), dtype=complex)
    >>> c[2, 0] = c[2, 1] = 1.0
    >>> sum_over_m(c)
    array([0., 0., 3.])
    """
    power = np.abs(coeffs) ** 2
    return power[..., 0] + 2.0 * power[..., 1:].sum(axis=-1)


def select_pressure_level(
    ds: xr.Dataset,
    level_hpa: float,
    plev_name: str | None = None,
    rtol: float = 0.01,
) -> xr.Dataset:
    """Select one pressure level, in hPa, whatever the coordinate's own units.

    The vertical coordinate's ``units`` attribute is used when present; when
    it is missing the units are inferred from the magnitude of the
    coordinate, so that both CMIP-style Pa axes and hPa axes work without the
    caller having to say which is which.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset with a vertical coordinate.
    level_hpa : float
        Requested pressure level in hPa.
    plev_name : str or None, optional
        Name of the vertical coordinate.  Default (``None``) resolves it from
        the dataset's own axis metadata.
    rtol : float, optional
        Relative tolerance on the match.  Default ``0.01`` (1%).

    Returns
    -------
    xarray.Dataset
        ``ds`` with the vertical dimension selected out.

    Raises
    ------
    ValueError
        If no level lies within ``rtol`` of the request.  Silently returning
        the nearest level is how a 500 hPa spectrum ends up labelled 250 hPa.

    Examples
    --------
    >>> ds = xr.Dataset(coords={"plev": ("plev", [25000.0, 50000.0])})
    >>> ds["plev"].attrs["units"] = "Pa"
    >>> float(select_pressure_level(ds, 250.0)["plev"])
    25000.0
    """
    if plev_name is None:
        plev_name = _vertical_key(ds)

    coord = ds[plev_name]
    units = str(coord.attrs.get("units", "")).strip().lower()
    if units in _PA_UNITS:
        scale = 100.0
    elif units in _HPA_UNITS:
        scale = 1.0
    else:
        # No usable units attribute: pressures above 2000 can only be pascals.
        scale = 100.0 if float(np.max(np.abs(coord.values))) > 2000.0 else 1.0

    target = level_hpa * scale
    selected = ds.sel({plev_name: target}, method="nearest")
    found = float(selected[plev_name])
    if abs(found - target) > rtol * abs(target):
        raise ValueError(
            f"No level within {rtol:.0%} of {level_hpa} hPa on coordinate "
            f"{plev_name!r}; nearest is {found / scale:g} hPa"
        )
    return selected


#: Vertical coordinate names to fall back on when axis metadata is absent.
_PLEV_NAMES = ("plev", "level", "lev", "pressure", "isobaric", "pfull", "p")


def _vertical_key(ds: xr.Dataset) -> str:
    """Name of the vertical coordinate of ``ds``.

    Uses the dataset's CF axis metadata when available, and falls back to a
    short list of conventional names, so that files without a complete set of
    axis attributes still work.
    """
    try:
        import xcdat as xc

        return str(xc.get_dim_keys(ds, "Z"))
    except Exception:
        pass
    for name in ds.dims:
        if str(name).lower() in _PLEV_NAMES:
            return str(name)
    raise KeyError(
        "Could not identify a vertical coordinate; pass plev_name explicitly"
    )


def compute_ke_spectra(
    ds: xr.Dataset,
    uvar: str = "ua",
    vvar: str = "va",
    ntrunc: int | None = None,
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    rsphere: float = EARTH_RADIUS,
) -> xr.Dataset:
    """Rotational and divergent KE spectra for a single 2-D wind field.

    Pure computation: no file I/O, no plotting.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset holding ``uvar`` and ``vvar`` as 2-D fields on a global
        latitude-longitude grid.  Any time or vertical dimension must already
        be selected out; see `compute_ke_spectra_timeseries` for the wrapper
        that loops over time.  Latitude and longitude are found from the
        dataset's own axis metadata, so non-standard coordinate names work.
    uvar, vvar : str, optional
        Names of the zonal and meridional wind variables.  Defaults ``"ua"``
        and ``"va"`` (CMIP conventions).
    ntrunc : int or None, optional
        Triangular truncation wavenumber.  Default (``None``) is ``nlat - 1``.
    gridtype : {"auto", "regular", "gaussian"}, optional
        Latitude grid type.  Default ``"auto"``.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.

    Returns
    -------
    xarray.Dataset
        Dataset on a ``wavenumber`` dimension with data variables ``ke_rot``,
        ``ke_div`` and ``ke_total`` in m\\ :sup:`2` s\\ :sup:`-2`, and an
        ``eddy_scale`` coordinate in km.  ``l = 0`` is dropped, Equation (1)
        being singular there.

    Notes
    -----
    The spectrum is *global*, deliberately: the latitudinal dependence of grid
    spacing differs between models, so a limited-area spectrum would not be
    comparable across an ensemble.  Klaver et al. also caution that a globally
    integrated quantity may obscure a phenomenon-dependent effective
    resolution, e.g. midlatitude storms versus equatorial updraughts.

    Examples
    --------
    >>> spec = compute_ke_spectra(ds.isel(time=0))  # doctest: +SKIP
    """
    lat_key = get_latitude_key(ds)
    lon_key = get_longitude_key(ds)
    lat = np.asarray(ds[lat_key].values, dtype=float)

    ell, vrt, div = vrtdiv_spectral_coefficients(
        ds[uvar].transpose(lat_key, lon_key).values,
        ds[vvar].transpose(lat_key, lon_key).values,
        lat,
        ntrunc=ntrunc,
        gridtype=gridtype,
        rsphere=rsphere,
    )

    # Equations (1) and (2).  l = 0 is dropped first: Equation (1) is singular
    # there and the mean flow carries no scale information.
    valid = ell > 0
    ell = ell[valid]
    factor = rsphere**2 / (2.0 * ell * (ell + 1.0))
    ke_rot = factor * sum_over_m(vrt)[valid]
    ke_div = factor * sum_over_m(div)[valid]

    out = xr.Dataset(
        data_vars={
            "ke_rot": ("wavenumber", ke_rot),
            "ke_div": ("wavenumber", ke_div),
            "ke_total": ("wavenumber", ke_rot + ke_div),
        },
        coords={
            "wavenumber": ("wavenumber", ell),
            "eddy_scale": ("wavenumber", eddy_scale(ell, rsphere)),
        },
    )
    out["ke_rot"].attrs = {
        "long_name": "Rotational kinetic energy spectrum",
        "units": "m2 s-2",
        "description": "Klaver et al. (2020) Eq. 1-2, vorticity term",
    }
    out["ke_div"].attrs = {
        "long_name": "Divergent kinetic energy spectrum",
        "units": "m2 s-2",
        "description": "Klaver et al. (2020) Eq. 1-2, divergence term",
    }
    out["ke_total"].attrs = {
        "long_name": "Total kinetic energy spectrum",
        "units": "m2 s-2",
    }
    out["eddy_scale"].attrs = {
        "long_name": "Eddy scale (half wavelength)",
        "units": "km",
        "description": "Klaver et al. (2020) Eq. 3",
    }
    out.attrs = {
        "ntrunc": int(ell.max()),
        "rsphere_m": rsphere,
        "reference": "Klaver et al. (2020), doi:10.1002/asl.952",
    }
    return out


def compute_ke_spectra_timeseries(
    ds: xr.Dataset,
    uvar: str = "ua",
    vvar: str = "va",
    level_hpa: float | None = None,
    time_mean: bool = True,
    plev_name: str | None = None,
    **kwargs: Any,
) -> xr.Dataset:
    """KE spectra for every time step at one pressure level, optionally averaged.

    Klaver et al. use 6-hourly winds at 250 and 500 hPa over four months of
    2014 and analyse the monthly mean spectra.  They note that spectral slopes
    vary little between months, so the diagnosed effective resolution behaves
    as a time-invariant model property.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset with ``uvar`` and ``vvar`` on ``(time, [plev,] lat, lon)``.
    uvar, vvar : str, optional
        Wind variable names.
    level_hpa : float or None, optional
        Pressure level to select, **in hPa** regardless of the coordinate's
        own units; see `select_pressure_level`.  ``None`` (default) assumes
        ``ds`` is already on a single level.
    time_mean : bool, optional
        If ``True`` (default), average the spectra over time *after* computing
        them.  Averaging spectra rather than fields is what the paper does;
        averaging the fields first would destroy the transient energy the
        diagnostic lives on.
    plev_name : str or None, optional
        Vertical coordinate name.  Default resolves it from ``ds``.
    **kwargs
        Forwarded to `compute_ke_spectra` (``ntrunc``, ``gridtype``,
        ``rsphere``).

    Returns
    -------
    xarray.Dataset
        As `compute_ke_spectra`, with a leading ``time`` dimension when
        ``time_mean`` is ``False``.

    Examples
    --------
    >>> spec250 = compute_ke_spectra_timeseries(ds, level_hpa=250.0)  # doctest: +SKIP
    """
    if level_hpa is not None:
        ds = select_pressure_level(ds, level_hpa, plev_name=plev_name)

    # Already a single 2-D field: nothing to loop over, and asking for a time
    # axis that cannot exist would only produce noise.
    if ds[uvar].ndim <= 2:
        return compute_ke_spectra(ds, uvar, vvar, **kwargs)

    try:
        time_key = get_time_key(ds)
    except Exception:
        time_key = None
    if time_key is None or time_key not in ds.dims:
        return compute_ke_spectra(ds, uvar, vvar, **kwargs)

    spectra = [
        compute_ke_spectra(ds.isel({time_key: i}), uvar, vvar, **kwargs)
        for i in range(ds.sizes[time_key])
    ]
    out = xr.concat(spectra, dim=time_key).assign_coords({time_key: ds[time_key]})
    attrs = dict(spectra[0].attrs)

    if time_mean:
        attrs["n_times_averaged"] = out.sizes[time_key]
        out = out.mean(dim=time_key, keep_attrs=True)
    out.attrs = attrs
    return out
