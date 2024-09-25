from typing import Union

import xarray as xr
import xcdat as xc

# Internal function


def _find_key(
    ds: Union[xr.Dataset, xr.DataArray], axis: str, potential_names: list
) -> str:
    """
    Internal function to find the appropriate key for a given axis.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.
    axis : str
        The axis to find the key for ('T', 'X', or 'Y').
    potential_names : list
        List of potential names for the axis.

    Returns
    -------
    str
        The key corresponding to the given axis.

    Raises
    ------
    Exception
        If no appropriate key can be found.
    """
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
    """
    Retrieve coordinate key names from the dataset or data array.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    list[str]
        List of coordinate key names.
    """
    axes = list(ds.coords.keys())
    return axes


def get_data_list(ds: Union[xr.Dataset, xr.DataArray]) -> list[str]:
    """
    Retrieve data variable names from the dataset or data array.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    list[str]
        List of data variable names.
    """
    if isinstance(ds, xr.Dataset):
        return list(ds.data_vars.keys())
    elif isinstance(ds, xr.DataArray):
        return [ds.name]


def get_time_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the key for the time dimension.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    str
        The key for the time dimension.
    """
    axis = "T"
    potential_names = ["time", "t"]
    return _find_key(ds, axis, potential_names)


def get_latitude_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the key for the latitude dimension.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    str
        The key for the latitude dimension.
    """
    axis = "Y"
    potential_names = ["lat", "latitude"]
    return _find_key(ds, axis, potential_names)


def get_longitude_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the key for the longitude dimension.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    str
        The key for the longitude dimension.
    """
    axis = "X"
    potential_names = ["lon", "longitude"]
    return _find_key(ds, axis, potential_names)


# Retrieve bounds key names


def get_time_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the key for the time bounds.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    str
        The key for the time bounds.
    """
    lat_key = get_time_key(ds)
    return ds[lat_key].attrs["bounds"]


def get_latitude_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the key for the latitude bounds.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    str
        The key for the latitude bounds.
    """
    lat_key = get_latitude_key(ds)
    return ds[lat_key].attrs["bounds"]


def get_longitude_bounds_key(ds: Union[xr.Dataset, xr.DataArray]) -> str:
    """
    Get the key for the longitude bounds.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    str
        The key for the longitude bounds.
    """
    lon_key = get_longitude_key(ds)
    return ds[lon_key].attrs["bounds"]


# Extract coordinate data


def get_time(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    """
    Extract time coordinate data.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    xr.DataArray
        The time coordinate data.
    """
    time_key = get_time_key(ds)
    time = ds[time_key]
    return time


def get_longitude(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    """
    Extract longitude coordinate data.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    xr.DataArray
        The longitude coordinate data.
    """
    lon_key = get_longitude_key(ds)
    lon = ds[lon_key]
    return lon


def get_latitude(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    """
    Extract latitude coordinate data.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    xr.DataArray
        The latitude coordinate data.
    """
    lat_key = get_latitude_key(ds)
    lat = ds[lat_key]
    return lat


# Extract coordinate bounds data


def get_time_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    """
    Extract time bounds data.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    xr.DataArray
        The time bounds data.
    """
    time_bounds_key = get_time_bounds_key(ds)
    time_bounds = ds[time_bounds_key]
    return time_bounds


def get_longitude_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    """
    Extract longitude bounds data.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    xr.DataArray
        The longitude bounds data.
    """
    lon_bounds_key = get_longitude_bounds_key(ds)
    lon_bounds = ds[lon_bounds_key]
    return lon_bounds


def get_latitude_bounds(ds: Union[xr.Dataset, xr.DataArray]) -> xr.DataArray:
    """
    Extract latitude bounds data.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The input dataset or data array.

    Returns
    -------
    xr.DataArray
        The latitude bounds data.
    """
    lat_bounds_key = get_latitude_bounds_key(ds)
    lat_bounds = ds[lat_bounds_key]
    return lat_bounds


# Select subset


def select_subset(
    ds: xr.Dataset, lat: tuple = None, lon: tuple = None, time: tuple = None
) -> xr.Dataset:
    """
    Select a subset of the given xarray dataset based on specified latitude, longitude, and time ranges.

    Parameters
    ----------
    ds : xr.Dataset
        The input xarray dataset.
    lat : tuple, optional
        Latitude range in the form of (min, max).
    lon : tuple, optional
        Longitude range in the form of (min, max).
    time : tuple, optional
        Time range in the form of (start_time, end_time). start_time and end_time
        can be integers, floats, strings, or cftime.datetime objects.

    Returns
    -------
    xr.Dataset
        Subset of the input dataset based on the specified latitude, longitude, and time ranges.

    Notes
    -----
    This function allows for flexible subsetting of xarray datasets based on
    geographical coordinates and time ranges.

    Examples
    --------
    >>> import xarray as xr
    >>> import cftime
    >>>
    >>> # Load your xarray dataset (ds) here
    >>> ds = xr.open_dataset('path/to/your/dataset.nc')
    >>>
    >>> # Define latitude, longitude, and time ranges
    >>> lat_tuple = (30, 50)  # Latitude range
    >>> lon_tuple = (110, 130)  # Longitude range
    >>> time_tuple = ("1850-01-01 00:00:00", "1851-12-31 23:59:59")  # Time range
    >>>
    >>> # Select subset based on specified ranges
    >>> ds_subset = select_subset(ds, lat=lat_tuple, lon=lon_tuple, time=time_tuple)
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
