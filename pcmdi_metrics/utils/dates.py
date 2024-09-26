import re

import xarray as xr

from pcmdi_metrics.io import get_calendar, get_time_bounds_key, get_time_key


def find_overlapping_dates(ds: xr.Dataset, start_date: str, end_date: str):
    """
    Find the overlapping period between given dates and a dataset's time range.

    Parameters
    ----------
    ds : xarray.Dataset
        The dataset containing a time dimension.
    start_date : str
        The start date in 'YYYY-MM-DD' format.
    end_date : str
        The end date in 'YYYY-MM-DD' format.

    Returns
    -------
    tuple or None
        A tuple containing the start and end dates of the overlapping period,
        or None if there is no overlap.

    Notes
    -----
    This function automatically detects the calendar used in the dataset
    and applies the appropriate datetime conversion.

    Examples
    --------
    >>> import xarray as xr
    >>> dates = xr.cftime_range('2000-01-01', periods=365)
    >>> ds = xr.Dataset({'time': dates})
    >>> find_overlapping_dates(ds, '2000-06-01', '2001-01-01')
    ('2000-06-01', '2000-12-30')
    """
    # Find time key in the dataset
    time_key = get_time_key(ds)

    # Determine the calendar type
    calendar = ds[time_key].dt.calendar
    date_type = type(ds[time_key].values[0])

    # Function to convert string to appropriate datetime object
    def str_to_date(date_str):
        year, month, day = map(int, date_str.split("-"))
        return date_type(year, month, day, calendar=calendar)

    # Convert string dates to appropriate datetime objects
    start = str_to_date(start_date)
    end = str_to_date(end_date)

    # Get the first and last dates from the dataset
    ds_start = ds[time_key].values[0]
    ds_end = ds[time_key].values[-1]

    # Find the later start date
    overlap_start = max(start, ds_start)

    # Find the earlier end date
    overlap_end = min(end, ds_end)

    # Check if there's a valid overlap
    if overlap_start <= overlap_end:
        return date_to_str(overlap_start), date_to_str(overlap_end)
    else:
        return None


def date_to_str(date_obj):
    """
    Convert a date object to a string in 'YYYY-MM-DD' format.

    Parameters
    ----------
    date_obj : datetime.datetime or cftime.datetime
        The date object to convert.

    Returns
    -------
    str
        The date in 'YYYY-MM-DD' format.

    Notes
    -----
    This function handles both standard Python datetime objects
    and cftime datetime objects.

    Examples
    --------
    >>> from datetime import datetime
    >>> date_to_str(datetime(2001, 1, 1))
    '2001-01-01'
    >>> import cftime
    >>> date_to_str(cftime.DatetimeGregorian(2001, 1, 1))
    '2001-01-01'
    """
    try:
        # Try to format using strftime (works for most datetime objects)
        return date_obj.strftime("%Y-%m-%d")
    except AttributeError:
        # If strftime is not available, construct the string manually
        return f"{date_obj.year:04d}-{date_obj.month:02d}-{date_obj.day:02d}"


def extract_date_components(ds, index=0):
    """
    Extract year, month, and day from a dataset's time dimension.

    Parameters
    ----------
    ds : xarray.Dataset
        The dataset containing a time dimension.
    index : int, optional
        The index of the time value to extract. Default is 0 (first time value).

    Returns
    -------
    tuple of int
        A tuple containing (year, month, day).

    Raises
    ------
    KeyError
        If no time dimension is found in the dataset.
    IndexError
        If the specified index is out of bounds for the time dimension.

    Notes
    -----
    This function assumes that the dataset has a time dimension and that the
    time values are datetime-like objects with year, month, and day attributes.

    Examples
    --------
    >>> import xarray as xr
    >>> dates = xr.cftime_range('2000-01-01', periods=365)
    >>> ds = xr.Dataset({'time': dates, 'data': ('time', range(365))})
    >>> extract_date(ds)
    (2000, 1, 1)
    >>> extract_date(ds, index=100)
    (2000, 4, 10)

    See Also
    --------
    get_time_key : Function to find the time dimension key in the dataset.
    """
    # Find time key in the dataset
    time_key = get_time_key(ds)
    date = ds[time_key].values[index]
    return date.year, date.month, date.day


