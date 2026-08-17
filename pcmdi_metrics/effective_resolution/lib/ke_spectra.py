#!/usr/bin/env python
"""Global kinetic energy spectra from rotational and divergent wind.

Implements Equations (1)-(3) of Klaver et al. (2020):

.. math::
    E_{l,m} = \\frac{a^2}{2 l (l+1)}
              \\left( |\\zeta_{l,m}|^2 + |d_{l,m}|^2 \\right)
    \\qquad
    E_l = \\sum_{m=-l}^{l} E_{l,m}
    \\qquad
    \\Delta S = \\pi \\sqrt{\\frac{a^2}{l(l+1)}} \\approx \\frac{20000\\,\\mathrm{km}}{l}

The rotational (vorticity-derived) and divergent (divergence-derived) parts
are kept separate throughout, because Klaver et al. show that the divergent
spectrum steepens earlier and more sharply and is therefore the more sensitive
indicator of the effective resolution.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import xarray as xr

from .spherical_harmonics import (
    EARTH_RADIUS,
    resolve_backend,
    sum_over_m,
    vrtdiv_spectral_coefficients,
)

__all__ = [
    "eddy_scale",
    "wavenumber_from_eddy_scale",
    "compute_ke_spectra",
    "compute_ke_spectra_timeseries",
]


def eddy_scale(
    ell: np.ndarray | float,
    rsphere: float = EARTH_RADIUS,
    formula: Literal["exact", "approx"] = "exact",
) -> np.ndarray | float:
    """Half-wavelength (eddy scale) corresponding to a total wavenumber.

    Equation (3) of Klaver et al. (2020),

    .. math::
        \\Delta S = \\pi \\sqrt{\\frac{a^2}{l(l+1)}}
                  \\approx \\frac{\\pi a}{l}
                  \\approx \\frac{20000\\,\\mathrm{km}}{l}.

    Parameters
    ----------
    ell : array_like or float
        Total wavenumber :math:`l`.  ``l = 0`` maps to ``inf``.
    rsphere : float, optional
        Sphere radius in metres.  Default is
        `~pcmdi_metrics.effective_resolution.lib.spherical_harmonics.EARTH_RADIUS`.
    formula : {"exact", "approx"}, optional
        ``"exact"`` (default) evaluates the left-hand side of Equation (3).
        ``"approx"`` uses the ``20000 / l`` shorthand, which is what the
        published Table 1 values were rounded from -- use it when comparing
        directly against the paper's numbers.  The two differ by about 1% at
        ``l = 50`` and less above that.

    Returns
    -------
    ndarray or float
        Eddy scale :math:`\\Delta S` in kilometres.

    Examples
    --------
    Reproduces the ``L_eff`` column of Table 1 to within rounding:

    >>> float(np.round(eddy_scale(108), 0))  # Table 1: 185 km
    184.0
    >>> float(np.round(eddy_scale(55), 0))  # Table 1: 364 km
    361.0
    >>> float(np.round(eddy_scale(55, formula="approx"), 0))
    364.0
    >>> float(np.round(eddy_scale(32), 0))  # the l_min cutoff, ~625 km
    616.0
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


def wavenumber_from_eddy_scale(
    scale_km: float, rsphere: float = EARTH_RADIUS
) -> float:
    """Invert `eddy_scale`: total wavenumber for a given half-wavelength.

    Parameters
    ----------
    scale_km : float
        Eddy scale in kilometres.
    rsphere : float, optional
        Sphere radius in metres.

    Returns
    -------
    float
        Total wavenumber :math:`l` (not rounded to an integer).

    Examples
    --------
    >>> int(round(wavenumber_from_eddy_scale(625.0)))
    32
    """
    ratio = (np.pi * rsphere / 1000.0 / scale_km) ** 2
    return float((-1.0 + np.sqrt(1.0 + 4.0 * ratio)) / 2.0)


