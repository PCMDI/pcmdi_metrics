import xarray as xr
import xcdat as xc


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
        lat_key = xc.axis.get_dim_keys(ds, axis="Y")
        sel_keys[lat_key] = slice(*lat)
    if lon is not None:
        lon_key = xc.axis.get_dim_keys(ds, axis="X")
        sel_keys[lon_key] = slice(*lon)
    if time is not None:
        time_key = xc.axis.get_dim_keys(ds, axis="T")
        sel_keys[time_key] = slice(*time)

    ds = ds.sel(**sel_keys)
    return ds
