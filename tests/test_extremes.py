import numpy as np
import xarray as xr

from pcmdi_metrics.extremes.lib import compute_metrics


def create_random_precip(years, max_val=None, min_val=None):
    # Returns array of precip along with covariate and sftlf
    times = xr.cftime_range(
        start="{0}-01-01".format(years[0]),
        end="{0}-12-31".format(years[1]),
        freq="D",
        calendar="noleap",
        name="time",
    )
    latd = 2
    lond = 2

    nyears = int(len(times) / 365)
    total_inc = 3
    n = np.arange(0, total_inc, total_inc / nyears)
    fake_cov = np.arange(0, 0 + total_inc, total_inc / nyears)[0:nyears]
    co2arr = np.zeros((len(times), latd, lond))
    n0 = 0
    for n in fake_cov:
        n1 = n0 + 365
        co2arr[n0:n1, :, :] = n
        n0 += 365

    values = (
        np.ones((len(times), latd, lond)) * 20
        + np.random.randint(-10, high=10, size=(len(times), latd, lond))
        + co2arr * np.random.random()
    )
    values = values / 86400  # convert to kg m-2 s-1
    lat = np.arange(0, latd)
    lon = np.arange(0, lond)
    fake_ds = xr.Dataset(
        {
            "pr": xr.DataArray(
                data=values,  # enter data here
                dims=["time", "lat", "lon"],
                coords={"time": times, "lat": lat, "lon": lon},
                attrs={"_FillValue": -999.9, "units": "kg m-2 s-1"},
            )
        }
    )

    fake_ds["time"].encoding["calendar"] = "noleap"
    fake_ds["time"].encoding["units"] = "days since 0000-01-01"
    fake_ds = fake_ds.bounds.add_missing_bounds()

    if max_val is not None:
        fake_ds["pr"] = fake_ds.pr.where(fake_ds.pr <= max_val, max_val)
    if min_val is not None:
        fake_ds["pr"] = fake_ds.pr.where(fake_ds.pr >= min_val, min_val)

    sftlf_arr = np.ones((latd, lond)) * 100
    sftlf_arr[0, 0] = 0
    sftlf = xr.Dataset(
        {
            "sftlf": xr.DataArray(
                data=sftlf_arr,
                dims=["lat", "lon"],
                coords={"lat": lat, "lon": lon},
                attrs={"_FillValue": -999.9},
            )
        }
    )
    sftlf = sftlf.bounds.add_missing_bounds(["X", "Y"])

    return fake_ds, fake_cov, sftlf


def create_seasonal_precip(season):
    # Returns array of precip along with covariate and sftlf
    sd = {"DJF": [1, 2, 12], "MAM": [3, 4, 5], "JJA": [6, 7, 8], "SON": [9, 10, 11]}
    mos = sd[season]

    years = [1980, 1981]
    times = xr.cftime_range(
        start="{0}-01-01".format(years[0]),
        end="{0}-12-31".format(years[1]),
        freq="D",
        calendar="noleap",
        name="time",
    )
    latd = 2
    lond = 2

    values = np.ones((len(times), latd, lond))
    lat = np.arange(0, latd)
    lon = np.arange(0, lond)
    fake_ds = xr.Dataset(
        {
            "pr": xr.DataArray(
                data=values,  # enter data here
                dims=["time", "lat", "lon"],
                coords={"time": times, "lat": lat, "lon": lon},
                attrs={"_FillValue": -999.9, "units": "kg m-2 s-1"},
            )
        }
    )
    fake_ds = fake_ds.where(
        (
            (fake_ds["time.month"] == mos[0])
            | (fake_ds["time.month"] == mos[1])
            | (fake_ds["time.month"] == mos[2])
        ),
        0.0,
    )
    fake_ds["time"].encoding["calendar"] = "noleap"
    fake_ds["time"].encoding["units"] = "days since 0000-01-01"
    fake_ds = fake_ds.bounds.add_missing_bounds()

    sftlf_arr = np.ones((latd, lond)) * 100
    sftlf_arr[0, 0] = 0
    sftlf = xr.Dataset(
        {
            "sftlf": xr.DataArray(
                data=sftlf_arr,
                dims=["lat", "lon"],
                coords={"lat": lat, "lon": lon},
                attrs={"_FillValue": -999.9},
            )
        }
    )
    sftlf = sftlf.bounds.add_missing_bounds(["X", "Y"])

    return fake_ds, sftlf


