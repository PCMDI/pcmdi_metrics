import copy
import os
import re
import warnings
from collections import defaultdict
from datetime import datetime
from time import gmtime, strftime
from typing import Union

import cftime
import numpy as np
import xarray as xr
import xcdat as xc

import pcmdi_metrics
from pcmdi_metrics.io import get_time, select_subset, xcdat_open
from pcmdi_metrics.utils import apply_landmask


def tree():
    warnings.warn(
        "pcmdi_metrics.variability_modes.lib.tree will be deprecated. Please use pcmdi_metrics.utils.tree, instead."
    )
    return defaultdict(tree)


def write_nc_output(output_file_name, eofMap, pc, frac, slopeMap, interceptMap):
    # Create a dataset
    ds = xr.Dataset(
        {
            "pc": pc,  # 1-d timeseries having time dimension
            "eof": eofMap,  # 2-d maps having no time axis
            "slope": slopeMap,
            "intercept": interceptMap,
            "frac": xr.DataArray(
                frac, dims=(), coords={}
            ),  # single number having no axis
        }
    )
    ds.to_netcdf(output_file_name + ".nc")
    ds.close()


def get_domain_range(mode: str, regions_specs: dict):
    if mode == "NPGO":
        mode_origin_domain = "PDO"
    elif mode == "NPO":
        mode_origin_domain = "PNA"
    else:
        mode_origin_domain = mode

    region_subdomain = regions_specs[mode_origin_domain]["domain"]
    return region_subdomain


def read_data_in(
    path: str,
    var_in_data: str,
    var_to_consider: str,
    syear: Union[str, int, float],
    eyear: Union[str, int, float],
    UnitsAdjust: tuple = None,
    lf_path: str = None,
    var_lf: str = "sftlf",
    LandMask: bool = False,
    debug: bool = False,
) -> xr.Dataset:
    # Open data file
    ds = xcdat_open(path)
    ds = (
        ds.bounds.add_missing_bounds()
    )  # https://xcdat.readthedocs.io/en/latest/generated/xarray.Dataset.bounds.add_missing_bounds.html

    # Time subset
    ds_time_subsetted = subset_time(ds, syear, eyear, debug=debug)
    data_timeseries = ds_time_subsetted[var_in_data]

    # Sanity checks
    time_coord = get_time(data_timeseries)
    data_syear = time_coord[0].item().year
    data_eyear = time_coord[-1].item().year

    if int(data_syear) != int(syear):
        print(f"Warning: Data now starts from {data_syear} instead of {syear}")

    if int(data_eyear) != int(eyear):
        print(f"Warning: Data now ends at {data_eyear} instead of {eyear}")

    # missing data check
    check_missing_data(data_timeseries)

    # Adjust units
    if UnitsAdjust is not None:
        data_timeseries = adjust_units(data_timeseries, UnitsAdjust)

    # Masking
    if var_to_consider == "ts" and LandMask:
        # Replace temperature below -1.8 C to -1.8 C (sea ice)
        data_timeseries = sea_ice_adjust(data_timeseries)

    # landmask if required
    if LandMask:
        # Extract SST (land region mask out)
        landfrac = None
        if lf_path is not None:
            if os.path.isfile(lf_path):
                landfrac_ds = xcdat_open(lf_path)
                landfrac = landfrac_ds[var_lf]
        data_timeseries = apply_landmask(data_timeseries, landfrac=landfrac)

    ds_time_subsetted[var_in_data] = data_timeseries

    return ds_time_subsetted


def check_start_end_year(ds: Union[xr.Dataset, xr.DataArray]):
    time_coord = get_time(ds)
    time_coord = get_time(ds)
    data_syear = time_coord[0].item().year
    data_eyear = time_coord[-1].item().year
    return data_syear, data_eyear


def subset_time(
    ds: xr.Dataset,
    syear: Union[str, int, float],
    eyear: Union[str, int, float],
    debug=False,
) -> xr.Dataset:
    #
    # Time subset
    #
    eday = pick_year_last_day(ds)

    if not isinstance(syear, int):
        syear = int(syear)

    if not isinstance(eyear, int):
        eyear = int(eyear)

    time1 = cftime.datetime(syear, 1, 1, 0, 0, 0, 0)
    time2 = cftime.datetime(eyear, 12, eday, 23, 59, 59, 0)
    time_tuple = (time1, time2)

    # First trimming
    ds = select_subset(ds, time=time_tuple)

    # Check available time window and adjust again if needed
    time_coord = get_time(ds)
    data_stime = time_coord[0]
    data_etime = time_coord[-1]
    data_syear = data_stime.item().year
    data_smonth = data_stime.item().month
    data_eyear = data_etime.item().year
    data_emonth = data_etime.item().month

    adjust_time_length = False

    if data_smonth > 1:
        data_syear = data_syear + 1
        adjust_time_length = True
    if data_emonth < 12:
        data_eyear = data_eyear - 1
        adjust_time_length = True

    debug_print(
        "data_syear: " + str(data_syear) + " data_eyear: " + str(data_eyear), debug
    )

    if adjust_time_length:
        time1 = cftime.datetime(data_syear, 1, 1, 0, 0, 0, 0)
        time2 = cftime.datetime(data_eyear, 12, eday, 23, 59, 59, 0)
        time_tuple = (time1, time2)
        # Second trimming
        ds = select_subset(ds, time=time_tuple)

    return ds


