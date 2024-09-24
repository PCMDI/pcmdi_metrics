from typing import Union

import xarray as xr
import xcdat as xc

# Internal function


def _find_key(
    ds: Union[xr.Dataset, xr.DataArray], axis: str, potential_names: list
) -> str:
    try:
        key = xc.get_dim_keys(ds, axis)
    except Exception as e:
        axes = get_axis_list(ds)
        key_candidates = [k for k in axes if k.lower() in potential_names]
        if len(key_candidates) > 0:
            key = key_candidates[0]
        else:
            data_keys = get_data_list(ds)
            key_candidates = [k for k in data_keys if k.lower() in potential_names]
            if len(key_candidates) > 0:
                key = key_candidates[0]
            else:
                all_keys = ", ".join(axes + data_keys)
                print(
                    f"Error: Cannot find a proper key name for {axis} from keys:{all_keys} {e}"
                )
    return key


# Retrieve coordinate key names


def get_axis_list(ds: Union[xr.Dataset, xr.DataArray]) -> list[str]:
    axes = list(ds.coords.keys())
    return axes


def get_data_list(ds: Union[xr.Dataset, xr.DataArray]) -> list[str]:
    if isinstance(ds, xr.Dataset):
        return list(ds.data_vars.keys())
    elif isinstance(ds, xr.DataArray):
        return [ds.name]


def get_time_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    axis = "T"
    potential_names = ["time", "t"]
    return _find_key(ds, axis, potential_names)


def get_latitude_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    axis = "Y"
    potential_names = ["lat", "latitude"]
    return _find_key(ds, axis, potential_names)


def get_longitude_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    axis = "X"
    potential_names = ["lon", "longitude"]
    return _find_key(ds, axis, potential_names)


# Retrieve bounds key names


def get_time_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    time_key = get_time_key(ds)
    return ds[time_key].attrs["bounds"]


def get_latitude_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    lat_key = get_latitude_key(ds)
    return ds[lat_key].attrs["bounds"]


def get_longitude_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    lon_key = get_longitude_key(ds)
    return ds[lon_key].attrs["bounds"]


# Extract coordinate data


def get_time(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    time_key = get_time_key(ds)
    time = ds[time_key]
    return time


def get_longitude(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lon_key = get_longitude_key(ds)
    lon = ds[lon_key]
    return lon


def get_latitude(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lat_key = get_latitude_key(ds)
    lat = ds[lat_key]
    return lat


# Extract coordinate bounds data


def get_time_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    time_bounds_key = get_time_bounds_key(ds)
    time_bounds = ds[time_bounds_key]
    return time_bounds


def get_longitude_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lon_bounds_key = get_longitude_bounds_key(ds)
    lon_bounds = ds[lon_bounds_key]
    return lon_bounds


def get_latitude_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    lat_bounds_key = get_latitude_bounds_key(ds)
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
      where start_time and end_time can be integers, floats, string, or cftime.datetime objects.

    Returns:
    - xr.Dataset: Subset of the input dataset based on the specified latitude, longitude, and time ranges.

    Example Usage:
    ```
    import cftime

    # Define latitude, longitude, and time ranges
    lat_tuple = (30, 50)  # Latitude range
    lon_tuple = (110, 130)  # Longitude range
    time_tuple = ("1850-01-01 00:00:00", "1851-12-31 23:59:59") # Time range

    # Load your xarray dataset (ds) here

    # Select subset based on specified ranges
    ds_subset = select_subset(ds, lat=lat_tuple, lon=lon_tuple, time=time_tuple)
    ```
    """
    sel_keys = {}
    if lat is not None:
        lat_key = get_latitude_key(ds)
        sel_keys[lat_key] = slice(*lat)
    if lon is not None:
        lon_key = get_longitude_key(ds)
        sel_keys[lon_key] = slice(*lon)
    if time is not None:
        time_key = get_time_key(ds)
        sel_keys[time_key] = slice(*time)

    ds = ds.sel(**sel_keys)
    return ds


def da_to_ds(d: Union[xr.Dataset, xr.DataArray], var: str = "variable") -> xr.Dataset:
    """Convert xarray DataArray to Dataset

    Parameters
    ----------
    d : Union[xr.Dataset, xr.DataArray]
        Input dataArray. If dataset is given, no process will be done
    var : str, optional
        Name of dataArray, by default "variable"

    Returns
    -------
    xr.Dataset
        xarray Dataset

    Raises
    ------
    TypeError
        Raised when given input is not xarray based variables
    """
    if isinstance(d, xr.Dataset):
        return d.copy()
    elif isinstance(d, xr.DataArray):
        return d.to_dataset(name=var).bounds.add_missing_bounds().copy()
    else:
        raise TypeError(
            "Input must be an instance of either xarrary.DataArray or xarrary.Dataset"
        )


def get_grid(
    d: Union[xr.Dataset, xr.DataArray],
) -> xr.Dataset:
    """Get grid information

    Parameters
    ----------
    d : Union[xr.Dataset, xr.DataArray]
        xarray dataset to extract grid information that has latitude, longitude, and their bounds included

    Returns
    -------
    xr.Dataset
        xarray dataset with grid information
    """
    if isinstance(d, xr.DataArray):
        d = da_to_ds(d, d.name)
    lat_key = get_latitude_key(d)
    lon_key = get_longitude_key(d)
    lat_bnds_key = get_latitude_bounds_key(d)
    lon_bnds_key = get_longitude_bounds_key(d)
    return d[[lat_key, lon_key, lat_bnds_key, lon_bnds_key]]


def get_calendar(d: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the calendar type from an xarray Dataset or DataArray.

    Parameters
    ----------
    d : xarray.Dataset or xarray.DataArray
        The input xarray object containing a time dimension.

    Returns
    -------
    str
        The calendar type as a string (e.g., 'proleptic_gregorian', 'noleap', '360_day').

    Raises
    ------
    ValueError
        If no time dimension is found in the input.
    AttributeError
        If the calendar information cannot be extracted from the time dimension.

    Notes
    -----
    This function first attempts to retrieve the calendar from the time dimension's
    encoding. If that fails, it tries to get the calendar from the time dimension's
    datetime accessor. If both methods fail, it raises an AttributeError.

    Examples
    --------
    >>> import xarray as xr
    >>> import pandas as pd
    >>> dates = xr.cftime_range('2000-01-01', periods=365)
    >>> ds = xr.Dataset({'time': dates, 'data': ('time', range(365))})
    >>> get_calendar(ds)
    'standard'

    See Also
    --------
    get_time : Function to extract the time dimension from a Dataset or DataArray.
    """
    time = get_time(d)

    if time is None:
        raise ValueError("No time dimension found in the input.")

    try:
        calendar = time.encoding.get("calendar")
        if calendar is not None:
            return calendar
    except AttributeError:
        pass

    try:
        return time.dt.calendar
    except AttributeError:
        raise AttributeError(
            "Unable to determine calendar type from the time dimension."
        )
