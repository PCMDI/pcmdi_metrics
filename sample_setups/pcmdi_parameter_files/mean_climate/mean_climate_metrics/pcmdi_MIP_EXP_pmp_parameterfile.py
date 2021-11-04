import datetime
import json
import os
import sys

import cdutil

# ver = datetime.datetime.now().strftime('v%Y%m%d%I%M')
ver = datetime.datetime.now().strftime("v%Y%m%d")

################################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
################################################################################
#
case_id = "regrid_testing_May2018"
case_id = ver

MIP = "cmip6"  #'CMIP6'
exp = "historical"
# exp = 'amip'
# exp = 'picontrol'

user_notes = "Provenance and results"
metrics_in_single_file = "n"  #  'y' or 'n'
regional = "n"  # 'n'

cmec = True

#################################################################

if MIP == "cmip6":
    modver = "v20200526"  #'v20200422'  #'v20191016'  #'v20190930' #'v20190926'  #'v20190920'   #k'v20190913'   #'v20190801'
if MIP == "cmip5":
    modver = "v20200423"  #'v20191016'   #'v20190820'
    if exp == "historical":
        modver = "v20200426"

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF CLIMATOLOGY FILENAME

# all_mods_dic= json.load(open('all_mip_mods-tmp.json'))
# all_mods_dic= json.load(open('all_mip_mods-v20200427.json'))
all_mods_dic = json.load(open("all_mip_mods-v20200528.json"))


# all_mods_dic = ['E3SM-1-0','ACCESS-CM2']

# test_data_set = all_mods_dic

test_data_set = all_mods_dic[MIP][exp]

test_data_set.sort()

print(len(test_data_set), " ", test_data_set)

print("----------------------------------------------------------------")


# jjjjtest_data_set = test_data_set[0:2]

simulation_description_mapping = {
    "creation_date": "creation_date",
    "tracking_id": "tracking_id",
}

### VARIABLES AND OBSERVATIONS TO USE

realm = "Amon"
# realm = 'Omon'

#####################
# WITHOUT PARALLELIZATION

"""
vars = ['pr','rltcre','rstcre','rt','rst','rlut','tauu','tauv']
vars = ['psl','tauu','tauv','tas','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500','pr','rltcre','rstcre','rt','rst','rlut']
vars = ['tas','rlut','pr','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500']
"""

if regional == "y":
    vars = [
        "tas",
        "ts",
        "psl",
        "sfcWind",
    ]  # ,'tauu','tauv']   ## THESE DO NOT WORK WITH PARALLELIZATON
# vars = ['tas']

#####################
# WITH PARALLELIZATION

"""
vars = [['psl',],['pr',],['prw',],['tas',],['uas',],['vas',],['sfcWind',],['tauu'],['tauv']]
#vars = [['ta_850',],['ta_200',],['ua_850',],['ua_200',],['va_850',],['va_200',],['zg_500']]
vars = [['rlut',],['rsut',],['rsutcs',],['rlutcs',],['rsdt',],['rsus',],['rsds',],['rlds',],['rlus',],['rldscs',],['rsdscs']]
"""
# ALL BUT NOT tas ts psl sfcwind tauu tauv
if regional == "n":
    vars = [
        [
            "pr",
        ],
        [
            "prw",
        ],
        [
            "uas",
        ],
        [
            "vas",
        ],
        [
            "ta_850",
        ],
        [
            "ta_200",
        ],
        [
            "ua_850",
        ],
        [
            "ua_200",
        ],
        [
            "va_850",
        ],
        [
            "va_200",
        ],
        [
            "zg_500",
        ],
        [
            "rlut",
        ],
        [
            "rsut",
        ],
        [
            "rsutcs",
        ],
        [
            "rlutcs",
        ],
        [
            "rsdt",
        ],
        [
            "rsus",
        ],
        [
            "rsds",
        ],
        [
            "rlds",
        ],
        [
            "rlus",
        ],
        [
            "rldscs",
        ],
        [
            "rsdscs",
        ],
        [
            "rltcre",
        ],
        [
            "rstcre",
        ],
        [
            "rt",
        ],
    ]

# vars = [['pr',],['rlut',],]
# vars = [['ts',],['psl',]]
# vars = ['ts']

# MODEL SPECIFC PARAMETERS
model_tweaks = {
    # Keys are model accronym or None which applies to all model entries
    None: {
        ## Variables name mapping
        "variable_mapping": {"rlwcrf1": "rlutcre1"},
    },
    "GFDL-ESM2G": {
        "variable_mapping": {"tos": "tos"},
    },
}


