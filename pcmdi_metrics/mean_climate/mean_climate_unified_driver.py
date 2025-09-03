#!/usr/bin/env python

import datetime
import glob
import json
import logging
import os

from pcmdi_metrics.mean_climate.lib_unified import (
    calculate_and_save_metrics,
    extract_info_from_model_catalogue,
    get_model_catalogue,
    get_ref_catalogue,
    get_unique_bases,
    multi_level_dict,
    print_dict,
    process_dataset,
    write_to_json,
)
from pcmdi_metrics.utils import create_target_grid

# USER SETTING ###########################################

working_dir = "/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output"

"""
variables = [
    "pr", "psl",
    "ua-200", "ua-850", "va-200", "ta-850",
    "rsdt", "rsut", "rsutcs", "rlut", "rlutcs",
    "rstcre", "rltcre", "rt", "rst"
]  # optional. If given, prioritized over the model_catalogue.json. If not given, use all variables commonly in ref_catalogue.json and model_catalogue.json

#variables = [
#    "ua-200", "ua-850", "va-200"
#]

#variables = ["psl"]
"""

variables = [
    "ta-850",
    "ta-500",
    "ta-200",
    "tas",
    "tasmax",
    "tasmin",
    "tauu",
    "tauv",
    "ts",
    "ua-850",
    "ua-200",
    "uas",
    "va-850",
    "va-200",
    "vas",
    "zg",
    "zos",
]

variables = [
    "ta-850",
    "ta-500",
    "ta-200",
]

model_data_path_template = "/home/data/%(model)/%(var)/%(model)_%(run)_%(var)_blabla.nc"  # optional. If given, prioritized over model_catalogue.json

models = [
    "model-a",
    "model-b",
]  # optional. If given, prioritized over the model_catalogue.json. If not given, use all models in model_catalogue.json

models_runs_dict = {
    "model-a": ["r1", "r2"],
    "model-b": ["r1", "r2"],
    "model-c": ["r1", "r2"],
}
# optional. If given, prioritized over the model_catalogue.json. If not given, use all runs in model_catalogue.json

output_path = "/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output/json"

ref_catalogue_file_path = "/global/cfs/projectdirs/m4581/obs4MIPs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_v20250825.json"
model_catalogue_file_path = "model_catalogue.json"

ref_data_head = "/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_LLNL"  # optional, if ref_catalogue file does not include entire directory path

all_ref_variables = False

############################################

regions = ["NHEX", "SHEX"]
target_grid = "2.5x2.5"
rad_diagnostic_variables = ["rt", "rst", "rstcre", "rltcre"]
default_regions = ["global", "NHEX", "SHEX", "TROPICS"]

############################################


