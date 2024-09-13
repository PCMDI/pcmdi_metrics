import cftime
import xarray as xr


def monthly_time_axis_checker(ds: xr.Dataset, time_key: str = "time") -> bool:
    """
    Check if the time axis of a dataset follows a correct monthly sequence.

    This function verifies if the months in the dataset's time dimension
    match the expected sequence of months, starting from the first month
    in the data and repeating as necessary.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        The dataset or data array containing the time dimension to check.
    time_key : str, optional
        The name of the time dimension in the dataset. Default is "time".

    Returns
    -------
    bool
        True if the time axis follows the correct monthly sequence,
        False otherwise.

    Prints
    ------
    If the check fails, the function prints:
    - An error message
    - The actual months from the data
    - The expected months sequence

    Raises
    ------
    KeyError
        If the specified time_key is not found in the dataset.
    AttributeError
        If the time dimension doesn't have a 'dt' accessor (i.e., not a datetime type).

    Example
    -------
    >>> import xarray as xr
    >>> import pandas as pd
    >>> dates = pd.date_range('2020-03-01', periods=14, freq='M')
    >>> ds = xr.Dataset({'time': dates})
    >>> monthly_time_axis_checker(ds)
    True
    """

    try:
        months_data = ds[time_key].dt.month.values.tolist()
    except KeyError:
        raise KeyError(f"Time dimension '{time_key}' not found in the dataset.")
    except AttributeError:
        raise AttributeError(
            f"The '{time_key}' dimension does not seem to be a datetime type."
        )

    start_month = months_data[0]
    num_time_steps = len(months_data)
    months_expected = repeating_months(start_month, num_time_steps)

    if months_data == months_expected:
        return True
    else:
        print("DATA ERROR: time is not correct!")
        print("Months from data:", months_data)
        print("Months expected:", months_expected)
        return False


def monthly_time_bnds_checker(
    ds: xr.Dataset,
    time_bounds_key: str = "time_bnds",
    month_check: bool = True,
    day_check: bool = True,
) -> bool:
    """
    Check the time bounds in a dataset to ensure they follow expected monthly and daily structures.

    This function verifies if the time bounds for specified months start on the first day
    of the month and end on the last day of the month. It can also check if time bounds
    span multiple months.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        The dataset or data array containing the time bounds to check.
    time_bounds_key : str, optional
        The key for the time bounds in the dataset. Default is "time_bnds".
    month_check : bool, optional
        Flag to enable month span checking. Default is True.
    day_check : bool, optional
        Flag to enable day validity checking. Default is True.

    Returns
    -------
    bool
        True if the time bounds are valid, False otherwise.

    Prints
    ------
    If there are errors, the function will print error messages indicating where the checks failed.

    Raises
    ------
    KeyError
        If the specified time_bounds_key is not found in the dataset.
    AttributeError
        If the time bounds do not have a 'dt' accessor (i.e., not a datetime type).

    Example
    -------
    >>> import xarray as xr
    >>> import pandas as pd
    >>> dates = pd.date_range('2021-01-01', periods=2, freq='M')
    >>> ds = xr.Dataset({'time_bnds': (['time', 'nv'], [[dates[0], dates[1]]])})
    >>> monthly_time_bnds_checker(ds)
    True
    """
    try:
        time_bnds = ds[time_bounds_key]
        time_bnds_year_pairs = time_bnds.dt.year.values
        time_bnds_month_pairs = time_bnds.dt.month.values
        time_bnds_day_pairs = time_bnds.dt.day.values
        calendar = time_bnds.dt.calendar
    except KeyError:
        raise KeyError(f"Time bounds key '{time_bounds_key}' not found in the dataset.")
    except AttributeError:
        raise AttributeError(
            f"The '{time_bounds_key}' dimension does not seem to be a datetime type."
        )

    if month_check:
        for i, (start_month, end_month) in enumerate(time_bnds_month_pairs):
            if start_month != end_month:
                print(
                    f"DATA ERROR: Time bounds for the month spread across different months: {start_month, end_month}"
                )
                print(f"{time_bnds.values[i]}")
                return False

    if day_check:
        for i, (start_day, end_day) in enumerate(time_bnds_day_pairs):
            supposed_start_day = 1
            supposed_end_day = last_day_of_month(
                time_bnds_year_pairs[i, 1], time_bnds_month_pairs[i, 1], calendar
            )

            if start_day != supposed_start_day or end_day != supposed_end_day:
                print(
                    f"DATA ERROR: Time bounds for the month does not start on day 1 or end on the last day of the month: {start_day, end_day}"
                )
                print(f"{time_bnds.values[i]}")
                return False

    return True


