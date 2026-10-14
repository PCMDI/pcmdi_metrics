#!/usr/bin/env python

# Code History
# ------------
# 2025-01-22 Peter J Glckler: Created
# 2025-02-13 Jiwoo Lee: Cleaned up
# 2025-02-18 Jiwoo Lee: default dict to record default reference dataset per variable
# 2025-02-19 Jiwoo Lee: Tar file archive

import datetime
import glob
import json
import os
import sys
import tarfile


def main():
    # Generate version string based on the current date
    version = datetime.datetime.now().strftime("v%Y%m%d")

    # Configuration
    version_input = "*"
    variable_scope = "*"
    season_search_term = "AC"
    output_dir = "../"
    tar_files = True
    grid_type = "gr"  # "gr" for regridded and "gn" for native grid

    # Set data path from command-line argument or use default
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = "/p/user_pub/pmp/pmp_reference/obs4MIPs_clims"

    # Define the full path for file search
    full_path = os.path.join(
        data_path,
        variable_scope,
        grid_type,
        version_input,
        f"*_{season_search_term}*.nc",
    )

    # Initialize dictionaries to store data
    by_source = {}
    by_var = {}

    # Process files matching the search pattern
    file_list = sorted(glob.glob(full_path))
    for file_path in file_list:
        # Extract path and filename components
        path = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        variable = filename.split("_")[0]
        period = filename.split("_")[5]
        source_id = filename.split("_")[2]
        version_name = path.split("/")[-1]

        # Update `by_source` dictionary
        if source_id not in by_source:
            by_source[source_id] = {}
        if variable not in by_source[source_id]:
            by_source[source_id][variable] = {}

        by_source[source_id][variable] = {
            "PCMDI-path": f"{path}/",
            "path": f"{path.split(data_path)[1].removeprefix('/')}/",
            "filename": filename,
            "template": f"{path.split(data_path)[1].removeprefix('/')}/{filename}",
            "version": version_name,
            "period": period,
        }

        # Update `by_var` dictionary
        if variable not in by_var:
            by_var[variable] = {}
        if source_id not in by_var[variable]:
            by_var[variable][source_id] = {}

        by_var[variable][source_id] = {
            "PCMDI-path": f"{path}/",
            "path": f"{path.split(data_path)[1].removeprefix('/')}/",
            "filename": filename,
            "template": f"{path.split(data_path)[1].removeprefix('/')}/{filename}",
            "version": version_name,
            "period": period,
        }

    # Update by_var to include default dataset info
    default_dict = load_default_dict()

    for variable in list(by_var.keys()):
        if variable in default_dict:
            default_dataset = default_dict[variable]["default"]
            if default_dataset in by_var[variable]:
                by_var[variable]["default"] = default_dataset
            else:
                datasets = list(by_var[variable].keys())
                print(
                    f"No matching reference dataset found for variable {variable}: default reference dataset {default_dataset}, available datasets: {datasets}"
                )

    # Write output JSON files
    by_source_json = os.path.join(
        output_dir, f"PMP-obs4MIPsClims-bySource-{version}.json"
    )
    by_var_json = os.path.join(output_dir, f"PMP-obs4MIPsClims-byVar-{version}.json")

    with open(by_source_json, "w") as outfile:
        json.dump(by_source, outfile, indent=4)
    with open(by_var_json, "w") as outfile:
        json.dump(by_var, outfile, indent=4)

    if tar_files:
        print("Start tar")
        tar_up_files(
            by_var,
            by_var_json,
            output_tar_file=f"/p/user_pub/pmp/pmp_reference/obs4MIPs_clims_tar/PMP-obs4MIPsClims_{version}.tar",
        )
        print("Tar done")


def tar_up_files(by_var, by_var_json, output_tar_file="output_archive.tar"):
    # List of file paths to be added to the tar archive
    file_paths = list()

    variables = list(by_var.keys())
    for variable in variables:
        datasets = list(by_var[variable].keys())
        if "default" in datasets:
            datasets.remove("default")
        for dataset in datasets:
            data_path = os.path.join(
                by_var[variable][dataset]["PCMDI-path"],
                by_var[variable][dataset]["filename"],
            )
            file_paths.append(data_path)

    # Define the level of directory structure to preserve
    preserve_level = 4  # level to preserve

    # Create a compressed tar archive (gzip compression)
    try:
        with tarfile.open(
            output_tar_file, "w"
        ) as tar:  # Use "w:gz" for gzip compression
            for file_path in file_paths:
                # Get the relative path
                relative_path = os.path.relpath(file_path)
                relative_path = relative_path.lstrip("./")
                # Split the path into components
                path_components = relative_path.split(os.sep)
                # path_components = file_path.split(os.sep)
                # Preserve only up to the specified level
                if len(path_components) > preserve_level:
                    arcname = os.path.join(
                        *path_components[:preserve_level], os.path.basename(file_path)
                    )
                else:
                    arcname = relative_path
                # Add the file to the tar archive with the modified arcname
                tar.add(file_path, arcname=arcname)
            # Add catalogue file
            tar.add(
                by_var_json,
                arcname=os.path.join("obs4MIPs_clims", os.path.basename(by_var_json)),
            )
        print(f"Compressed tar file '{output_tar_file}' created successfully!")
    except FileNotFoundError as e:
        print(f"Error: One or more files not found. {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def load_default_dict():
    default_dict = {
        "hfls": {"default": "ERA-INT"},
        "hfns": {"default": "TropFlux-1-0"},
        "hfss": {"default": "ERA-INT"},
        "hur": {"default": "ERA-INT"},
        "hus": {"default": "ERA-INT"},
        "pr": {"default": "GPCP-2-3"},
        "prw": {"default": "REMSS-PRW-v07r01"},
        "psl": {"default": "ERA-5"},
        "rlds": {"default": "CERES-EBAF-4-2"},
        "rldscs": {"default": "CERES-EBAF-4-2"},
        "rltcre": {"default": "CERES-EBAF-4-2"},
        "rlus": {"default": "CERES-EBAF-4-2"},
        "rlut": {"default": "CERES-EBAF-4-2"},
        "rlutcs": {"default": "CERES-EBAF-4-2"},
        "rsds": {"default": "CERES-EBAF-4-2"},
        "rsdscs": {"default": "CERES-EBAF-4-2"},
        "rsdt": {"default": "CERES-EBAF-4-2"},
        "rstcre": {"default": "CERES-EBAF-4-2"},
        "rsus": {"default": "CERES-EBAF-4-2"},
        "rsuscs": {"default": "CERES-EBAF-4-2"},
        "rsut": {"default": "CERES-EBAF-4-2"},
        "rsutcs": {"default": "CERES-EBAF-4-2"},
        "rt": {"default": "CERES-EBAF-4-2"},
        "sfcWind": {"default": "REMSS-PRW-v07r01"},
        "ta": {"default": "ERA-5"},
        "tas": {"default": "ERA-5"},
        "tauu": {"default": "ERA-INT"},
        "tauv": {"default": "ERA-INT"},
        "ts": {"default": "ERA-5"},
        "ua": {"default": "ERA-5"},
        "uas": {"default": "ERA-5"},
        "va": {"default": "ERA-5"},
        "vas": {"default": "ERA-5"},
        "zg": {"default": "ERA-5"},
        "zos": {"default": "AVISO-1-0"},
    }
    return default_dict


if __name__ == "__main__":
    main()
