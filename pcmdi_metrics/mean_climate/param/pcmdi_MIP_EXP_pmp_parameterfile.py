import datetime
import json
import os
import sys

import cdutil

ver = datetime.datetime.now().strftime('v%Y%m%d')

# ###############################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
# ###############################################################################
case_id = ver

MIP = 'cmip6'  # 'CMIP6'
# MIP = 'cmip5'  # 'CMIP6'
exp = 'historical'
# exp = 'amip'
# exp = 'picontrol'

user_notes = "Provenance and results"
metrics_in_single_file = 'y'  # 'y' or 'n'

cmec = False  # True

# ################################################################

if MIP == 'cmip6':
    modver = 'v20230201'
if MIP == 'cmip5':
    modver = 'v20220928'
    if exp == 'historical':
        modver = 'v20220928'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME

all_mods_dic = json.load(open('all_mip_mods-v20230201.json'))  #all_mip_mods-v20200528.json'))
# all_mods_dic = ['E3SM-1-0', 'ACCESS-CM2']

# test_data_set = all_mods_dic
test_data_set = all_mods_dic[MIP][exp]
test_data_set.sort()
test_data_set = ['ACCESS-CM2']

print(len(test_data_set), ' ', test_data_set)
print('----------------------------------------------------------------')

simulation_description_mapping = {"creation_date": "creation_date", "tracking_id": 'tracking_id', }

# VARIABLES AND OBSERVATIONS TO USE

realm = 'Amon'
# realm = 'Omon'

vars = ['ts']

# MODEL SPECIFIC PARAMETERS
model_tweaks = {
    # Keys are model accronym or None which applies to all model entries
    None: {"variable_mapping": {"rlwcrf1": "rlutcre1"}},  # Variables name mapping
    "GFDL-ESM2G": {"variable_mapping": {"tos": "tos"}},
}

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
    # "ts": ["global", "NHEX", "SHEX", "TROPICS", "ocean", "CONUS"],
    # "ts": ["global"],
    "ts": ["global", "CONUS"],
    # "ts": ["CONUS"],
}

# USER CAN CUSTOMIZE REGIONS VALUES NAMES
# regions_values = {"land": 100., "ocean": 0.}

# Observations to use at the moment "default" or "alternate"
ref = 'all'
reference_data_set = ['default']  # ['default']  #, 'alternate1']  #, 'alternate', 'ref3']
ext = '.xml'  #'.nc'
ext = '.nc'

# INTERPOLATION OPTIONS

target_grid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
targetGrid = target_grid
target_grid_string = '2p5x2p5'
regrid_tool = 'regrid2'  # 'esmf' #'regrid2' # OPTIONS: 'regrid2', 'esmf'
regrid_method = 'regrid2'  # 'conservative'  #'linear'  # OPTIONS: 'linear', 'conservative', only if tool is esmf
regrid_tool_ocn = 'esmf'     # OPTIONS: "regrid2", "esmf"
regrid_method_ocn = 'conservative'  # OPTIONS: 'linear', 'conservative', only if tool is esmf

# regrid_tool       = 'esmf' #'esmf' #'regrid2' # OPTIONS: 'regrid2', 'esmf'
# regrid_method     = 'linear'  #'conservative'  #'linear'  # OPTIONS: 'linear', 'conservative', only if tool is esmf

# SIMULATION PARAMETERg
period = '1981-2005'
# period = '1979-1989'

realization = 'r1i1p1f1'

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_test_clims = True  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
# ################################################
# Templates for climatology files

verd = '*'
if exp == 'historical' and MIP == 'cmip5':
    filename_template = MIP + '.historical.%(model).r1i1p1.mon.%(variable).198101-200512.AC.' + modver + '.nc'
if exp == 'amip' and MIP == 'cmip5':
    filename_template = MIP + '.amip.%(model).r1i1p1.mon.%(variable).198101-200512.AC.' + modver + '.nc'
if exp == 'historical' and MIP == 'cmip6':
    filename_template = MIP + '.historical.%(model).r1i1p1f1.mon.%(variable).198101-200512.AC.' + modver + '.nc'
if exp == 'amip' and MIP == 'cmip6':
    filename_template = MIP + '.amip.%(model).r1i1p1f1.mon.%(variable).198101-200512.AC.' + modver + '.nc'
if exp == 'picontrol':
    filename_template = "%(variable)_%(model)_%(table)_picontrol_%(exp)_r1i1p1_01-12-clim.nc"

# Templates for MODEL land/sea mask (sftlf)
# filename template for landsea masks ('sftlf')
# sftlf_filename_template = "/work/gleckler1/processed_data/cmip5_fixed_fields/sftlf/sftlf_%(model).nc"

generate_sftlf = True    # ESTIMATE LAND SEA MASK IF NOT FOUND

sftlf_filename_template = "cmip6.historical.%(model).sftlf.nc"   # "sftlf_%(model).nc"

# ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/' + MIP + '/' + exp + '/' + modver + '/%(variable)/'

# ROOT PATH FOR OBSERVATIONS
reference_data_path = '/p/user_pub/PCMDIobs/obs4MIPs_clims/'
custom_observations = os.path.abspath('/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_clims_byVar_catalogue_v20210816.json')
# custom_observations = './obs4MIPs_PCMDI_clims_byVar_catalogue_v20210805_ljw.json'

print('CUSTOM OBS ARE ', custom_observations)
if not os.path.exists(custom_observations):
    sys.exit()

# ######################################
# DIRECTORY AND FILENAME FOR OUTPUTING METRICS RESULTS
# BY INDIVIDUAL MODELS
if metrics_in_single_file != 'y':
    metrics_output_path = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/' + MIP + '/' + exp + '/%(case_id)/%(variable)%(level)/'  # INDIVIDUAL MOD FILES
    output_json_template = '%(model).%(variable)%(level).' + MIP + '.' + exp + '.%(regrid_method).' + target_grid_string + '.' + case_id  # INDIVIDUAL MOD FILES
# ALL MODELS IN ONE FILE
if metrics_in_single_file == 'y':
    metrics_output_path = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/' + MIP + '/' + exp + '/%(case_id)/'  # All SAME FILE
    output_json_template = '%(variable)%(level).' + MIP + '.' + exp + '.%(regrid_method).' + target_grid_string + '.' + case_id  # ALL SAME FILE
# #######################################

# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
test_clims_interpolated_output = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results' + '/interpolated_model_clims/' + MIP + '/' + exp + '/' + case_id

# FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
filename_output_template = MIP + ".%(model)." + exp + "." + realization + ".mo.%(variable)%(level).%(period).interpolated.%(regrid_method).%(region).AC." + case_id + "%(ext)"
