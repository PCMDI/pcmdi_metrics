import json
import sys

import numpy as np
import pandas as pd

from pcmdi_metrics.utils import sort_human


def read_mean_clim_json_files(
    json_list, regions=None, stats=None, mip=None, debug=False
):
    """
    Parameters
    ----------
    - `json_list`: list of string, where each element is for path/file for PMP output JSON files
    - `regions`: list of string, where each element is region to extract from the JSON.  Optional
    - `stats`: list of string, where each element is statistic to extract from the JSON.  Optional
    - `mip`: string, category for mip, e.g., 'cmip6'.  Optional
    - `debug`: bool, default=False, enable few print statements to help debug

    Returns
    -------
    - `df_dict`: dictionary that has [stat][season][region] hierarchy structure
                 storing pandas dataframe for metric numbers
                 (Rows: models, Columns: variables (i.e., 2d array)
    - `var_list`: list of string, all variables from JSON files
    - `var_unit_list`: list of string, all variables and its units from JSON files
    - `var_ref_list`: list of string, list for default reference dataset for each variable
    - `regions`: list of string, regions
    - `stats`: list of string, statistics
    """
    # Read JSON and get unit for each variable
    results_dict = {}  # merged dict by reading all JSON files
    var_list = []
    var_unit_list = []
    var_ref_dict = {}
    regions_all = []

    for json_file in json_list:
        if debug:
            print("json_file:", json_file)
        with open(json_file) as fj:
            dict_temp = json.load(fj)  # e.g., load contents of precipitation json file
        var = dict_temp["Variable"]["id"]  # e.g., 'pr'
        if "level" in list(dict_temp["Variable"].keys()):
            # defaul PCMDI prefers name convention for pressulre level variables with "name"-"pressure(hPa)"
            # e.g. ua-200, zg-500 etc. In case the user used a pressure in Pa rather than hPa, we add a check
            # with warning message and convert unit to hPa to be consistent with the default PCMDI setup
            level = int(dict_temp["Variable"]["level"])
            if level > 1100:
                print(
                    f"Warning: The provided level value {level} appears to be in Pa. It will be automatically converted to hPa by dividing by 100."
                )
                level = int(level / 100.0)
            var = f"{var}-{str(level)}"  # always hPa
        results_dict[var] = dict_temp
        unit = extract_unit(var, results_dict[var])
        if unit is not None:
            var_unit = f"{var} [{unit}]"
        else:
            var_unit = var
        var_list.append(var)
        var_unit_list.append(var_unit)
        var_ref_dict[var] = extract_ref(var, results_dict[var])
        regions_all.extend(extract_region(var, results_dict[var]))
        if stats is None:
            stats = extract_stat(var, results_dict[var])
    if debug:
        print("var_unit_list:", var_unit_list)
        print("var_ref_dict:", var_ref_dict)

    if regions is None:
        regions = list(set(regions_all))  # Remove duplicates

    # Archive pandas dataframe in returning dictionary
    df_dict = {}

    for stat in stats:
        df_dict[stat] = {}

        if stat in [
            "rms_devzm",
            "rms_xyt",
            "rms_y",
            "std-obs_xy_devzm",
            "std-obs_xyt",
            "std_xy_devzm",
            "std_xyt",
        ]:
            seasons = ["ann"]
        else:
            seasons = ["djf", "mam", "jja", "son"]

        for season in seasons:
            df_dict[stat][season] = {}
            for region in regions:
                df_dict[stat][season][region] = extract_data(
                    results_dict, var_list, region, stat, season, mip, debug
                )

    return df_dict, var_list, var_unit_list, var_ref_dict, regions, stats


def extract_unit(var, results_dict_var):
    model_list = sorted(list(results_dict_var["RESULTS"].keys()))
    try:
        units = results_dict_var["RESULTS"][model_list[0]]["units"]
    except Exception:
        units = None
    return units


