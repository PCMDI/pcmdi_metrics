def create_fake_sea_ice_ds():
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

    values = np.ones((len(times), latd, lond)) * 100.
    lat = np.arange(0, latd)
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

    area = np.ones((latd,lond)) * 25
    fake_area = xr.Dataset(
      {
        "areacello": xr.DataArray(
          data=area,
          dims=["lat","lon"],
          coords={"lat":lat,"lon":lon},
          attrs={"_FillValue": -999.9, "units": "km2"}
        )
      }
    )

    return fake_ds, fake_area

def test_get_total_extent():
    pass

def test_mse_t():
    pass

def test_mse_model():
    pass

def test_adjust_units():
    pass

