import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'obsByNameTest'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
test_data_set = ['GFDL-ESM2G', ]

# dictionary of keywords for simulation description that you want to save
# or remap
simulation_description_mapping = {
    "Login": "Login",
    "Center": "Center",
    "SimTrackingDate": "creation_date"}

# VARIABLES AND OBSERVATIONS TO USE
vars = ['tas', ]

# MODEL SPECIFC PARAMETERS
model_tweaks = {
    # Keys are model accronym or None which applies to all model entries
    "GFDL-ESM2G": {
        "variable_mapping": {"tas": "tas_ac"},
    },
}

# REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
# Here we run glb for both but also terre and ocean for tas (only)
regions = {"tas": [None, "terre"], }
# USER CAN CUSTOMIZE REGIONS VALUES NMAES
regions_values = {"terre": 100.}

# Observations to use at the moment "default" or "alternate"
reference_data_set = ['ERAINT', ]
ext = '.nc'

# INTERPOLATION OPTIONS
target_grid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'

# SIMULATION PARAMETERS
period = '198501-200512'
realization = 'r1i1p1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_test_clims = False  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
# TEMPLATE EXAMPLE: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)-clim.nc"
# filename template for landsea masks ('sftlf')
sftlf_filename_template = "sftlf_%(model_version).nc"

# ROOT PATH FOR MODELS CLIMATOLOGIES
pth = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(pth, "data"))
# ROOT PATH FOR OBSERVATIONS
reference_data_path = os.path.abspath(os.path.join(pth, "obs"))
# Custom obs dictionary file (one we use for tests)
custom_observations = os.path.abspath(
    os.path.join(
        reference_data_path,
        "obs_info_dictionary.json"))
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join(
    'pcmdi_install_test_results',
    'metrics_results', '%(case_id)')
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
test_clims_interpolated_output = os.path.join(
    'pcmdi_install_test_results',
    'interpolated_model_clims')
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_" +\
    "historical_%(realization)_%(period).interpolated.%(regrid_method).%(target_grid_name)-clim%(ext)"

dry_run = False
