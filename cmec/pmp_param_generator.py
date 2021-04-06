"""
pmp_param_generator.py

This script converts parameters from the cmec configuration file to
the format needed to run the PMP metrics. It assumes that the CMEC
environment variables have been set.

Usage:
    python pmp_param_generator.py <output_file_name> <config name>
"""

import datetime
import glob
import json
import os
import sys
import genutil

config_json = sys.argv[1]
out_file_name = sys.argv[2]
pmp_config = sys.argv[3]

wk_dir = os.getenv("CMEC_WK_DIR",default=None)
model_dir = os.getenv("CMEC_MODEL_DATA",default=None)
obs_dir = os.getenv("CMEC_OBS_DATA",default=None)

print(wk_dir)
print(model_dir)
print(obs_dir)

# getenv returns a string 'None' when no variable set
if obs_dir == "None":
    print("$CMEC_OBS_DATA is not set")

try:
    with open(config_json) as config:
        settings = json.load(config)["PMP/"+pmp_config]
except json.decoder.JSONDecodeError:
    print("Error: could not read " + config_json + ". File might not be valid JSON.")
    sys.exit(1)

param_file = open(out_file_name, "w")

param_file.write("import datetime\n")
param_file.write("import glob\n")
param_file.write("import os\n")
param_file.write("\n")

# Overwrite some specific metrics settings
if pmp_config == "mean_climate":
    settings["test_data_path"] = model_dir
    settings["reference_data_path"] = obs_dir
    settings["metrics_output_path"] = wk_dir
    # also hard code interpolated field output path to wk_dir

# Universal setting for all metrics
settings["cmec"] = True

if pmp_config == "diurnal_cycle":
    settings["modpath"] = model_dir
else:
    settings["results_dir"] = wk_dir

"""if "test_data_set" not in settings:
    # See what model folders exist in model directory
    model_list = os.listdir(model_dir)
    test_data_set = []
    for model in model_list:
        fpath = os.path.join(model_dir,model)
        if os.path.isdir(fpath):
            test_data_set.append(model)
    # Derive filename template
    if "filename_template" not in settings:
        var_name = os.path.join(fpath,os.path.listdir(fpath)[0])
        test_name = os.listdir(var_name)[0]
    if "%(model)" not in filename_template:
        test_name.replace(model,"%(model)")
        filename_template = "%(model)/"+test_name

# TODO: also check aliases
if "vars" not in settings:
    # build variable list from directories in model directory
    varlist = os.listdir(model_dir)
    var = []
    for item in varlist:
        if item != "fx" and os.path.isdir(os.path.join(model_dir,item)):
            var.append(item)
    settings["vars"] = var
    if "filename_template" not in settings:
        for varname in var:
            if varname in filename_template:
                filename_template.replace(varname,"%(variable)")
"""

for item in settings:
    val = settings[item]
    # JSON doesn't support several data types, including tuples,
    # dictionaries, and functions. We use the eval statement
    # to extract those from strings in the config file.
    if isinstance(val,str) and val != "":
        # get tuples
        if (val[0] == '(') and (val[-1] == ')'):
            val = eval(val)
        # get dictionary
        elif (val[0] == '{') and (val[-1] == '}'):
            val = eval(val)
        # get function calls, assumed to end with )
        elif (val[-1] == ')'):
            val = eval(val)
        # also possible someone wrote a bool as a string:
        elif ((val == 'true') or (val == 'True')):
            val = True
        elif ((val == 'false') or (val == 'False')):
            val = False

    if item in ["modpath"]:
        val = os.path.join(model_dir, val)
    elif item in ["custom_observations"]:
        val = os.path.join(obs_dir, val)

    # write parameters to file
    if isinstance(val,str):
        # Need to add quotes for string
        param_file.write("{0} = \'{1}\'\n".format(item,val))
    else:
        param_file.write("{0} = {1}\n".format(item,val))

param_file.close()
sys.exit(0)