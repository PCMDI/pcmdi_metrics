import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict

import xarray as xr

from pcmdi_metrics.io import load_regions_specs, region_subset, xcdat_open
from pcmdi_metrics.mean_climate.lib import (
    calculate_climatology,
    compute_metrics,
    extract_level,
    extract_levels,
    is_4d_variable,
    plot_climatology,
    plot_climatology_diff,
)
from pcmdi_metrics.mean_climate.lib_unified.lib_unified_dict import (
    load_json_as_dict,
    multi_level_dict,
    print_dict,
    write_to_json,
)
from pcmdi_metrics.mean_climate.lib_unified.lib_unified_rad import derive_rad_var
from pcmdi_metrics.utils import apply_landmask, regrid, replace_date_pattern, sort_human


def process_references(
    var,
    refs,
    rad_diagnostic_variables,
    levels,
    common_grid,
    start,
    end,
    version,
    interim_output_path_dict,
    refs_dict,
    anncyc_ref_dict,
    encountered_variables,
):
    for ref in refs:
        print(f"=== var, ref: {var}, {ref}")
        try:
            ds_ref_level_interp_dict = process_dataset(
                var,
                ref,
                refs_dict,
                anncyc_ref_dict,
                rad_diagnostic_variables,
                encountered_variables,
                levels,
                common_grid,
                interim_output_path_dict["ref"],
                data_type="ref",
                start=start,
                end=end,
                repair_time_axis=True,
                overwrite_output_ac=True,
                version=version,
            )

            anncyc_ref_dict[var][ref] = ds_ref_level_interp_dict

        except Exception as e:
            # Log the error to a file
            logging.error(f"Error for {var} {ref}: {str(e)}")
            print(f"Error logged for {var} {ref}")
            print(f"Error from process_references for {var} {ref}:", e)

    return anncyc_ref_dict


