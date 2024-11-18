import cftime
import numpy as np
import xarray as xr


def check_daily_time_axis(ds, time_key="time"):
    """
    Check if the time axis in an xarray dataset follows a correct daily sequence, considering all CFTime calendars.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        The dataset or data array containing the time axis to be checked.
    time_key : str, optional
        The key corresponding to the time dimension in the dataset (default is 'time').

    Returns
    -------
    None
        The function doesn't return a value if the check passes.

    Raises
    ------
    ValueError
        If the time axis does not use CFTime objects or does not follow a correct daily sequence.

    Example
    -------
    >>> from pcmdi_metrics.utils import check_daily_time_axis
    >>> # generate a dummy daily dataset to test
    >>> import xarray as xr
    >>> ds = xr.Dataset({"time": xr.cftime_range("2000-01-01", periods=400, freq="D", calendar="gregorian")})
    >>> # check axis
    >>> check_daily_time_axis(ds, "time")
    # No output if check passes
    """
    # Extract the time values from the dataset
    time_data = ds[time_key].values

    # Check if the time axis is based on CFTime objects
    if not isinstance(time_data[0], cftime.datetime):
        raise ValueError(
            f"The time axis does not use CFTime objects (uses {type(time_data[0])})."
        )

    # Convert time_data into numpy datetime64 for delta comparison
    for i in range(1, len(time_data)):
        # Calculate the difference in days between consecutive time points
        delta = time_data[i] - time_data[i - 1]

        # Check if the difference is exactly 1 day (as a timedelta64 object)
        if np.abs(delta) != np.timedelta64(1, "D"):
            raise ValueError(
                f"Time axis is not correct! Error at index {i}: {time_data[i - 1]} to {time_data[i]}"
            )

    # If we've made it through the loop without raising an error, the check has passed


def check_monthly_time_axis(ds: xr.Dataset, time_key: str = "time") -> None:
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
    None
        The function doesn't return a value if the check passes.

    Raises
    ------
    KeyError
        If the specified time_key is not found in the dataset.
    AttributeError
        If the time dimension doesn't have a 'dt' accessor (i.e., not a datetime type).
    ValueError
        If the time axis does not follow the correct monthly sequence.

    Example
    -------
    >>> from pcmdi_metrics.utils import check_monthly_time_axis
    >>> # generate a dummy monthly dataset to test
    >>> import xarray as xr
    >>> ds = xr.Dataset({"time": xr.cftime_range("2000-01-01", periods=20, freq="M", calendar="gregorian")})
    >>> # check axis
    >>> check_monthly_time_axis(ds)
    # No output if check passes
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

    if months_data != months_expected:
        raise ValueError(
            f"DATA ERROR: time is not correct!\n"
            f"Months from data: {months_data}\n"
            f"Months expected: {months_expected}"
        )

    # If we've made it here without raising an error, the check has passed


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
    >>> from pcmdi_metrics.utils import repeating_months
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
    >>> from pcmdi_metrics.utils import last_day_of_month
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