def adjust_units(da: xr.DataArray, adjust_tuple: tuple) -> xr.DataArray:
    action_dict = {"multiply": "*", "divide": "/", "add": "+", "subtract": "-"}
    if adjust_tuple[0]:
        print("Converting units by ", adjust_tuple[1], adjust_tuple[2])
        cmd = " ".join(["da", str(action_dict[adjust_tuple[1]]), str(adjust_tuple[2])])
        da = eval(cmd)
    return da


def check_missing_data(da: xr.DataArray):
    """Sanity check for dataset time steps

    Parameters
    ----------
    da : xr.DataArray
        Input data array that has monthly time series

    Raises
    ------
    ValueError
        Raise error if number of time step mismatches to the time in the data
    """
    num_tstep = da.shape[0]

    time = get_time(da)
    date_start = datetime(time[0].item().year, time[0].item().month, time[0].item().day)
    date_end = datetime(
        time[-1].item().year, time[-1].item().month, time[-1].item().day
    )
    months_between = diff_month(date_start, date_end)

    if num_tstep != months_between:
        raise ValueError(
            "ERROR: check_missing_data: num_data_timestep, expected_num_timestep:",
            num_tstep,
            months_between,
        )


def diff_month(date1, date2):
    return (date2.year - date1.year) * 12 + date2.month - date1.month + 1


def debug_print(to_check, debug):
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        if isinstance(to_check, str):
            print("debug: " + nowtime + " " + to_check)
        else:
            print("debug: " + nowtime)
            print(to_check)


def pick_year_last_day(ds):
    eday = 31
    try:
        time_key = xc.axis.get_dim_keys(ds, axis="T")
        if "calendar" in ds[time_key].attrs.keys():
            if "360" in ds[time_key]["calendar"]:
                eday = 30
    except Exception:
        pass
    return eday


def sort_human(input_list):
    warnings.warn(
        "pcmdi_metrics.variability_modes.lib.sort_human will be deprecated. Please use pcmdi_metrics.utils.sort_human, instead."
    )
    lst = copy.copy(input_list)

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split("([0-9]+)", key)]

    lst.sort(key=alphanum)
    return lst


def sea_ice_adjust(data_array: xr.DataArray) -> xr.DataArray:
    """
    Adjust sea ice values in a DataArray.

    Parameters:
    - data_array (xarray.DataArray): Input data array containing sea ice values.

    Returns:
    - xarray.DataArray: New data array with values less than -1.8 replaced by -1.8.
    """
    # Replace values less than -1.8 with -1.8 while conserving attributes
    new_data_array = xr.where(
        (np.isnan(data_array)) | (data_array >= -1.8), data_array, -1.8, keep_attrs=True
    )
    return new_data_array


def variability_metrics_to_json(
    outdir: str,
    json_filename: str,
    result_dict: dict,
    model: str = None,
    run: str = None,
    cmec_flag: bool = False,
):
    # Open JSON
    JSON = pcmdi_metrics.io.base.Base(outdir, json_filename)
    # Dict for JSON
    json_dict = copy.deepcopy(result_dict)
    if model is not None or run is not None:
        # Preserve only needed dict branch -- delete rest keys
        models_in_dict = list(json_dict["RESULTS"].keys())
        for m in models_in_dict:
            if m == model:
                runs_in_model_dict = list(json_dict["RESULTS"][m].keys())
                for r in runs_in_model_dict:
                    if r != run and run is not None:
                        del json_dict["RESULTS"][m][r]
            else:
                del json_dict["RESULTS"][m]
    # Write selected dict to JSON
    JSON.write(
        json_dict,
        json_structure=[
            "model",
            "realization",
            "reference",
            "mode",
            "season",
            "method",
            "statistic",
        ],
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    if cmec_flag:
        print("Writing cmec file")
        JSON.write_cmec(indent=4, separators=(",", ": "))
