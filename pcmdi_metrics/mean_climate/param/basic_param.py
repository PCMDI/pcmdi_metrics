import os

#
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
#

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = "v20221130"

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
test_data_set = ["E3SMv2"]


# VARIABLES TO USE
# vars = ['pr', 'ua_850']
# vars = ['pr']
# vars = ['ta-850']
vars = ["ua-850"]


# Observations to use at the moment "default" or "alternate"
# reference_data_set = ['all']
reference_data_set = ["default"]
# ext = '.nc'

# INTERPOLATION OPTIONS
target_grid = "2.5x2.5"  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = "regrid2"  # 'regrid2' # OPTIONS: 'regrid2','esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = "linear"
regrid_tool_ocn = "esmf"  # OPTIONS: "regrid2","esmf"
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = "linear"

# SAVE INTERPOLATED MODEL CLIMATOLOGIES?
save_test_clims = True  # True or False

# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
test_clims_interpolated_output = "./interpolated_model_clims"


# Templates for climatology files
# %(param) will subsitute param with values in this file
filename_template = (
    "cmip6.historical.E3SMv2.r1i1p1.mon.%(variable).198101-200512.AC.v20221027.nc"
)

# filename template for landsea masks ('sftlf')
# sftlf_filename_template = "sftlf_fx_E3SM-1-0_historical_r1i1p1f1_gr.nc"
# sftlf_filename_template = "/p/user_pub/work/CMIP6/CMIP/E3SM-Project/E3SM-2-0/piControl/r1i1p1f1/fx/sftlf/gr/v20220913/sftlf_fx_E3SM-2-0_piControl_r1i1p1f1_gr.nc"
sftlf_filename_template = "sftlf_fx_E3SM-2-0_piControl_r1i1p1f1_gr.nc"
# sftlf_filename_template = None

generate_sftlf = False  # if land surface type mask cannot be found, generate one
# generate_sftlf = True  # if land surface type mask cannot be found, generate one

# Region (if not given, default region applied: global, NHEX, SHEX, TROPICS)
regions = {
    # "pr": ["global", "NHEX", "SHEX", "TROPICS", "land_NHEX", "ocean_SHEX"],
    "pr": ["global"],
    # "pr": ["land", "ocean", "land_TROPICS", "ocean_SHEX"],
    "ua": ["global"],
    "ta": ["global", "NHEX", "SHEX", "TROPICS", "land_NHEX", "ocean_SHEX"],
    # "ta": ["NHEX"],
    # "ta": ["land_NHEX"]
    # "ta": ["global"]
}

# ROOT PATH FOR MODELS CLIMATOLOGIES
# test_data_path = '/work/lee1043/ESGF/E3SMv2/atmos/mon'
test_data_path = "./clim"
# ROOT PATH FOR OBSERVATIONS
# Note that atm/mo/%(variable)/ac will be added to this
reference_data_path = "/p/user_pub/PCMDIobs/obs4MIPs_clims"

# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join("output", "%(case_id)")
