#!/usr/bin/env python
import cftime
import cdms2
import datetime
import glob
import json
import numpy as np
import os
import sys
import xarray as xr
import xcdat

from pcmdi_metrics.io.base import Base


def write_to_nc(filepath,ds):
    try:
        ds.to_netcdf(filepath,mode="w")
    except PermissionError as e:
        if os.path.exists(filepath):
            print("  Permission error. Removing existing file",filepath)
            os.remove(filepath)
            print("  Writing new netcdf file",filepath)
            ds.to_netcdf(filepath,mode="w")
        else:
            print("  Permission error. Could not write netcdf file",filepath)
            print("  ",e)
    except Error as e:
        print("  Error: Could not write netcdf file",filepath)
        print("  ",e)

def write_to_json(outdir,json_filename,json_dict):
    # Open JSON
    JSON = Base(
        outdir, json_filename
    )
    json_structure = json_dict["DIMENSIONS"]["json_structure"]

    JSON.write(
        json_dict,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    return

def verify_output_path(metrics_output_path,case_id):
    if metrics_output_path is None:
        metrics_output_path = datetime.datetime.now().strftime("v%Y%m%d")
    if case_id is not None:
        metrics_output_path = metrics_output_path.replace('%(case_id)', case_id)
    if not os.path.exists(metrics_output_path):
        print("\nMetrics output path not found.")
        print("Creating metrics output directory",metrics_output_path)
        try:
            os.makedirs(metrics_output_path)
        except Error as e:
            print("\nError: Could not create metrics output path",metrics_output_path)
            print(e)
            print("Exiting.")
            sys.exit()
    return metrics_output_path

def set_up_realizations(realization):
    find_all_realizations = False
    if realization is None:
        realization = ""
        realizations = [realization]
    elif isinstance(realization, str):
        if realization.lower() in ["all", "*"]:
            find_all_realizations = True
        else:
            realizations = [realization]
    elif isinstance(realization,list):
        realizations = realization
    
    return find_all_realizations,realizations
