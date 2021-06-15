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
import subprocess
import sys
import genutil
from climatologies import make_climatologies

def check_for_opt(key,settings):
    result = False
    if key in settings:
        result = settings[key]
    return result

if __name__ == '__main__':

    config_json = sys.argv[1]
    out_file_name = sys.argv[2]
    pmp_config = sys.argv[3]

    wk_dir = os.getenv("CMEC_WK_DIR",default=None)
    model_dir = os.getenv("CMEC_MODEL_DATA",default=None)
    obs_dir = os.getenv("CMEC_OBS_DATA",default=None)

    # getenv returns a string 'None' when no variable set
    if obs_dir == "None":
        print("$CMEC_OBS_DATA is not set")
        if pmp_config in ["mean_climate","variability_modes","monsoon_wang","mjo"]:
            print("Error: PMP/{} requires obs directory".format(pmp_config))
            sys.exit(1)

    try:
        with open(config_json) as config:
            settings = json.load(config)["PMP/"+pmp_config]
    except json.decoder.JSONDecodeError:
        print("Error: could not read " + config_json + ". File might not be valid JSON.")
        sys.exit(1)

    param_file = open(out_file_name, "w")

    # Add commonly used packages to param header
    param_file.write("import datetime\n")
    param_file.write("import glob\n")
    param_file.write("import os\n")
    param_file.write("\n")

    # Overwrite some specific metrics settings
    if pmp_config == "mean_climate":
        settings["test_data_path"] = model_dir
        settings["reference_data_path"] = obs_dir
        settings["metrics_output_path"] = wk_dir

        # TODO: also hard code interpolated field output path to wk_dir

        if check_for_opt("compute_climatologies",settings):
            print("\nGenerating climatologies")
            settings = make_climatologies(settings,model_dir,wk_dir)

    if pmp_config == "monsoon_wang":
        settings["test_data_path"] = os.path.join(model_dir,settings["test_data_path"])
        settings["reference_data_path"] = os.path.join(obs_dir,settings["reference_data_path"])

    if pmp_config in ["variability_modes", "mjo", "monsoon_sperber"]:
        settings["modpath"] = os.path.join(model_dir,settings["modpath"])
        settings["reference_data_path"] = os.path.join(obs_dir,settings["reference_data_path"])
        if "modpath_lf" in settings:
            settings["modpath_lf"] = os.path.join(model_dir,settings["modpath_lf"])
        if "reference_data_lf_path" in settings:
            settings["reference_data_lf_path"] = os.path.join(obs_dir,settings["reference_data_lf_path"])

    if pmp_config == "diurnal_cycle":
        settings["modpath"] = model_dir
    else:
        # other metrics can have single results dir set
        settings["results_dir"] = wk_dir

    # Universal setting for all metrics
    settings["cmec"] = True

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