def test_seasonal_averager_settings():
    # Testing that the defaults and mask are set
    ds, _, sftlf = create_random_precip([1980, 1981])
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(PR, sftlf)

    assert S.dec_mode == "DJF"
    assert S.drop_incomplete_djf
    assert S.annual_strict
    assert S.sftlf.equals(sftlf["sftlf"])


def test_seasonal_averager_ann_max():
    drop_incomplete_djf = True
    dec_mode = "DJF"
    annual_strict = True
    ds, _, sftlf = create_random_precip([1980, 1981])
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    ann_max = S.annual_stats("max", pentad=False)

    assert np.mean(ann_max) == np.mean(ds.groupby("time.year").max(dim="time"))


def test_seasonal_averager_ann_min():
    drop_incomplete_djf = True
    dec_mode = "DJF"
    annual_strict = True
    ds, _, sftlf = create_random_precip([1980, 1981])
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    ann_min = S.annual_stats("min", pentad=False)

    assert np.mean(ann_min) == np.mean(ds.groupby("time.year").min(dim="time"))


# Test that drop_incomplete_djf puts nans in correct places
# Test that rolling averages for say a month is matching manual version


def test_seasonal_averager_ann_djf():
    drop_incomplete_djf = True
    dec_mode = "DJF"
    annual_strict = True
    ds, sftlf = create_seasonal_precip("DJF")
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    djf = S.seasonal_stats("DJF", "max", pentad=False)

    assert djf.max() == 1.0
    assert djf.mean() == 1.0


def test_seasonal_averager_rolling_mam():
    ds, sftlf = create_seasonal_precip("MAM")
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(PR, sftlf)
    S.calc_5day_mean()

    # Get the MAM mean value of the rolling mean calculated by the seasonal averager
    rolling_mean = float(
        S.pentad.where(((ds["time.month"] >= 3) & (ds["time.month"] <= 5))).mean()
    )

    # This is what the mean value of the 5-day rolling means should be, if
    # MAM are 1 and all other times are 0
    true_mean = ((1 / 5) + (2 / 5) + (3 / 5) + (4 / 5) + 1 * (31 - 4) + 30 + 31) / (
        31 + 30 + 31
    )

    assert rolling_mean == true_mean


def test_seasonal_averager_rolling_djf():
    drop_incomplete_djf = False
    dec_mode = "DJF"
    annual_strict = True
    ds, sftlf = create_seasonal_precip("DJF")
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    S.calc_5day_mean()

    # Get the DJF mean value of the rolling mean calculated by the seasonal averager
    rolling_mean = float(
        S.pentad.where(
            (
                (ds["time.month"] == 1)
                | (ds["time.month"] == 2)
                | (ds["time.month"] == 12)
            )
        ).mean()
    )

    # This is what the mean value of the 5-day rolling means should be, if
    # DJF are 1 and all other times are 0. Have to slice off 4 days from the first January
    # because that is where the time series starts
    D = 31
    J = 31
    F = 28
    total_days = D + J + F
    true_mean = (
        (J - 4)
        + F
        + (1 / 5)
        + (2 / 5)
        + (3 / 5)
        + (4 / 5)
        + (D - 4)
        + J
        + F
        + (1 / 5)
        + (2 / 5)
        + (3 / 5)
        + (4 / 5)
        + (D - 4)
    ) / (2 * total_days - 4)

    assert rolling_mean == true_mean


"""def test_seasonal_averager_drop_djf():
    drop_incomplete_djf = True
    dec_mode = "DJF"
    annual_strict = True
    ds, sftlf = create_seasonal_precip("DJF")
    PR = compute_metrics.TimeSeriesData(ds, "pr")
    S = compute_metrics.SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    djf = S.seasonal_stats("DJF", "max", pentad=False)
"""
