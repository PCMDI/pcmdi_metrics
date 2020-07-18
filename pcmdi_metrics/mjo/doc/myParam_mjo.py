import datetime
import glob
import os


def find_latest(path):
    dir_list = [p for p in glob.glob(path+"/v????????")]
    return sorted(dir_list)[-1]


# =================================================
# Background Information
# -------------------------------------------------
mip = 'cmip5'
exp = 'historical'
frequency = 'da'
realm = 'atm'

# =================================================
# Miscellaneous
# -------------------------------------------------
debug = False
# debug = True

nc_out = True
plot = True  # Create map graphics
update_json = False

# =================================================
# Observation
# -------------------------------------------------
reference_data_name = 'GPCP-1-3'
reference_data_path = '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/day/pr/GPCP-1-3/gn/v20200402/pr_day_GPCP-1-3_BE_gn_v20200402_19961002-20170101.nc'  # noqa

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

# =================================================
# Models
# -------------------------------------------------
modpath = os.path.join(
    find_latest('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest'),
    '%(mip)/%(exp)/%(realm)/day/%(variable)',
    '%(mip).%(exp).%(model).%(realization).day.%(variable).xml')

modnames = ['ACCESS1-0']
# modnames = 'all'

realization = 'r1i1p1'
# realization = '*'

varModel = 'pr'
ModUnitsAdjust = (True, 'multiply', 86400.0, 'mm d-1')  # kg m-2 s-1 to mm day-1
units = 'mm/d'

msyear = 1985
meyear = 2004

# =================================================
# Output
# -------------------------------------------------
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmprdir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2'

if debug:
    pmprdir = '/work/lee1043/imsi/result_test'

results_dir = os.path.join(
    pmprdir,
    '%(output_type)', 'mjo',
    '%(mip)', '%(exp)', '%(case_id)')