def compute_ke_spectra(
    ds: xr.Dataset,
    uvar: str = "ua",
    vvar: str = "va",
    ntrunc: int | None = None,
    backend: Literal["auto", "windspharm", "shtns", "numpy"] = "auto",
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    rsphere: float = EARTH_RADIUS,
    lat_name: str = "lat",
    lon_name: str = "lon",
) -> xr.Dataset:
    """Rotational and divergent KE spectra for a single 2-D wind field.

    Pure computation: no file I/O, no plotting.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset holding ``uvar`` and ``vvar`` as 2-D ``(lat, lon)`` fields on
        a global grid.  Any time or vertical dimension must already be
        selected out; see `compute_ke_spectra_timeseries` for the looping
        wrapper.
    uvar, vvar : str, optional
        Names of the zonal and meridional wind variables.  Defaults are
        ``"ua"`` and ``"va"`` (CMIP conventions).
    ntrunc : int or None, optional
        Triangular truncation wavenumber.  Default (``None``) is
        ``nlat - 1``.  Klaver et al. truncate below the model's own
        truncation, both to save cost and because grid-point-model spectral
        coefficients lose accuracy near the truncation limit.
    backend : {"auto", "windspharm", "shtns", "numpy"}, optional
        Spherical-harmonic backend.  Default is ``"auto"``.
    gridtype : {"auto", "regular", "gaussian"}, optional
        Latitude grid type.  Default is ``"auto"``.
    rsphere : float, optional
        Sphere radius in metres.
    lat_name, lon_name : str, optional
        Coordinate names in ``ds``.

    Returns
    -------
    xarray.Dataset
        Dataset on a ``wavenumber`` dimension with data variables

        - ``ke_rot``: rotational KE spectrum :math:`E_l^{rot}`, m\\ :sup:`2` s\\ :sup:`-2`
        - ``ke_div``: divergent KE spectrum :math:`E_l^{div}`
        - ``ke_total``: their sum

        and coordinate ``eddy_scale`` (km) attached to ``wavenumber``.
        ``l = 0`` is dropped, since Equation (1) is singular there.

    Notes
    -----
    The spectrum is *global*.  Klaver et al. argue this deliberately: the
    latitudinal dependence of grid spacing differs between models, so a
    limited-area spectrum would not be comparable across the ensemble.  They
    also caution that a globally integrated quantity may obscure a
    phenomenon-dependent effective resolution (e.g. midlatitude storms versus
    equatorial updraughts).

    Examples
    --------
    >>> spec = compute_ke_spectra(ds.isel(time=0), "ua", "va")  # doctest: +SKIP
    >>> spec["ke_div"].sel(wavenumber=slice(30, 40))  # doctest: +SKIP
    """
    u = np.asarray(ds[uvar].transpose(lat_name, lon_name).values, dtype=float)
    v = np.asarray(ds[vvar].transpose(lat_name, lon_name).values, dtype=float)
    lat = np.asarray(ds[lat_name].values, dtype=float)
    lon = np.asarray(ds[lon_name].values, dtype=float)

    ell, vrt, div = vrtdiv_spectral_coefficients(
        u,
        v,
        lat,
        lon,
        ntrunc=ntrunc,
        backend=backend,
        gridtype=gridtype,
        rsphere=rsphere,
    )

    # Equations (1) and (2)
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = rsphere**2 / (2.0 * ell * (ell + 1.0))
    ke_rot = factor * sum_over_m(vrt)
    ke_div = factor * sum_over_m(div)

    valid = ell > 0
    ell = ell[valid]
    ke_rot = ke_rot[valid]
    ke_div = ke_div[valid]

    out = xr.Dataset(
        data_vars={
            "ke_rot": ("wavenumber", ke_rot),
            "ke_div": ("wavenumber", ke_div),
            "ke_total": ("wavenumber", ke_rot + ke_div),
        },
        coords={
            "wavenumber": ("wavenumber", ell),
            "eddy_scale": ("wavenumber", np.asarray(eddy_scale(ell, rsphere))),
        },
    )
    out["ke_rot"].attrs = {
        "long_name": "Rotational kinetic energy spectrum",
        "units": "m2 s-2",
        "description": "Klaver et al. (2020) Eq. 1-2, vorticity term only",
    }
    out["ke_div"].attrs = {
        "long_name": "Divergent kinetic energy spectrum",
        "units": "m2 s-2",
        "description": "Klaver et al. (2020) Eq. 1-2, divergence term only",
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
        "sh_backend": resolve_backend(backend),
        "ntrunc": int(ell.max()),
        "rsphere_m": rsphere,
        "reference": "Klaver et al. (2020), doi:10.1002/asl.952",
    }
    return out


def compute_ke_spectra_timeseries(
    ds: xr.Dataset,
    uvar: str = "ua",
    vvar: str = "va",
    plev: float | None = None,
    time_mean: bool = True,
    time_name: str = "time",
    plev_name: str = "plev",
    plev_units: Literal["Pa", "hPa"] = "Pa",
    **kwargs: Any,
) -> xr.Dataset:
    """KE spectra for every time step at one pressure level, optionally averaged.

    Klaver et al. use 6-hourly winds at 250 and 500 hPa over four months
    (March, June, September, December 2014) and analyse the *monthly mean
    spectra*.  They note that spectral slopes vary little between months, so
    the diagnosed effective resolution is a time-invariant model property.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset with ``uvar`` and ``vvar`` on ``(time, [plev,] lat, lon)``.
    uvar, vvar : str, optional
        Wind variable names.
    plev : float or None, optional
        Pressure level to select, in the units given by ``plev_units``.  If
        ``None``, ``ds`` is assumed to be on a single level already.
    time_mean : bool, optional
        If ``True`` (default), average the spectra over ``time`` after
        computing them.  Averaging spectra (not fields) is what the paper
        does; averaging the fields first would destroy the transient energy.
    time_name, plev_name : str, optional
        Dimension names.
    plev_units : {"Pa", "hPa"}, optional
        Units of the ``plev_name`` coordinate in ``ds``.  Default ``"Pa"``
        (CMIP convention).
    **kwargs
        Forwarded to `compute_ke_spectra` (``ntrunc``, ``backend``,
        ``gridtype``, ``rsphere``, ``lat_name``, ``lon_name``).

    Returns
    -------
    xarray.Dataset
        As `compute_ke_spectra`, with a leading ``time`` dimension if
        ``time_mean`` is ``False``.

    Examples
    --------
    >>> spec250 = compute_ke_spectra_timeseries(  # doctest: +SKIP
    ...     ds, "ua", "va", plev=250.0, plev_units="hPa"
    ... )
    """
    if plev is not None:
        target = plev * 100.0 if plev_units == "hPa" else plev
        ds = ds.sel({plev_name: target}, method="nearest")

    if time_name not in ds.dims:
        return compute_ke_spectra(ds, uvar, vvar, **kwargs)

    spectra = [
        compute_ke_spectra(ds.isel({time_name: i}), uvar, vvar, **kwargs)
        for i in range(ds.sizes[time_name])
    ]
    out = xr.concat(spectra, dim=time_name)
    out = out.assign_coords({time_name: ds[time_name]})
    attrs = spectra[0].attrs

    if time_mean:
        n = out.sizes[time_name]
        out = out.mean(dim=time_name, keep_attrs=True)
        attrs = {**attrs, "n_times_averaged": n}
    out.attrs = attrs
    return out
