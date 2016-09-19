##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW:
##########################################################################

# METRICS RUN IDENTIFICATION
# Defines a subdirectory to output metrics results so multiple runs can be
# compared
case_id = 'sampletest_140910'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
model_versions = ['GFDL-CM4', ]  # ['GFDL-ESM2G',] ; # Model identifier
period = '000101-000112'  # Model climatological period (if relevant)
realization = 'r1i1p1'  # Model run identifier (if relevant)

# VARIABLES AND OBSERVATIONS TO USE
# Variable acronyms are described in the CMIP5 standard output document -
# http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
vars = [
    'pr',
    'psl',
    'rlut',
    'rlutcs',
    'rsut',
    'rsutcs',
    'ta_200',
    'ta_850',
    'tas',
    'ua_200',
    'ua_850',
    'va_200',
    'va_850',
    'zg_500']  # GFDL atmos test suite

# Observations to use 'default', 'alternate' or specific enumerated
# climatology e.g. 'ref3'
ref = ['default']  # ,'all','alternate','ref3'

# INTERPOLATION OPTIONS
targetGrid = '2.5x2.5'  # Options: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # Options: 'regrid2','esmf'
# Options: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
# Options: 'regrid2','esmf' - Note regrid2 will fail with non lat/lon grids
regrid_tool_ocn = 'esmf'
# Options: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'
# Options: True or False (Save interpolated model climatologies used in
# metrics calculations)
save_mod_clims = True

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT - AND TEMPLATES FOR MODEL OUTPUT CLIMATOLOGY FILES
# Template example: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)-clim.nc"
# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/export/durack1/140701_metrics/test_new'
# ROOT PATH FOR OBSERVATIONS
obs_data_path = '/export/durack1/140701_metrics/obs'
# DIRECTORY WHERE TO PUT RESULTS - will create case_id subdirectory
metrics_output_path = '/export/durack1/140701_metrics/test_new'
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - will create
# case_id subdirectory
model_clims_interpolated_output = '/export/durack1/140701_metrics/test_new'
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_historical_" +\
    "%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim%(ext)"

# DICTIONARY FOR CUSTOM %(keyword) IMPLEMENTED BY USER FOR CUSTOM METRICS
# Driver will match each key to its value defined by a variable name OR
# None if variable name is not present, OR "" if None is not defined
custom_keys = {
    "key1": {
        None: "key1_value_for_all_var",
        "tas": "key1_value_for_tas"},
}
