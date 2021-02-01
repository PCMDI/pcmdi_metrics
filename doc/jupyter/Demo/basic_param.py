import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'basicTest'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
test_data_set = ['ACCESS1-0', 'CanCM4']


# VARIABLES TO USE
vars = ['rlut']


# Observations to use at the moment "default" or "alternate"
reference_data_set = ['all']
#ext = '.nc'

# INTERPOLATION OPTIONS
target_grid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
regrid_tool_ocn = 'esmf'    # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'

# Templates for climatology files
# %(param) will subsitute param with values in this file
filename_template = "cmip5.historical.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC.v20200426.nc"

# filename template for landsea masks ('sftlf')
sftlf_filename_template = "sftlf_%(model_version).nc"
generate_sftlf = True # if land surface type mask cannot be found, generate one


pth = os.path.dirname(__file__)
# ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = 'demo_data/CMIP5_demo_clims/'
# ROOT PATH FOR OBSERVATIONS
# Note that atm/mo/%(variable)/ac will be added to this
reference_data_path = 'demo_data/PCMDIobs2_clims'

# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join(
    'demo_output',
    "%(case_id)")

