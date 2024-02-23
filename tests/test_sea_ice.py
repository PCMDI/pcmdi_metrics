import numpy as np
import xarray as xr

from pcmdi_metrics.sea_ice.lib import sea_ice_lib as lib


def create_fake_sea_ice_ds():
    years = [1980, 1999]
    times = xr.cftime_range(
        start="{0}-01-01".format(years[0]),
        end="{0}-12-31".format(years[1]),
        freq="ME",
        calendar="noleap",
        name="time",
    )
    latd = 2
    lond = 2

    values = np.ones((len(times), latd, lond)) * 100.0
    lat = np.arange(80, 80 + latd)
    lon = np.arange(0, lond)
    fake_ds = xr.Dataset(
        {
            "siconc": xr.DataArray(
                data=values,  # enter data here
                dims=["time", "lat", "lon"],
                coords={"time": times, "lat": lat, "lon": lon},
                attrs={"_FillValue": -999.9, "units": "%"},
            )
        }
    )

    area = np.ones((latd, lond)) * 600
    fake_area = xr.Dataset(
        {
            "areacello": xr.DataArray(
                data=area,
                dims=["lat", "lon"],
                coords={"lat": lat, "lon": lon},
                attrs={"_FillValue": -999.9, "units": "km2"},
            )
        }
    )

    return fake_ds, fake_area


def test_get_total_extent():
    siconc, area = create_fake_sea_ice_ds()
    total_extent, te_mean = lib.get_total_extent(siconc.siconc / 100, area.areacello)

    total_ext_true = 600.0 * len(area.lat) * len(area.lon)

    assert te_mean == total_ext_true


def test_mse_t_identical():
    siconc, area = create_fake_sea_ice_ds()
    ts = (siconc.siconc / 100 * area.areacello).sum(("lat", "lon"))
    mse = lib.mse_t(ts, ts, weights=None)
    assert mse == 0.0


def test_mse_twos():
    siconc, area = create_fake_sea_ice_ds()
    ts = (siconc.siconc / 100 * area.areacello).sum(("lat", "lon"))
    ts2 = ts.copy()
    ts2 = ts2 + 2.0
    mse = lib.mse_t(ts, ts2, weights=None)
    assert mse == 4.0


def test_mse_model_identical():
    siconc, area = create_fake_sea_ice_ds()
    ts = (siconc.siconc / 100 * area.areacello).sum(("lat", "lon"))
    mse = lib.mse_model(ts, ts, var=None)
    mse_true = np.zeros(np.shape(ts))
    assert np.array_equal(mse, mse_true)


def test_mse_model_twos():
    siconc, area = create_fake_sea_ice_ds()
    ts = (siconc.siconc / 100 * area.areacello).sum(("lat", "lon"))
    ts2 = ts.copy()
    ts2 = ts2 + 2.0
    mse = lib.mse_model(ts, ts2, var=None)
    mse_true = np.ones(np.shape(ts)) * 4.0
    assert np.array_equal(mse, mse_true)


def test_adjust_units_False():
    ds, _ = create_fake_sea_ice_ds()
    adjust_tuple = (False, 0, 0)
    dsnew = lib.adjust_units(ds, adjust_tuple)
    assert dsnew.equals(ds)


def test_adjust_units_True():
    ds, _ = create_fake_sea_ice_ds()
    adjust_tuple = (True, "multiply", 1e-2)
    ds_new = lib.adjust_units(ds, adjust_tuple)
    ds_true = ds
    ds_true["siconc"] = ds_true.siconc * 1e-2
    assert ds_new.equals(ds_true)


def get_clim_time_bounds():
    siconc, area = create_fake_sea_ice_ds()
    ts = (siconc.siconc / 100 * area.areacello).sum(("lat", "lon"))
    clim1 = lib.get_clim(ts, siconc, "siconc")
    ts2 = ts.copy()
    # Change time bounds name so bounds won't be found
    ts2 = ts2.rename("time_bnds", "time_bounds")
    clim2 = lib.get_clim(ts2, siconc, "siconc")
    assert clim1.equals(clim2)
