#!/usr/bin/env python
"""Representative grid box distance :math:`\\tilde{L}_{box}`.

Klaver et al. (2020, Appendix S1) characterise a model's *nominal* resolution
by an area-weighted mean grid box diagonal, :math:`\\tilde{L}_{box}`.  This is
the denominator of their headline dimensionless metric,
:math:`L_{eff}/\\tilde{L}_{box}`, which they find lies between 2.7 and 4.8
across a set of models spanning regular lat-lon, Gaussian, reduced Gaussian
and octahedral grids.

Working in terms of that ratio -- rather than raw kilometres -- is what makes
the diagnostic comparable across grid types, and is the reason this module
supports reduced grids explicitly rather than assuming a rectilinear mesh.

Relation to other conventions
-----------------------------
Skamarock (2004) and Abdalla et al. (2013) quote :math:`L_{eff} \\approx
7\\Delta x` and :math:`8\\Delta x` respectively, where :math:`\\Delta x
\\approx \\tilde{L}_{box}/\\sqrt{2}` is a grid *side* rather than a diagonal,
and their length scales are full wavelengths rather than eddy scales (half
wavelengths).  `ratio_to_dx_convention` converts between the two.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

from .spherical_harmonics import EARTH_RADIUS

__all__ = [
    "representative_grid_box_distance",
    "grid_box_distance_from_dataset",
    "ratio_to_dx_convention",
]


def representative_grid_box_distance(
    lat: np.ndarray,
    lon: np.ndarray | None = None,
    nlon_per_lat: np.ndarray | None = None,
    lat_bounds: np.ndarray | None = None,
    rsphere: float = EARTH_RADIUS,
) -> float:
    """Area-weighted mean grid box diagonal, in kilometres.

    For each grid cell the zonal and meridional side lengths are

    .. math::
        \\Delta x = a \\cos\\phi \\, \\Delta\\lambda, \\qquad
        \\Delta y = a \\, \\Delta\\phi,

    the diagonal is :math:`\\sqrt{\\Delta x^2 + \\Delta y^2}`, and the mean is
    weighted by cell area.

    Parameters
    ----------
    lat : ndarray
        Latitudes of the grid rows in degrees north, shape ``(nlat,)``.  For
        a reduced grid these are the row latitudes.
    lon : ndarray or None, optional
        Longitudes in degrees east, shape ``(nlon,)``.  Used only to infer a
        constant number of longitudes per row; ignored if ``nlon_per_lat`` is
        given.  One of ``lon`` or ``nlon_per_lat`` is required.
    nlon_per_lat : ndarray or None, optional
        Number of longitude points in each latitude row, shape ``(nlat,)``.
        Supply this for reduced Gaussian and octahedral grids (e.g. the
        ECMWF-IFS ``TCO`` grids), where the zonal point count decreases
        poleward.
    lat_bounds : ndarray or None, optional
        Latitude cell edges in degrees north, shape ``(nlat, 2)`` or
        ``(nlat + 1,)``.  If ``None``, edges are inferred as the midpoints
        between adjacent latitudes, with the outermost cells extended
        symmetrically and clipped to the poles.
    rsphere : float, optional
        Sphere radius in metres.

    Returns
    -------
    float
        :math:`\\tilde{L}_{box}` in kilometres.

    Examples
    --------
    A 1-degree regular grid.  Note this is well below the 157 km equatorial
    diagonal: cells narrow poleward, and the area weighting still gives the
    shrinking high-latitude rows appreciable influence.

    >>> lat = np.arange(-89.5, 90.0, 1.0)
    >>> lon = np.arange(0.0, 360.0, 1.0)
    >>> float(np.round(representative_grid_box_distance(lat, lon), 1))
    142.9

    Reproduces the ``L_box`` column of Klaver et al. Table 1 for the
    grid-point models:

    >>> for nlat, nlon, published in [
    ...     (145, 192, 217.0), (325, 432, 96.7), (769, 1024, 40.8),
    ...     (192, 288, 153.0), (768, 1152, 38.2),
    ... ]:
    ...     lat = np.linspace(-90.0, 90.0, nlat)
    ...     lon = np.arange(0.0, 360.0, 360.0 / nlon)
    ...     got = representative_grid_box_distance(lat, lon)
    ...     print(f"{nlat}x{nlon}: {got:6.1f} km (Table 1: {published})")
    145x192:  217.5 km (Table 1: 217.0)
    325x432:   96.7 km (Table 1: 96.7)
    769x1024:   40.8 km (Table 1: 40.8)
    192x288:  153.2 km (Table 1: 153.0)
    768x1152:   38.2 km (Table 1: 38.2)
    """
    lat = np.asarray(lat, dtype=float)
    nlat = lat.size

    if nlon_per_lat is None:
        if lon is None:
            raise ValueError("Provide either 'lon' or 'nlon_per_lat'")
        nlon_per_lat = np.full(nlat, np.asarray(lon).size, dtype=float)
    nlon_per_lat = np.asarray(nlon_per_lat, dtype=float)
    if nlon_per_lat.size != nlat:
        raise ValueError(
            f"nlon_per_lat has size {nlon_per_lat.size}, expected {nlat} to match lat"
        )

    edges = _latitude_edges(lat, lat_bounds)
    dphi = np.deg2rad(np.abs(np.diff(edges)))
    phi = np.deg2rad(lat)

    dy = rsphere * dphi
    dx = rsphere * np.cos(phi) * (2.0 * np.pi / nlon_per_lat)
    diagonal = np.sqrt(dx**2 + dy**2)

    # Area of one cell in the row, times the number of cells in the row.
    sin_edges = np.sin(np.deg2rad(edges))
    row_area = 2.0 * np.pi * rsphere**2 * np.abs(np.diff(sin_edges))

    return float(np.sum(row_area * diagonal) / np.sum(row_area) / 1000.0)


def _latitude_edges(lat: np.ndarray, lat_bounds: np.ndarray | None) -> np.ndarray:
    """Return monotonic latitude cell edges of shape ``(nlat + 1,)``."""
    if lat_bounds is not None:
        bounds = np.asarray(lat_bounds, dtype=float)
        if bounds.ndim == 2:
            return np.concatenate([bounds[:, 0], bounds[-1:, 1]])
        return bounds

    mid = 0.5 * (lat[:-1] + lat[1:])
    first = lat[0] - (mid[0] - lat[0])
    last = lat[-1] + (lat[-1] - mid[-1])
    edges = np.concatenate([[first], mid, [last]])
    return np.clip(edges, -90.0, 90.0)


def grid_box_distance_from_dataset(
    ds: xr.Dataset,
    lat_name: str = "lat",
    lon_name: str = "lon",
    lat_bnds_name: str | None = "lat_bnds",
    rsphere: float = EARTH_RADIUS,
) -> float:
    """Convenience wrapper: :math:`\\tilde{L}_{box}` straight from a Dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset carrying the grid coordinates.
    lat_name, lon_name : str, optional
        Coordinate names.
    lat_bnds_name : str or None, optional
        Name of the latitude bounds variable, used when present.  Default
        ``"lat_bnds"``.
    rsphere : float, optional
        Sphere radius in metres.

    Returns
    -------
    float
        :math:`\\tilde{L}_{box}` in kilometres.

    Notes
    -----
    This reads the grid of ``ds`` *as given*.  If the caller regridded the
    data before computing spectra, this returns the target grid's spacing,
    not the model's native spacing -- and the resulting
    :math:`L_{eff}/\\tilde{L}_{box}` would be meaningless.  Compute
    :math:`\\tilde{L}_{box}` from the native grid, and prefer not to regrid at
    all for this diagnostic.
    """
    bounds = None
    if lat_bnds_name is not None and lat_bnds_name in ds:
        bounds = np.asarray(ds[lat_bnds_name].values, dtype=float)
    return representative_grid_box_distance(
        np.asarray(ds[lat_name].values, dtype=float),
        lon=np.asarray(ds[lon_name].values, dtype=float),
        lat_bounds=bounds,
        rsphere=rsphere,
    )


def ratio_to_dx_convention(ratio_leff_lbox: float) -> float:
    """Convert :math:`L_{eff}/\\tilde{L}_{box}` to the :math:`L_{eff}/\\Delta x` convention.

    Klaver et al. express the effective resolution as an eddy scale (half
    wavelength) over a grid box *diagonal*; Skamarock (2004) and Abdalla et
    al. (2013) express it as a full wavelength over a grid box *side*.  The
    two differ by a factor :math:`2\\sqrt{2}`, which is why this paper's
    2.7-4.8 corresponds to the familiar 7-8 :math:`\\Delta x`.

    Parameters
    ----------
    ratio_leff_lbox : float
        Ratio in the Klaver et al. convention.

    Returns
    -------
    float
        Ratio in the Skamarock/Abdalla convention.

    Examples
    --------
    >>> float(np.round(ratio_to_dx_convention(2.7), 1))
    7.6
    >>> float(np.round(ratio_to_dx_convention(4.8), 1))
    13.6
    """
    return 2.0 * np.sqrt(2.0) * ratio_leff_lbox
