##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
##########################################################################

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'sampletest'
# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
model_versions = ['GFDL-ESM2G', ]

# VARIABLES AND OBSERVATIONS TO USE
vars = ['ta_85000']

# regions of mask to use when processing variables
regions = {"tas": ["terre", "ocean", "global"]}
regions_values = {"terre": 0., }

# Observations to use at the moment "default" or "alternate"
ref = 'default'

# INTERPOLATION OPTIONS
targetGrid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_mod_clims = True  # True or False


# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
filename_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm).%(variable).ver-1.%(period).AC.%(ext)"
filename_ouput_template = "cmip5.%(model_version).historical.r1i1p1.mo.%(table_realm)." +\
    "%(variable).ver-1.%(period).%{region}.AC.%(ext)"
# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/work/gleckler1/processed_data/metrics_package/inhouse_model_clims/'
# ROOT PATH FOR OBSERVATIONS
obs_data_path = '/work/gleckler1/processed_data/metrics_package/'
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = '/work/gleckler1/processed_data/metrics_package/metrics_results/'
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = '/work/gleckler1/processed_data/metrics_package/interpolated_model_clims/'
