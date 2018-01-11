#=================================================
# Analysis Options
#-------------------------------------------------
mode = 'PDO' # Available domains: NAM, NAO, SAM, PNA, PDO
#seasons = ['DJF', 'MAM', 'JJA', 'SON'] # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
#seasons = ['DJF'] 
seasons = ['monthly'] # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
#seasons = ['yearly'] # Available seasons: DJF, MAM, JJA, SON, monthly, yearly

RemoveDomainMean = True # True: Remove Domain Mean from each time step
EofScaling = False # True: Consider EOF with unit variance

""" LandMask option:
- 0 (mask out land, thus over ocean only)
- 1 (mask out ocean, thus over land only)
- None (No masking out)
"""
LandMask = 0

ConvEOF = False # False : On/Off switch for Conventioanl EOF for model
CBF = True # False : On/Off switch for Common Basis Function for model

#=================================================
# Observation
#-------------------------------------------------
obs_name = 'HadISSTv1.1'
obs_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'

varOBS = 'sst'
ObsUnitsAdjust = (False, 0, 0) # degC

osyear = 1900
oeyear = 2005
eofn_obs = 1

#=================================================
# Models
#-------------------------------------------------
modpath = '/work/lee1043/ESGF/xmls/cmip5/historical/atm/mo/VAR/cmip5.MOD.historical.RUN.mo.atm.Amon.VAR.xml'

modpath_lf = '/work/lee1043/ESGF/xmls/cmip5/fx/atm/fx/sftlf/cmip5.MOD.fx.r0i0p0.fx.atm.Amon.sftlf.xml'

modnames = ['ACCESS1-0', 'ACCESS1-3', 'BCC-CSM1-1', 'BCC-CSM1-1-M', 'BNU-ESM',
            'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CESM1-WACCM',
            'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CNRM-CM5-2', 'CSIRO-Mk3-6-0',
            'EC-EARTH', 'FGOALS-g2', 'FGOALS-s2', 'FIO-ESM', 'FIO-ESM',
            'GFDL-CM2p1', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M',
            'GISS-E2-H', 'GISS-E2-H-CC', 'GISS-E2-R', 'GISS-E2-R-CC',
            'HadCM3', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES',
            'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR',
            'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5',
            'MPI-ESM-LR', 'MPI-ESM-MR', 'MPI-ESM-P', 'NorESM1-M', 'NorESM1-ME']

modnames = ['ACCESS1-0', 'ACCESS1-3']

run = '*' # realizations
#run = 'r1i1p1'

varModel = 'ts'
ModUnitsAdjust = (True, 'subtract', 273.15) # degK to degC

msyear = 1900
meyear = 2005
eofn_mod = 1

#=================================================
# Output
#-------------------------------------------------
outdir = './result_test/'+mode
nc_out = True # Write output in NetCDF
plot = True # Create map graphics

#=================================================
# Miss....
#-------------------------------------------------
update_json = True # False
debug = True # False
