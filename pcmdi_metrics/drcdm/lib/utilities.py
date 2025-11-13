#!/usr/bin/env python
import datetime
import os
import sys

import cftime
import xcdat

from pcmdi_metrics.io import xcdat_openxml
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.io.xcdat_dataset_io import get_latitude_key, get_longitude_key


def load_dataset(
    filepath, varname, var_map, use_dask, chunk_lat, chunk_lon, chunk_time
):
    # Load an xarray dataset from the given filepath.
    # If list of netcdf files, opens mfdataset.
    # If list of xmls, open last file in list.
    def fix_calendar(ds):
        cal = ds.time.calendar
        # Add any calendar fixes here
        cal = cal.replace("-", "_")
        ds.time.attrs["calendar"] = cal
        ds = xcdat.decode_time(ds)
        return ds

    if filepath[-1].endswith(".xml"):
        # Final item of sorted list would have most recent version date
        ds = xcdat_openxml.xcdat_openxml(filepath[-1])
    elif len(filepath) > 1:  # 3650, "lat": 100, "lon": 100}
        try:
            ds = xcdat.open_mfdataset(
                filepath,
                chunks="auto",
                combine="by_coords",
                data_vars="minimal",
                coords="minimal",
                compat="override",
                parallel=use_dask,
                autoclose=True,
            )
            ds = ds.unify_chunks()
        except ValueError:
            ds = xcdat.open_mfdataset(
                filepath,
                chunks="auto",
                combine="by_coords",
                data_vars="minimal",
                coords="minimal",
                compat="override",
                parallel=use_dask,
                decode_times=False,
                autoclose=True,
            )
            ds = fix_calendar(ds)

        lat_name = get_latitude_key(ds)
        lon_name = get_longitude_key(ds)

        chunks = {"time": chunk_time, lat_name: chunk_lat, lon_name: chunk_lon}
        ds = ds.unify_chunks().chunk(chunks)
    else:
        try:
            ds = xcdat.open_dataset(filepath[0], chunks={"time": 100})
        except ValueError:
            ds = xcdat.open_dataset(
                filepath[0], chunks={"time": 100}, decode_times=False
            )
            ds = fix_calendar(ds)

    # Fix alternate variable naming

    if varname not in ds.data_vars:
        for v in var_map[varname]:
            if v in ds.data_vars:
                ds = ds.rename({v: varname})
                print(f"[Renamed Variable] {v} -> {varname}")
                break
        else:
            raise ValueError("Variable not found in dataset")

    return ds


def slice_dataset(ds, start_year, end_year):
    cal = ds.time.encoding["calendar"]
    start_time = cftime.datetime(
        start_year, 1, 1, 0, 0, calendar=cal
    ) - datetime.timedelta(days=0)
    end_time = cftime.datetime(
        end_year + 1, 1, 1, 23, 59, 59, calendar=cal
    ) - datetime.timedelta(days=1)
    ds = ds.sel(time=slice(start_time, end_time))

    return ds


def replace_multi(string, rdict):
    # Replace multiple keyworks in a string template
    # based on key-value pairs in 'rdict'.
    for k in rdict.keys():
        string = string.replace(k, rdict[k])
    return string


def write_to_nc(data, model, run, region_name, index, years, ncdir, desc, meta):
    # Consolidating some netcdf writing code here to streamline main function
    yrs = "-".join(years)
    filepath = os.path.join(
        ncdir, "_".join([model, run, region_name, index, yrs]) + ".nc"
    )
    write_netcdf_file(filepath, data)
    meta.update_data(os.path.basename(filepath), filepath, index, desc)
    return meta


def write_netcdf_file(filepath, ds):
    try:
        ds.to_netcdf(filepath, mode="w")
    except PermissionError as e:
        if os.path.exists(filepath):
            print("  Permission error. Removing existing file", filepath)
            os.remove(filepath)
            print("  Writing new netcdf file", filepath)
            ds.to_netcdf(filepath, mode="w")
        else:
            print("  Permission error. Could not write netcdf file", filepath)
            print("  ", e)
    except Exception as e:
        print("  Error: Could not write netcdf file", filepath)
        print("  ", e)


def write_to_json(outdir, json_filename, json_dict):
    # Open JSON
    JSON = Base(outdir, json_filename)
    json_structure = json_dict["DIMENSIONS"]["json_structure"]

    JSON.write(
        json_dict,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    return


def verify_years(start_year, end_year, msg="Error: Invalid start or end year"):
    if start_year is None and end_year is None:
        return
    elif start_year is None or end_year is None:
        # If only one of the two is set, exit.
        print(msg)
        print("Exiting")
        sys.exit()


def verify_output_path(metrics_output_path, case_id):
    if metrics_output_path is None:
        metrics_output_path = datetime.datetime.now().strftime("v%Y%m%d")
    if case_id is not None:
        metrics_output_path = metrics_output_path.replace("%(case_id)", case_id)
    if not os.path.exists(metrics_output_path):
        print("\nMetrics output path not found.")
        print("Creating metrics output directory", metrics_output_path)
        try:
            os.makedirs(metrics_output_path)
        except Exception as e:
            print("\nError: Could not create metrics output path", metrics_output_path)
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
            realizations = None
        else:
            realizations = [realization]
    elif isinstance(realization, list):
        realizations = realization

    return find_all_realizations, realizations
