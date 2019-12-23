import datetime
import os

# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip5'
exp = 'historical'
frequency = 'da'
realm = 'atm'

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'GPCP-1-3'
#reference_data_path = '/p/user_pub/pmp/pmp_results/tree_v0.3/pmp_v1.1.2/data/PMPObs/PMPObs_v1.3/atmos/day/pr/GPCP-1-3/gn/v20180816/pr_day_GPCP-1-3_BE_gn_19961002-20170101.nc'  # noqa
reference_data_path = '/p/user_pub/PCMDIobs/PCMDIobs2.0/atmos/day/pr/GPCP-1-3/gn/v20190225/pr_day_GPCP-1-3_BE_gn_19961002-20170101.nc'  # noqa

varOBS = 'pr'
ObsUnitsAdjust = (True, 'multiply', 86400.0, 'mm d-1')  # kg m-2 s-1 to mm day-1

"""
reference_data_name = 'GPCP-1-2'
reference_data_path = '/work/lee1043/cdat/pmp/MJO_metrics/UW_raw_201812/DATA/GPCPv1.2/daily.19970101_20101231.nc'
varOBS = 'p'
ObsUnitsAdjust = (False, 0, 0, 0, 0)
"""

osyear = 1997
oeyear = 2010

includeOBS = True

# =================================================
# Models
# -------------------------------------------------
modpath = '/work/lee1043/ESGF/xmls/%(mip)/historical/day/pr/%(mip).%(model).%(exp).%(realization).day.%(variable).xml'

modnames = ['ACCESS1-0', 'ACCESS1-3', 'BCC-CSM1-1', 'BCC-CSM1-1-M', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-R', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'INMCM4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC-ESM', 'MIROC-ESM-CHEM', 'MIROC4h', 'MIROC5', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M']  # noqa

#modnames = ['ACCESS1-0']
modnames = ['CanCM4']
modnames = 'all'

#realization = 'r1i1p1'
realization = '*'

varModel = 'pr'
ModUnitsAdjust = (True, 'multiply', 86400.0, 'mm d-1')  # kg m-2 s-1 to mm day-1
units = 'mm/d'

msyear = 1985
meyear = 2004

# =================================================
# Output
# -------------------------------------------------
#case_id = "{:v%Y%m%d-%H%M}".format(datetime.datetime.now())
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
#results_dir = '/work/lee1043/imsi/result_test/%(output_type)/monsoon/monsoon_sperber/'+case_id
results_dir = os.path.join(
    #'/work/lee1043/imsi/result_test',
    '/p/user_pub/pmp/pmp_results/pmp_v1.1.2',
    '%(output_type)', 'mjo',
    mip, exp, case_id)
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics

# =================================================
# Miscellaneous
# -------------------------------------------------
debug = False
update_json = True
