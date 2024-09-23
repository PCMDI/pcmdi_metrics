import xarray as xr


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
    """
    # Determine the calendar type
    calendar = ds.time.dt.calendar
    date_type = type(ds.time.values[0])

    # Function to convert string to appropriate datetime object
    def str_to_date(date_str):
        year, month, day = map(int, date_str.split("-"))
        return date_type(year, month, day, calendar=calendar)

    # Convert string dates to appropriate datetime objects
    start = str_to_date(start_date)
    end = str_to_date(end_date)

    # Get the first and last dates from the dataset
    ds_start = ds.time.values[0]
    ds_end = ds.time.values[-1]

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
