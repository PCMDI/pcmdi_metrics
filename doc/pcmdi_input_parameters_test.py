import genutil

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'sampletest1'
#case_id = 'cmip5_test'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G',]
#model_versions = ['MRI-CGCM3',]

### VARIABLES AND OBSERVATIONS TO USE
vars = ['zos','pr','rlut','tos']
#vars = ['tas','pr']
#vars = ['pr','tas','tos']
#vars = ['tas','tos']
vars = ['tos']
vars = ['tas']
vars=['hus_850',]
vars = ['pr','tas','rlut','rsut','hus_850']
vars = ['ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500','rlut','rsut','rlutcs','rsutcs','tas']
#vars = ['rlutcs','rsutcs','vas','tas']
vars = ['tauu','tauv']
#vars = ['ta_850']
vars = ['zos']

# Observations to use at the moment "default" or "alternate"
ref = 'all'
ref = ['default']  #,'alternate','ref3']
ext = '.xml'  #'.nc'
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'regrid2' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
model_period = '198501-200512'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
## TEMPLATE EXAMPLE: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(model_period)-clim.nc"

## dictionary for custom %(keyword) designed by user
# Driver will match each key to its value defined by a variable name OR all if variable name is not present, OR "" if "all" is not defined
custom_keys = { "key1": {"all":"key1_value_for_all_var", "tas" : "key1_value_for_tas"}, }

## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package/' 
#mod_data_path = '/work/gleckler1/processed_data/cmip5clims-AR5-frozen_1dir/' 
## ROOT PATH FOR OBSERVATIONS
obs_data_path = '/work/gleckler1/processed_data/metrics_package/obs/%{realm}/'
## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/'
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'
## FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
#filename_output_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table).%(variable)%(level).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_historical_%(realization)_%(period).interpolated.%(regridMethod).%(targetGridName)-clim%(ext)"
