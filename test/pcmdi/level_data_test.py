import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'level_data'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
model_versions = ['GISS-E2-H', ]

# dictionary of keywords for simulation description that you want to save
# or remap
simulation_description_mapping = {
    "Login": "Login",
    "Center": "Center",
    "SimTrackingDate": "creation_date"}

# VARIABLES AND OBSERVATIONS TO USE
vars = ['ta_200']

# Observations to use at the moment "default" or "alternate"
ref = ['all']
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
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
# Custom key
custom_keys = {
            "experiment": {
                None: "historical",
            }  } 

# Templates for climatology files
# TEMPLATE EXAMPLE: ta_GISS-E2-H_historical_r1i1p1_mo_atm_Amon_ta_ver-1_ac.nc
filename_template = "%(variable)_%(model_version)_%(experiment)_%(realization)_mo_atm_Amon_%(variable)_ver-1_ac.nc"

pth = os.path.dirname(__file__)
# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = os.path.abspath(os.path.join(pth, "data"))
# ROOT PATH FOR OBSERVATIONS
obs_data_path = os.path.abspath(os.path.join(pth, "obs"))
# Custom obs dictionary file (one we use for tests)
custom_observations = os.path.abspath(
    os.path.join(
        obs_data_path,
        "obs_info_dictionary.json"))
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join(
    'pcmdi_install_test_results',
    'metrics_results', "%(case_id)")
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = os.path.join(
    'pcmdi_install_test_results',
    'interpolated_model_clims')
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_" +\
    "%(experiment)_%(realization)_%(period).interpolated.%(regridMethod).%(targetGridName)-clim%(ext)"
