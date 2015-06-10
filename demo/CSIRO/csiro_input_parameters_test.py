import datetime,getpass

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
################################################################################

# Set timestamp to use in metrics generation
time_format = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
#case_id = '_'.join([time_format,'sampletest']) ; # Create timestamped output directory
case_id = 'sampletest'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['ACCESS1-0','ACCESS1-3',]

### VARIABLES AND OBSERVATIONS TO USE
# Variable acronyms are described in the CMIP5 standard output document - http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
#vars = ['clt','hfss','pr','prw','psl','rlut','rlutcs','rsdt','rsut','rsutcs','tas','tauu','tauv','ts','uas','vas'] ; # 2d atmos variables
#vars = ['hur','hus','huss','ta','ua','va','zg'] ; # 3d atmos variables
#vars = ['hus_850','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500'] ; # 3d atmos variables - example heights
#vars = ['sos','tos','zos'] ; # 2d ocean variables
#vars = ['rlwcrf','rswcrf'] ; # Non-standard CMIP5 variables (available from obs output)
vars = ['pr','psl','rlut','rlutcs','rsut','rsutcs','ta_850','tas','tos','ua_200','ua_850','uas','va_200','va_850','vas','zg_500'] ; # CSIRO test suite

# Observations to use "default", "alternate" or "all" or a specific obs reference e.g. "ref3"
ref = 'all' ; # 'default' ; 'all' ; # Selecting 'default' uses a single obs dataset, 'all' processes against all available datasets
ext = '.nc' ; # '.xml'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
period      = '050001-052912'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
## TEMPLATE EXAMPLE: pr_ACCESS1-0_piControl_Amon_r1i1p1_050001-052912-clim.nc
filename_template = "%(variable)_%(model_version)_piControl_%(table)_%(realization)_%(period)-clim.nc"

## dictionary for custom %(keyword) designed by user
# Driver will match each key to its value defined by a variable name OR all if variable name is not present, OR "" if "all" is not defined
#custom_keys = { "key1": {"all":"key1_value_for_all_var", "tas" : "key1_value_for_tas"},
#    }

## ROOT PATH FOR MODELS CLIMATOLOGIES
#mod_data_path = ''.join(['/short/p66/pjd599/PCMDI_METRICS/test/'])
mod_data_path = ''.join(['/short/p66/',getpass.getuser(),'/test/ncs/'])
## ROOT PATH FOR OBSERVATIONS
#obs_data_path = '/short/p66/pjd599/obs/'
obs_data_path = ''.join(['/short/p66/',getpass.getuser(),'/obs/'])
## DIRECTORY WHERE TO PUT RESULTS - case_id will be appended to this path
metrics_output_path = './metrics_output_path'
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - case_id will be appended to this path
model_clims_interpolated_output = './metrics_output_path/interpolation_output'
## FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(model_version)_experiment_%(table)_%(realization)_%(variable)%(level)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-AC%(ext)"
