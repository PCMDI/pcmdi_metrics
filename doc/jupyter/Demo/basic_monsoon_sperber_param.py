import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# MODEL VARIABLES THAT MUST BE SET
mip = 'cmip5'
exp = 'historical'
#frequency = 'da'
#realm = 'atm'
realization = 'r1i1p1'

# MODEL VERSIONS AND ROOT PATH
#modnames = ['GISS-E2-H']
#modpath = 'demo_data/CMIP5_demo_timeseries/historical/atmos/day/pr/pr_day_GISS-E2-H_historical_r6i1p1_20000101-20051231.nc'
#modpath_lf = 'demo_data/CMIP5_demo_data/cmip5.historical.GISS-E2-H.sftlf.nc' # land fraction mask
#modnames = ['ACCESS1-0']
#modnames = ['CanESM2']
#modnames = ['CCSM4']
modnames = ['all']
modpath = "/work/lee1043/ESGF/xmls/cmip5/historical/day/pr/cmip5.%(model).%(exp).%(realization).day.pr.xml"
modpath_lf = "/work/lee1043/ESGF/xmls/cmip5/historical/fx/sftlf/cmip5.%(model).historical.r0i0p0.fx.sftlf.xml"

varModel = 'pr'
ModUnitsAdjust = (True, 'multiply', 86400.0)  # kg m-2 s-1 to mm day-1
units = 'mm/d'

msyear = 2000
meyear = 2005

# ROOT PATH FOR OBSERVATIONS
reference_data_path = 'demo_data/obs4MIPs_PCMDI_daily/NASA-JPL/GPCP-1-3/day/pr/gn/latest/pr_day_GPCP-1-3_PCMDI_gn_19961002-20170101.nc'
reference_data_name = 'GPCP-IP'
reference_data_lf_path = 'demo_data/misc_demo_data/fx/sftlf.GPCP-IP.1x1.nc'  # land fraction mask

varOBS = 'pr'
ObsUnitsAdjust = (True, 'multiply', 86400.0)  # kg m-2 s-1 to mm day-1

osyear = 1998
oeyear = 2000

includeOBS = False #True

# DIRECTORY WHERE TO PUT RESULTS
results_dir = 'demo_output/monsoon_sperber/Ex1'

# OUTPUT OPTIONS
update_json = False
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
