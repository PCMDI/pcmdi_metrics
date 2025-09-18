#!/usr/bin/env python

import datetime
import logging
import os

from pcmdi_metrics.mean_climate.lib_unified import (  # extract_info_from_model_catalogue,
    get_model_catalogue,
    get_ref_catalogue,
    get_unique_bases,
    multi_level_dict,
    print_dict,
    process_models,
    process_references,
)
from pcmdi_metrics.utils import create_target_grid

# USER SETTING ###########################################

working_dir = "/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output"

variables = [
    # "ta-850",
    # "ta-500",
    # "ta-200",
    # "tas",
    # "tasmax",
    # "tasmin",
    # "tauu",
    # "tauv",
    # "ts",  # need to recheck!
    # "ua-850",
    # "ua-200",
    # "uas",
    # "va-850",
    # "va-200",
    # "vas",
    "zg-200",
    "zg-500",
    "zg-850",
    # "zos",
]

output_path = "/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output/json"

# ref_catalogue_file_path = "/global/cfs/projectdirs/m4581/obs4MIPs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_v20250825.json"
# is_ref_annual_cycle = False

ref_catalogue_file_path = "/global/cfs/projectdirs/m4581/PMP/pmp_reference/catalogue/PMP_obs4MIPsClims_1980-2014_catalogue_byVar_v20250826.json"
is_ref_annual_cycle = True

model_catalogue_file_path = "/pscratch/sd/l/lee1043/git/pcmdi_metrics/sample_setups/pcmdi/data_search/models_path_CMIP6_amip_mon.json"
is_model_processed = False

# Read model_catalogue to get models and runs
models_dict = get_model_catalogue(model_catalogue_file_path)
models = sorted(list(models_dict.keys()))

ref_data_head = "/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_LLNL"  # optional, if ref_catalogue file does not include entire directory path

all_ref_variables = False

regions = ["global"]

target_grid = "2.5x2.5"

# start = "1981-01"
# end = "2004-12"

start = "1980-01"
end = "2014-12"

syear = start.split("-")[0]
eyear = end.split("-")[0]

base_ref_ac_path = f"/global/cfs/projectdirs/m4581/PMP/pmp_reference/obs4MIPs_clims_{syear}-{eyear}/%(var)"
base_model_ac_path = f"/global/cfs/cdirs/m4581/lee1043/work/cdat/pmp/mean_climate/mean_climate_workflow_refactorization/output/clim_models_{syear}-{eyear}/%(var)"

# Set version identifier using the current date if not provided
version = datetime.datetime.now().strftime("v%Y%m%d")
version = "v20250825"
print("version:", version)

############################################

target_ref = None
# target_ref = "CERES-EBAF-4-2"
# target_ref = "ERA-5"

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

common_grid = create_target_grid(target_grid_resolution=target_grid)

encountered_variables = set()
anncyc_ref_dict = multi_level_dict()
anncyc_model_run_dict = multi_level_dict()
metrics_dict = multi_level_dict()

if all_ref_variables:
    variables = sorted(list(refs_dict.keys()))

variables_level_dict = get_unique_bases(variables)
variables_unique = list(variables_level_dict.keys())

print("variables_unique:", variables_unique)
print("variables_level_dict:", variables_level_dict)

print("refs_dict:")
print_dict(refs_dict)
print("models_dict:")
print_dict(models_dict)

interim_output_path_dict = {
    "ref": {
        "path_ac": f"{base_ref_ac_path}/gn",
        "path_ac_interp": f"{base_ref_ac_path}/gr",
    },
    "model": {
        "path_ac": f"{base_model_ac_path}/gn",
        "path_ac_interp": f"{base_model_ac_path}/gr",
    },
}

# variables_unique = ["pr"]
# variables_unique = ["psl"]
# variables_unique = ["ta", "ua", "va", "zg"]
# variables_unique = ["tas", "ta"]
# variables_unique = ["ta"]
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

            if not is_ref_annual_cycle:
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
                    refs_dict,
                    anncyc_ref_dict,
                    encountered_variables,
                )
            else:
                print(
                    f"Skipping process_references for {var} since is_ref_annual_cycle=True"
                )
                # ref_data_path =
                # anncyc_ref_dict[var]["ann"] = xcdat_open()

            process_models(
                var,
                models,
                models_dict,
                rad_diagnostic_variables,
                levels,
                common_grid,
                refs,
                start,
                end,
                version,
                interim_output_path_dict,
                anncyc_model_run_dict,
                encountered_variables,
                regions,
                anncyc_ref_dict,
                refs_dict,
                output_path,
                metrics_dict,
                is_model_processed=is_model_processed,
            )

    except Exception as e:
        print(f"Error from main for {var}:", e)
