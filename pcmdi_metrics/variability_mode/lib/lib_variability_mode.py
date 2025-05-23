import copy
import os
import re
import warnings
from collections import defaultdict
from datetime import datetime
from time import gmtime, strftime
from typing import Union

import numpy as np
import xarray as xr
import xcdat as xc

import pcmdi_metrics
from pcmdi_metrics.io import get_time, select_subset, xcdat_open
from pcmdi_metrics.utils import apply_landmask, check_monthly_time_axis


def search_paths(paths, index1, index2, case_sensitive=False):
    def split_string(text):
        return set(re.split(r"[._ /]", text.lower() if not case_sensitive else text))

    index1 = index1 if case_sensitive else index1.lower()
    index2 = index2 if case_sensitive else index2.lower()

    return [path for path in paths if {index1, index2}.issubset(split_string(path))]


def tree():
    warnings.warn(
        "pcmdi_metrics.variability_modes.lib.tree will be deprecated. Please use pcmdi_metrics.utils.tree, instead."
    )
    return defaultdict(tree)


def get_eof_numbers(mode: str, param) -> tuple:
    """
    Determine the EOF (Empirical Orthogonal Function) numbers for observations and models.

    Parameters
    ----------
    mode : str
        The climate variability mode. Supported modes include:
        - "NAM", "NAO", "SAM", "PNA", "PDO", "AMO" (expected EOF number: 1)
        - "NPGO", "NPO", "PSA1", "EA" (expected EOF number: 2)
        - "PSA2", "SCA" (expected EOF number: 3)
        If the mode is not recognized, a warning is issued, and the expected EOF number is set to None.
    param : object
        An object containing the following attributes:
        - eofn_obs : int or None
            The EOF number for observations. Defaults to the expected EOF number if not provided.
        - eofn_mod : int or None
            The EOF number for models. Defaults to the expected EOF number if not provided.
        - eofn_mod_max : int or None
            The maximum EOF number for models. Defaults to `eofn_mod` if not provided.

    Returns
    -------
    tuple
        A tuple containing:
        - eofn_obs : int
            The EOF number for observations.
        - eofn_mod : int
            The EOF number for models.
        - eofn_mod_max : int
            The maximum EOF number for models.
        - eofn_expected : int
            The expected EOF number for the given mode.

    Notes
    -----
    - If the provided `eofn_obs` or `eofn_mod` does not match the expected EOF number for the given mode,
      a warning is issued.
    - If the mode is not recognized, the expected EOF number is set to None, and the function attempts to
      use the provided `eofn_mod` as the fallback expected value.
    """

    eofn_obs = param.eofn_obs
    eofn_mod = param.eofn_mod
    eofn_mod_max = param.eofn_mod_max

    if mode in ["NAM", "NAO", "SAM", "PNA", "PDO", "AMO"]:
        eofn_expected = 1
    elif mode in ["NPGO", "NPO", "PSA1", "EA"]:
        eofn_expected = 2
    elif mode in ["PSA2", "SCA"]:
        eofn_expected = 3
    else:
        print(
            f"Warning: Mode '{mode}' is not defined with an associated expected EOF number"
        )
        eofn_expected = None

    if eofn_obs is None:
        eofn_obs = eofn_expected
    else:
        eofn_obs = int(eofn_obs)
        if eofn_expected is not None:
            if eofn_obs != eofn_expected:
                print(
                    f"Warning: Observation EOF number ({eofn_obs}) does not match expected EOF number ({eofn_expected}) for mode {mode}"
                )

    if eofn_mod is None:
        eofn_mod = eofn_expected
    else:
        eofn_mod = int(eofn_mod)
        if eofn_expected is not None:
            if eofn_mod != eofn_expected:
                print(
                    f"Warning: Model EOF number ({eofn_mod}) does not match expected EOF number ({eofn_expected}) for mode {mode}"
                )

    if eofn_expected is None:
        eofn_expected = eofn_mod

    if eofn_mod_max is None:
        eofn_mod_max = eofn_mod

    return eofn_obs, eofn_mod, eofn_mod_max, eofn_expected


