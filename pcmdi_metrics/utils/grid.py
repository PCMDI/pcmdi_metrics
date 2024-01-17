import numpy as np
import xarray as xr
import xcdat as xc

from pcmdi_metrics.io import (
    get_latitude_bounds_key,
    get_latitude_key,
    get_longitude_bounds_key,
    get_longitude_key,
)


def create_target_grid(
    lat1: float = -90.0,
    lat2: float = 90.0,
    lon1: float = 0.0,
    lon2: float = 360.0,
    target_grid_resolution: str = "2.5x2.5",
) -> xr.Dataset:
    """Generate a uniform grid for given latitude/longitude ranges and resolution

    Parameters
    ----------
    lat1 : float, optional
        Starting latitude, by default -90.
    lat2 : float, optional
        Starting latitude, by default 90.
    lon1 : float, optional
        Starting latitude, by default 0.
    lon2 : float, optional
        Starting latitude, by default 360.
    target_grid_resolution : str, optional
        grid resolution in degree for lat and lon, by default "2.5x2.5"

    Returns
    -------
    xr.Dataset
        generated grid

    Examples
    ---------
    Import:

    >>> from pcmdi_metrics.utils import create_target_grid

    Global uniform grid:

    >>> t_grid = create_target_grid(-90, 90, 0, 360, target_grid="5x5")

    Regional uniform grid:

    >>> t_grid = create_target_grid(30, 50, 100, 150, target_grid="0.5x0.5")
    """
    # generate target grid
    res = target_grid_resolution.split("x")
    lat_res = float(res[0])
    lon_res = float(res[1])
    start_lat = lat1 + lat_res / 2.0
    start_lon = lon1 + lon_res / 2.0
    end_lat = lat2 - lat_res / 2
    end_lon = lon2 - lon_res / 2
    t_grid = xc.create_uniform_grid(
        start_lat, end_lat, lat_res, start_lon, end_lon, lon_res
    )
    return t_grid


def __haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance (in meters) between two points
    on the Earth's surface given their latitude and longitude in decimal degrees.

    Parameters:
    - lat1 (float or array-like): Latitude of the first point in decimal degrees.
    - lon1 (float or array-like): Longitude of the first point in decimal degrees.
    - lat2 (float or array-like): Latitude of the second point in decimal degrees.
    - lon2 (float or array-like): Longitude of the second point in decimal degrees.

    Returns:
    - distance (float): Great-circle distance between the two points in meters.
    """
    R = 6371000  # Earth radius in meters
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c
    return distance


def calculate_grid_area(ds: xr.Dataset) -> xr.DataArray:
    """
    Calculate the area of each grid cell in a latitude-longitude dataset and
    compute area weights for each cell.

    Parameters:
    - ds (xarray.Dataset): Input dataset containing latitude and longitude bounds.

    Returns:
    - ds_new (xarray.Dataset): New dataset with additional variables:
        - 'grid_area': Area of each grid cell in square meters.
        - 'area_weights': Area weights for each grid cell, normalized to sum to 1.
    """
    lat_key = get_latitude_key(ds)
    lon_key = get_longitude_key(ds)

    lat_bounds_key = get_latitude_bounds_key(ds)
    lon_bounds_key = get_longitude_bounds_key(ds)

    lat_bounds = ds[lat_bounds_key]
    lon_bounds = ds[lon_bounds_key]

    lat1, lat2 = lat_bounds[:, 0], lat_bounds[:, 1]
    lon1, lon2 = lon_bounds[:, 0], lon_bounds[:, 1]

    # Calculate distances using Haversine formula
    delta_lat = __haversine(lat1, lon1, lat2, lon1)  # trapezoid height
    delta_lon1 = __haversine(lat1, lon1, lat1, lon2)  # trapezoid lower base
    delta_lon2 = __haversine(lat2, lon1, lat2, lon2)  # trapezoid upper base
    delta_lon = (delta_lon1 + delta_lon2) / 2.0

    # Calculate area
    area = delta_lat * delta_lon

    # Create a new variable in the dataset with the calculated areas
    grid_area = xr.DataArray(area, dims=[lat_key, lon_key], attrs={"units": "m2"})

    return grid_area


def calculate_area_weights(grid_area):
    # Calculate area weighting for each grid
    total_area = grid_area.sum()
    area_weights = np.sqrt(grid_area / total_area)
    return area_weights


def regrid(
    ds: xr.Dataset,
    data_var: str,
    target_grid: xr.Dataset,
    regrid_tool: str = "regrid2",
    regrid_method: str = None,
) -> xr.Dataset:
    # regrid
    if regrid_tool == "regrid2":
        ds_regridded = ds.regridder.horizontal(data_var, target_grid, tool=regrid_tool)
    elif regrid_tool in ["esmf", "xesmf"]:
        regrid_tool = "xesmf"
        regrid_method = "bilinear"
        ds_regridded = ds.regridder.horizontal(
            data_var, target_grid, tool=regrid_tool, method=regrid_method
        )
    return ds_regridded
