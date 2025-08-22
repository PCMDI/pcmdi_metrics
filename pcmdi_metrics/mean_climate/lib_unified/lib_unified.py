import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import xarray as xr

from pcmdi_metrics.mean_climate.lib import (
    calculate_climatology,
    extract_level,
    is_4d_variable,
    plot_climatology,
)
from pcmdi_metrics.mean_climate.lib_unified.lib_unified_dict import (
    load_json_as_dict,
    multi_level_dict,
    print_dict,
    write_to_json,
)
from pcmdi_metrics.mean_climate.lib_unified.lib_unified_rad import derive_rad_var
from pcmdi_metrics.utils import regrid, replace_date_pattern


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


def get_annual_cycle(
    var,
    data_path,
    out_path,
    start="1981-01",
    end="2005-12",
    repair_time_axis=True,
    overwrite_output_ac=True,
    save_ac_netcdf=True,
    ver: str = None,
):
    # Set version identifier using the current date if not provided
    ver = ver or datetime.now().strftime("v%Y%m%d")
    print("ver:", ver)

    out_path_ver = os.path.join(out_path, ver)
    os.makedirs(out_path_ver, exist_ok=True)

    outfilename_head = (
        f"{replace_date_pattern(str(os.path.basename(data_path)), '')}".replace(
            "_.nc", ""
        )
        .replace("_*", "")
        .replace(".nc", "")
        .replace("*", "")
    )
    outfilename_template = (
        f"{outfilename_head}_%(start-yyyymm)-%(end-yyyymm)_%(season)_{ver}.nc"
    )

    print("get_annual_cycle, var:", var)
    print("data_path:", data_path)
    print("out_path:", out_path)
    print("outfilename_head:", outfilename_head)
    print("outfilename_template:", outfilename_template)

    d_clim_dict = calculate_climatology(
        var,
        infile=data_path,
        outpath=out_path_ver,
        outfilename=outfilename_template,
        outfilename_default_template=False,
        start=start,
        end=end,
        ver="",
        periodinname=False,
        repair_time_axis=repair_time_axis,
        overwrite_output=overwrite_output_ac,
        save_ac_netcdf=save_ac_netcdf,
    )

    return d_clim_dict["AC"]


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


def get_interim_out_path(interim_output_path_dict_data, path_key, var):
    path = interim_output_path_dict_data[path_key].replace("%(var)", var)
    os.makedirs(path, exist_ok=True)
    return path


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


def get_ref_catalogue(ref_catalogue_file_path, ref_data_head=None):
    refs_dict = load_json_as_dict(ref_catalogue_file_path)
    if ref_data_head:
        for var in refs_dict:
            for data in refs_dict[var]:
                data_path = ""
                potential_keys = ["template", "obs4MIPs-template"]
                for potential_key in potential_keys:
                    if potential_key in refs_dict[var][data].keys():
                        data_path = os.path.join(
                            ref_data_head, refs_dict[var][data][potential_key]
                        )
                        break
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


def calc_metrics(ac_ref, ac_run, in_progress=True):
    if in_progress:
        metrics = None

    return metrics