def write_nc_output(
    output_file_name, eofMap, pc, frac, slopeMap, interceptMap, identifier=None
):
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
    # Add global attributes
    ds.attrs[
        "title"
    ] = "PCMDI Metrics Package Extratropical Modes of Variability diagnostics"
    ds.attrs["author"] = "PCMDI"
    ds.attrs["contact"] = "pcmdi-metrics@llnl.gov"
    ds.attrs["creation_date"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    ds.attrs[
        "references"
    ] = """
    Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019: Quantifying the Agreement Between Observed and Simulated Extratropical Modes of Interannual Variability. Climate Dynamics, 52, 4057-4089, doi: 10.1007/s00382-018-4355-4,
    Lee, J., K. Sperber, P. Gleckler, K. Taylor, and C. Bonfils, 2021: Benchmarking performance changes in the simulation of extratropical modes of variability across CMIP generations. Journal of Climate, 34, 6945–6969, doi: 10.1175/JCLI-D-20-0832.1,
    Lee, J., P. J. Gleckler, M.-S. Ahn, A. Ordonez, P. Ullrich, K. R. Sperber, K. E. Taylor, Y. Y. Planton, E. Guilyardi, P. Durack, C. Bonfils, M. D. Zelinka, L.-W. Chao, B. Dong, C. Doutriaux, C. Zhang, T. Vo, J. Boutte, M. F. Wehner, A. G. Pendergrass, D. Kim, Z. Xue, A. T. Wittenberg, and J. Krasting, 2024: Systematic and Objective Evaluation of Earth System Models: PCMDI Metrics Package (PMP) version 3. Geoscientific Model Development, 17, 3919–3948, doi: 10.5194/gmd-17-3919-2024
    """
    if identifier is not None:
        ds.attrs["identifier"] = identifier
    # Save the dataset to a netcdf file
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
    path: Union[str, list],
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
    ds = xcdat_open(path, chunks=None)

    # Data QC check -- time axis check
    check_monthly_time_axis(ds)

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
        landfrac = None  # by default, generate a land sea mask
        if lf_path is not None:
            if os.path.isfile(lf_path):
                try:
                    landfrac_ds = xcdat_open(lf_path)
                    landfrac = landfrac_ds[var_lf]
                except Exception:
                    landfrac = None  # if unsuccessful, generate a land sea mask

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

    # First trimming
    time1 = f"{syear:04d}-01-01 00:00:00"
    time2 = f"{eyear:04d}-12-{eday:02d} 23:59:59"
    ds = select_subset(ds, time=(time1, time2))

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

    # Second trimming
    if adjust_time_length:
        time1 = f"{data_syear:04d}-01-01 00:00:00"
        time2 = f"{data_eyear:04d}-12-{eday:02d} 23:59:59"
        ds = select_subset(ds, time=(time1, time2))

    return ds


def adjust_units(da: xr.DataArray, adjust_tuple: tuple) -> xr.DataArray:
    action_dict = {"multiply": "*", "divide": "/", "add": "+", "subtract": "-"}
    if adjust_tuple[0]:
        print("Converting units by ", adjust_tuple[1], adjust_tuple[2])
        cmd = " ".join(["da", str(action_dict[adjust_tuple[1]]), str(adjust_tuple[2])])
        da = eval(cmd)
    return da


def check_missing_data(da: xr.DataArray):
    """
    Sanity check for dataset time steps

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
        else:
            if "360" in ds[time_key][0].values.item().calendar:
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
    include_provenance: bool = True,
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
        include_provenance=include_provenance,
    )
    if cmec_flag:
        print("Writing cmec file")
        JSON.write_cmec(indent=4, separators=(",", ": "))
