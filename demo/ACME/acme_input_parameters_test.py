import os

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW: 
################################################################################

## METRICS RUN IDENTIFICATION
case_id = 'sampletest_141126' ; # Defines a subdirectory to output metrics results so multiple runs can be compared

## LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions  = ['ACME-CAM5-SE_v0pt1'] ; # Model identifier
period          = '01-12' ; # Model climatological period (if relevant)
realization     = 'r1i1p1' ; # Model run identifier (if relevant)

## VARIABLES AND OBSERVATIONS TO USE
# Variable acronyms are described in the CMIP5 standard output document - http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
vars = ['pr','prw','tas'] ; # ACME atmos subsuite test
#vars = ['pr','prw','tas'] ; # NCAR atmos subsuite test
#vars = ['pr','psl','rlut','rlutcs','rsut','rsutcs','ta_200','ta_850','tas','ua_200','ua_850','va_200','va_850','zg_500'] ; # GFDL atmos test suite
#vars = ['clt','hfss','pr','prw','psl','rlut','rlutcs','rsdt','rsut','rsutcs','tas','tauu','tauv','ts','uas','vas'] ; # 2d atmos variables
#vars = ['hur','hus','huss','ta','ua','va','zg'] ; # 3d atmos variables
#vars = ['hus_850','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500'] ; # 3d atmos variables - example heights
#vars = ['sos','tos','zos'] ; # 2d ocean variables
#vars = ['rlwcrf','rswcrf'] ; # Non-standard CMIP5 variables (available from obs output)

# Observations to use 'default', 'alternate' or specific enumerated climatology e.g. 'ref3'
ref = ['default'] ; #,'all','alternate','ref3'

## INTERPOLATION OPTIONS
targetGrid          = '2.5x2.5' # Options: '2.5x2.5' or an actual cdms2 grid object
regrid_tool         = 'regrid2' # Options: 'regrid2','esmf'
regrid_method       = 'linear'  # Options: 'linear','conservative', only if tool is esmf
regrid_tool_ocn     = 'esmf'    # Options: 'regrid2','esmf' - Note regrid2 will fail with non lat/lon grids
regrid_method_ocn   = 'linear'  # Options: 'linear','conservative', only if tool is esmf
save_mod_clims      = True      # Options: True or False (Save interpolated model climatologies used in metrics calculations)

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT - AND TEMPLATES FOR MODEL OUTPUT CLIMATOLOGY FILES
base_dir                        = '/work/durack1/Shared/141126_metrics-acme'
# Template example: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template               = "%(variable)_%(model_version)_%(table)_%(period)-clim.nc"
# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path                   = os.path.join(base_dir,"%(model_version)")
# ROOT PATH FOR OBSERVATIONS
obs_data_path                   = '/work/gleckler1/processed_data/metrics_package/obs'
# DIRECTORY WHERE TO PUT RESULTS - will create case_id subdirectory
metrics_output_path             = base_dir
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - will create case_id subdirectory
model_clims_interpolated_output = metrics_output_path
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template        = "%(variable)%(level)_%(model_version)_%(table)_%(realization)_%(model_period)interpolated%(regrid_method)_%(targetGridName)-clim"

## DICTIONARY FOR CUSTOM %(keyword) IMPLEMENTED BY USER FOR CUSTOM METRICS
# Driver will match each key to its value defined by a variable name OR all if variable name is not present, OR "" if "all" is not defined
custom_keys = { "key1": {"all":"key1_value_for_all_var", "tas" : "key1_value_for_tas"}, }