logging.basicConfig(
    filename=os.path.join(working_dir, "error_log.txt"),
    level=logging.ERROR,
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if not regions:
    regions = default_regions


refs_dict = get_ref_catalogue(ref_catalogue_file_path, ref_data_head)

if variables is None:
    variables = sorted(list(refs_dict.keys()))


models_dict = get_model_catalogue(
    model_catalogue_file_path,
    variables,
    models,
    models_runs_dict,
    model_data_path_template,
)


era5_files = glob.glob(
    "/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_LLNL/ECMWF/ERA-5/mon/*/gn/latest/*.nc"
)


# List of files (replace this with your full list of files)
files = era5_files

# Initialize an empty dictionary to group files
grouped_files = {}

# Loop through each file path
for file in files:
    # Extract the variable name (e.g., vas, va, tas, etc.)
    variable = file.split("/")[-1].split("_")[0]

    # Extract the dataset name (e.g., ERA-5)
    dataset = file.split("/")[8]

    # Construct the template path with wildcard for the time range
    template = (
        "/".join(file.split("/")[:-1]) + f"/{variable}_mon_{dataset}_PCMDI_gn_*.nc"
    )

    # Add to the dictionary
    if variable not in grouped_files:
        grouped_files[variable] = {}
    if dataset not in grouped_files[variable]:
        grouped_files[variable][dataset] = {"template": template}

# Print the resulting dictionary

print(json.dumps(grouped_files, indent=4))


era5_vars = sorted(list(grouped_files.keys()))


if any(var is None for var in (variables, models, models_runs_dict)):
    variables, models, models_runs_dict = extract_info_from_model_catalogue(
        variables, models, models_runs_dict, refs_dict, models_dict
    )


common_grid = create_target_grid(target_grid_resolution=target_grid)


encountered_variables = set()
anncyc_ref_dict = multi_level_dict()
anncyc_model_run_dict = multi_level_dict()
metrics_dict = multi_level_dict()


if all_ref_variables:
    variables = sorted(list(refs_dict.keys()))

variables_level_dict = get_unique_bases(variables)
variables_unique = list(variables_level_dict.keys())


# target_ref = None
# target_ref = "CERES-EBAF-4-2"
target_ref = "ERA-5"

if target_ref == "ERA-5":
    variables_unique = era5_vars
    refs_dict = grouped_files

print("variables_unique:", variables_unique)
print("variables_level_dict:", variables_level_dict)

print("refs_dict:")
print_dict(refs_dict)
print("models_dict:")
print_dict(models_dict)


def process_references(
    var,
    refs,
    rad_diagnostic_variables,
    levels,
    common_grid,
    start,
    end,
    version,
    interim_output_path_dict,
):
    for ref in refs:
        print(f"=== var, ref: {var}, {ref}")
        # try:
        if 1:
            process_dataset(
                var,
                ref,
                refs_dict,
                anncyc_ref_dict,
                rad_diagnostic_variables,
                encountered_variables,
                levels,
                common_grid,
                interim_output_path_dict["ref"],
                data_type="ref",
                start=start,
                end=end,
                repair_time_axis=True,
                overwrite_output_ac=True,
                version=version,
            )

        """
        except Exception as e:
            # Log the error to a file
            logging.error(f"Error for {var} {ref}: {str(e)}")
            print(f"Error logged for {var} {ref}")
            print(f"Error from process_references for {var} {ref}:", e)
        """


def process_models(
    var,
    models,
    models_runs_dict,
    rad_diagnostic_variables,
    levels,
    common_grid,
    refs,
    start,
    end,
    version,
    interim_output_path_dict,
):
    for model in models:
        for run in models_runs_dict[model]:
            try:
                process_dataset(
                    var,
                    (model, run),
                    models_dict,
                    anncyc_model_run_dict,
                    rad_diagnostic_variables,
                    encountered_variables,
                    levels,
                    common_grid,
                    interim_output_path_dict["model"],
                    data_type="model",
                    start=start,
                    end=end,
                    version=version,
                )
                for level in levels:
                    anncyc_model_run_level_interp = anncyc_model_run_dict[var][model][
                        run
                    ][level]
                    calculate_and_save_metrics(
                        var,
                        model,
                        run,
                        level,
                        regions,
                        refs,
                        anncyc_ref_dict,
                        anncyc_model_run_level_interp,
                        output_path,
                        refs_dict,
                        metrics_dict,
                    )
            except Exception as e:
                print(f"Error from process_models for {var} {model} {run}:", e)

    for level in levels:
        if level is None:
            var_key = var
        else:
            var_key = f"{var}-{level}"
        write_to_json(
            metrics_dict[var_key], os.path.join(output_path, f"output_{var_key}.json")
        )


def main():
    # Set version identifier using the current date if not provided
    version = datetime.datetime.now().strftime("v%Y%m%d")
    version = "v20250825"
    print("version:", version)

    # start = "1981-01"
    # end = "2004-12"

    start = "1980-01"
    end = "2014-12"

    syear = start.split("-")[0]
    eyear = end.split("-")[0]

    interim_output_path_dict = {
        "ref": {
            "path_ac": f"/global/cfs/projectdirs/m4581/PMP/pmp_reference/obs4MIPs_clims_{syear}-{eyear}/%(var)/gn",
            "path_ac_interp": f"/global/cfs/projectdirs/m4581/PMP/pmp_reference/obs4MIPs_clims_{syear}-{eyear}/%(var)/gr",
        },
        "model": {
            "path_ac": f"/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output/clim_models_{syear}-{eyear}/%(var)/gn",
            "path_ac_interp": f"/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output/clim_models_{syear}-{eyear}/%(var)/gr",
        },
    }

    # variables_unique = ["pr"]
    # variables_unique = ["psl"]
    # variables_unique = ["ta", "ua", "va", "zg"]
    # variables_unique = ["tas", "ta"]
    variables_unique = ["ta"]
    # variables_unique = ["ua", "va"]
    # variables_unique.remove("pr")

    for var in variables_unique:
        try:
            print("var:", var)
            encountered_variables.add(var)
            levels = variables_level_dict[var]

            print("levels:", levels)

            # import sys
            # sys.exit("test")

            if var in refs_dict:
                refs = refs_dict[var].keys()

                if target_ref is not None:
                    if target_ref in refs:
                        refs = [target_ref]
                    else:
                        refs = []

                process_references(
                    var,
                    refs,
                    rad_diagnostic_variables,
                    levels,
                    common_grid,
                    start,
                    end,
                    version,
                    interim_output_path_dict,
                )

                # process_models(var, models, models_runs_dict, rad_diagnostic_variables, levels, common_grid, refs, start, end, version)

        except Exception as e:
            print(f"Error from main for {var}:", e)


if __name__ == "__main__":
    main()
