import xcdat as xc


def load_regions_specs():
    regions_specs = {
        # Mean Climate
        "global": {},
        "NHEX": {"domain": {"latitude": (30.0, 90)}},
        "SHEX": {"domain": {"latitude": (-90.0, -30)}},
        "TROPICS": {"domain": {"latitude": (-30.0, 30)}},
        "90S50S": {"domain": {"latitude": (-90.0, -50)}},
        "50S20S": {"domain": {"latitude": (-50.0, -20)}},
        "20S20N": {"domain": {"latitude": (-20.0, 20)}},
        "20N50N": {"domain": {"latitude": (20.0, 50)}},
        "50N90N": {"domain": {"latitude": (50.0, 90)}},
        "CONUS": {"domain": {"latitude": (24.7, 49.4), "longitude": (-124.78, -66.92)}},
        "land": {"value": 100},
        "land_NHEX": {"value": 100, "domain": {"latitude": (30.0, 90)}},
        "land_SHEX": {"value": 100, "domain": {"latitude": (-90.0, -30)}},
        "land_TROPICS": {"value": 100, "domain": {"latitude": (-30.0, 30)}},
        "land_CONUS": {
            "value": 100,
            "domain": {"latitude": (24.7, 49.4), "longitude": (-124.78, -66.92)},
        },
        "ocean": {"value": 0},
        "ocean_NHEX": {"value": 0, "domain": {"latitude": (30.0, 90)}},
        "ocean_SHEX": {"value": 0, "domain": {"latitude": (-90.0, -30)}},
        "ocean_TROPICS": {"value": 0, "domain": {"latitude": (30.0, 30)}},
        "ocean_50S50N": {"value": 0.0, "domain": {"latitude": (-50.0, 50)}},
        "ocean_50S20S": {"value": 0.0, "domain": {"latitude": (-50.0, -20)}},
        "ocean_20S20N": {"value": 0.0, "domain": {"latitude": (-20.0, 20)}},
        "ocean_20N50N": {"value": 0.0, "domain": {"latitude": (20.0, 50)}},
        # Modes of variability
        "NAM": {"domain": {"latitude": (20.0, 90), "longitude": (-180, 180)}},
        "NAO": {"domain": {"latitude": (20.0, 80), "longitude": (-90, 40)}},
        "SAM": {"domain": {"latitude": (-20.0, -90), "longitude": (0, 360)}},
        "PNA": {"domain": {"latitude": (20.0, 85), "longitude": (120, 240)}},
        "PDO": {"domain": {"latitude": (20.0, 70), "longitude": (110, 260)}},
        # Monsoon domains for Wang metrics
        # All monsoon domains
        "AllMW": {"domain": {"latitude": (-40.0, 45.0), "longitude": (0.0, 360.0)}},
        "AllM": {"domain": {"latitude": (-45.0, 45.0), "longitude": (0.0, 360.0)}},
        # North American Monsoon
        "NAMM": {"domain": {"latitude": (0.0, 45.0), "longitude": (210.0, 310.0)}},
        # South American Monsoon
        "SAMM": {"domain": {"latitude": (-45.0, 0.0), "longitude": (240.0, 330.0)}},
        # North African Monsoon
        "NAFM": {"domain": {"latitude": (0.0, 45.0), "longitude": (310.0, 60.0)}},
        # South African Monsoon
        "SAFM": {"domain": {"latitude": (-45.0, 0.0), "longitude": (0.0, 90.0)}},
        # Asian Summer Monsoon
        "ASM": {"domain": {"latitude": (0.0, 45.0), "longitude": (60.0, 180.0)}},
        # Australian Monsoon
        "AUSM": {"domain": {"latitude": (-45.0, 0.0), "longitude": (90.0, 160.0)}},
        # Monsoon domains for Sperber metrics
        # All India rainfall
        "AIR": {"domain": {"latitude": (7.0, 25.0), "longitude": (65.0, 85.0)}},
        # North Australian
        "AUS": {"domain": {"latitude": (-20.0, -10.0), "longitude": (120.0, 150.0)}},
        # Sahel
        "Sahel": {"domain": {"latitude": (13.0, 18.0), "longitude": (-10.0, 10.0)}},
        # Gulf of Guinea
        "GoG": {"domain": {"latitude": (0.0, 5.0), "longitude": (-10.0, 10.0)}},
        # North American monsoon
        "NAmo": {"domain": {"latitude": (20.0, 37.0), "longitude": (-112.0, -103.0)}},
        # South American monsoon
        "SAmo": {"domain": {"latitude": (-20.0, 2.5), "longitude": (-65.0, -40.0)}},
    }

    return regions_specs


def region_subset(ds, regions_specs, region=None):
    """
    d: xarray.Dataset
    regions_specs: dict
    region: string
    """

    if (region is None) or (
        (region is not None) and (region not in list(regions_specs.keys()))
    ):
        print("Error: region not defined")
    else:
        if "domain" in list(regions_specs[region].keys()):
            if "latitude" in list(regions_specs[region]["domain"].keys()):
                lat0 = regions_specs[region]["domain"]["latitude"][0]
                lat1 = regions_specs[region]["domain"]["latitude"][1]
                # proceed subset
                if "latitude" in (ds.coords.dims):
                    ds = ds.sel(latitude=slice(lat0, lat1))
                elif "lat" in (ds.coords.dims):
                    ds = ds.sel(lat=slice(lat0, lat1))

            if "longitude" in list(regions_specs[region]["domain"].keys()):
                lon0 = regions_specs[region]["domain"]["longitude"][0]
                lon1 = regions_specs[region]["domain"]["longitude"][1]

                # check original dataset longitude range
                if "longitude" in (ds.coords.dims):
                    lon_min = ds.longitude.min()
                    lon_max = ds.longitude.max()
                elif "lon" in (ds.coords.dims):
                    lon_min = ds.lon.min()
                    lon_max = ds.lon.max()

                # longitude range swap if needed
                if (
                    min(lon0, lon1) < 0
                ):  # when subset region lon is defined in (-180, 180) range
                    if (
                        min(lon_min, lon_max) < 0
                    ):  # if original data lon range is (-180, 180) no treatment needed
                        pass
                    else:  # if original data lon range is (0, 360), convert swap lon
                        ds = xc.swap_lon_axis(ds, to=(-180, 180))

                # proceed subset
                if "longitude" in (ds.coords.dims):
                    ds = ds.sel(longitude=slice(lon0, lon1))
                elif "lon" in (ds.coords.dims):
                    ds = ds.sel(lon=slice(lon0, lon1))

    return ds
