import cdutil

regions_specs = {
    "NHEX": {"domain": cdutil.region.domain(latitude=(30.0, 90))},
    "SHEX": {"domain": cdutil.region.domain(latitude=(-90.0, -30))},
    "TROPICS": {"domain": cdutil.region.domain(latitude=(-30.0, 30))},
    "global": {},
    "90S50S": {"domain": cdutil.region.domain(latitude=(-90.0, -50))},
    "50S20S": {"domain": cdutil.region.domain(latitude=(-50.0, -20))},
    "20S20N": {"domain": cdutil.region.domain(latitude=(-20.0, 20))},
    "20N50N": {"domain": cdutil.region.domain(latitude=(20.0, 50))},
    "50N90N": {"domain": cdutil.region.domain(latitude=(50.0, 90))},
    "land_NHEX": {"value": 100, "domain": cdutil.region.domain(latitude=(30.0, 90))},
    "land_SHEX": {"value": 100, "domain": cdutil.region.domain(latitude=(-90.0, -30))},
    "land_TROPICS": {
        "value": 100,
        "domain": cdutil.region.domain(latitude=(-30.0, 30)),
    },
    "land": {
        "value": 100,
    },
    "ocean_NHEX": {"value": 0, "domain": cdutil.region.domain(latitude=(30.0, 90))},
    "ocean_SHEX": {"value": 0, "domain": cdutil.region.domain(latitude=(-90.0, -30))},
    "ocean_TROPICS": {"value": 0, "domain": cdutil.region.domain(latitude=(30.0, 30))},
    "ocean": {
        "value": 0,
    },
    # Modes of variability
    "NAM": {"domain": cdutil.region.domain(latitude=(20.0, 90), longitude=(-180, 180))},
    "NAO": {"domain": cdutil.region.domain(latitude=(20.0, 80), longitude=(-90, 40))},
    "SAM": {"domain": cdutil.region.domain(latitude=(-20.0, -90), longitude=(0, 360))},
    "PNA": {"domain": cdutil.region.domain(latitude=(20.0, 85), longitude=(120, 240))},
    "PDO": {"domain": cdutil.region.domain(latitude=(20.0, 70), longitude=(110, 260))},
    "AMO": {"domain": cdutil.region.domain(latitude=(0.0, 70), longitude=(-80, 0))},
    # Monsoon domains for Wang metrics
    # All monsoon domains
    "AllMW": {
        "domain": cdutil.region.domain(latitude=(-40.0, 45.0), longitude=(0.0, 360.0))
    },
    "AllM": {
        "domain": cdutil.region.domain(latitude=(-45.0, 45.0), longitude=(0.0, 360.0))
    },
    # North American Monsoon
    "NAMM": {
        "domain": cdutil.region.domain(latitude=(0.0, 45.0), longitude=(210.0, 310.0))
    },
    # South American Monsoon
    "SAMM": {
        "domain": cdutil.region.domain(latitude=(-45.0, 0.0), longitude=(240.0, 330.0))
    },
    # North African Monsoon
    "NAFM": {
        "domain": cdutil.region.domain(latitude=(0.0, 45.0), longitude=(310.0, 60.0))
    },
    # South African Monsoon
    "SAFM": {
        "domain": cdutil.region.domain(latitude=(-45.0, 0.0), longitude=(0.0, 90.0))
    },
    # Asian Summer Monsoon
    "ASM": {
        "domain": cdutil.region.domain(latitude=(0.0, 45.0), longitude=(60.0, 180.0))
    },
    # Australian Monsoon
    "AUSM": {
        "domain": cdutil.region.domain(latitude=(-45.0, 0.0), longitude=(90.0, 160.0))
    },
    # Monsoon domains for Sperber metrics
    # All India rainfall
    "AIR": {
        "domain": cdutil.region.domain(latitude=(7.0, 25.0), longitude=(65.0, 85.0))
    },
    # North Australian
    "AUS": {
        "domain": cdutil.region.domain(
            latitude=(-20.0, -10.0), longitude=(120.0, 150.0)
        )
    },
    # Sahel
    "Sahel": {
        "domain": cdutil.region.domain(latitude=(13.0, 18.0), longitude=(-10.0, 10.0))
    },
    # Gulf of Guinea
    "GoG": {
        "domain": cdutil.region.domain(latitude=(0.0, 5.0), longitude=(-10.0, 10.0))
    },
    # North American monsoon
    "NAmo": {
        "domain": cdutil.region.domain(
            latitude=(20.0, 37.0), longitude=(-112.0, -103.0)
        )
    },
    # South American monsoon
    "SAmo": {
        "domain": cdutil.region.domain(latitude=(-20.0, 2.5), longitude=(-65.0, -40.0))
    },
}

default_regions = ["global", "NHEX", "SHEX", "TROPICS"]
