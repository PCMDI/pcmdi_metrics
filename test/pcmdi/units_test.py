import os

##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
##########################################################################

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'unitsTest'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G', ]

# dictionary of keywords for simulation description that you want to save
# or remap
simulation_description_mapping = {
    "Login": "Login",
    "Center": "Center",
    "SimTrackingDate": "creation_date"}

# VARIABLES AND OBSERVATIONS TO USE
vars = ['tas', ]

# Observations to use at the moment "default" or "alternate"
ref = ['default']
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'esmf'  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'

# MODEL SPECIFC PARAMETERS
model_tweaks = {
    "GFDL-ESM2G": {
        "variable_mapping": {"tas": "tas_ac"},
    },
}

# SIMULATION PARAMETERS
period = '000101-010012'
realization = "r1i1p1"  # mandatory

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
# TEMPLATE EXAMPLE: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_piControl_%(period)-clim01.xml"
# filename template for landsea masks ('sftlf')
sftlf_filename_template = "sftlf_%(model_version).nc"

# ROOT PATH FOR MODELS CLIMATOLOGIES
pth = os.path.dirname(__file__)
mod_data_path = os.path.abspath(os.path.join(pth, "data"))
# ROOT PATH FOR OBSERVATIONS
obs_data_path = os.path.abspath(os.path.join(pth, "obs"))
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join(
    'pcmdi_install_test_results',
    'metrics_results')
