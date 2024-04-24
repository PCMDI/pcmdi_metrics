import datetime
import glob
import multiprocessing
import os

import xsearch as xs
from compute_qbo_mjo_metrics import process_qbo_mjo_metrics
from utils_parallel import process

# User options (reference) --------------------------------------------------------------

reference_name = "ERA5"

# ref_input_file = "/work/lee1043/DATA/ERA5/ERA5_u50_monthly_1979-2021.nc"
ref_input_file = "/work/lee1043/DATA/ERA5/ERA5_u50_monthly_1979-2021_rewrite.nc"
# ref_input_file2 = "/work/lee1043/DATA/ERA5/ERA5_olr_daily_40s40n_1979-2021.nc"
ref_input_file2 = "/work/lee1043/DATA/ERA5/ERA5_olr_daily_40s40n_1979-2021_rewrite.nc"

ref_var1 = "u50"
ref_level1 = None  # hPa (=mb)

ref_var2 = "olr"

ref_start = "1979-01"
ref_end = "2005-12"
# ref_end = "2021-12"

include_reference = True
# include_reference = False

# User options (model) ------------------------------------------------------------------

exps = ["historical"]
# exps = ["ssp126", "ssp245", "ssp375", "ssp585"]
# exps = ["ssp370"]

mip_era = "CMIP6"
# mip_era = "CMIP5"

# models = "all"
# models = ["ACCESS-CM2"]
models = []

mip = mip_era.lower()

# Input 1: u50 monthly
var1 = "ua"
freq1 = "mon"
cmipTable1 = "Amon"
level1 = 50  # hPa

# Input 2: olr daily
var2 = "rlut"
freq2 = "day"
cmipTable2 = "day"

# first_member_only = True
first_member_only = False

debug = False
# debug = True

#
# parallel
#
parallel = False
# parallel = True  # not complete yet ... working on it!

num_processes = 10
# num_processes = 3

#
# output
#
result_dir = "output"
if parallel:
    result_dir = "output_parallel"
if debug:
    result_dir = "output_debug"

# Output: diagnostics --- netcdf file
output_filename_template = "qbo_mjo_%(model)_%(exp)_%(realization)_%(start)_%(end).nc"

overwrite_output = False

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())

#
# Processing options
#
regrid = True
regrid_tool = "xesmf"
target_grid = "2x2"

taper_to_mean = True

# -------------------------------------------------------------------------------

params_collect = list()

