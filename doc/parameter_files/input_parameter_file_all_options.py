##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW:
##########################################################################

# METRICS RUN IDENTIFICATION
# Defines a subdirectory to output metrics results so multiple runs can be
# compared
case_id = 'sampletest_140910'

# LIST OF MODEL VERSIONS TO BE TESTED - WHICH ARE EXPECTED TO BE PART OF
# CLIMATOLOGY FILENAME
model_versions = ['GFDL-CM4', ]  # ['GFDL-ESM2G',] ; # Model identifier

# Below are the STANDARD keys that the main code will be looking for
period = '000101-000112'  # Model climatological period (if relevant)
realization = 'r1i1p1'  # Model run identifier (if relevant)

# MODEL SPECIFIC PARAMETERS
model_tweaks = {
    # Keys are model acronym or None which applies to all model entries
    None: {
        # Variable name mapping - map your model var names to CMIP5 official
        # names
        "variable_mapping": {"tos": "tos"},
    },
    "GFDL-ESM2G": {
        "variable_mapping": {"tas": "tas_ac"},
    },
}

# VARIABLES AND OBSERVATIONS AVAILABLE FOR USE
# Variable acronyms are described in the CMIP5 standard output document
# see: http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
# 2d atmos variables
#   vars = ['clt','hfss','pr','prw','psl','rlut','rlutcs','rsdt','rsut','rsutcs','tas','tauu','tauv','ts','uas','vas']
# 3d atmos variables
#   vars = ['hur','hus','huss','ta','ua','va','zg']
# 3d atmos variables - example heights
#   vars = ['hus_850','ta_850','ta_200','ua_850','ua_200','va_850','va_200','zg_500']
# 2d ocean variables
#   vars = ['sos','tos','zos']
# Non-standard CMIP5 variables (available from obs output)
#   vars = ['rlwcrf','rswcrf']
# vars for processing
vars = [
    'pr',
    'psl',
    'rlut',
    'rlutcs',
    'rsut',
    'rsutcs',
    'ta_200',
    'ta_850',
    'tas',
    'ua_200',
    'ua_850',
    'va_200',
    'va_850',
    'zg_500']

# Observations to use 'default', 'alternate', 'all or specific enumerated
# climatology e.g. 'ref3'
ref = ['default']  # ,'all','alternate','ref3'
# INTERPOLATION OPTIONS
targetGrid = '2.5x2.5'  # Options: '2.5x2.5' or an actual cdms2 grid object
regrid_tool = 'regrid2'  # Options: 'regrid2','esmf'
# Options: 'linear','conservative', only if tool is esmf
regrid_method = 'linear'
# Options: 'regrid2','esmf' - Note regrid2 will fail with non lat/lon grids
regrid_tool_ocn = 'esmf'
# Options: 'linear','conservative', only if tool is esmf
regrid_method_ocn = 'linear'
# Options: True or False (Save interpolated model climatologies used in
# metrics calculations)
save_mod_clims = True


# REGIONAL STUDIES
# USER CAN CREATE CUSTOM REGIONS
import cdutil
regions_specs = {"Nino34":
                 {"value": 0.,
                  "domain": cdutil.region.domain(latitude=(-5., 5., "ccb"), longitude=(190., 240., "ccb"))},
                 "NAM": {"value": 0.,
                         "domain": {'latitude': (0., 45.), 'longitude': (210., 310.)},
                         }
                 }
# REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
# Here we run "all" default regions (glb, NHEX, SHEX, TROP) for both
# but also ocean and user defined Nino34 and NAME for tas (only)
regions = {"tas": [None, "ocean", "Nino34", "NAM"], "tos": None}


# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT - AND TEMPLATES FOR MODEL OUTPUT CLIMATOLOGY FILES
# Following are custom keys specific to your local system
# it is a python dictionary
# keys are your custom keys, the "value" for this key is actually defined by another dictionary
# This second dictionary maps the key value to each specific variable
# use None if you want a value to be used for every variables not
# specifically defined
custom_keys = {
    "key1": {
        None: "key1_value_for_all_vars",
        "tas": "key1_value_for_tas"},
}

# By default file names are constructed using the following keys:
# %(variable) # set by driver - this loops over all variables specified in vars list above
# %(realm)
# %(table) # CMIP standard table id - e.g. Amon (Atmosphere monthly), Omon (Ocean monthly)
# %(level) # extracted by driver from vars list defined above
# %(model_version) # set by driver from model_versions list defined above
# %(realization) # Model realization information - e.g. r1i1p1
# %(period) # Time period of analysis
# %(ext) # Output file extension
# %(case_id) # Output file extension

# Templates for input climatology files
# TEMPLATE EXAMPLE (once constructed) :
# tas: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912_key1_value_for_tas-clim.nc
# tos:
# tos_GFDL-ESM2G_Omon_historical_r1i1p1_198001-199912_key1_value_for_all_vars-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)_%(key1)-clim.nc"
# filename template for input landsea masks ('sftlf')
sftlf_filename_template = "sftlf_%(model_version).nc"
# Do we generate sftlf if file not found?
# default is False
generate_sftlf = True

# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = '/export/durack1/140701_metrics/test_new'
# ROOT PATH FOR OBSERVATIONS
obs_data_path = '/export/durack1/140701_metrics/obs'
# DIRECTORY WHERE TO PUT RESULTS - will create case_id subdirectory
metrics_output_path = '/export/durack1/140701_metrics/test_new'
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES - will create
# case_id subdirectory
model_clims_interpolated_output = '/export/durack1/140701_metrics/test_new'
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_historical_" +\
    "%(realization)_%(period)_interpolated_%(regridMethod)_%(targetGridName)-clim%(ext)"

# Observation json file can be customized and overwritten as follow:
# Custom obs dictionary file
custom_observations = os.path.abspath(
    os.path.join(
        obs_data_path,
        "obs_info_dictionary.json"))

# CUSTOM METRICS
# The following examples allow users to plug in a set of custom metrics
# Function needs:
# INPUT: var name, model clim, obs clim
# OUTPUT: dictionary
# dict pairs are: { metrics_name:float }

import pcmdi_metrics  # Or whatever your custom metrics package name is
compute_custom_metrics = pcmdi_metrics.pcmdi.compute_metrics
# or


def mymax(slab, nm):
    if slab is None:
        return {"custom_%s_max" % nm:
                {"Abstract": "Computes Custom Maximum for demo purposes",
                 "Name": "Custom Maximum",
                 "Contact": "doutriaux1@llnl.gov"},
                }
    else:
        return {"custom_%s_max" % nm: float(slab.max())}


def mymin(slab, nm):
    if slab is None:
        return {"custom_%s_min" % nm:
                {"Abstract": "Computes Custom Minimum for demo purposes",
                 "Name": "Custom Minimum",
                 "Contact": "doutriaux1@llnl.gov"},
                }
    else:
        return {"custom_%s_min" % nm: float(slab.min())}


def my_custom(var, dm, do):
    out = {}
    if var == "tas":
        out.update(mymax(dm, "model"))
    elif var == "tos":
        out.update(mymin(dm, "ref"))
    if dm is None and do is None:
        out["some_custom"] = {
            "Name": "SomeCustom",
            "Abstract": "For demo purpose really does nothing",
            "Contact": "doutriaux1@llnl.gov",
        }
    else:
        out["some_custom"] = 1.5
    return out
compute_custom_metrics = my_custom
