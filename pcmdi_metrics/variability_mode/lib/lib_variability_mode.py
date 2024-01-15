import copy
import os
import re
import warnings
from collections import defaultdict
from datetime import datetime
from time import gmtime, strftime

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


def get_domain_range(mode, regions_specs):
    if mode == "NPGO":
        mode_origin_domain = "PDO"
    elif mode == "NPO":
        mode_origin_domain = "PNA"
    else:
        mode_origin_domain = mode

    region_subdomain = regions_specs[mode_origin_domain]["domain"]
    return region_subdomain


def read_data_in(
    path,
    lf_path,
    var_in_data,
    var_to_consider,
    syear,
    eyear,
    UnitsAdjust,
    LandMask,
    debug=False,
):
    # Open data file
    ds = xcdat_open(path)

    #
    # Time subset
    #
    eday = pick_year_last_day(ds)

    time1 = cftime.datetime(syear, 1, 1, 0, 0, 0, 0)
    time2 = cftime.datetime(eyear, 12, eday, 23, 59, 59, 0)
    time_tuple = (time1, time2)

    # First trimming
    data_timeseries = select_subset(ds, time=time_tuple)[var_in_data]

    # missing data check
    check_missing_data(data_timeseries)

    # Check available time window and adjust again if needed
    time = get_time(data_timeseries)
    data_stime = time[0]
    data_etime = time[-1]
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
        data_timeseries = select_subset(data_timeseries, time=time_tuple)

    #
    # Adjust units
    #
    data_timeseries = adjust_units(data_timeseries, UnitsAdjust)

    #
    # Masking
    #
    if var_to_consider == "ts" and LandMask:
        # Replace temperature below -1.8 C to -1.8 C (sea ice)
        data_timeseries = sea_ice_adjust(data_timeseries)

    # landmask if required
    if LandMask:
        # Extract SST (land region mask out)
        # data_timeseries = data_land_mask_out(dataname, data_timeseries, lf_path=lf_path)
        if lf_path is not None:
            if os.path.isfile(lf_path):
                landfrac = xcdat_open(lf_path)
        data_timeseries = apply_landmask(data_timeseries, landfrac=landfrac)

    return data_timeseries, data_syear, data_eyear


def adjust_units(ds, adjust_tuple):
    action_dict = {"multiply": "*", "divide": "/", "add": "+", "subtract": "-"}
    if adjust_tuple[0]:
        print("Converting units by ", adjust_tuple[1], adjust_tuple[2])
        cmd = " ".join(["ds", str(action_dict[adjust_tuple[1]]), str(adjust_tuple[2])])
        ds = eval(cmd)
    return ds


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


def debug_print(string, debug):
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print("debug: " + nowtime + " " + string)


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
    outdir, json_filename, result_dict, model=None, run=None, cmec_flag=False
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
