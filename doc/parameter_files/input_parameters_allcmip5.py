##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
##########################################################################

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'sampletest1'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G', ]

# VARIABLES AND OBSERVATIONS TO USE
vars = ['zos', 'pr', 'rlut', 'tos']

# Observations to use at the moment "default" or "alternate"
ref = 'all'
ref = ['default']  # ,'alternate','ref3']
ext = '.xml'  # '.nc'
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'

# SIMULATION PARAMETERS
period = '1980-2005'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
# TEMPLATE EXAMPLE:
# cmip5.GFDL-ESM2G.historical.r1i1p1.mo.atm.Amon.rlut.ver-1.1980-1999.AC.nc
filename_template = "%(variable)_%(model_version)_%(table_realm)_historical_r1i1p1_198501-200512-clim.nc"

# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package/'
# ROOT PATH FOR OBSERVATIONS
obs_data_path = '/work/gleckler1/processed_data/metrics_package/'
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/'
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'
# FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
filename_output_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm)." +\
    "%(variable)%(level).ver-1.%(period).interpolated.%(regridMethod).%(targetGridName).AC%(ext)"
