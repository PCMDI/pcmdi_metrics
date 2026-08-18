#!/usr/bin/env python
"""Representative grid box distance :math:`\\tilde{L}_{box}`.

Klaver et al. (2020, Appendix S1) characterise a model's *nominal* resolution
by an area-weighted mean grid box diagonal, :math:`\\tilde{L}_{box}`.  It is
the denominator of their headline dimensionless metric
:math:`L_{eff}/\\tilde{L}_{box}`, which lies between 2.7 and 4.8 across models
spanning regular latitude-longitude, Gaussian, reduced Gaussian and octahedral
grids.  Working in that ratio rather than in raw kilometres is what makes the
diagnostic comparable across grid types.

Skamarock (2004) and Abdalla et al. (2013) instead quote the effective
resolution as a full wavelength over a grid box *side*
:math:`\\Delta x \\approx \\tilde{L}_{box}/\\sqrt{2}`;
`ratio_to_dx_convention` converts between the two.

References
----------
Abdalla, S., Isaksen, L., Janssen, P., & Wedi, N. (2013). Effective spectral
    resolution of ECMWF atmospheric forecast models. *ECMWF Newsletter*, 137,
    19-22.
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
Skamarock, W. C. (2004). Evaluating mesoscale NWP models using kinetic energy
    spectra. *Monthly Weather Review*, 132, 3019-3032.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

from pcmdi_metrics.io import get_latitude_bounds, get_latitude_key, get_longitude_key

from .ke_spectra import EARTH_RADIUS

__all__ = [
    "grid_box_distance_from_dataset",
    "ratio_to_dx_convention",
    "representative_grid_box_distance",
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
    :math:`\\Delta x = a\\cos\\phi\\,\\Delta\\lambda` and
    :math:`\\Delta y = a\\,\\Delta\\phi`; the diagonal is
    :math:`\\sqrt{\\Delta x^2 + \\Delta y^2}`, and the mean is weighted by cell
    area.

    Parameters
    ----------
    lat : ndarray
        Latitudes of the grid rows in degrees north, shape ``(nlat,)``.
    lon : ndarray or None, optional
        Longitudes in degrees east.  Used only to count longitudes per row;
        ignored when ``nlon_per_lat`` is given.  One of the two is required.
    nlon_per_lat : ndarray or None, optional
        Number of longitude points in each latitude row, shape ``(nlat,)``.
        Supply this for reduced Gaussian and octahedral grids (e.g. the ECMWF
        ``TCO`` grids), where the zonal point count decreases poleward.
    lat_bounds : ndarray or None, optional
        Latitude cell edges, shape ``(nlat, 2)`` or ``(nlat + 1,)``.  If
        ``None``, edges are inferred as midpoints between adjacent latitudes,
        with the outermost cells extended symmetrically and clipped to the
        poles.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.

    Returns
    -------
    float
        :math:`\\tilde{L}_{box}` in kilometres.

    Examples
    --------
    A 1-degree regular grid.  This is well below the 157 km equatorial
    diagonal: cells narrow poleward, and the area weighting still gives the
    shrinking high-latitude rows appreciable influence.

    >>> lat = np.arange(-89.5, 90.0, 1.0)
    >>> lon = np.arange(0.0, 360.0, 1.0)
    >>> float(np.round(representative_grid_box_distance(lat, lon), 1))
    142.9

    Reproduces the :math:`\\tilde{L}_{box}` column of Klaver et al. Table 1
    for the grid-point models:

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

    if nlon_per_lat is None:
        if lon is None:
            raise ValueError("Provide either 'lon' or 'nlon_per_lat'")
        nlon_per_lat = np.full(lat.size, np.asarray(lon).size, dtype=float)
    nlon_per_lat = np.asarray(nlon_per_lat, dtype=float)
    if nlon_per_lat.size != lat.size:
        raise ValueError(
            f"nlon_per_lat has size {nlon_per_lat.size}, expected {lat.size}"
        )

    edges = _latitude_edges(lat, lat_bounds)
    dy = rsphere * np.deg2rad(np.abs(np.diff(edges)))
    dx = rsphere * np.cos(np.deg2rad(lat)) * (2.0 * np.pi / nlon_per_lat)
    diagonal = np.sqrt(dx**2 + dy**2)

    # Area of one cell in a row times the number of cells in that row.
    row_area = 2.0 * np.pi * rsphere**2 * np.abs(np.diff(np.sin(np.deg2rad(edges))))
    return float(np.sum(row_area * diagonal) / np.sum(row_area) / 1000.0)


def _latitude_edges(lat: np.ndarray, lat_bounds: np.ndarray | None) -> np.ndarray:
    """Monotonic latitude cell edges of shape ``(nlat + 1,)``."""
    if lat_bounds is not None:
        bounds = np.asarray(lat_bounds, dtype=float)
        if bounds.ndim == 2:
            return np.concatenate([bounds[:, 0], bounds[-1:, 1]])
        return bounds

    mid = 0.5 * (lat[:-1] + lat[1:])
    edges = np.concatenate(
        [[lat[0] - (mid[0] - lat[0])], mid, [lat[-1] + (lat[-1] - mid[-1])]]
    )
    return np.clip(edges, -90.0, 90.0)


def grid_box_distance_from_dataset(
    ds: xr.Dataset, rsphere: float = EARTH_RADIUS
) -> float:
    """:math:`\\tilde{L}_{box}` straight from a Dataset's own grid.

    Latitude, longitude and latitude bounds are resolved from the dataset's
    axis metadata, so non-standard coordinate names work.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset carrying the grid coordinates.
    rsphere : float, optional
        Sphere radius in metres.  Default is `EARTH_RADIUS`.

    Returns
    -------
    float
        :math:`\\tilde{L}_{box}` in kilometres.

    Notes
    -----
    This reads the grid of ``ds`` *as given*.  If the data were regridded
    before the spectra were computed, this returns the target grid's spacing
    rather than the model's native spacing, and the resulting ratio would be
    meaningless.  Compute it from the native grid, and prefer not to regrid at
    all for this diagnostic.  For reduced Gaussian and octahedral grids the
    rectilinear coordinates misrepresent the mesh; pass an explicit value to
    `~pcmdi_metrics.effective_resolution.compute_effective_resolution` instead.
    """
    try:
        bounds = np.asarray(get_latitude_bounds(ds).values, dtype=float)
    except Exception:
        bounds = None
    return representative_grid_box_distance(
        np.asarray(ds[get_latitude_key(ds)].values, dtype=float),
        lon=np.asarray(ds[get_longitude_key(ds)].values, dtype=float),
        lat_bounds=bounds,
        rsphere=rsphere,
    )


def ratio_to_dx_convention(ratio_leff_lbox: float) -> float:
    """Convert :math:`L_{eff}/\\tilde{L}_{box}` to the :math:`L_{eff}/\\Delta x` convention.

    Klaver et al. express the effective resolution as an eddy scale (half
    wavelength) over a grid box *diagonal*; Skamarock (2004) and Abdalla et
    al. (2013) express it as a full wavelength over a grid box *side*.  The
    two differ by a factor :math:`2\\sqrt{2}`.  The lower end of the paper's
    2.7-4.8 range therefore corresponds to the familiar :math:`7\\Delta x` of
    the NWP literature, while its upper end is coarser still.

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
