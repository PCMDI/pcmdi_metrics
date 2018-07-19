
# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip5'
#exp = 'piControl'
exp = 'historical'
frequency = 'da'
realm = 'atm'

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'CPC'
reference_data_path = '/work/lee1043/DATA/CPC/cpc_precip_1979-2018.xml'

varOBS = 'precip'
ObsUnitsAdjust = (False, 0, 0)  # Pa to hPa; or (False, 0, 0)

osyear = 1961
#oeyear = 1999
oeyear = 1978

# =================================================
# Models
# -------------------------------------------------
modpath = '/work/cmip5-test/new/historical/atmos/day/pr/cmip5.%(model).%(exp).%(realization).day.atmos.day.%(variable).*.xml'
modpath_lf = '/work/lee1043/ESGF/xmls/cmip5/fx/fx/sftlf/cmip5.%(model).fx.r0i0p0.fx.sftlf.xml'

modnames = ['ACCESS1-0', 'ACCESS1-3', 
            'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM', 
            'CanCM4', 'CanESM2', 'CCSM4', 
            'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 
            'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 
            'EC-EARTH', 'FGOALS-g2', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 
            'GISS-E2-H', 'GISS-E2-R', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 
            'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 
            'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5', 
            'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M'] 

modnames = ['CanESM2']

#realization = '*' # realizations
realization = 'r1i1p1'

varModel = 'pr'
ModUnitsAdjust = (True, 'multiply', 86400.0) # kg m-2 s-1 to mm day-1

msyear = 1961
meyear = 1999

# =================================================
# Output
# -------------------------------------------------
results_dir = '/work/lee1043/imsi/result_test/monsoon_sperber'
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics

# =================================================
# Miscellaneous
# -------------------------------------------------
update_json = True  # False
#debug = True # False
debug = False # False