def replace_date_pattern(filename, replacement):
    """
    Replace the 'YYYYMM-YYYYMM' pattern in a filename with a specified replacement.

    Parameters
    ----------
    filename : str
        The original filename containing the date pattern.
    replacement : str
        The string to replace the date pattern with.

    Returns
    -------
    str
        The filename with the date pattern replaced.

    Examples
    --------
    >>> replace_date_pattern("pr_mon_GPCP-2-3_PCMDI_gn_197901-201907.nc", "DATE_RANGE")
    'pr_mon_GPCP-2-3_PCMDI_gn_DATE_RANGE.nc'

    >>> replace_date_pattern("temp_daily_197001-202012_processed.nc", "FULL_PERIOD")
    'temp_daily_FULL_PERIOD_processed.nc'

    Notes
    -----
    This function assumes that there's only one occurrence of the 'YYYYMM-YYYYMM'
    pattern in the filename. If multiple occurrences are possible, consider using
    re.sub() instead of re.subn().
    """
    pattern = r"\d{6}-\d{6}"
    new_filename, n = re.subn(pattern, replacement, filename)

    if n == 0:
        print(f"Warning: No 'YYYYMM-YYYYMM' pattern found in {filename}")
    elif n > 1:
        print(f"Warning: Multiple 'YYYYMM-YYYYMM' patterns found in {filename}")

    return new_filename


def regenerate_time_axis(
    ds: xr.Dataset,
    start_str: str = None,
    periods: int = None,
    frequency: str = "monthly",
) -> xr.Dataset:
    """
    Regenerate the time axis and bounds for an xarray Dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The input dataset with a time dimension.
    start_str : str, optional
        The start date in 'YYYY-MM-DD' format. If None, it's extracted from the dataset.
    periods : int, optional
        The number of time periods. If None, it's inferred from the dataset.
    frequency : {'monthly', 'daily'}, optional
        The frequency of the time axis. Default is 'monthly'.

    Returns
    -------
    xr.Dataset
        The dataset with regenerated time axis and bounds.

    Raises
    ------
    ValueError
        If an unsupported frequency is provided.

    Notes
    -----
    This function uses `get_time_key`, `get_time_bounds_key`,
    and `extract_date_components` functions.

    Examples
    --------
    >>> import xarray as xr
    >>> dates = xr.cftime_range('2000-01-01', periods=12, freq='MS')
    >>> ds = xr.Dataset({'time': dates, 'data': ('time', range(12))})
    >>> regenerated_ds = regenerate_time_axis(ds, frequency='monthly')
    >>> print(regenerated_ds.time)
    """

    # Deep copy the dataset
    ds_new = ds.copy(deep=True)

    # Preserve the attributes by manually copying them
    for coord in ds.coords:
        ds_new[coord].attrs = ds[coord].attrs
        ds_new[coord].encoding = ds[coord].encoding

    time_key = get_time_key(ds_new)
    time_bnds_key = get_time_bounds_key(ds_new)
    calendar = get_calendar(ds)

    if start_str is None:
        # Extract the start year, month, and day from the dataset time coordinate
        start_yr, start_mo, start_da = extract_date_components(ds_new, index=0)
        start_str = f"{start_yr:04d}-{start_mo:02d}-{start_da:02d}"

    if periods is None:
        periods = len(ds_new[time_key])

    freq_map = {"monthly": "MS", "daily": "D"}

    if frequency.lower() not in freq_map:
        raise ValueError(
            f"Unsupported frequency: {frequency.lower()}. Supported frequencies are: {', '.join(freq_map.keys())}"
        )

    dates = xr.cftime_range(
        start_str,
        freq=freq_map[frequency.lower()],
        periods=periods,
        calendar=calendar,
    )
    print("Regenerating time axis and bounds")

    # Regenerate time axis
    ds_new[time_key] = xr.DataArray(dates, dims=time_key, attrs=ds[time_key].attrs)
    ds_new[time_key].encoding = ds[time_key].encoding

    # Regenerate time bounds
    ds_new = ds_new.drop_vars([time_bnds_key])
    ds_new = ds_new.bounds.add_time_bounds("freq", freq="month")

    print("Regenerated time axis and bounds")

    return ds_new
