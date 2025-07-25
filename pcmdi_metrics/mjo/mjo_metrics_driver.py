#!/usr/bin/env python

"""
Code written by Jiwoo Lee, LLNL. Feb. 2019
Inspired by Daehyun Kim and Min-Seop Ahn's MJO metrics.

Reference:
Ahn, MS., Kim, D., Sperber, K.R. et al. Clim Dyn (2017) 49: 4023.
https://doi.org/10.1007/s00382-017-3558-4

Auspices:
This work was performed under the auspices of the U.S. Department of
Energy by Lawrence Livermore National Laboratory under Contract
DE-AC52-07NA27344. Lawrence Livermore National Laboratory is operated by
Lawrence Livermore National Security, LLC, for the U.S. Department of Energy,
National Nuclear Security Administration under Contract DE-AC52-07NA27344.

Disclaimer:
This document was prepared as an account of work sponsored by an
agency of the United States government. Neither the United States government
nor Lawrence Livermore National Security, LLC, nor any of their employees
makes any warranty, expressed or implied, or assumes any legal liability or
responsibility for the accuracy, completeness, or usefulness of any
information, apparatus, product, or process disclosed, or represents that its
use would not infringe privately owned rights. Reference herein to any specific
commercial product, process, or service by trade name, trademark, manufacturer,
or otherwise does not necessarily constitute or imply its endorsement,
recommendation, or favoring by the United States government or Lawrence
Livermore National Security, LLC. The views and opinions of authors expressed
herein do not necessarily state or reflect those of the United States
government or Lawrence Livermore National Security, LLC, and shall not be used
for advertising or product endorsement purposes.
"""

import glob
import json
import os
import re
import sys
import time
from argparse import RawTextHelpFormatter
from shutil import copyfile

import pcmdi_metrics
from pcmdi_metrics.mean_climate.lib import pmp_parser
from pcmdi_metrics.mjo.lib import (
    AddParserArgument,
    YearCheck,
    mjo_metric_ewr_calculation,
    mjo_metrics_to_json,
)
from pcmdi_metrics.utils import fill_template, tree

# Must be done before any CDAT library is called.
# https://github.com/CDAT/cdat/issues/2213
if "UVCDAT_ANONYMOUS_LOG" not in os.environ:
    os.environ["UVCDAT_ANONYMOUS_LOG"] = "no"

# =================================================
# Hard coded options... will be moved out later
# -------------------------------------------------
# cmmGrid = False
cmmGrid = True
segmentLength = 180  # number of time step for each segment (in day, in this case)
degX = 2.5  # grid distance for common grid (in degree)

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pmp_parser.PMPParser(
    description="Runs PCMDI MJO Computations", formatter_class=RawTextHelpFormatter
)
P = AddParserArgument(P)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
fq = param.frequency
realm = param.realm

# Variables
varModel = param.varModel
varOBS = param.varOBS

# On/off switches
nc_out = param.nc_out  # Record NetCDF output
plot = param.plot  # Generate plots
includeOBS = param.includeOBS  # Loop run for OBS or not
print("includeOBS:", includeOBS)

# Path to reference data
reference_data_name = param.reference_data_name
reference_data_path = param.reference_data_path

# Path to model data as string template
modpath = param.modpath

# Check given model option
models = param.modnames

# Include all models if conditioned
if ("all" in [m.lower() for m in models]) or (models == "all"):
    model_index_path = re.split(". |_", modpath.split("/")[-1]).index("%(model)")
    models = [
        re.split(". |_", p.split("/")[-1])[model_index_path]
        for p in glob.glob(
            fill_template(
                modpath, mip=mip, exp=exp, model="*", realization="*", variable=varModel
            )
        )
    ]
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print("models:", models)

# Realizations
realization = param.realization
print("realization: ", realization)

# case id
case_id = param.case_id

# Output directory
outdir_template = param.results_dir

# Create output directories
output_types = ["graphics", "diagnostic_results", "metrics_results"]
dir_paths = {}

print("output directories:")

for output_type in output_types:
    dir_path = fill_template(
        outdir_template,
        output_type=output_type,
        mip=mip,
        exp=exp,
        case_id=case_id,
    )
    os.makedirs(dir_path, exist_ok=True)
    print(output_type, ":", dir_path)
    dir_paths[output_type] = dir_path

# Generate CMEC compliant json
if hasattr(param, "cmec"):
    cmec = param.cmec
print("CMEC: " + str(cmec))

# Debug
debug = param.debug
print("debug: ", debug)

# Year
#  model
msyear = param.msyear
meyear = param.meyear
YearCheck(msyear, meyear, P)
#  obs
osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# seasons
seasons = param.seasons
if seasons is None:
    seasons = ["NDJFMA", "MJJASO"]

# Units
units = param.units
#  model
ModUnitsAdjust = param.ModUnitsAdjust
#  obs
ObsUnitsAdjust = param.ObsUnitsAdjust

# JSON update
update_json = param.update_json

# parallel
parallel = param.parallel
print("parallel:", parallel)

# =================================================
# Declare dictionary for .json record
# -------------------------------------------------
result_dict = tree()

