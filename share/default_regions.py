import cdutil

regions_specs = {
        'NHEX' : {'domain':cdutil.region.domain(latitude=(30.,90,'ccb'))},
        'SHEX' : {'domain':cdutil.region.domain(latitude=(-90.,-30,'ccb'))},
        'TROPICS': {'domain':cdutil.region.domain(latitude=(-30.,30,'ccb'))},
        "global" : {},
        'land_NHEX' : {'value':100, 'domain':cdutil.region.domain(latitude=(30.,90,'ccb'))},
        'land_SHEX' : {'value':100, 'domain':cdutil.region.domain(latitude=(-90.,-30,'ccb'))},
        'land_TROPICS': {'value':100, 'domain':cdutil.region.domain(latitude=(-30.,30,'ccb'))},
        "land" : {'value':100, },
        'ocean_NHEX' : {'value':0, 'domain':cdutil.region.domain(latitude=(30.,90,'ccb'))},
        'ocean_SHEX' : {'value':0, 'domain':cdutil.region.domain(latitude=(-90.,-30,'ccb'))},
        'ocean_TROPICS': {'value':0, 'domain':cdutil.region.domain(latitude=(30.,30,'ccb'))},
        "ocean" : {'value':0, },
        # Below is for modes of variability
        "NAM" : {'domain':cdutil.region.domain(latitude=(20.,90.),longitude=(-180.,180.,'oob'))},
        "NAO" : {'domain':cdutil.region.domain(latitude=(20.,80.,'ccn'),longitude=(-90.,40.,'ccn'))},
        "SAM" : {'domain':cdutil.region.domain(latitude=(-20.,-90,'ccn'),longitude=(0.,360.,'ccn'))},
        "PNA" : {'domain':cdutil.region.domain(latitude=(20.,85.,'ccn'),longitude=(120.,240.,'ccn'))},
        "PDO" : {'domain':cdutil.region.domain(latitude=(20.,70.,'ccn'),longitude=(110.,260.,'ccn'))},
        }

default_regions = ['global','NHEX','SHEX','TROPICS']
