import os
import re
from typing import Dict, List, Optional

from pcmdi_metrics.mean_climate.lib_unified.lib_unified_dict import (
    load_json_as_dict,
    multi_level_dict,
    print_dict,
    write_to_json,
)
from pcmdi_metrics.mean_climate.lib_unified.lib_unified_rad import derive_rad_var

# from pcmdi_metrics.mean_climate.lib import calculate_climatology


def extract_info_from_model_catalogue(
    variables, models, runs_dict, refs_dict, models_dict, debug=False
):
    if not variables:
        variables_ref = list(refs_dict.keys())
        variables_model = list(models_dict.keys())

        # Find common elements while preserving order
        variables = [var for var in variables_ref if var in variables_model]

        if debug:
            # Print the results
            print("Reference variables:", variables_ref)
            print("Model variables:", variables_model)
            print("Common variables:", variables)

    if not models:
        models = list()
        for var in variables:
            models.extend(list(models_dict[var].keys()))
        models = remove_duplicates(models)

        if debug:
            print("models:", models)

    if runs_dict:
        runs_dict = {}
        for model in models:
            tmp = list()
            for var in variables:
                tmp.extend(list(models_dict[var][model].keys()))
            runs_dict[model] = remove_duplicates(tmp)

        if debug:
            print("runs_dict:", runs_dict)

    return variables, models, runs_dict


def generate_model_data_path(model_data_path_template, var, model, run):
    return (
        model_data_path_template.replace("%(var)", var)
        .replace("%(model)", model)
        .replace("%(run)", run)
    )


def get_model_catalogue(
    model_catalogue_file_path: str,
    variables: Optional[List[str]] = None,
    models: Optional[List[str]] = None,
    runs_dict: Optional[Dict[str, List[str]]] = None,
    model_data_path_template: Optional[str] = None,
) -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
    def update_model_dict(
        model_dict: Dict,
        model_data_path_template: str,
        varname: str,
        model: str,
        run: str,
    ) -> None:
        data_path = generate_model_data_path(
            model_data_path_template, varname, model, run
        )
        model_dict[var][model][run].update(
            {
                "path": os.path.dirname(data_path),
                "filename": os.path.basename(data_path),
                "template": data_path,
                "varname": varname,
            }
        )

    if os.path.isfile(model_catalogue_file_path):
        # Option 1: Simply read models_dict from given catalogue JSON
        models_dict = load_json_as_dict(model_catalogue_file_path)
        # After read models_dict from given catalogue JSON and overwrite it using information from given parameter (model_data_path_template) info
        if model_data_path_template:
            for var in models_dict:
                for model in models_dict[var]:
                    for run in models_dict[var][model]:
                        update_model_dict(
                            models_dict, model_data_path_template, var, model, run
                        )
    elif all(var is not None for var in (variables, models, runs_dict)):
        # Option 2: Create models_dict from given parameters (variables, models, runs_dict, and model_data_path_template) info
        models_dict = multi_level_dict()

        variables_dict = get_unique_bases(variables)
        variables_unique = list(variables_dict.keys())

        for var in variables_unique:
            for model in models:
                runs = runs_dict[model]
                for run in runs:
                    update_model_dict(
                        models_dict,
                        model_data_path_template,
                        var,
                        model,
                        run,
                    )
    else:
        raise ValueError(
            "Either a valid model catalogue file or complete set of parameters (variables, models, runs_dict, and model_data_path_template) must be provided"
        )

    return dict(models_dict)


def get_model_run_data_path(models_dict, var, model, run):
    if (
        "path" in models_dict[var][model][run]
        and "filename" in models_dict[var][model][run]
    ):
        model_data_path = os.path.join(
            models_dict[var][model][run]["path"],
            models_dict[var][model][run]["filename"],
        )
    elif "template" in models_dict[var][model][run]:
        model_data_path = models_dict[var][model][run]["template"]
    else:
        raise ValueError(f"No path, filename, or template found for model: {model}")
    return model_data_path


def get_model_run_out_path(interim_output_path_dict, var):
    path = interim_output_path_dict["model"].replace("%(var)", var)
    os.makedirs(path, exist_ok=True)
    return path


def get_ref_catalogue(ref_catalogue_file_path, ref_data_head=None):
    refs_dict = load_json_as_dict(ref_catalogue_file_path)
    if ref_data_head:
        for var in refs_dict:
            for data in refs_dict[var]:
                data_path = os.path.join(
                    ref_data_head, refs_dict[var][data]["template"]
                )
                refs_dict[var][data].update(
                    {
                        "path": os.path.dirname(data_path),
                        "filename": os.path.basename(data_path),
                        "template": data_path,
                    }
                )
    return refs_dict


def get_ref_data_path(refs_dict, var, ref):
    if "path" in refs_dict[var][ref] and "filename" in refs_dict[var][ref]:
        ref_data_path = os.path.join(
            refs_dict[var][ref]["path"], refs_dict[var][ref]["filename"]
        )
    elif "template" in refs_dict[var][ref]:
        ref_data_path = refs_dict[var][ref]["template"]
    else:
        raise ValueError(f"No path, filename, or template found for ref: {ref}")
    return ref_data_path


def get_ref_out_path(interim_output_path_dict, var):
    path = interim_output_path_dict["ref"].replace("%(var)", var)
    os.makedirs(path, exist_ok=True)
    return path


