
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
reference_data_name = 'GPCP'
reference_data_path = '/p/user_pub/pmp/pmp_results/tree_v0.3/pmp_v1.1.2/data/PMPObs/PMPObs_v1.3/atmos/day/pr/GPCP-1-3/gn/v20180816/pr_day_GPCP-1-3_BE_gn_19961002-20170101.nc'
reference_data_lf_path = '/work/lee1043/DATA/LandSeaMask_1x1_NCL/NCL_LandSeaMask_rewritten.nc'

varOBS = 'pr'
ObsUnitsAdjust = (True, 'multiply', 86400.0) # kg m-2 s-1 to mm day-1

osyear = 1996
oeyear = 2016

includeOBS = True

# =================================================
# Models
# -------------------------------------------------
modpath = '/work/lee1043/ESGF/xmls/cmip5/historical/day/pr/cmip5.%(model).%(exp).%(realization).day.pr.xml'
modpath_lf = '/work/lee1043/ESGF/xmls/cmip5/fx/fx/sftlf/cmip5.%(model).fx.r0i0p0.fx.sftlf.xml'

modnames = ['ACCESS1-0', 'ACCESS1-3', 'BCC-CSM1-1', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-R', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M']

#modnames = ['CanESM2']

#realization = '*' # realizations
realization = 'r1i1p1'

varModel = 'pr'
ModUnitsAdjust = (True, 'multiply', 86400.0) # kg m-2 s-1 to mm day-1
units = 'mm/d'

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
