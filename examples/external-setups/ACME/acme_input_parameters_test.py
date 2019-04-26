import os

##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW:
##########################################################################

# METRICS RUN IDENTIFICATION
# Defines a subdirectory to output metrics results so multiple runs can be
# compared
case_id = 'sampletest_141126'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
test_data_set = ['ACME-CAM5-SE_v0pt1']  # Model identifier
period = '01-12'  # Model climatological period (if relevant)
realization = 'r1i1p1'  # Model run identifier (if relevant)

# VARIABLES AND OBSERVATIONS TO USE
# Variable acronyms are described in the CMIP5 standard output document -
# http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
vars = ['pr', 'prw', 'tas']  # ACME atmos subsuite test

# Observations to use 'default', 'alternate' or specific enumerated
# climatology e.g. 'ref3'
reference_data_set = ['default']  # ,'all','alternate','ref3'

# INTERPOLATION OPTIONS
target_grid = '2.5x2.5'  # Options: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # Options: 'regrid2','esmf'
# Options: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
# Options: 'regrid2','esmf' - Note regrid2 will fail with non lat/lon grids
regrid_tool_ocn = 'esmf'
# Options: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'
# Options: True or False (Save interpolated model climatologies used in
# metrics calculations)
save_test_clims = True

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT - AND TEMPLATES FOR MODEL
# OUTPUT CLIMATOLOGY FILES
base_dir = '/work/durack1/Shared/141126_metrics-acme'
# Template example: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_%(period)-clim.nc"
# ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = os.path.join(base_dir, "%(model_version)")
# ROOT PATH FOR OBSERVATIONS
reference_data_path = '/work/gleckler1/processed_data/metrics_package/obs'
# DIRECTORY WHERE TO PUT RESULTS - will create case_id subdirectory
metrics_output_path = base_dir
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - will create
# case_id subdirectory
test_clims_interpolated_output = metrics_output_path
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_%(realization)_" +\
    "%(model_period)interpolated%(regrid_method)_%(targetGridName)-clim"

# DICTIONARY FOR CUSTOM %(keyword) IMPLEMENTED BY USER FOR CUSTOM METRICS
# Driver will match each key to its value defined by a variable name OR
# all if variable name is not present, OR "" if "all" is not defined
custom_keys = {
    "key1": {
        "all": "key1_value_for_all_var",
        "tas": "key1_value_for_tas"},
}
