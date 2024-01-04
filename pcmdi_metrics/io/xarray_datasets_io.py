from typing import Union

import xarray as xr
import xcdat as xc

# Retrieve coordinate key names


def get_axis_list(ds: Union[xr.Dataset, xr.DataArray]) -> list[str]:
    axes = list(ds.coords.keys())
    return axes


def get_time_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    try:
        time_key = xc.get_dim_keys(ds, "T")
    except Exception:
        axes = get_axis_list(ds)
        time_key = [k for k in axes if k.lower() in ["time"]][0]
    return time_key


def get_lat_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    try:
        lat_key = xc.get_dim_keys(ds, "Y")
    except Exception:
        axes = get_axis_list(ds)
        lat_key = [k for k in axes if k.lower() in ["lat", "latitude"]][0]
    return lat_key


def get_lon_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    try:
        lon_key = xc.get_dim_keys(ds, "X")
    except Exception:
        axes = get_axis_list(ds)
        lon_key = [k for k in axes if k.lower() in ["lon", "longitude"]][0]
    return lon_key


# Retrieve bounds key names


def get_time_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    lat_key = get_time_key(ds)
    return ds[lat_key].attrs["bounds"]


def get_lat_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    lat_key = get_lat_key(ds)
    return ds[lat_key].attrs["bounds"]


def get_lon_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    lon_key = get_lon_key(ds)
    return ds[lon_key].attrs["bounds"]


# Extract coordinate data


def get_time(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    time_key = get_time_key(ds)
    time = ds[time_key]
    return time


def get_longitude(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lon_key = get_lon_key(ds)
    lon = ds[lon_key]
    return lon


def get_latitude(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lat_key = get_lat_key(ds)
    lat = ds[lat_key]
    return lat


# Extract coordinate bounds data


def get_time_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    time_bounds_key = get_time_bounds_key(ds)
    time_bounds = ds[time_bounds_key]
    return time_bounds


def get_longitude_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lon_bounds_key = get_lon_bounds_key(ds)
    lon_bounds = ds[lon_bounds_key]
    return lon_bounds


def get_latitude_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lat_bounds_key = get_lat_bounds_key(ds)
    lat_bounds = ds[lat_bounds_key]
    return lat_bounds


# Select subset


def select_subset(
    ds: xr.Dataset, lat: tuple = None, lon: tuple = None, time: tuple = None
) -> xr.Dataset:
    """
    Selects a subset of the given xarray dataset based on specified latitude, longitude, and time ranges.

    Parameters:
    - ds (xr.Dataset): The input xarray dataset.
    - lat (tuple, optional): Latitude range in the form of (min, max).
    - lon (tuple, optional): Longitude range in the form of (min, max).
    - time (tuple, optional): Time range. If time is specified, it should be in the form of (start_time, end_time),
      where start_time and end_time can be integers, floats, or cftime.DatetimeProlepticGregorian objects.

    Returns:
    - xr.Dataset: Subset of the input dataset based on the specified latitude, longitude, and time ranges.

    Example Usage:
    ```
    import cftime

    # Define latitude, longitude, and time ranges
    lat_tuple = (30, 50)  # Latitude range
    lon_tuple = (110, 130)  # Longitude range
    time_tuple = (cftime.datetime(1850, 1, 1, 0, 0, 0, 0),
                  cftime.datetime(1851, 12, 31, 23, 59, 59, 0))  # Time range

    # Load your xarray dataset (ds) here

    # Select subset based on specified ranges
    ds_subset = select_subset(ds, lat=lat_tuple, lon=lon_tuple, time=time_tuple)
    ```
    """
    sel_keys = {}
    if lat is not None:
        lat_key = get_lat_key(ds) 
        sel_keys[lat_key] = slice(*lat)
    if lon is not None:
        lon_key = get_lon_key(ds) 
        sel_keys[lon_key] = slice(*lon)
    if time is not None:
        time_key = get_time_key(ds)
        sel_keys[time_key] = slice(*time)

    ds = ds.sel(**sel_keys)
    return ds
