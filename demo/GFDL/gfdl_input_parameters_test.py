import genutil
import getpass

buildDate = '140922' ; # Must be set to allow correct metrics install to be picked up

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'sampletest'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['GFDL-CM4','GFDL-ESM2G',]

### VARIABLES AND OBSERVATIONS TO USE
vars = ['pr','tos']
#vars = ['pr','tas','rlut','rsut','hus_850']
#vars = ['ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500','rlut','rsut','rlutcs','rsutcs','tas']
#vars = ['pr','psl','rlut','rlutcs','rsut','rsutcs','ta_200','ta_850','tas','tauu','tauv','ua_200','ua_850','va_200','va_850','vas','zg_500']

# Observations to use at the moment "default" or "alternate"
ref = 'default'  #'all'
ext = '.nc' ; # '.xml'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
period = '01-12'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
## TEMPLATE EXAMPLE: cmip5.GFDL-ESM2G.historical.r1i1p1.mo.atm.Amon.rlut.ver-1.1980-1999.AC.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)-clim.nc"

## dictionary for custom %(keyword) designed by user
# Driver will match each key to its value defined by a variable name OR all if variable name is not present, OR "" if "all" is not defined
#custom_keys = { "key1": {"all":"key1_value_for_all_var", "tas" : "key1_value_for_tas"},
#    }

## ROOT PATH FOR MODELS CLIMATOLOGIES
#mod_data_path = ''.join(['/home/p1d/',buildDate,'_metrics/test/'])
mod_data_path = ''.join(['/home/',getpass.getuser(),'/',buildDate,'_metrics/test/'])
## ROOT PATH FOR OBSERVATIONS
#obs_data_path = '/home/p1d/obs/'
obs_data_path = ''.join(['/home/',getpass.getuser(),'/obs/'])
## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = './metrics_output_path'
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = './metrics_output_path/Interpolation_Output'
## FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable)%(level).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"
