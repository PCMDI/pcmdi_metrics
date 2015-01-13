################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW: 
################################################################################

## METRICS RUN IDENTIFICATION
case_id = 'sampletest_140910' ; # Defines a subdirectory to output metrics results so multiple runs can be compared

## LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions  = ['GFDL-CM4',] ; # ['GFDL-ESM2G',] ; # Model identifier

## Below are the STANDARD keys that the main code will be looking for
period    = '000101-000112' ; # Model climatological period (if relevant)
realization     = 'r1i1p1' ; # Model run identifier (if relevant)


## MODEL SPECIFIC PARAMETERS
model_tweaks = {
    ## Keys are model accronym or None which applies to all model entries
    None : {
      ## Variables name mapping to map your local var names to CMIP5 official
      "variable_mapping" : { "tos" : "tos"},
      },
    "GFDL-ESM2G" : {
      "variable_mapping" : { "tas" : "tas_ac"},
      },
    }

## VARIABLES AND OBSERVATIONS TO USE
# Variable acronyms are described in the CMIP5 standard output document - http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
# 2d atmos variables
#   vars = ['clt','hfss','pr','prw','psl','rlut','rlutcs','rsdt','rsut','rsutcs','tas','tauu','tauv','ts','uas','vas']
# 3d atmos variables
#   vars = ['hur','hus','huss','ta','ua','va','zg']
# 3d atmos variables - example heights
#   vars = ['hus_850','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500']
# 2d ocean variables
#   vars = ['sos','tos','zos']
# Non-standard CMIP5 variables (available from obs output)
#   vars = ['rlwcrf','rswcrf']
# vars you are actually interested in
vars = ['pr','psl','rlut','rlutcs','rsut','rsutcs','ta_200','ta_850','tas','ua_200','ua_850','va_200','va_850','zg_500']

# Observations to use 'default', 'alternate' or specific enumerated climatology e.g. 'ref3'
ref = ['default'] #,'all','alternate','ref3'

## INTERPOLATION OPTIONS
targetGrid          = '2.5x2.5' # Options: '2.5x2.5' or an actual cdms2 grid object
regrid_tool         = 'regrid2' # Options: 'regrid2','esmf'
regrid_method       = 'linear'  # Options: 'linear','conservative', only if tool is esmf
regrid_tool_ocn     = 'esmf'    # Options: 'regrid2','esmf' - Note regrid2 will fail with non lat/lon grids
regrid_method_ocn   = 'linear'  # Options: 'linear','conservative', only if tool is esmf
save_mod_clims      = True      # Options: True or False (Save interpolated model climatologies used in metrics calculations)

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT - AND TEMPLATES FOR MODEL OUTPUT CLIMATOLOGY FILES
## Following are custom keys specific to your local system
## it is a python dictionary
## keys are your custom keys, the "value" for this key is actually defined by another dictionary
## This second dictionary maps the key value to each specific variable
## use None if you want a value to be used for every variables not specifically defined
custom_keys = { "key1": {None:"key1_value_for_all_var", "tas" : "key1_value_for_tas"}, }

## By default file names are constructed using the following keys:
## %(variable) # set by driver
## %(realm)
## %(table)
## %(level) # extracted by driver from your var input above (if defined)
## %(model_version) # set by driver from list model_versions defined above
## %(realization)
## %(period)
## %(ext)

## Templates for input climatology files
## TEMPLATE EXAMPLE (once constructed) :
## tas: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912_key1_value_for_tas-clim.nc
## tos: tos_GFDL-ESM2G_Omon_historical_r1i1p1_198001-199912_key1_value_for_all_var-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)_%(key1)-clim.nc"
## filename template for input landsea masks ('sftlf')
sftlf_filename_template = "sftlf_%(model_version).nc"
## Do we generate sftlf if file not found?
## default is False
generate_sftlf = True

# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path                   = '/export/durack1/140701_metrics/test_new'
# ROOT PATH FOR OBSERVATIONS
obs_data_path                   = '/export/durack1/140701_metrics/obs'
# DIRECTORY WHERE TO PUT RESULTS - will create case_id subdirectory
metrics_output_path             = '/export/durack1/140701_metrics/test_new'
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - will create case_id subdirectory
model_clims_interpolated_output = '/export/durack1/140701_metrics/test_new'
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template        = "%(variable)%(level)_%(model_version)_%(table)_historical_%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim%(ext)"

## CUSTOM METRICS
## The following allow users to plug in a set of custom metrics
## Function needs to take in var name, model clim, obs clim
## Function needs to return a dictionary
## dict pairs are: { metrics_name:float }

import pcmdi_metrics # Or whatever your custom metrics package name is
compute_custom_metrics = pcmdi_metrics.pcmdi.compute_metrics
#or
def mymax(slab,nm):
  return {"custom_%s_max" % nm:float(slab.max())}

def mymin(slab,nm):
  return {"custom_%s_min" % nm:float(slab.min())}

def my_custom(var,dm,do):
  out = {}
  for f in [mymax,mymin]:
    out.update(f(dm,"model"))
    out.update(f(dm,"ref"))
  out["some_custom"]=1.5
  return out
compute_custom_metrics = my_custom