# USER CUSTOMIZED REGIONS
if regional == "y":

    regions_specs = {
        "Nino34": {
            "value": 0.0,
            "domain": cdutil.region.domain(
                latitude=(-5.0, 5.0), longitude=(190.0, 240.0)
            ),
        },
        "ocean": {"value": 0.0, "domain": cdutil.region.domain(latitude=(-90.0, 90))},
        "land": {"value": 100.0, "domain": cdutil.region.domain(latitude=(-90.0, 90))},
        "ocean_50S50N": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(-50.0, 50)),
        },
        "ocean_50S20S": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(-50.0, -20)),
        },
        "ocean_20S20N": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(-20.0, 20)),
        },
        "ocean_20N50N": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(20.0, 50)),
        },
        "ocean_50N90N": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(50.0, 90)),
        },
        "90S50S": {
            "value": None,
            "domain": cdutil.region.domain(latitude=(-90.0, -50)),
        },
        "50S20S": {
            "value": None,
            "domain": cdutil.region.domain(latitude=(-50.0, -20)),
        },
        "20S20N": {"value": None, "domain": cdutil.region.domain(latitude=(-20.0, 20))},
        "20N50N": {"value": None, "domain": cdutil.region.domain(latitude=(20.0, 50))},
        "50N90N": {"value": None, "domain": cdutil.region.domain(latitude=(50.0, 90))},
        "NH": {"value": None, "domain": cdutil.region.domain(latitude=(0.0, 90))},
        "SH": {"value": None, "domain": cdutil.region.domain(latitude=(-90.0, 0))},
        "NHEX_ocean": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(0.0, 90)),
        },
        "SHEX_ocean": {
            "value": 0.0,
            "domain": cdutil.region.domain(latitude=(-90.0, 0)),
        },
        "NHEX_land": {
            "value": 100.0,
            "domain": cdutil.region.domain(latitude=(20.0, 90)),
        },
        "SHEX_land": {
            "value": 100.0,
            "domain": cdutil.region.domain(latitude=(-90.0, -20.0)),
        },
    }
    #       'GLOBAL' : {"value":0.,'domain':cdutil.region.domain(latitude=(-90.,90.))},

    regions = {
        "tas": [None, "land", "ocean", "ocean_50S50N", "NHEX_land", "SHEX_land"],
        "tauu": [None, "ocean_50S50N"],
        "tauv": [None, "ocean_50S50N"],
        "psl": [None, "ocean", "ocean_50S50N", "NHEX_ocean", "SHEX_ocean"],
        "sfcWind": [None, "ocean", "ocean_50S50N", "NHEX_ocean", "SHEX_ocean"],
        "ts": [None, "ocean", "ocean_50S50N", "NHEX_ocean", "SHEX_ocean"],
        "tos": [None],
    }

## USER CAN CUSTOMIZE REGIONS VALUES NAMES
# regions_values = {"land":100.,"ocean":0.}

# Observations to use at the moment "default" or "alternate"
ref = "all"
reference_data_set = ["default"]  # ['default']  #,'alternate1']  #,'alternate','ref3']
ext = ".xml"  #'.nc'
ext = ".nc"

# INTERPOLATION OPTIONS

target_grid = "2.5x2.5"  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
targetGrid = target_grid
target_grid_string = "2p5x2p5"
regrid_tool = "regrid2"  #'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method = "regrid2"  #'conservative'  #'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn = "esmf"  # OPTIONS: "regrid2","esmf"
regrid_method_ocn = (
    "conservative"  # OPTIONS: 'linear','conservative', only if tool is esmf
)

# regrid_tool       = 'esmf' #'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
# regrid_method     = 'linear'  #'conservative'  #'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf


# SIMULATION PARAMETERg
period = "1981-2005"
# period = '1979-1989'

realization = "r1i1p1"

# SAVE INTERPOLATED MODEL CLIMATOLOGIES ?
save_test_clims = True  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
# ---------------------------------------------
# Templates for climatology files

verd = "*"
if exp == "amip":
    filename_template = (
        "%(variable)_%(model_version)_%(table)_amip_%(exp)r1i1p1_198101-200512-clim.nc"
    )
if exp == "amip":
    filename_template = "CMIP5.amip.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC.v20190225.nc"
# if exp == 'historical': filename_template = "CMIP5.historical.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC.v20190307.nc"
if exp == "historical" and MIP == "cmip5":
    filename_template = (
        MIP
        + ".historical.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC."
        + modver
        + ".nc"
    )
if exp == "amip" and MIP == "cmip5":
    filename_template = (
        MIP
        + ".amip.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC."
        + modver
        + ".nc"
    )
if exp == "historical" and MIP == "cmip6":
    filename_template = (
        MIP
        + ".historical.%(model_version).r1i1p1f1.mon.%(variable).198101-200512.AC."
        + modver
        + ".nc"
    )
if exp == "amip" and MIP == "cmip6":
    filename_template = (
        MIP
        + ".amip.%(model_version).r1i1p1f1.mon.%(variable).198101-200512.AC."
        + modver
        + ".nc"
    )


