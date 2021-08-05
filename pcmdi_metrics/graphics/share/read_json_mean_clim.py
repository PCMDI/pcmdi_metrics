import numpy as np
import json
import pandas as pd


def read_mean_clim_json_files(json_list, stats, regions, mip=None, debug=False):
    """
    Parameters
    ----------
    - `json_list`: list of string, where each element is for path/file for PMP output JSON files
    - `stats`: list of string, where each element is statistic to extract from the JSON
    - `regions`: list of string, where each element is region to extract from the JSON
    - `mip`: string, category for mip, e.g., 'cmip6'.  Optional
    - `debug`: bool, default=False, enable few print statements to help debug
    
    Returns
    -------
    - `df_dict`: dictionary that has [stat][season][region] hierarchy structure storing pandas dataframe for metric numbers (Rows: models, Columns: variables (i.e., 2d array)
    - `var_list`: list of string, all variables from JSON files
    - `var_unit_list`: list of string, all variables and its units from JSON files
    """
    # Find variables
    var_list = sorted([p.split('/')[-1].split('.')[0] for p in json_list])

    # Simple re-order variables
    if 'zg-500' in var_list and 'sfcWind' in var_list:
        var_list.remove('zg-500')
        idx_sfcWind = var_list.index('sfcWind')
        var_list.insert(idx_sfcWind+1, 'zg-500')
    if debug:
        print("var_list:", var_list)

    # Read JSON and get unit for each variable
    results_dict = {}  # merged dict by reading all JSON files
    var_unit_list = []

    for var, json_file in zip(var_list, json_list):
        with open(json_file) as fj:
            results_dict[var] = json.load(fj)
        unit = extract_unit(var, results_dict[var])
        var_unit = var + " [" + unit + "]"   
        var_unit_list.append(var_unit)
    if debug:
        print("var_unit_list:", var_unit_list)

    # Archive pandas dataframe in returning dictionary
    df_dict = {}

    for stat in stats:
        df_dict[stat] = {}

        if stat in ['rms_devzm', 'rms_xyt', 'rms_y', 'std-obs_xy_devzm',
                    'std-obs_xyt', 'std_xy_devzm', 'std_xyt']:
            seasons = ['ann']
        else:
            seasons = ['djf', 'mam', 'jja', 'son']

        for season in seasons:
            df_dict[stat][season] = {}
            for region in regions:
                df_dict[stat][season][region] = extract_data(results_dict, var_list,
                                                             region, stat, season, mip)

    return df_dict, var_list, var_unit_list


def extract_unit(var, results_dict_var):
    model_list = sorted(list(results_dict_var['RESULTS'].keys()))
    units = results_dict_var['RESULTS'][model_list[0]]["units"]
    return units


def extract_data(results_dict, var_list, region, stat, season, mip):
    """
    Return a pandas dataframe for metric numbers at given region/stat/season.
    Rows: models, Columns: variables (i.e., 2d array)
    """
    try:
        model_list = sorted(list(results_dict['rlut']['RESULTS'].keys()))
    except:
        model_list = sorted(list(results_dict[var_list[0]]['RESULTS'].keys()))
    
    data_list = []
    for model in model_list:
        try:
            run_list = list(results_dict['rlut']['RESULTS'][model]['default'].keys())
        except:
            run_list = list(results_dict[var_list[0]]['RESULTS'][model]['default'].keys())
            
        run_list.remove('source')
        for run in run_list:
            tmp_list = []
            for var in var_list:
                try:
                    tmp = float(results_dict[var]['RESULTS'][model]['default'][run][region][stat][season])
                except:
                    tmp = None
                tmp_list.append(tmp)
            if mip is None:
                data_list.append([model, run, model+'_'+run] + tmp_list)
            else:
                data_list.append([mip, model, run, model+'_'+run] + tmp_list)

    if mip is None:
        data_list_column_names = ['model', 'run', 'model_run'] + var_list
    else:
        data_list_column_names = ['mip', 'model', 'run', 'model_run'] + var_list

    # Convert data in pythin dict to pandas dataframe format
    df = pd.DataFrame(columns=data_list_column_names, data=data_list)
    return df


def normalize_by_median(data, axis=0):
    """
    Parameters
    ----------
    - `data`: 2d numpy array
    - `axis`: 0 (normalize each column) or 1 (normalize each row), default=0 
    
    Return
    ------
    - `data_nor`: 2d numpy array
    """
    median = np.nanmedian(data, axis=0)
    data_nor = (data - median) / median
    return data_nor