def process_models(
    var,
    models,
    models_dict,
    rad_diagnostic_variables,
    levels,
    common_grid,
    refs,
    start,
    end,
    version,
    interim_output_path_dict,
    anncyc_model_run_dict,
    encountered_variables,
    regions,
    anncyc_ref_dict,
    refs_dict,
    output_path,
    metrics_dict,
    first_member_only=False,
    is_model_input_annual_cycle=False,
):

    for model in models:
        runs = sort_human(list(models_dict[model].keys()))

        if first_member_only:
            runs = runs[0:1]  # use only the first member of each model
        print("model, runs:", model, runs)

        for run in runs:
            try:
                if not is_model_input_annual_cycle:
                    print(f"=== var, model, run: {var}, {model}, {run}")
                    print("process_dataset for model starts")
                    ac_model_dict = process_dataset(
                        var,
                        (model, run),
                        models_dict,
                        anncyc_model_run_dict,
                        rad_diagnostic_variables,
                        encountered_variables,
                        levels,
                        common_grid,
                        interim_output_path_dict["model"],
                        data_type="model",
                        start=start,
                        end=end,
                        version=version,
                    )
                    print("process_dataset for model done")
                else:
                    print(
                        f"Skipping process_dataset for {var} {model} {run} since is_model_input_annual_cycle=True"
                    )
                    pass
                    # Assume anncyc_model_run_dict is already populated externally
                    ac_model_dict = anncyc_model_run_dict[var][model][run]

                for level in levels:
                    print("calculate_and_save_metrics for model starts")
                    calculate_and_save_metrics(
                        var,
                        model,
                        run,
                        level,
                        regions,
                        refs,
                        anncyc_ref_dict,
                        ac_model_dict[var][model][run][level],
                        output_path,
                        refs_dict,
                        metrics_dict,
                        common_grid,
                        case_id=version,
                    )
                    print("calculate_and_save_metrics for model done")
            except Exception as e:
                print(f"Error from process_models for {var} {model} {run}:", e)

    for level in levels:
        if level is None:
            var_key = var
        else:
            var_key = f"{var}-{level}"
        write_to_json(
            metrics_dict[var_key], os.path.join(output_path, f"output_{var_key}.json")
        )


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
    plot_gn: bool = False,
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
        print("ref, data_path:", ref, data_path)
        out_path = get_interim_out_path(interim_output_path_dict_data, "path_ac", var)
        out_path_interp = get_interim_out_path(
            interim_output_path_dict_data, "path_ac_interp", var
        )
        refs_dict[var][ref]["path_ac"] = out_path
        if "varname" in refs_dict[var][ref]:
            varname = refs_dict[var][ref]["varname"]
        else:
            varname = var
        variables_in_dict = list(refs_dict.keys())
    else:
        model, run = data_name
        models_dict = data_dict
        print(f"Processing data for: {model}, {run}")
        print("!!!! debugging point !!!!")
        if var not in models_dict[model][run]:
            models_dict[model][run][var] = {}
        # Construct paths
        data_path = get_model_run_data_path(models_dict, var, model, run)
        print("!!!! data_path:", data_path)
        out_path = get_interim_out_path(
            interim_output_path_dict_data, "path_ac_interp", var
        )
        print("!!!! out_path:", out_path)
        out_path_interp = get_interim_out_path(
            interim_output_path_dict_data, "path_ac", var
        )
        print("!!!! out_path_interp:", out_path_interp)
        models_dict[model][run][var]["path_ac"] = out_path
        if "varname" in models_dict[model][run][var]:
            varname = models_dict[model][run][var]["varname"]
        else:
            varname = var
        print("!!!! varname:", varname)
        variables_in_dict = set()
        for model_tmp, runs in models_dict.items():
            for run, vars_dict in runs.items():
                variables_in_dict.update(vars_dict.keys())

    print("variables_in_dict:", variables_in_dict)

    print(
        f"Processing {data_type} dataset - varname: {varname}, data: {data_name}, path: {data_path}"
    )

    # Set version identifier using the current date if not provided
    if version is None:
        version = datetime.now().strftime("v%Y%m%d")
        print("ver:", version)

    # Calculate the annual cycle and save annual cycle
    if var in rad_diagnostic_variables:
        print(f"{var} is a radiation diagnostic variable")
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
    elif var in variables_in_dict:
        print("get_annual_cycle starts")
        ds_ac = get_annual_cycle(
            varname,
            data_path,
            out_path,
            levels=levels,
            start=start,
            end=end,
            repair_time_axis=repair_time_axis,
            overwrite_output_ac=overwrite_output_ac,
            save_ac_netcdf=save_ac_netcdf,
            ver=version,
            plot=plot_gn,
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
            if isinstance(data_path, list):
                interp_filename_head = str(os.path.basename(data_path[0])).replace(
                    "*", ""
                )
            else:
                interp_filename_head = str(os.path.basename(data_path)).replace("*", "")

        # Proceed interpolation using regrid
        print(f"regrid starts, ds_ac[{varname}].shape: {ds_ac[varname].shape}")
        ds_ac_interp = regrid(ds_ac, varname, common_grid)
        print(
            f"regrid done, ds_ac_interp[{varname}].shape: {ds_ac_interp[varname].shape}"
        )

        # Update attrs
        # Get the current time with UTC timezone
        current_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if isinstance(data_path, list):
            data_path_str = ",".join([os.path.basename(f) for f in data_path])
        else:
            data_path_str = os.path.basename(data_path)

        ds_ac_interp = ds_ac_interp.assign_attrs(
            current_date=f"{current_time_utc}",
            history=f"{current_time_utc}; PCMDI Metrics Package (PMP) calculated climatology and interpolated using {data_path_str}",
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
    if levels is None:
        levels_to_plot = [None]
    else:
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
        else:
            levels_to_plot = [None]

    # Plotting
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
                (
                    interp_filename_head.replace(
                        ".nc", f"_{grid_resolution}.png"
                    ).replace("_gn_", "_gr_")
                ),
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

        # Save to dict for later use (accumulated dict)
        if data_type == "ref":
            ac_dict[var][ref][level] = ds_ac_interp_level
        else:
            ac_dict[var][model][run][level] = ds_ac_interp_level

    return ac_dict


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
    levels: list = [None],
    start: str = "1981-01",
    end: str = "2005-12",
    repair_time_axis: bool = True,
    overwrite_output_ac: bool = True,
    save_ac_netcdf: bool = True,
    ver: str = None,
    plot: bool = True,
):
    # Set version identifier using the current date if not provided
    ver = ver or datetime.now().strftime("v%Y%m%d")
    print("ver:", ver)

    out_path_ver = os.path.join(out_path, ver)
    os.makedirs(out_path_ver, exist_ok=True)

    print("data_path:", data_path)

    if isinstance(data_path, list):
        data_path_template = data_path[0]
    else:
        data_path_template = data_path

    outfilename_head = (
        f"{replace_date_pattern(str(os.path.basename(data_path_template)), '')}".replace(
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

    ds = xcdat_open(data_path, data_var=var)

    if levels == [None]:
        ds_arg = ds
    else:
        if is_4d_variable(ds, var):
            ds = ds.bounds.add_missing_bounds(["Z"])
            print(f"ds[{var}] is 4D variable")
            print("levels:", levels)
            ds_arg = extract_levels(ds, data_var=var, levels=levels)
            print(f"ds_arg[{var}].shape:", ds_arg[var].shape)
        else:
            ds_arg = None

    print("call calculate_climatology")
    d_clim_dict = calculate_climatology(
        var,
        infile=data_path,
        ds=ds_arg,
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
        plot=plot,
    )
    print("done calculate_climatology")

    return d_clim_dict["AC"]


def generate_model_data_path(model_data_path_template, var, model, run):
    return (
        model_data_path_template.replace("%(var)", var)
        .replace("%(model)", model)
        .replace("%(run)", run)
    )


def get_model_catalogue(
    model_catalogue_file_path: str,
) -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
    if os.path.isfile(model_catalogue_file_path):
        # Simply read models_dict from given catalogue JSON
        models_dict = load_json_as_dict(model_catalogue_file_path)
    else:
        raise ValueError("A valid model catalogue file must be provided")

    return dict(models_dict)


def get_interim_out_path(interim_output_path_dict_data, path_key, var) -> str:
    path = interim_output_path_dict_data[path_key].replace("%(var)", var)
    os.makedirs(path, exist_ok=True)
    return path


def get_model_run_data_path(models_dict, var, model, run, debug=False) -> str:
    if debug:
        print("get_model_run_data_path, model, run, var:", model, run, var)
        print("models_dict keys:", models_dict.keys())
        print("models_dict[model] keys:", models_dict[model].keys())
        print("models_dict[model][run] keys:", models_dict[model][run].keys())

    data_path = ""
    if var in models_dict[model][run]:
        if debug:
            print("models_dict[model][run][var]:", models_dict[model][run][var])

        if (
            "path" in models_dict[model][run][var]
            and "filename" in models_dict[model][run][var]
        ):
            data_path = os.path.join(
                models_dict[model][run][var]["path"],
                models_dict[model][run][var]["filename"],
            )
        elif "path" in models_dict[model][run][var]:
            data_path = models_dict[model][run][var]["path"]
        elif "template" in models_dict[model][run][var]:
            data_path = models_dict[model][run][var]["template"]
        else:
            print(f"No path, filename, or template found for model: {model}")
    else:
        print(f"Variable {var} not found for model {model}, run {run}")
    return data_path


def get_ref_catalogue(ref_catalogue_file_path, ref_data_head=None) -> dict:
    refs_dict = load_json_as_dict(ref_catalogue_file_path)
    if ref_data_head:
        for var in refs_dict:
            for data in refs_dict[var]:
                if data not in [
                    "default",
                    "alternate",
                    "alternate1",
                    "alternate2",
                    "alternate3",
                ]:
                    data_path = ""
                    potential_keys = ["template", "obs4MIPs-template"]
                    for potential_key in potential_keys:
                        if potential_key in refs_dict[var][data]:
                            data_path = os.path.join(
                                ref_data_head, refs_dict[var][data][potential_key]
                            )
                            break
                    refs_dict[var][data] = {
                        "path": os.path.dirname(data_path),
                        "filename": os.path.basename(data_path),
                        "template": data_path,
                    }
    return refs_dict


def get_ref_data_path(refs_dict, var, ref):
    if "path" in refs_dict[var][ref] and "filename" in refs_dict[var][ref]:
        return os.path.join(
            refs_dict[var][ref]["path"], refs_dict[var][ref]["filename"]
        )
    elif "template" in refs_dict[var][ref]:
        return refs_dict[var][ref]["template"]
    else:
        print(f"No path, filename, or template found for ref: {ref}")
        return None


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
    common_grid,
    regrid_tool="regrid2",
    case_id="test_case",
    ref_dataset_name=None,
    debug=False,
):
    print("refs:", refs)
    print("ac_ref_dict[var].keys():", ac_ref_dict[var].keys())

    if level is None:
        var_key = var
    else:
        var_key = f"{var}-{level}"

    sftlf = common_grid["sftlf"]

    test_clims_plot_dir = os.path.join(output_path, var_key)
    os.makedirs(test_clims_plot_dir, exist_ok=True)

    for ref in refs:
        if ref not in ac_ref_dict[var].keys():
            raise KeyError(f"Reference data {ref} is not available for {var}.")

        # Extract level for ref
        if level is None:
            ac_ref_level = ac_ref_dict[var][ref]
        else:
            ac_ref_level = extract_level(ac_ref_dict[var][ref], level)

        if debug:
            print("ac_ref_dict[var][ref]:", ac_ref_dict[var][ref])
            print("ac_ref_level:", ac_ref_level)
            print("ac_model_run_level_interp:", ac_model_run_level_interp)

        if ref_dataset_name is None:
            ref_dataset_name = ref

        # Calculate metrics
        for region in regions:
            # Region subsetting
            do = get_region_ds(ac_ref_level, var, sftlf, region)
            dm = get_region_ds(ac_model_run_level_interp, var, sftlf, region)

            # Compute metrics
            metrics = compute_metrics(
                var, dm.squeeze(), do.squeeze(), time_dim_sync=True, debug=debug
            )

            # Save to dict for later use (accumulated dict)
            metrics_dict[var_key]["RESULTS"][model][run][ref][region] = metrics

            # plot map
            for season in ["AC", "DJF", "MAM", "JJA", "SON"]:
                output_filename = "_".join(
                    [
                        var_key,
                        model,
                        run,
                        "interpolated",
                        regrid_tool,
                        region,
                        season,
                        case_id + ".png",
                    ]
                )
                plot_climatology_diff(
                    dm,
                    var,
                    do,
                    var,
                    level=level,
                    season=season,
                    output_dir=test_clims_plot_dir,
                    output_filename=output_filename,
                    dataname_test=f"{model}_{run}",
                    dataname_ref=ref_dataset_name,
                    fig_title=f"Climatology ({season}, {region}): {var_key}",
                )
                print("plot map done")

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


def get_region_ds(ds, data_var, sftlf, region, regions_specs=None):
    # land/sea mask -- conduct masking only for variable data array, not entire data
    if any(keyword in region.split("_") for keyword in ["land", "ocean"]):
        ds_tmp = ds.copy(deep=True)
        if "land" in region.split("_"):
            ds_tmp[data_var] = apply_landmask(
                ds[data_var],
                landfrac=sftlf,
                keep_over="land",
            )
        elif "ocean" in region.split("_"):
            ds_tmp[data_var] = apply_landmask(
                ds[data_var],
                landfrac=sftlf,
                keep_over="ocean",
            )
        print("mask done")
    else:
        ds_tmp = ds

    if regions_specs is None or not bool(regions_specs):
        regions_specs = load_regions_specs()

    # spatial subset
    if region.lower() in ["global", "land", "ocean"]:
        return ds_tmp
    else:
        return region_subset(
            ds_tmp,
            region=region,
            regions_specs=regions_specs,
        )


def remove_duplicates(tmp: list) -> list:
    return sorted(list(dict.fromkeys(tmp)))


def split_string(s):
    return re.split(r"[-_]", s)