# if exp == 'historical': filename_template = "CMIP5.historical.%(model_version).r1i1p1.mon.%(variable).198101-200512.AC.%('*').nc"
if exp == "picontrol":
    filename_template = (
        "%(variable)_%(model_version)_%(table)_picontrol_%(exp)r1i1p1_01-12-clim.nc"
    )

# Templates for MODEL land/sea mask (sftlf)
# filename template for landsea masks ('sftlf')
# sftlf_filename_template = "/work/gleckler1/processed_data/cmip5_fixed_fields/sftlf/sftlf_%(model_version).nc"

generate_sftlf = True  # ESTIMATE LAND SEA MASK IF NOT FOUND

sftlf_filename_template = (
    "cmip6.historical.%(model_version).sftlf.nc"  # "sftlf_%(model_version).nc"
)


## ROOT PATH FOR MODELS CLIMATOLOGIES
test_data_path = (
    "/work/gleckler1/processed_data/cmip5clims_metrics_package-" + exp + "/"
)
test_data_path = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/CMIP5/historical/v20190307/%(variable)/"
test_data_path = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/CMIP5/historical/v20190307/%(variable)/"
test_data_path = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/"
    + MIP
    + "/"
    + exp
    + "/"
    + modver
    + "/%(variable)/"
)


## ROOT PATH FOR OBSERVATIONS
# reference_data_path = '/work/gleckler1/processed_data/obs/'
reference_data_path = "/p/user_pub/PCMDIobs/PCMDIobs2.0/"
reference_data_path = "/p/user_pub/PCMDIobs/PCMDIobs2.0-beta/"
reference_data_path = "/p/user_pub/PCMDIobs/PCMDIobs2_clims/"


# custom_observations = os.path.abspath(os.path.join(reference_data_path, "obs_info_dictionary.json"))
# custom_observations = os.path.abspath('./pcmdiobs_info_dictionary.json')
# custom_observations = os.path.abspath('/p/user_pub/PCMDIobs/misc_meta_info/obs_info_dictionary.json')
custom_observations = os.path.abspath(
    "/p/user_pub/PCMDIobs/catalogue/pcmdiobs2_clims_catalogue_v20200420.json"
)
custom_observations = os.path.abspath("./pcmdiobs2_clims_catalogue_v20200420.json")
custom_observations = "./pcmdiobs2_clims_byVar_catalogue_v20200528.json"
custom_observations = "./pcmdiobs2_clims_byVar_catalogue_v20200615.json"


print("CUSTOM OBS ARE ", custom_observations)
if not os.path.exists(custom_observations):
    sys.exit()

#######################################
### DIRECTORY AND FILENAME FOR OUTPUTING METRICS RESULTS
## BY INDIVIDUAL MODELS
if metrics_in_single_file != "y":
    metrics_output_path = (
        "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/"
        + MIP
        + "/"
        + exp
        + "/%(case_id)/%(variable)%(level)/"
    )  # INDIVIDUAL MOD FILES
    output_json_template = (
        "%(model_version).%(variable)%(level)."
        + MIP
        + "."
        + exp
        + ".%(regrid_method)."
        + target_grid_string
        + "."
        + case_id
    )  # INDIVIDUAL MOD FILES
## ALL MODELS IN ONE FILE
if metrics_in_single_file == "y":
    metrics_output_path = (
        "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/"
        + MIP
        + "/"
        + exp
        + "/%(case_id)/"
    )  # All SAME FILE
    output_json_template = (
        "%(variable)%(level)."
        + MIP
        + "."
        + exp
        + ".%(regrid_method)."
        + target_grid_string
        + "."
        + case_id
    )  # ALL SAME FILE
########################################

## DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
test_clims_interpolated_output = (
    "/work/gleckler1/processed_data/metrics_package/pmp_diagnostics"
    + "/interpolated_model_clims_"
    + exp
    + "/"
    + case_id
)
test_clims_interpolated_output = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results"
    + "/interpolated_model_clims_"
    + exp
    + "/"
    + case_id
)

test_clims_interpolated_output = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results"
    + "/interpolated_model_clims/"
    + MIP
    + "/"
    + exp
    + "/"
    + case_id
)


## FILENAME FOR INTERPOLATED CLIMATOLGIES OUTPUT
# filename_output_template = MIP + ".%(model_version).historical.r1i1p1.mo.%(table).%(variable)%(level).ver-1.%(period).interpolated.%(regrid_method).%(region).AC%(ext)"
filename_output_template = (
    MIP
    + ".%(model_version)."
    + exp
    + ".r1i1p1.mo.%(variable)%(level).%(period).interpolated.%(regrid_method).%(region).AC."
    + case_id
    + "%(ext)"
)

if regional == "n":
    num_workers = 20  # 17
    granularize = ["vars"]
