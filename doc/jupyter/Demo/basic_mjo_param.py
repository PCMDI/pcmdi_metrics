import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

case_id = 'Ex1'

# ROOT PATH FOR MODELS CLIMATOLOGIES
modnames = ['ACCESS1-0']
#modpath = '/Users/ordonez4/Metrics/demo_data/pr.day.ACCESS1-0.historical.r1i1p1.20000101-20051231.nc'
modpath = '~/Metrics/demo_data/pr_day_ACCESS1-0_historical_r1i1p1_20000101-20051231.nc'
varModel = 'pr'
ModUnitsAdjust = (True, 'multiply', 86400.0, 'mm d-1')  # kg m-2 s-1 to mm day-1
units = 'mm/d'
msyear = 2000
meyear = 2005

# ROOT PATH FOR OBSERVATIONS
reference_data_name = 'GPCP-1-3'
#reference_data_path = '/Users/ordonez4/Metrics/demo_data/pr_day_GPCP-1-3_BE_gn_v20200924_19961002-20170101.nc'
reference_data_path = '~/Metrics/demo_data/pr_day_GPCP-1-3_BE_gn_v20200924_19961002-20170101.nc'
varOBS = 'pr'
ObsUnitsAdjust = (True, 'multiply', 86400.0, 'mm d-1')  # kg m-2 s-1 to mm day-1
osyear = 1996
oeyear = 2017

# DIRECTORY WHERE TO PUT RESULTS
results_dir = 'demo_output/mjo/%(case_id)'

# MISCELLANEOUS
nc_out = False
plot = False  # Create map graphics
update_json = False