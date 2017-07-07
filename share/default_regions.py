import cdutil

regions_specs = {
        'NHEX' : {'domain':cdutil.region.domain(latitude=(30.,90,'ccb'))},
        'SHEX' : {'domain':cdutil.region.domain(latitude=(-90.,-30,'ccb'))},
        'TROPICS': {'domain':cdutil.region.domain(latitude=(-30.,30,'ccb'))},
        'global' : {},
        '90S50S' : {'domain':cdutil.region.domain(latitude=(-90.,-50,'ccb'))},
        '50S20S' : {'domain':cdutil.region.domain(latitude=(-50.,-20,'ccb'))},
        '20S20N': {'domain':cdutil.region.domain(latitude=(-20.,20,'ccb'))},
        '20N50N' : {'domain':cdutil.region.domain(latitude=(20.,50,'ccb'))},
        '50N90N' : {'domain':cdutil.region.domain(latitude=(50.,90,'ccb'))},
        'land_NHEX' : {'value':100, 'domain':cdutil.region.domain(latitude=(30.,90,'ccb'))},
        'land_SHEX' : {'value':100, 'domain':cdutil.region.domain(latitude=(-90.,-30,'ccb'))},
        'land_TROPICS': {'value':100, 'domain':cdutil.region.domain(latitude=(-30.,30,'ccb'))},
        'land' : {'value':100, },
        'ocean_NHEX' : {'value':0, 'domain':cdutil.region.domain(latitude=(30.,90,'ccb'))},
        'ocean_SHEX' : {'value':0, 'domain':cdutil.region.domain(latitude=(-90.,-30,'ccb'))},
        'ocean_TROPICS': {'value':0, 'domain':cdutil.region.domain(latitude=(30.,30,'ccb'))},
        'ocean' : {'value':0, },
        # Below is for modes of variability
        'NAM' : {'domain':cdutil.region.domain(latitude=(20.,90,'ccb'),  longitude=(-180,180,'ccb'))},
        'NAO' : {'domain':cdutil.region.domain(latitude=(20.,80,'ccb'),  longitude=(-90,40,'ccb'))},
        'SAM' : {'domain':cdutil.region.domain(latitude=(-20.,-90,'ccb'),longitude=(0,360,'ccb'))},
        'PNA' : {'domain':cdutil.region.domain(latitude=(20.,85,'ccb'),  longitude=(120,240,'ccb'))},
        'PDO' : {'domain':cdutil.region.domain(latitude=(20.,70,'ccb'),  longitude=(110,260,'ccb'))},
        # Below is for ENSO metrics
        'Nino4'   : {'domain':cdutil.region.domain(latitude=(-5.,5,'ccb'),    longitude=(160,210,'ccb'))},
        'Nino3'   : {'domain':cdutil.region.domain(latitude=(-5.,5,'ccb'),    longitude=(210,270,'ccb'))}, 
        'Nino3.4' : {'domain':cdutil.region.domain(latitude=(-5.,5,'ccb'),    longitude=(190,240,'ccb'))}, 
        'Nino1.2' : {'domain':cdutil.region.domain(latitude=(-10.,0,'ccb'),   longitude=(270,280,'ccb'))}, 
        'TSA'     : {'domain':cdutil.region.domain(latitude=(-20.,0,'ccb'),   longitude=(-30,10,'ccb'))},     # Tropical Southern Atlantic
        'TNA'     : {'domain':cdutil.region.domain(latitude=(5.5,23.5,'ccb'), longitude=(302.5,345.,'ccb'))}, # Tropical Northern Atlantic
        'IO'      : {'domain':cdutil.region.domain(latitude=(-15.,15.,'ccb'), longitude=(40.,110.,'ccb'))},   # Indian Ocean
        'TropPac' : {'domain':cdutil.region.domain(latitude=(-10.,10.,'ccb'), longitude=(150.,270.,'ccb'))},  # Tropical Pacific (correct range?)
        'EqPac'   : {'domain':cdutil.region.domain(latitude=(-5.,5.,'ccb'),   longitude=(150.,270.,'ccb'))},  # Equatorial Pacific
        'IndoPac' : {'domain':cdutil.region.domain(latitude=(-30.,30.,'ccb'), longitude=(30.,240.,'ccb'))},   # Indo-Pacific (correct range?)
        }

default_regions = ['global','NHEX','SHEX','TROPICS']
