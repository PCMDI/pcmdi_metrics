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
    print("Error: $CMEC_OBS_DATA is not set")
    sys.exit(1)

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
        # get functions
        elif (val[-1] == ')'):
            val = eval(val)
        # also possible someone wrote a bool as a string:
        elif ((val == 'true') or (val == 'True')):
            val = True
        elif ((val == 'false') or (val == 'False')):
            val = False

    if item in ["test_data_path", "modpath"]:
        val = os.path.join(model_dir, val)
    elif item in ["reference_data_path","custom_observations"]:
        val = os.path.join(obs_dir, val)
    elif item in ["metrics_output_path"]:
        val = os.path.join(wk_dir, val)

    # write parameters to file
    if isinstance(val,str):
        # Need to add quotes for string
        param_file.write("{0} = \'{1}\'\n".format(item,val))
    else:
        param_file.write("{0} = {1}\n".format(item,val))

param_file.close()
sys.exit(0)