def extract_ref(var, results_dict_var):
    model_list = sorted(list(results_dict_var["RESULTS"].keys()))
    try:
        ref = results_dict_var["RESULTS"][model_list[0]]["default"]["source"]
    except Exception:
        ref = None
    return ref


def extract_region(var, results_dict_var):
    region_list, stat_list = extract_region_stat(var, results_dict_var)
    return region_list


def extract_stat(var, results_dict_var):
    region_list, stat_list = extract_region_stat(var, results_dict_var)
    return stat_list


def extract_region_stat(var, results_dict_var):
    model_list = sorted(list(results_dict_var["RESULTS"].keys()))
    run_list = sort_human(
        list(results_dict_var["RESULTS"][model_list[0]]["default"].keys())
    )
    if "source" in run_list:
        run_list.remove("source")
    region_list = sorted(
        list(results_dict_var["RESULTS"][model_list[0]]["default"][run_list[0]].keys())
    )
    if "InputClimatologyFileName" in region_list:
        region_list.remove("InputClimatologyFileName")
    stat_list = sorted(
        list(
            results_dict_var["RESULTS"][model_list[0]]["default"][run_list[0]][
                region_list[0]
            ].keys()
        )
    )
    return region_list, stat_list


def extract_data(results_dict, var_list, region, stat, season, mip, debug=False):
    """
    Return a pandas dataframe for metric numbers at given region/stat/season.
    Rows: models, Columns: variables (i.e., 2d array)
    """
    model_list = sorted(
        list(results_dict[var_list[0]]["RESULTS"].keys()), key=str.casefold
    )
    # update model_list
    if "rlut" in list(results_dict.keys()):
        if "rlut" in list(results_dict["rlut"]["RESULTS"].keys()):
            model_list = sorted(
                list(results_dict["rlut"]["RESULTS"].keys()), key=str.casefold
            )
    if debug:
        print("extract_data:: model_list: ", model_list)

    data_list = []
    for model in model_list:
        run_list = sort_human(
            list(results_dict[var_list[0]]["RESULTS"][model]["default"].keys())
        )
        if "rlut" in list(results_dict.keys()):
            if "rlut" in list(results_dict["rlut"]["RESULTS"].keys()):
                run_list = sort_human(
                    list(results_dict["rlut"]["RESULTS"][model]["default"].keys())
                )

        if debug:
            print("model, run_list:", model, run_list)

        if "source" in run_list:
            run_list.remove("source")

        for run in run_list:
            tmp_list = []
            for var in var_list:
                try:
                    tmp = float(
                        results_dict[var]["RESULTS"][model]["default"][run][region][
                            stat
                        ][season]
                    )
                except Exception:
                    tmp = None
                if debug:
                    print("model, run, season, var, tmp:", model, run, season, var, tmp)
                tmp_list.append(tmp)
            if mip is None:
                data_list.append([model, run, model + "_" + run] + tmp_list)
            else:
                data_list.append([mip, model, run, model + "_" + run] + tmp_list)
    if mip is None:
        data_list_column_names = ["model", "run", "model_run"] + var_list
    else:
        data_list_column_names = ["mip", "model", "run", "model_run"] + var_list
    # Convert data in pythin dict to pandas dataframe format
    df = pd.DataFrame(columns=data_list_column_names, data=data_list)
    return df


def normalize_by_median(data, data_median=None, axis=0):
    """
    Parameters
    ----------
    - `data`: 2d numpy array
    - `data_median`: 2d numpy array, optional, data for median calculation if different to `data`
    - `axis`: 0 (normalize each column) or 1 (normalize each row), default=0
    Return
    ------
    - `data_nor`: 2d numpy array
    """
    if data_median is None:
        data_median = data
    median = np.nanmedian(data_median, axis=axis)
    if axis == 0:
        data_nor = (data - median) / median
    elif axis == 1:
        data_nor = (data - median[:, np.newaxis]) / median[:, np.newaxis]
    else:
        sys.exit("Error: given axis option is not available")
    return data_nor
