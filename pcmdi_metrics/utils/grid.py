import numpy as np
import xarray as xr

from pcmdi_metrics.io import (
    get_latitude_bounds_key,
    get_latitude_key,
    get_longitude_bounds_key,
    get_longitude_key,
)


def haversine(lat1, lon1, lat2, lon2):
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
    delta_lat = haversine(lat1, lon1, lat2, lon1)  # trapezoid height
    delta_lon1 = haversine(lat1, lon1, lat1, lon2)  # trapezoid lower base
    delta_lon2 = haversine(lat2, lon1, lat2, lon2)  # trapezoid upper base
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