def get_unique_bases(variables):
    """
    Extract unique base variable names and their associated numbers from a list of variable strings.

    Given a list of variables that may include hyphenated suffixes, this function
    returns a dictionary of unique base names and their associated numbers, preserving the original order.

    Parameters
    ----------
    variables : list of str
        A list of variable names, some of which may include hyphenated suffixes.

    Returns
    -------
    dict
        A dictionary of unique base names and their associated numbers.

    Example
    -------
    >>> variables = ["pr", "ua-200", "va-200", "ua-850"]
    >>> get_unique_bases(variables)
    {'pr': None, 'ua': [200, 850], 'va': [200]}
    """
    result = {}
    for v in variables:
        base, *suffix = v.split("-")
        if base not in result:
            result[base] = []
        if suffix:
            if None not in result[base]:
                result[base].append(int(suffix[0]))
            else:
                raise ValueError(
                    f"Duplicate base name '{base}' with different associated numbers: {result[base]}, {int(suffix[0])}"
                )
        else:
            result[base].append(None)
    return result


def get_annual_cycle(var, data_path, common_grid=None, in_progress=True):
    if in_progress:
        return

    """
    outfile = None
    outpath = None
    outfilename = None
    start = None
    end = None
    ver = None

    d_clim_dict = calculate_climatology(
        var,
        data_path,
        outfile,
        outpath,
        outfilename,
        start,
        end,
        ver,
        periodinname=True,
        climlist=["AC"],
    )

    result = d_clim_dict["AC"]
    """
    result = None

    return result


def calc_metrics(ac_ref, ac_run, in_progress=True):
    if in_progress:
        metrics = None

    return metrics


def extract_level(data, level, in_progress=True):
    if in_progress:
        return

    if level is None:
        return data
    else:
        return data[level]


def interpolate(data, common_grid, in_progress=True):
    if in_progress or common_grid is None:
        return None

    # Interpolation
    ### implement interpolation here


def process_dataset(
    var,
    data_name,
    data_dict,
    ac_dict,
    rad_diagnostic_variables,
    encountered_variables,
    levels,
    common_grid,
    interim_output_path_dict,
    data_type="ref",
):
    # Sanity checks
    if data_type not in ["ref", "model"]:
        raise ValueError("Invalid data_type. Expected 'ref' or 'model'.")
    if (data_type == "ref" and not isinstance(data_name, str)) or (
        data_type == "model"
        and not (
            isinstance(data_name, tuple)
            and all(isinstance(item, str) for item in data_name)
        )
    ):
        raise TypeError("Invalid data_name for the specified data_type.")

    ref, model, run = None, None, None
    if data_type == "ref":
        ref = data_name
        refs_dict = data_dict
        print(f"Processing data for: {ref}")
        # Construct paths
        data_path = get_ref_data_path(refs_dict, var, ref)
        out_path = get_ref_out_path(interim_output_path_dict, var)
        refs_dict[var][ref]["path_ac"] = out_path
        if "varname" in refs_dict[var][ref]:
            varname = refs_dict[var][ref]["varname"]
        else:
            varname = var
    else:
        model, run = data_name
        models_dict = data_dict
        print(f"Processing data for: {model}, {run}")
        # Construct paths
        data_path = get_model_run_data_path(data_dict, var, model, run)
        out_path = get_model_run_out_path(interim_output_path_dict, var)
        models_dict[var][model][run]["path_ac"] = out_path
        if "varname" in models_dict[var][model][run]:
            varname = models_dict[var][model][run]["varname"]
        else:
            varname = var

    print(
        f"Processing {data_type} dataset - varname: {varname}, data: {data_name}, path: {data_path}"
    )

    # Calculate the annual cycle and save annual cycle
    if var not in rad_diagnostic_variables:
        ac = get_annual_cycle(varname, data_path, out_path)
    else:
        ac = derive_rad_var(
            var,
            encountered_variables,
            data_name,
            ac_dict,
            data_dict,
            out_path,
            data_type=data_type,
        )

    # Extract level and interpolation
    for level in levels:
        ac_level = extract_level(ac, level)
        ac_level_interp = interpolate(ac_level, common_grid)

        ### implement plot here if necessary
        print("level:", level)
        ### implement save

        if data_type == "ref":
            ac_dict[var][ref][level] = ac_level_interp
        else:
            ac_dict[var][model][run][level] = ac_level_interp

    return


def calculate_and_save_metrics(
    var,
    model,
    run,
    level,
    regions,
    refs,
    ac_ref_dict,
    ac_model_run_level_interp,
    output_path,
    refs_dict,
    metrics_dict,
    debug=False,
):
    print("refs:", refs)
    print("ac_ref_dict[var].keys():", ac_ref_dict[var].keys())

    if level is None:
        var_key = var
    else:
        var_key = f"{var}-{level}"

    for ref in refs:
        if ref not in ac_ref_dict[var].keys():
            raise KeyError(f"Reference data {ref} is not available for {var}.")

        # Calculate metrics
        for region in regions:
            metrics = calc_metrics(ac_ref_dict[var][ref], ac_model_run_level_interp)

            # Save to dict for later use (accumulated dict)
            metrics_dict[var_key]["RESULTS"][model][run][ref][region] = metrics

    # Dump the dictionary as a JSON file per run
    dict_to_write = multi_level_dict()
    dict_to_write["RESULTS"][model][run] = metrics_dict[var_key]["RESULTS"][model][run]
    dict_to_write["References"] = refs_dict[var]

    metrics_dict.update({"References": {var_key: refs_dict[var]}})

    output_dir = os.path.join(output_path, var_key)
    output_file = os.path.join(output_dir, f"output_{var_key}_{model}_{run}.json")

    os.makedirs(output_dir, exist_ok=True)
    write_to_json(dict_to_write, output_file)

    if debug:
        print_dict(dict_to_write)

    return


def remove_duplicates(tmp: list) -> list:
    return sorted(list(dict.fromkeys(tmp)))


def split_string(s):
    return re.split(r"[-_]", s)
