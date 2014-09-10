################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
################################################################################

## METRICS RUN IDENTIFICATION
case_id = 'sampletest_140910' ; # Defines a subdirectory to output metrics results so multiple runs can be compared

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions  = ['GFDL-CM4',] ; # ['GFDL-ESM2G',] ; # Model identifier
model_period    = '000101-000112' ; # Model climatological period (if relevant)
realization     = 'r1i1p1' ; # Model run identifier (if relevant)

### VARIABLES AND OBSERVATIONS TO USE
# Variable acronyms are described in the CMIP5 standard output document - http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
vars = ['pr','psl','rlut','rlutcs','rsut','rsutcs','ta_200','ta_850','tas','ua_200','ua_850','va_200','va_850','zg_500'] ; # GFDL atmos test suite
#vars = ['clt','hfss','pr','prw','psl','rlut','rlutcs','rsdt','rsut','rsutcs','tas','tauu','tauv','ts','uas','vas'] ; # 2d atmos variables
#vars = ['hur','hus','huss','ta','ua','va','zg'] ; # 3d atmos variables
#vars = ['hus_850','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500'] ; # 3d atmos variables - example heights
#vars = ['sos','tos','zos'] ; # 2d ocean variables
#vars = ['rlwcrf','rswcrf'] ; # Non-standard CMIP5 variables (available from obs output)

# Observations to use "default" or "alternate"
ref = ['default']  #,'all','alternate','ref3']

# INTERPOLATION OPTIONS
targetGrid          = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool         = 'regrid2' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method       = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn     = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn   = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
save_mod_clims      = True      # Options: True or False (Save interpolated model climatologies used in metrics calculations)

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## TEMPLATES FOR CLIMATOLOGY FILES
## Template example: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template               = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(model_period)-clim.nc"
## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path                   = '/export/durack1/140701_metrics/test_new'
## ROOT PATH FOR OBSERVATIONS
obs_data_path                   = '/export/durack1/140701_metrics/obs'
## DIRECTORY WHERE TO PUT RESULTS - will create case_id subdirectory
metrics_output_path             = '/export/durack1/140701_metrics/test_new'
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - will create case_id subdirectory
model_clims_interpolated_output = '/export/durack1/140701_metrics/test_new'
## FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template        = "%(variable)%(level)_%(model_version)_%(table)_historical_%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim%(ext)"

## dictionary for custom %(keyword) designed by user
# Driver will match each key to its value defined by a variable name OR all if variable name is not present, OR "" if "all" is not defined
custom_keys = { "key1": {"all":"key1_value_for_all_var", "tas" : "key1_value_for_tas"}, }