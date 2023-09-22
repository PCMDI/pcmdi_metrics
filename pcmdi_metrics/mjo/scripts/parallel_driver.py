#!/usr/bin/env python

from __future__ import print_function

import glob
import os
from argparse import RawTextHelpFormatter

from genutil import StringConstructor

import pcmdi_metrics
from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.misc.scripts import parallel_submitter
from pcmdi_metrics.mjo.lib import AddParserArgument
from pcmdi_metrics.variability_mode.lib import sort_human

# =================================================
# Collect user defined options
# -------------------------------------------------
P = PMPParser(
    description="Runs PCMDI Modes of MJO Computations",
    formatter_class=RawTextHelpFormatter,
)
P = AddParserArgument(P)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
print("mip:", mip)
print("exp:", exp)

# Variables
var = param.varModel

# Path to model data as string template
modpath = StringConstructor(param.modpath)

# Check given model option
models = param.modnames

# Include all models if conditioned
if ("all" in [m.lower() for m in models]) or (models == "all"):
    model_index_path = param.modpath.split("/")[-1].split(".").index("%(model)")
    models = [
        p.split("/")[-1].split(".")[model_index_path]
        for p in glob.glob(
            modpath(
                mip=mip,
                exp=exp,
                realm="atmos",
                model="*",
                realization="*",
                variable=var,
            )
        )
    ]
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())
    print("param.modpath:", param.modpath)
    print("model_index_path:", model_index_path)

print("models:", models)
print("number of models:", len(models))

# Realizations
realization = param.realization
if ("all" in [r.lower() for r in realization]) or (realization == "all"):
    realization = "*"
print("realization: ", realization)

# case id
case_id = param.case_id
print("case_id:", case_id)

# Output
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(
    str(outdir_template(output_type="%(output_type)", mip=mip, exp=exp))
)

# Debug
debug = param.debug
print("debug:", debug)

# number of tasks to submit at the same time
# num_workers = 20
num_workers = param.num_workers

# =================================================
# Create output directories
# -------------------------------------------------
for output_type in ["graphics", "diagnostic_results", "metrics_results"]:
    os.makedirs(outdir(output_type=output_type), exist_ok=True)
    print(outdir(output_type=output_type))

# =================================================
# Generates list of command
# -------------------------------------------------
param_file = "../param/myParam_mjo.py"

if debug:
    param_file = "../param/myParam_test.py"
    print("number of models (debug mode):", len(models))

cmds_list = list()
logfilename_list = list()
for m, model in enumerate(models):
    print(" ----- model: ", model, " ---------------------")
    # Find all xmls for the given model
    model_path_list = glob.glob(
        modpath(
            mip=mip, exp=exp, realm="atmos", model=model, realization="*", variable=var
        )
    )
    # sort in nice way
    model_path_list = sort_human(model_path_list)
    # Find where run can be gripped from given filename template for modpath
    run_in_modpath = (
        modpath(
            mip=mip,
            exp=exp,
            realm="atmos",
            model=model,
            realization=realization,
            variable=var,
        )
        .split("/")[-1]
        .split(".")
        .index(realization)
    )
    # Collect available runs
    runs_list = [
        model_path.split("/")[-1].split(".")[run_in_modpath]
        for model_path in model_path_list
    ]
    if debug:
        print("runs_list (all):", runs_list)
    # Check if given run member is included. If not for all runs and given run member is not included,
    # take alternative run
    if realization != "*":
        if realization in runs_list:
            runs_list = [realization]
        else:
            runs_list = runs_list[0:1]
        if debug:
            print("runs_list (revised):", runs_list)
    for r, run in enumerate(runs_list):
        # command line for queue
        cmd = [
            "python",
            "mjo_metrics_driver.py",
            "-p",
            param_file,
            "--case_id",
            case_id,
            "--mip",
            mip,
            "--modnames",
            model,
            "--realization",
            run,
            "--parallel",
        ]
        if m > 0 or r > 0:
            cmd += ["--no_OBS"]
        cmds_list.append(" ".join(cmd))
        # log file for each process
        logfilename = "_".join(["log_mjo", mip, exp, model, run, case_id])
        logfilename_list.append(logfilename)

if debug:
    for cmd_list in cmds_list:
        print(" ".join(cmd_list))
    print("num models:", len(models))
    print("num cmds_list:", len(cmds_list))

# =================================================
# Run subprocesses in parallel
# -------------------------------------------------
# log dir
log_dir = outdir(output_type="log")
os.makedirs(log_dir, exist_ok=True)

parallel_submitter(
    cmds_list,
    log_dir=log_dir,
    logfilename_list=logfilename_list,
    num_workers=num_workers,
)