# Define output json file
json_filename = "_".join(
    ["mjo_stat", mip, exp, fq, realm, str(msyear) + "-" + str(meyear)]
)
json_file = os.path.join(dir_paths["metrics_results"], json_filename + ".json")
json_file_org = os.path.join(
    dir_paths["metrics_results"],
    "_".join([json_filename, "org", str(os.getpid())]) + ".json",
)

# Save pre-existing json file against overwriting
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)
    if update_json:
        fj = open(json_file)
        result_dict = json.loads(fj.read())
        fj.close()

if "REF" not in list(result_dict.keys()):
    result_dict["REF"] = {}
if "RESULTS" not in list(result_dict.keys()):
    result_dict["RESULTS"] = {}

# =================================================
# Loop start for given models
# -------------------------------------------------
if includeOBS:
    models.insert(0, "obs")

for model in models:
    print(" ----- ", model, " ---------------------")
    try:
        # Conditions depending obs or model
        if model == "obs":
            var = varOBS
            UnitsAdjust = ObsUnitsAdjust
            syear = osyear
            eyear = oeyear
            # variable data
            model_path_list = [reference_data_path]
            # dict for output JSON
            if reference_data_name not in list(result_dict["REF"].keys()):
                result_dict["REF"][reference_data_name] = {}
            # dict for plottng
            dict_obs_composite = {}
            dict_obs_composite[reference_data_name] = {}
        else:  # for rest of models
            var = varModel
            UnitsAdjust = ModUnitsAdjust
            syear = msyear
            eyear = meyear
            # variable data
            model_path_list = glob.glob(
                fill_template(
                    modpath,
                    mip=mip,
                    exp=exp,
                    realm="atmos",
                    model=model,
                    realization=realization,
                    variable=var,
                )
            )
            model_path_list = sorted(model_path_list)
            if debug:
                print("debug: model_path_list: ", model_path_list)
            # dict for output JSON
            if model not in list(result_dict["RESULTS"].keys()):
                result_dict["RESULTS"][model] = {}

        # -------------------------------------------------
        # Loop start - Realization
        # -------------------------------------------------
        for model_path in model_path_list:
            timechk1 = time.time()
            try:
                if model == "obs":
                    run = reference_data_name
                else:
                    if realization in ["all", "All", "ALL", "*"]:
                        run_index = re.split(". |_", modpath.split("/")[-1]).index(
                            "%(realization)"
                        )
                        run = re.split(". |_", model_path.split("/")[-1])[run_index]
                    else:
                        run = realization
                    # dict
                    if run not in result_dict["RESULTS"][model]:
                        result_dict["RESULTS"][model][run] = {}

                print(" --- ", run, " ---")
                print(model_path)

                for season in seasons:
                    print(" -- ", season, " --")
                    if model == "obs":
                        result_dict["REF"][reference_data_name][season] = {}
                    else:
                        result_dict["RESULTS"][model][run][season] = {}

                    # Calculate metric
                    metrics_result = mjo_metric_ewr_calculation(
                        mip,
                        model,
                        exp,
                        run,
                        debug,
                        plot,
                        nc_out,
                        cmmGrid,
                        degX,
                        UnitsAdjust,
                        model_path,
                        var,
                        syear,
                        eyear,
                        segmentLength,
                        dir_paths,
                        season=season,
                    )

                    # Archive as dict for JSON
                    if model == "obs":
                        result_dict["REF"][reference_data_name][season] = metrics_result
                    else:
                        result_dict["RESULTS"][model][run][season] = metrics_result
                        # Nomalized East power by observation (E/O ratio)
                        if includeOBS:
                            result_dict["RESULTS"][model][run][season][
                                "east_power_normalized_by_observation"
                            ] = (
                                result_dict["RESULTS"][model][run][season]["east_power"]
                                / result_dict["REF"][reference_data_name][season][
                                    "east_power"
                                ]
                            )
                # Output to JSON
                # ================================================================
                # Dictionary to JSON: individual JSON during model_realization loop
                # ----------------------------------------------------------------
                json_filename_tmp = "_".join(
                    [
                        "mjo_stat",
                        mip,
                        exp,
                        fq,
                        realm,
                        model,
                        run,
                        str(msyear) + "-" + str(meyear),
                    ]
                )
                mjo_metrics_to_json(
                    dir_paths["metrics_results"],
                    json_filename_tmp,
                    result_dict,
                    model=model,
                    run=run,
                )
                # =================================================
                # Write dictionary to json file
                # (let the json keep overwritten in model loop)
                # -------------------------------------------------
                if not parallel:
                    JSON = pcmdi_metrics.io.base.Base(
                        dir_paths["metrics_results"], json_filename
                    )
                    JSON.write(
                        result_dict,
                        json_structure=["model", "realization", "season", "metric"],
                        sort_keys=True,
                        indent=4,
                        separators=(",", ": "),
                    )
                    if cmec:
                        JSON.write_cmec(indent=4, separators=(",", ": "))
                print("Done")

            except Exception as err:
                if debug:
                    raise
                else:
                    print("warning: failed for ", model, run, err)
                    pass

        # --- Realization loop end

    except Exception as err:
        if debug:
            raise
        else:
            print("warning: failed for ", model, err)
            pass

# --- Model loop end

sys.exit(0)
