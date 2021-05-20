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
from pcmdi_metrics.io.base import Base

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
            filename_template = settings["filename_template"]
            modellist = settings["test_data_set"]
            varlist = settings["vars"]
            realization = settings.get("realization","")
            period = settings.get("period","")
            model_file = Base(model_dir, filename_template)
            model_file.period = period
            model_file.realization = realization
            out_base = os.path.join(wk_dir,"AC")
            os.mkdir(out_base)

            for model in modellist:
                for var in varlist:
                    model_file.model_version = model
                    model_file.variable = var
                    cmd = ["pcmdi_compute_climatologies.py","--infile",model_file(),"--outpath",out_base,"--var",var]
                    outfilename = out_base + "/pcmdi_compute_climatologies_{0}_{1}.log".format(model,var)
                    with open (outfilename,"w") as outfile:
                        subprocess.run(cmd, env=os.environ.copy(), stdout=outfile)

            # Get the date strings from the climo files for the filename template
            settings["test_data_path"] = out_base
            filelist = os.listdir(out_base)
            try:
                for file in filelist:
                    if ".AC." in file:
                        suffix = file[-30:]
                        break
                settings["filename_template"] = os.path.basename(filename_template)[:-3] + suffix
                print("Success in generating climatologies\n")
            except TypeError:
                print("Error: Could not find climatologies.")
                sys.exit(1)
            # TODO : Should also link sftlf file in AC folder if exists
            if check_for_opt("sftlf_filename_template",settings):
                sftlf=settings["sftlf_filename_template"]

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
