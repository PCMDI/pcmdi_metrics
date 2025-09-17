import datetime
import os
import sys

import cdutil

ver = datetime.datetime.now().strftime("v%Y%m%d")

################################################################################
#  Options set by user
################################################################################
# By default use the current date (variable 'ver').
# User can change to another descriptive string.
case_id = ver

# If 'y', each model has its own metrics output file.
metrics_in_single_file = "n"  #  'y' or 'n'

# List of model versions to be tested
test_data_set = ["E3SM-1-0"]

# List of variables to test
# Vertical level indicated after underscore
vars = [
    "tas",
    "psl",
    "tauu",
    "tauv",
    "ta_850",
    "ta_200",
    "ua_850",
    "ua_200",
    "va_850",
    "va_200",
    "zg_500",
    "pr",
    "rltcre",
    "rstcre",
    "rt",
    "rst",
    "rlut",
]

# Optional model parameters
period = "1981-2005"
realization = "r1i1p1f1"
realm = "Amon"
ext = ".xml"  # .xml or .nc

# Optional parameters for metrics json
user_notes = "Provenance and results"
# simulation_description_mapping = {'creation_date' : 'creation_date', 'tracking_id': 'tracking_id',}

# True to save interpolated model climatologies
save_test_clims = True

################################################
## DATA LOCATION: MODELS, OBS AND METRICS OUTPUT
# The file paths in this section must be edited
# to reflect your data locations.
#
# See Advanced Settings to change 'output_json_template'
#
# Chain notation in templates allows variable substitution, e.g.
# %(model_version) for models in 'test_data_set'
# %(variable) for variables in 'vars'

# data version
modver = "v20200526"

filename_template = (
    "cmip6.historical.%(model_version).r1i1p1f1.mon.%(variable).198101-200512.AC."
    + modver
    + ".nc"
)

# Templates for MODEL land/sea mask (sftlf)
generate_sftlf = True  # ESTIMATE LAND SEA MASK IF NOT FOUND
sftlf_filename_template = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/sftlf-generic/v20200513/cmip6/cmip6.historical.%(model_version).sftlf.nc"  #'sftlf_%(model_version).nc'

# Root path for model climatologies
test_data_path = (
    "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/"
    + modver
    + "/%(variable)/"
)

# Root path for observations
reference_data_path = "/p/user_pub/PCMDIobs/PCMDIobs2_clims/"
custom_observations = "./pcmdiobs2_clims_byVar_catalogue_v20200615.json"

print("CUSTOM OBS ARE ", custom_observations)
if not os.path.exists(custom_observations):
    sys.exit()

# Directory and filename for outputing metrics results
results_dir = "/export/ordonez4/pmp_results/"

if metrics_in_single_file == "y":
    # All in same file
    metrics_output_path = (
        results_dir
        + "/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/cmip6/historical/%(case_id)/"
    )
else:
    # Individual model files
    metrics_output_path = (
        results_dir
        + "/pmp_results/pmp_v1.1.2/metrics_results/mean_climate/cmip6/historical/%(case_id)/%(variable)%(level)/"
    )

# Directory to store interpolated models' climatologies
test_clims_interpolated_output = (
    results_dir
    + "/pmp_results/pmp_v1.1.2/diagnostic_results/interpolated_model_clims/cmip6/historical/"
    + case_id
)

# Filename for interpolated climatologies output
filename_output_template = (
    "cmip6.%(model_version).historical.r1i1p1.mo.%(variable)%(level).%(period).interpolated.%(regrid_method).%(region).AC."
    + case_id
    + "%(ext)"
)


################################################################################
#  Advanced settings
################################################################################

## MODEL SPECIFC PARAMETERS
## Use this parameter to map non-cmor/cmip variables names
"""
model_tweaks = {
    ## Keys are model accronym or None which applies to all model entries
    None : {
      ## Variables name mapping
      'variable_mapping' : { 'rlwcrf1' : 'rlutcre1'},
      },
    }
"""

## USER CUSTOMIZED REGIONS

# Region definitions
regions_specs = {
    "Nino34": {
        "value": 0.0,
        "domain": cdutil.region.domain(latitude=(-5.0, 5.0), longitude=(190.0, 240.0)),
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
    "ocean_20N50N": {"value": 0.0, "domain": cdutil.region.domain(latitude=(20.0, 50))},
    "ocean_50N90N": {"value": 0.0, "domain": cdutil.region.domain(latitude=(50.0, 90))},
    "90S50S": {"value": None, "domain": cdutil.region.domain(latitude=(-90.0, -50))},
    "50S20S": {"value": None, "domain": cdutil.region.domain(latitude=(-50.0, -20))},
    "20S20N": {"value": None, "domain": cdutil.region.domain(latitude=(-20.0, 20))},
    "20N50N": {"value": None, "domain": cdutil.region.domain(latitude=(20.0, 50))},
    "50N90N": {"value": None, "domain": cdutil.region.domain(latitude=(50.0, 90))},
    "NH": {"value": None, "domain": cdutil.region.domain(latitude=(0.0, 90))},
    "SH": {"value": None, "domain": cdutil.region.domain(latitude=(-90.0, 0))},
    "NHEX_ocean": {"value": 0.0, "domain": cdutil.region.domain(latitude=(0.0, 90))},
    "SHEX_ocean": {"value": 0.0, "domain": cdutil.region.domain(latitude=(-90.0, 0))},
    "NHEX_land": {"value": 100.0, "domain": cdutil.region.domain(latitude=(20.0, 90))},
    "SHEX_land": {
        "value": 100.0,
        "domain": cdutil.region.domain(latitude=(-90.0, -20.0)),
    },
    "GLOBAL": {"value": 0.0, "domain": cdutil.region.domain(latitude=(-90.0, 90.0))},
}

# Select regions to run here. Non-specified variables will use default regions.
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
# regions_values = {'land':100.,'ocean':0.}

## OBSERVATIONS
# Options to use at the moment: 'default' or 'alternate'
ref = "all"
reference_data_set = ["default"]  # ['default']  #,'alternate1']  #,'alternate','ref3']

## INTERPOLATION OPTIONS
# These default options are recommended.
target_grid = "2.5x2.5"  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
targetGrid = target_grid
target_grid_string = "2p5x2p5"
regrid_tool = "regrid2"  #'esmf' #'regrid2' # OPTIONS: 'regrid2','esmf'
regrid_method = "regrid2"  #'conservative'  #'linear'  # OPTIONS: 'linear','conservative', only if tool is esmf
regrid_tool_ocn = "esmf"  # OPTIONS: 'regrid2','esmf'
regrid_method_ocn = (
    "conservative"  # OPTIONS: 'linear','conservative', only if tool is esmf
)

if metrics_in_single_file == "y":
    # All in same file
    output_json_template = (
        "%(variable)%(level).cmip6.historical.%(regrid_method)."
        + target_grid_string
        + "."
        + case_id
    )
else:
    # Individual model files
    output_json_template = (
        "%(model_version).%(variable)%(level).cmip6.historical.%(regrid_method)."
        + target_grid_string
        + "."
        + case_id
    )
