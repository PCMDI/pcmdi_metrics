import pandas as pd
import pytest
import xarray as xr

from pcmdi_metrics.utils import (
    check_daily_time_axis,
    check_monthly_time_axis,
    last_day_of_month,
    repeating_months,
)


@pytest.fixture
def create_dataset():
    def _create_dataset(start_date, periods, freq, calendar="gregorian"):
        dates = xr.cftime_range(
            start_date, periods=periods, freq=freq, calendar=calendar
        )
        return xr.Dataset({"time": dates})

    return _create_dataset


# Test check_daily_time_axis
@pytest.mark.parametrize("calendar", ["gregorian", "noleap", "360_day"])
def test_check_daily_time_axis_correct(create_dataset, calendar):
    ds = create_dataset("2000-01-01", 400, "D", calendar=calendar)
    assert check_daily_time_axis(ds) is None


def test_check_daily_time_axis_incorrect(create_dataset):
    # Test with incorrect daily sequence
    ds = create_dataset("2000-01-01", 400, "2D")
    with pytest.raises(ValueError, match="Time axis is not correct!"):
        check_daily_time_axis(ds)


def test_check_daily_time_axis_non_cftime():
    ds = xr.Dataset({"time": pd.date_range("2000-01-01", periods=400, freq="D")})
    with pytest.raises(ValueError, match="The time axis does not use CFTime objects"):
        check_daily_time_axis(ds)


def test_check_daily_time_axis_missing_time_key(create_dataset):
    ds = create_dataset("2000-01-01", 400, "D")
    with pytest.raises(KeyError):
        check_daily_time_axis(ds, time_key="non_existent_key")


# Test check_monthly_time_axis
@pytest.mark.parametrize("calendar", ["gregorian", "noleap", "360_day"])
def test_check_monthly_time_axis_correct(create_dataset, calendar):
    ds = create_dataset("2000-01-01", 24, "M", calendar=calendar)
    assert check_monthly_time_axis(ds) is None


def test_check_monthly_time_axis_incorrect(create_dataset):
    # Test with incorrect monthly sequence
    ds = create_dataset("2000-01-01", 24, "2M")
    with pytest.raises(ValueError, match="DATA ERROR: time is not correct!"):
        check_monthly_time_axis(ds)


def test_check_monthly_time_axis_non_datetime():
    ds = xr.Dataset({"time": range(24)})
    with pytest.raises(AttributeError):
        check_monthly_time_axis(ds)


def test_check_monthly_time_axis_missing_time_key(create_dataset):
    ds = create_dataset("2000-01-01", 24, "M")
    with pytest.raises(KeyError):
        check_monthly_time_axis(ds, time_key="non_existent_key")


# Test repeating_months
@pytest.mark.parametrize(
    "start,length,expected",
    [
        (3, 15, [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5]),
        (1, 5, [1, 2, 3, 4, 5]),
        (12, 3, [12, 1, 2]),
    ],
)
def test_repeating_months(start, length, expected):
    assert repeating_months(start, length) == expected


def test_repeating_months_invalid_start():
    with pytest.raises(ValueError):
        repeating_months(13, 5)


# Test last_day_of_month
@pytest.mark.parametrize(
    "year,month,calendar,expected",
    [
        (2024, 2, "gregorian", 29),
        (2023, 2, "noleap", 28),
        (2023, 2, "360_day", 30),
        (2023, 4, "standard", 30),
        (2023, 1, "all_leap", 31),
        (2023, 2, "366_day", 29),
    ],
)
def test_last_day_of_month(year, month, calendar, expected):
    assert last_day_of_month(year, month, calendar) == expected


def test_last_day_of_month_invalid_month():
    with pytest.raises(ValueError):
        last_day_of_month(2023, 13, "gregorian")


def test_last_day_of_month_invalid_calendar():
    with pytest.raises(ValueError):
        last_day_of_month(2023, 1, "invalid_calendar")