for exp in exps:
    if exp in ["historical", "amip"]:
        if debug:
            model_start = "2000-01"
            model_end = "2005-12"
        else:
            model_start = "1979-01"
            """
            if mip_era == "CMIP6":
                model_end = "2010-12"
            elif mip_era == "CMIP5":
                model_end = "2005-12"
            else:
                raise ValueError(f"{mip_era} is not defined for 'mip_era'")
            """
            model_end = "2005-12"
    else:
        model_start = "2014-01"
        model_end = "2100-12"

    outdir = os.path.join(result_dir, "diagnostics", mip, exp, case_id)
    logdir = os.path.join(result_dir, "log", mip, exp, case_id)

    # Prepare a directory for output files
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)

    # Search all available models
    dpaths1 = xs.findPaths(exp, var1, freq1, cmipTable=cmipTable1, mip_era=mip_era)
    dpaths2 = xs.findPaths(exp, var2, freq2, cmipTable=cmipTable2, mip_era=mip_era)
    models1 = xs.natural_sort(xs.getGroupValues(dpaths1, "model"))
    models2 = xs.natural_sort(xs.getGroupValues(dpaths2, "model"))

    common_models = [m for m in models1 if m in models2]

    print("exp:", exp)
    print("models1:", models1)
    print("number of models1:", len(models1))
    print("models2:", models2)
    print("number of models2:", len(models2))

    if models == "all":
        models = common_models

    print("models:", models)
    print("number of models:", len(models))

    print("model_start:", model_start)
    print("model_end:", model_end)

    if debug:
        models = models[0:1]
        print("exp:", exp)
        print("models:", models)
        print("number of models:", len(models))

    if include_reference:
        models.insert(0, "reference")

    # model loop
    for model in models:
        if model == "reference":
            members = [reference_name]

        else:
            dpaths_model1 = xs.retainDataByFacetValue(dpaths1, "model", model)
            dpaths_model2 = xs.retainDataByFacetValue(dpaths2, "model", model)
            members1 = xs.natural_sort(xs.getGroupValues(dpaths_model1, "member"))
            members2 = xs.natural_sort(xs.getGroupValues(dpaths_model2, "member"))
            members = [m for m in members1 if m in members2]

            if first_member_only or debug:
                members = members[0:1]
            if debug:
                print("members1 (" + str(len(members1)) + "):", members1)
                print("members2 (" + str(len(members2)) + "):", members2)

        if debug:
            print("members (" + str(len(members)) + "):", members)

        # ensemble member loop
        for member in members:
            if model == "reference" and member == reference_name:
                ncfiles1 = glob.glob(ref_input_file)
                ncfiles2 = glob.glob(ref_input_file2)

                level_extract = ref_level1
                varname = ref_var1
                varname2 = ref_var2

                start = ref_start
                end = ref_end

            else:
                dpaths_model_member_list1 = xs.getValuesForFacet(
                    dpaths_model1, "member", member
                )
                dpaths_model_member_list2 = xs.getValuesForFacet(
                    dpaths_model2, "member", member
                )

                if debug:
                    print("dpaths_model_member_list1:", dpaths_model_member_list1)
                    print("dpaths_model_member_list2:", dpaths_model_member_list2)

                # Sanity check -- var1
                if len(dpaths_model_member_list1) > 1:
                    print(
                        "Error: multiple paths detected for ",
                        model,
                        member,
                        ": ",
                        dpaths_model_member_list1,
                    )
                else:
                    dpath1 = dpaths_model_member_list1[0]
                    ncfiles1 = xs.natural_sort(glob.glob(os.path.join(dpath1, "*.nc")))
                # Sanity check -- var2
                if len(dpaths_model_member_list2) > 1:
                    print(
                        "Error: multiple paths detected for ",
                        model,
                        member,
                        ": ",
                        dpaths_model_member_list2,
                    )
                else:
                    dpath2 = dpaths_model_member_list2[0]
                    ncfiles2 = xs.natural_sort(glob.glob(os.path.join(dpath2, "*.nc")))

                level_extract = level1
                varname = var1
                varname2 = var2
                start = model_start
                end = model_end

            if debug:
                print("ncfiles1:", ncfiles1)
                print("ncfiles2:", ncfiles2)

            # Set output file
            output_filename = (
                output_filename_template.replace("%(exp)", exp)
                .replace("%(model)", model)
                .replace("%(realization)", member)
                .replace("%(start)", start)
                .replace("%(end)", end)
            )
            output_file = os.path.join(outdir, output_filename)

            log_filename = output_filename.replace(".nc", ".log")
            log_file = os.path.join(logdir, log_filename)

            # Set up parameters
            params = {
                "model": model,
                "exp": exp,
                "member": member,
                "input_file": ncfiles1,
                "input_file2": ncfiles2,
                "varname": varname,
                "level": level_extract,  # hPa (=mb)
                "varname2": varname2,
                "start": start,
                "end": end,
                "regrid": regrid,
                "regrid_tool": regrid_tool,
                "target_grid": target_grid,
                "taper_to_mean": taper_to_mean,
                "output_dir": outdir,
                "debug": debug,
                "log_file": log_file,
            }

            # Process -------------------------------------
            if overwrite_output:
                pass
            else:
                if os.path.isfile(output_file):
                    continue  # skip over the below part of the loop, and go on to the next to complete the rest of the loop.

            if parallel:
                params_collect.append(params)
            else:
                # Call detection function
                print("call process_qbo_mjo_metrics for", model, member)
                # if 1:
                try:
                    process_qbo_mjo_metrics(params)
                    print("done process_qbo_mjo_metrics for ", model, member)
                except Exception as e:
                    print("process_qbo_mjo_metrics failed for ", model, member, e)


# The below is yet to work ... in progress!
if parallel:
    num_task = len(params_collect)
    print("number of total tasks: ", len(params_collect))
    if num_task < num_processes:
        num_processes = num_task
    print("number of processes for parallel: ", len(params_collect))

    # pool object with number of element
    pool = multiprocessing.Pool(processes=num_processes)

    # map the function to the list and pass
    # function and input list as arguments
    pool.starmap(process, params_collect)
