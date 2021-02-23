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
modpath = '$INPUT_DIR$/...'
modnames = ['ACCESS1-0', 'CanCM4']
varModel = 'psl'
ModUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa
msyear = 1900
meyear = 2005
eofn_mod = 1

# OBSERVATIONS SETTINGS
reference_data_path = '$INPUT_DIR$/PCMDIobs2_clims'
reference_data_name = ''
varOBS = 'psl'
ObsUnitsAdjust = (True, 'divide', 100.0)  # Pa to hPa; or (False, 0, 0)
osyear = 1900
oeyear = 2005
eofn_obs = 1

# DIRECTORY WHERE TO PUT RESULTS
results_dir = os.path.join(
    '$OUTPUT_DIR$',
    "%(case_id)")

# OUTPUT OPTIONS    
nc_out = False  # Write output in NetCDF
plot = False  # Create map graphics
update_json = True  # False

