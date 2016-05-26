import os

##########################################################################
#  OPTIONS ARE SET BY USER IN THIS FILE AS INDICATED BELOW BY:
#
##########################################################################

# RUN IDENTIFICATION
# DEFINES A SUBDIRECTORY TO METRICS OUTPUT RESULTS SO MULTIPLE CASES CAN
# BE COMPARED
case_id = 'installationTest'

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
vars = ['tos', 'tas']

# MODEL SPECIFC PARAMETERS
model_tweaks = {
    # Keys are model accronym or None which applies to all model entries
    None: {
        # Variables name mapping
        "variable_mapping": {"tos": "tos"},
    },
    "GFDL-ESM2G": {
        "variable_mapping": {"tas": "tas_ac"},
    },
}

# REGIONS ON WHICH WE WANT TO RUN METRICS (var specific)
# Here we run glb for both but also terre and ocean for tas (only)
regions = {"tas": [None, "terre", "ocean"], "tos": [None, ]}
# USER CAN CUSTOMIZE REGIONS VALUES NMAES
regions_values = {"terre": 100.}

# Observations to use at the moment "default" or "alternate"
ref = ['all']
ext = '.nc'

# INTERPOLATION OPTIONS
targetGrid = '2.5x2.5'  # OPTIONS: '2.5x2.5' or an actual cdms2 grid object
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
save_mod_clims = True  # True or False

# DATA LOCATION: MODELS, OBS AND METRICS OUTPUT

# Templates for climatology files
# TEMPLATE EXAMPLE: tas_GFDL-ESM2G_Amon_historical_r1i1p1_198001-199912-clim.nc
filename_template = "%(variable)_%(model_version)_%(table)_historical_%(realization)_%(period)-clim.nc"
# filename template for landsea masks ('sftlf')
sftlf_filename_template = "sftlf_%(model_version).nc"

pth = os.path.dirname(__file__)
# ROOT PATH FOR MODELS CLIMATOLOGIES
mod_data_path = os.path.abspath(os.path.join(pth, "data"))
# ROOT PATH FOR OBSERVATIONS
obs_data_path = os.path.abspath(os.path.join(pth, "obs"))
# Custom obs dictionary file (one we use for tests)
custom_observations = os.path.abspath(
    os.path.join(
        obs_data_path,
        "obs_info_dictionary.json"))
# DIRECTORY WHERE TO PUT RESULTS
metrics_output_path = os.path.join(
    'pcmdi_install_test_results',
    'metrics_results',"%(case_id)")
# DIRECTORY WHERE TO PUT INTERPOLATED MODELS' CLIMATOLOGIES
model_clims_interpolated_output = os.path.join(
    'pcmdi_install_test_results',
    'interpolated_model_clims')
# FILENAME FOR INTERPOLATED CLIMATOLOGIES OUTPUT
filename_output_template = "%(variable)%(level)_%(model_version)_%(table)_" +\
    "historical_%(realization)_%(period).interpolated.%(regridMethod).%(targetGridName)-clim%(ext)"

# Ok do we have custom metrics?
# The following allow users to plug in a set of custom metrics
# Function needs to take in var name, model clim, obs clim
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
# or for different metrics