def repeating_months(start: int, length: int) -> list:
    """
    Generate a list of repeating numbers in the range 1 to 12, starting from a given number.

    Parameters
    ----------
    start : int
        The number to start from (must be in the range 1 to 12).
    length : int
        The total number of elements in the resulting list.

    Returns
    -------
    list
        A list of numbers repeating from the range 1 to 12.

    Raises
    ------
    ValueError
        If the starting number is not in the range 1 to 12.

    Example
    -------
    >>> repeating_months(3, 20)
    [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    >>> repeating_months(1, 5)
    [1, 2, 3, 4, 5]
    """
    if not 1 <= start <= 12:
        raise ValueError("Start number must be in the range 1 to 12")

    return [(start + i - 1) % 12 + 1 for i in range(length)]


def last_day_of_month(year: int, month: int, calendar: str = "standard") -> int:
    """
    Get the last day of a given month for different calendar types.

    Parameters
    ----------
    year : int
        The year for which the last day of the month is determined.
    month : int
        The month (1-12) for which the last day is determined.
    calendar : str, optional
        The type of calendar. Options are 'standard', 'gregorian', 'proleptic_gregorian',
        'noleap', '365_day', 'all_leap', '366_day', '360_day'. Default is 'standard'.

    Returns
    -------
    int
        The last day of the specified month for the given calendar type.

    Raises
    ------
    ValueError
        If an unsupported calendar type is provided or the month is invalid.

    Example
    -------
    >>> last_day_of_month(2024, 2, 'gregorian')  # Leap year in gregorian calendar (should return 29)
    29

    >>> last_day_of_month(2023, 2, 'noleap')  # No leap year in noleap calendar (should return 28)
    28

    >>> last_day_of_month(2023, 2, '360_day')  # 360-day calendar (should return 30)
    30
    """

    # Validate inputs
    if month < 1 or month > 12:
        raise ValueError("Month must be in the range 1 to 12.")
    if calendar not in [
        "standard",
        "gregorian",
        "proleptic_gregorian",
        "noleap",
        "365_day",
        "all_leap",
        "366_day",
        "360_day",
    ]:
        raise ValueError(
            "Unsupported calendar type. Choose from 'standard', 'gregorian', 'noleap', '365_day', 'all_leap', '366_day', or '360_day'."
        )

    days_in_month = {
        1: 31,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }

    # Return last day based on the calendar type
    if calendar == "360_day":
        return 30  # All months have 30 days in the 360-day calendar
    if calendar in ["noleap", "365_day"] and month == 2:
        return 28
    if calendar in ["all_leap", "366_day"] and month == 2:
        return 29
    if calendar in ["standard", "gregorian", "proleptic_gregorian"] and month == 2:
        return 29 if is_leap_year(year) else 28
    return days_in_month.get(month, 31)


def is_leap_year(year):
    """
    Determine if a year is a leap year in the Gregorian calendar.

    Parameters
    ----------
    year : int
        The year to check.

    Returns
    -------
    bool
        True if the year is a leap year, False otherwise.
    """
    return cftime.DatetimeGregorian(year, 3, 1).day == 1
