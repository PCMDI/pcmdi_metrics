import numpy as np
import xarray as xr


def create_fake_sea_ice_ds():
    years = [1980, 1999]
    times = xr.cftime_range(
        start="{0}-01-01".format(years[0]),
        end="{0}-12-31".format(years[1]),
        freq="M",
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
    total_extent, te_mean = get_total_extent(siconc, area)

    total_ext_true = 600.0 * len(area.lat) * len(area.lon)

    assert te_mean == total_ext_true


def test_mse_t():
    siconc, area = create_fake_sea_ice_ds()
    mse = mse_t(siconc, siconc, weights=None)
    assert mse == 0.0


def test_mse_model():
    siconc, area = create_fake_sea_ice_ds()
    mse = mse_model(siconc, siconc, var=None)
    assert mse == 0.0


def test_adjust_units():
    ds, _ = create_fake_sea_ice_ds()
    adjust_tuple = (False, 0, 0)
    dsnew = adjust_units(ds, adjust_tuple)
    assert dsnew.equals(ds)
