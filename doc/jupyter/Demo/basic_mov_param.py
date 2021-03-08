import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'basicTestMOV'

# ANALYSIS OPTIONS
variability_mode = 'NAM'  # Available domains: NAM, NAO, SAM, PNA, PDO
seasons = ['DJF']  # Available seasons: DJF, MAM, JJA, SON, monthly, yearly
ConvEOF = True  # Calculate conventioanl EOF for model
CBF = True  # Calculate Common Basis Function (CBF) for model

# MODEL SETTINGS
modpath = 'demo_data/CMIP5_demo_data/psl_Amon_%(model)_historical_r1i1p1_185001-200512.nc'
modnames = ['ACCESS1-0']
varModel = 'psl'
ModUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa
msyear = 1900
meyear = 2005
eofn_mod = 1

# OBSERVATIONS SETTINGS
reference_data_path = 'demo_data/PCMDIobs2/atmos/mon/psl/20CR/gn/v20200707/psl_mon_20CR_BE_gn_v20200707_187101-201212.nc'
reference_data_name = 'NOAA-20CR'
varOBS = 'psl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)
osyear = 1900
oeyear = 2005
eofn_obs = 1

# DIRECTORY WHERE TO PUT RESULTS
results_dir = os.path.join(
    'demo_output',
    "%(case_id)")

# OUTPUT OPTIONS    
nc_out = True  # Write output in NetCDF
plot = True  # Create map graphics
update_json = True  # False

