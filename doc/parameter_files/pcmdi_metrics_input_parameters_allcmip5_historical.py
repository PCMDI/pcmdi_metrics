import  genutil

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY: 
#
################################################################################

## RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN BE COMPARED
case_id = 'sampletest1'
case_id = 'cmip5_test'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G',]

model_versions = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5-1-FV2', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CESM1-WACCM', 'CESM1-WSCCM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'EC-EARTH', 'FGOALS-g2', 'FGOALS-s2', 'FIO-ESM', 'GFDL-CM2p1', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H-CC', 'GISS-E2-H', 'GISS-E2-R-CC', 'GISS-E2-R', 'HadCM3', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC4h', 'MIROC5', 'MIROC-ESM-CHEM', 'MIROC-ESM', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'NorESM1-ME', 'NorESM1-M']

#model_versions = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1' ]

#model_versions = ['MRI-CGCM3',]

simulation_description_mapping = {"Login":"Login", "Center":"Center", "CMIP5CreationDate" : "CMIP5_creation_date","CMIP5_tracking_id":'tracking_id'}

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


# Observations to use at the moment "default" or "alternate"
ref = 'all'
#ref = ['default']  #,'alternate','ref3']
ext = '.xml'  #'.nc'
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid        = '2.5x2.5' # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool       = 'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method     = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn   = 'esmf'    # OPTIONS: "regrid2","esmf"
regrid_method_ocn = 'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf

# SIMULATION PARAMETERS
model_period = '1980-2005'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True # True or False

## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

## Templates for climatology files
## TEMPLATE EXAMPLE: cmip5.GFDL-ESM2G.historical.r1i1p1.mo.atm.Amon.rlut.ver-1.1980-1999.AC.nc
filename_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.%(period).AC.%(ext)" 
filename_template = "cmip5.%(model_version).historical.%(realization).mo.%(table_realm).%(variable).ver-1.%(model_period).AC.%(ext)"
#filename_template = "%(variable)_MEAN_CLIM_METRICS_%(model_version)_%(realization)_%(model_period)-clim.xml"
filename_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.latestX.1980-2005.AC.nc"
filename_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-v20110601.1980-2005.AC.nc" ## tos 
filename_template = "%(variable)_%(model_version)_Amon_historical_r1i1p1_198001-200512-clim.nc"
#filename_template = "%(variable)_%(model_version)_Omon_historical_r1i1p1_198001-200512-clim.nc"



## ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package-historical/' 
#mod_data_path = '/work/gleckler1/processed_data/cmip5clims-AR5-frozen_1dir/' 
## ROOT PATH FOR OBSERVATIONS
obs_data_path = '/work/gleckler1/processed_data/metrics_package/obs/'
## DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/cmip5clims_metrics_package-historical'
## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'
## FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
filename_output_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable)%(level).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"