def process_dataset(
    var,
    data_name,
    data_dict,
    ac_dict,
    rad_diagnostic_variables,
    encountered_variables,
    levels: list,
    common_grid: xr.Dataset = None,
    interim_output_path_dict_data: dict = None,
    data_type: str = "ref",
    start: str = "1981-01",
    end: str = "2005-12",
    repair_time_axis: bool = False,
    overwrite_output_ac: bool = True,
    save_ac_netcdf: bool = True,
    save_ac_interp_netcdf: bool = True,
    plot_gn: bool = True,
    plot_gr: bool = True,
    version: str = None,
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
        print("jwlee123, ref, data_path:", ref, data_path)
        out_path = get_interim_out_path(interim_output_path_dict_data, "path_ac", var)
        out_path_interp = get_interim_out_path(
            interim_output_path_dict_data, "path_ac_interp", var
        )
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
        out_path = get_interim_out_path(
            interim_output_path_dict_data, "path_ac_interp", var
        )
        out_path_interp = get_interim_out_path(
            interim_output_path_dict_data, "path_ac", var
        )
        models_dict[var][model][run]["path_ac"] = out_path
        if "varname" in models_dict[var][model][run]:
            varname = models_dict[var][model][run]["varname"]
        else:
            varname = var

    print(
        f"Processing {data_type} dataset - varname: {varname}, data: {data_name}, path: {data_path}"
    )

    # Set version identifier using the current date if not provided
    version = datetime.now().strftime("v%Y%m%d")
    print("ver:", version)

    # Calculate the annual cycle and save annual cycle
    if var in data_dict:
        ds_ac = get_annual_cycle(
            varname,
            data_path,
            out_path,
            start=start,
            end=end,
            repair_time_axis=repair_time_axis,
            overwrite_output_ac=overwrite_output_ac,
            save_ac_netcdf=save_ac_netcdf,
            ver=version,
        )
    elif var in rad_diagnostic_variables:
        print(
            f"Note: {var} has to be derived from other variables -- calling 'derive_rad_var'"
        )
        ds_ac = derive_rad_var(
            varname,
            encountered_variables,
            data_name,
            ac_dict,
            data_dict,
            os.path.join(out_path, version),
            data_type=data_type,
            save_ac_netcdf=save_ac_netcdf,
        )
    else:
        raise ValueError(f"Cannot find {var} in data collection.")

    # Interpolation
    if common_grid is not None:
        # Prepare for output file name
        grid_resolution = common_grid.attrs.get("grid_resolution")

        if "filename" in ds_ac.attrs:
            interp_filename_head = str(ds_ac.attrs.get("filename"))
        else:
            interp_filename_head = str(os.path.basename(data_path)).replace("*", "")

        # Proceed interpolation
        print("regrid starts")
        ds_ac_interp = regrid(ds_ac, varname, common_grid)
        print(
            f"regrid done, ds_ac_interp[{varname}].shape: {ds_ac_interp[varname].shape}"
        )

        # Update attrs
        # Get the current time with UTC timezone
        current_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        ds_ac_interp = ds_ac_interp.assign_attrs(
            current_date=f"{current_time_utc}",
            history=f"{current_time_utc}; PCMDI Metrics Package (PMP) calculated climatology and interpolated using {os.path.basename(data_path)}",
        )

        # Save to netcdf file
        if save_ac_interp_netcdf:
            interp_filename_nc = interp_filename_head.replace(
                ".nc", f"_{grid_resolution}.nc"
            ).replace("_gn_", "_gr_")
            os.makedirs(os.path.join(out_path_interp, version), exist_ok=True)
            ds_ac_interp.to_netcdf(
                os.path.join(out_path_interp, version, interp_filename_nc)
            )

    # Extract level and plot climatology
    # Check if variable is 4D
    if is_4d_variable(ds_ac_interp, varname):
        print(f"ds_ac_interp[{varname}] is 4D variable")
        print("levels:", levels)
        # Plot 3 levels (hPa) for 4D variables for quick check
        if len(levels) == 1 and levels[0] is None:
            print("The list contains exactly one element, and it is None.")
            levels_to_plot = [200, 500, 850]
            print("levels_to_plot:", levels_to_plot)
        else:
            levels_to_plot = levels

    for level in levels_to_plot:
        print("level:", level)

        # Extract level
        if level is None:
            ds_ac_interp_level = ds_ac_interp
        else:
            ds_ac_interp_level = extract_level(ds_ac_interp, level)

        # plot for regrided grid
        if plot_gr:
            output_fig_path = os.path.join(
                out_path_interp,
                version,
                (interp_filename_head.replace(".nc", f"_{grid_resolution}.png")),
            )

            if level is not None:
                if var in output_fig_path:
                    output_fig_path = os.path.join(
                        out_path_interp,
                        version,
                        output_fig_path.split("/")[-1].replace(
                            f"{var}_", f"{var}-{level}_"
                        ),
                    )
                else:
                    output_fig_path = output_fig_path.replace(".png", f"-{level}.png")

            # plot climatology for each level
            plot_climatology(
                ds_ac_interp,
                var,
                level=level,
                season_to_plot="all",
                output_filename=output_fig_path,
                period=ds_ac_interp.attrs["period"],
            )

            print(f"plot_gr fig: {output_fig_path}")

        if data_type == "ref":
            ac_dict[var][ref][level] = ds_ac_interp_level
        else:
            ac_dict[var][model][run][level] = ds_ac_interp_level

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

    metrics_dict[var_key].update({"References": refs_dict[var]})

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
