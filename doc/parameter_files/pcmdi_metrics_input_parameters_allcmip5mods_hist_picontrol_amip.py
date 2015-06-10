################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################
#  
#  EXPERIMENT OPTIONS:  amip, historical or picontrol
exp = 'amip'
exp = 'historical'
exp = 'picontrol'

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'sampletest1'

if exp == 'amip': case_id = 'amip5_test'
if exp == 'historical': case_id = 'cmip5_test'
#if exp == 'picontrol': case_id = 'cmip5_test'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME

if exp == 'historical':
  model_versions = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5-1-FV2', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CESM1-WACCM', 'CESM1-WSCCM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'FGOALS-s2', 'FIO-ESM', 'GFDL-CM2p1', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H-CC', 'GISS-E2-H', 'GISS-E2-R-CC', 'GISS-E2-R', 'HadCM3', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC4h', 'MIROC5', 'MIROC-ESM-CHEM', 'MIROC-ESM', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'NorESM1-ME', 'NorESM1-M']
if exp == 'amip':
  model_versions = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM', 'CanAM4', 'CCSM4', 'CESM1-CAM5', 'CMCC-CM', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'FGOALS-s2', 'GFDL-CM3', 'GFDL-HIRAM-C180', 'GFDL-HIRAM-C360', 'GISS-E2-R', 'HadGEM2-A', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC5', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MRI-AGCM3-2H', 'MRI-AGCM3-2S', 'MRI-CGCM3', 'NorESM1-M']
if exp == 'picontrol':
  model_versions =['CSIRO-Mk3-6-0', 'CESM1-CAM5', 'GFDL-ESM2G', 'MIROC4h', 'bcc-csm1-1', 'HadGEM2-AO', 'GFDL-ESM2M', 'CCSM4', 'ACCESS1-3', 'CESM1-BGC', 'FGOALS-g2', 'CESM1-FASTCHEM', 'ACCESS1-0', 'bcc-csm1-1-m', 'GFDL-CM3', 'CESM1-WACCM'] 
#model_versions = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1' ]

simulation_description_mapping = {"Login":"Login", "Center":"Center", "CMIP5CreationDate" : "creation_date","CMIP5_tracking_id":'tracking_id'}
simulation_description_mapping = {"creation_date" : "creation_date","tracking_id":'tracking_id',}

### VARIABLES AND OBSERVATIONS TO USE
vars = ['zos','tos']
realm = 'Omon'
#vars = ['pr','prw','tas','huss','uas','vas','psl','rlut','rsut','rlutcs','rsutcs','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500','hus_850']
#realm = 'Amon'

## MODEL SPECIFIC PARAMETERS
model_tweaks = {
    ## Keys are model accronym or None which applies to all model entries
    None : {
      ## Variables name mapping
      "variable_mapping" : { "rlwcrf" : "rlutcre"},
      },
    "GFDL-ESM2G" : {
      "variable_mapping" : { "tos" : "tos"},
      },
    }

## REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
regions = {"tas" : [None,"land","ocean"],
           "uas" : [None,"land","ocean"],
           "vas" : [None,"land","ocean"],
            "pr" : [None,"land","ocean"],
            "psl": [None,"land","ocean"],
           "huss": [None,"land","ocean"],
            "prw": [None,"land","ocean"], 
                  }  #terre

#regions = {"pr":["ocean"],}

## USER CAN CUSTOMIZE REGIONS VALUES NAMES 
regions_values = {"land":100.,"ocean":0.}

# Observations to use at the moment "default" or "alternate"
ref = 'all'
ref = ['default']  #,'alternate','ref3']
ext = '.xml'  #'.nc'
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
period      = '1980-2005'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
#################################################
## Templates for climatology files
## TEMPLATE EXAMPLE: cmip5.GFDL-ESM2G.historical.r1i1p1.mo.atm.Amon.rlut.ver-1.1980-1999.AC.nc

#filename_template = "cmip5.%(model_version).' + exp + '.r1i1p1.mo.%(table_realm).%(variable).ver-v20110601.1980-2005.AC.nc" ## tos 

if exp == 'historical':
  filename_template = "%(variable)_%(model_version)_Amon_historical_%(exp)r1i1p1_198001-200512-clim.nc"  # FOR AMON FIELDS
  filename_template = "%(variable)_%(model_version)_Omon_historical_%(exp)r1i1p1_198001-200512-clim.nc"  # FOR OMON FIELDS

if exp == 'amip':
  filename_template = "%(variable)_%(model_version)_Amon_amip_%(exp)r1i1p1_198001-200512-clim.nc"

if exp == 'picontrol':
  filename_template = "%(variable)_%(model_version)_Amon_picontrol_%(exp)r1i1p1_01-12-clim.nc"   # FOR AMON FIELDS
  filename_template = "%(variable)_%(model_version)_Omon_picontrol_%(exp)r1i1p1_01-12-clim.nc"   # FOR OMON FIELDS

#filename_template = "%(variable)_%(model_version)_Omon_historical_r1i1p1_198001-200512-clim.nc"

## Templates for MODEL land/sea mask (sftlf)
## filename template for landsea masks ('sftlf')
##sftlf_filename_template = "/work/gleckler1/processed_data/cmip5_fixed_fields/sftlf/sftlf_%(model_version).nc"

#generate_sftlf = True

sftlf_filename_template = "sftlf_%(model_version).nc"

## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package-' + exp + '/' 
#mod_data_path = '/work/gleckler1/processed_data/cmip5clims-AR5-frozen_1dir/' 
## ROOT PATH FOR OBSERVATIONS
obs_data_path = '/work/gleckler1/processed_data/metrics_package/obs/'
## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/cmip5clims_metrics_package-' + exp 
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims_' + exp +'/'
## FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable)%(level).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"
