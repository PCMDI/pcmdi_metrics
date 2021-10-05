import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'salinityTest'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
test_data_set = ['GFDL-CM3', ]

# VARIABLES AND OBSERVATIONS TO USE
vars = ['sos', ]

# Observations to use at the moment "default" or "alternate"
reference_data_set = ['JPL-Aquarius-v2']
ext = '.nc'

# INTERPOLATION OPTIONS
target_grid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'esmf'  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'


# SIMULATION PARAMETERS
period = '000101-010012'
realization = "r1i1p1"  # mandatory

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_test_clims = False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
# TEMPLATE EXAMPLE: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(period)-clim.nc"

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

dry_run = False