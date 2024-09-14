import pytest
import xarray as xr

from pcmdi_metrics.utils import (
    daily_time_axis_checker,
    last_day_of_month,
    monthly_time_axis_checker,
    repeating_months,
)

## Test daily_time_axis_checker


def test_daily_time_axis_checker():
    # Test with correct daily sequence
    ds = xr.Dataset(
        {
            "time": xr.cftime_range(
                "2000-01-01", periods=400, freq="D", calendar="gregorian"
            )
        }
    )
    assert daily_time_axis_checker(ds, "time") is True

    # Test with incorrect daily sequence
    ds = xr.Dataset(
        {
            "time": xr.cftime_range(
                "2000-01-01", periods=400, freq="2D", calendar="gregorian"
            )
        }
    )
    assert daily_time_axis_checker(ds, "time") is False

    # Test with non-CFTime objects
    ds = xr.Dataset(
        {
            "time": xr.cftime_range(
                "2000-01-01", periods=400, freq="D", calendar="360_day"
            )
        }
    )
    assert daily_time_axis_checker(ds, "time") is True


## Test monthly_time_axis_checker


def test_monthly_time_axis_checker():
    # Test with correct monthly sequence
    ds = xr.Dataset(
        {
            "time": xr.cftime_range(
                "2020-03-01", periods=14, freq="MS", calendar="gregorian"
            )
        }
    )
    assert monthly_time_axis_checker(ds) is True

    # Test with incorrect monthly sequence
    ds = xr.Dataset(
        {
            "time": xr.cftime_range(
                "2020-03-01", periods=14, freq="2MS", calendar="gregorian"
            )
        }
    )
    assert monthly_time_axis_checker(ds) is False

    # Test with non-existent time key
    ds = xr.Dataset(
        {
            "not_time": xr.cftime_range(
                "2020-03-01", periods=14, freq="MS", calendar="gregorian"
            )
        }
    )
    with pytest.raises(KeyError):
        monthly_time_axis_checker(ds, time_key="time")


## Test repeating_months


def test_repeating_months():
    assert repeating_months(3, 15) == [
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        1,
        2,
        3,
        4,
        5,
    ]
    assert repeating_months(1, 5) == [1, 2, 3, 4, 5]

    with pytest.raises(ValueError):
        repeating_months(13, 5)


## Test last_day_of_month


def test_last_day_of_month():
    assert last_day_of_month(2024, 2, "gregorian") == 29
    assert last_day_of_month(2023, 2, "noleap") == 28
    assert last_day_of_month(2023, 2, "360_day") == 30
    assert last_day_of_month(2023, 4, "standard") == 30

    with pytest.raises(ValueError):
        last_day_of_month(2023, 13, "gregorian")

    with pytest.raises(ValueError):
        last_day_of_month(2023, 1, "invalid_calendar")
