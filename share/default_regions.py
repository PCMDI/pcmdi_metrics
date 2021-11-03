import cdutil

regions_specs = {
    'NHEX': {'domain': cdutil.region.domain(latitude=(30., 90))},
    'SHEX': {'domain': cdutil.region.domain(latitude=(-90., -30))},
    'TROPICS': {'domain': cdutil.region.domain(latitude=(-30., 30))},
    "global": {},
    '90S50S': {'domain': cdutil.region.domain(latitude=(-90., -50))},
    '50S20S': {'domain': cdutil.region.domain(latitude=(-50., -20))},
    '20S20N': {'domain': cdutil.region.domain(latitude=(-20., 20))},
    '20N50N': {'domain': cdutil.region.domain(latitude=(20., 50))},
    '50N90N': {'domain': cdutil.region.domain(latitude=(50., 90))},
    'land_NHEX': {'value': 100, 'domain': cdutil.region.domain(latitude=(30., 90))},
    'land_SHEX': {'value': 100, 'domain': cdutil.region.domain(latitude=(-90., -30))},
    'land_TROPICS': {'value': 100, 'domain': cdutil.region.domain(latitude=(-30., 30))},
    "land": {'value': 100, },
    'ocean_NHEX': {'value': 0, 'domain': cdutil.region.domain(latitude=(30., 90))},
    'ocean_SHEX': {'value': 0, 'domain': cdutil.region.domain(latitude=(-90., -30))},
    'ocean_TROPICS': {'value': 0, 'domain': cdutil.region.domain(latitude=(30., 30))},
    "ocean": {'value': 0, },

    # Modes of variability
    "NAM": {'domain': cdutil.region.domain(latitude=(20., 90), longitude=(-180, 180))},
    "NAO": {'domain': cdutil.region.domain(latitude=(20., 80), longitude=(-90, 40))},
    "SAM": {'domain': cdutil.region.domain(latitude=(-20., -90), longitude=(0, 360))},
    "PNA": {'domain': cdutil.region.domain(latitude=(20., 85), longitude=(120, 240))},
    "PDO": {'domain': cdutil.region.domain(latitude=(20., 70), longitude=(110, 260))},

    # Monsoon domains for Wang metrics
    # All monsoon domains
    'AllMW': {'domain': cdutil.region.domain(latitude=(-40., 45.), longitude=(0., 360.))},
    'AllM': {'domain': cdutil.region.domain(latitude=(-45., 45.), longitude=(0., 360.))},
    # North American Monsoon
    'NAMM': {'domain': cdutil.region.domain(latitude=(0., 45.), longitude=(210., 310.))},
    # South American Monsoon
    'SAMM': {'domain': cdutil.region.domain(latitude=(-45., 0.), longitude=(240., 330.))},
    # North African Monsoon
    'NAFM': {'domain': cdutil.region.domain(latitude=(0., 45.), longitude=(310., 60.))},
    # South African Monsoon
    'SAFM': {'domain': cdutil.region.domain(latitude=(-45., 0.), longitude=(0., 90.))},
    # Asian Summer Monsoon
    'ASM': {'domain': cdutil.region.domain(latitude=(0., 45.), longitude=(60., 180.))},
    # Australian Monsoon
    'AUSM': {'domain': cdutil.region.domain(latitude=(-45., 0.), longitude=(90., 160.))},

    # Monsoon domains for Sperber metrics
    # All India rainfall
    'AIR': {'domain': cdutil.region.domain(latitude=(7., 25.), longitude=(65., 85.))},
    # North Australian
    'AUS': {'domain': cdutil.region.domain(latitude=(-20., -10.), longitude=(120., 150.))},
    # Sahel
    'Sahel': {'domain': cdutil.region.domain(latitude=(13., 18.), longitude=(-10., 10.))},
    # Gulf of Guinea
    'GoG': {'domain': cdutil.region.domain(latitude=(0., 5.), longitude=(-10., 10.))},
    # North American monsoon
    'NAmo': {'domain': cdutil.region.domain(latitude=(20., 37.), longitude=(-112., -103.))},
    # South American monsoon
    'SAmo': {'domain': cdutil.region.domain(latitude=(-20., 2.5), longitude=(-65., -40.))},
}

default_regions = ['global', 'NHEX', 'SHEX', 'TROPICS']
