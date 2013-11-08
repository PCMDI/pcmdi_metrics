import  genutil

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'sampletest'
case_id = 'cmip5_test'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G',]
model_versions = ['crap','MRI-CGCM3',]
model_versions = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5-1-FV2', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CESM1-WACCM', 'CESM1-WSCCM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'FGOALS-s2', 'FIO-ESM', 'GFDL-CM2p1', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H-CC', 'GISS-E2-H', 'GISS-E2-R-CC', 'GISS-E2-R', 'HadCM3', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC4h', 'MIROC5', 'MIROC-ESM-CHEM', 'MIROC-ESM', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'NorESM1-ME', 'NorESM1-M']


### VARIABLES AND OBSERVATIONS TO USE
vars = ['zos','pr','rlut','rsut','tas','tos','tauu','tauv']
#vars = ['tas','pr']
#vars = ['pr','tas','tos']
vars = ['uas']

# Observations to use at the moment "default" or "alternate"
ref = 'default' 

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True  #False   #True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
filename_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.%(period).AC.%(ext)" 
filename_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.1980-2005.AC.%(ext)"
## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/work/gleckler1/processed_data/metrics_package/inhouse_model_clims/' 
mod_data_path = '/work/gleckler1/processed_data/cmip5clims-AR5-frozen_1dir/' 
## ROOT PATH FOR OBSERVATIONS
obs_data_path = '/work/gleckler1/processed_data/metrics_package/'
## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/'
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'
## FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
filename_output_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"

