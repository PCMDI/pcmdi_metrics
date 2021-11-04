import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

case_id = "Ex1"
realization = "r6i1p1"

# ROOT PATH FOR MODELS CLIMATOLOGIES
modnames = ["GISS-E2-H"]
modpath = "demo_data/CMIP5_demo_timeseries/historical/atmos/day/pr/pr_day_%(model)_historical_r6i1p1_20000101-20051231.nc"
varModel = "pr"
ModUnitsAdjust = (True, "multiply", 86400.0, "mm d-1")  # kg m-2 s-1 to mm day-1
units = "mm/d"
msyear = 2000
meyear = 2002

# ROOT PATH FOR OBSERVATIONS
reference_data_name = "GPCP-IP"
reference_data_path = "demo_data/PCMDIobs2/atmos/day/pr/GPCP-IP/gn/v20200719/pr.day.GPCP-IP.BE.gn.v20200719.1998-1999.xml"
varOBS = "pr"
ObsUnitsAdjust = (True, "multiply", 86400.0, "mm d-1")  # kg m-2 s-1 to mm day-1
osyear = 1998
oeyear = 1999

# DIRECTORY WHERE TO PUT RESULTS
results_dir = "demo_output/mjo/%(case_id)"

# MISCELLANEOUS
nc_out = False
plot = False  # Create map graphics
update_json = False
