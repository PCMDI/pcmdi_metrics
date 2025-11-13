#!/usr/bin/env python
# flake8: noqa
import glob
import json
import os

import dask
import numpy as np
import xarray
import xcdat
from pint import UnitRegistry

from pcmdi_metrics.drcdm.lib import (
    compute_metrics,
    create_drcdm_parser,
    metadata,
    region_utilities,
    utilities,
)
from pcmdi_metrics.io.xcdat_dataset_io import get_latitude_key, get_longitude_key
from pcmdi_metrics.utils import create_land_sea_mask

ureg = UnitRegistry()
Q_ = ureg.Quantity

if __name__ == "__main__":
    ##########
    # Set up
    ##########

    parser = create_drcdm_parser.create_extremes_parser()
    parameter = parser.get_parameter(argparse_vals_only=False)

    # Parameters
    # I/O settings
    case_id = parameter.case_id
    model_list = parameter.test_data_set
    realization = parameter.realization
    # Expected variables - pr, tasmax, tasmin, tas
    variable_list = parameter.vars
    # variable_name_map = parameter.varmap # TODO: handling datasets without the default variable names in them

    expected_order = ["tasmax", "tasmin", "pr", "tas"]

    ## Creating the variable list
    # Ordering -> expected order is ['tasmax', 'tasmin', 'tas', 'pr']
    ordered_vars = [
        variable for variable in expected_order if variable in variable_list
    ]
    other_vars = [
        variable for variable in variable_list if variable not in expected_order
    ]
    variable_list = ordered_vars + other_vars

    # Tasmax needs to come before tasmin, because one of tasmin datasets relies on stored tasmax
    filename_template = parameter.filename_template
    sftlf_filename_template = parameter.sftlf_filename_template
    test_data_path = parameter.test_data_path
    reference_data_path = parameter.reference_data_path
    reference_data_set = parameter.reference_data_set
    reference_filename_template = parameter.reference_filename_template
    reference_sftlf_template = parameter.reference_sftlf_template
    metrics_output_path = parameter.metrics_output_path

    # Do we require variables to use certain units?
    ModUnitsAdjust = parameter.ModUnitsAdjust
    ObsUnitsAdjust = parameter.ObsUnitsAdjust
    custom_thresholds = parameter.custom_thresholds
    include_metrics = parameter.include_metrics
    var_metric_dict = parameter.var_metric_map
    var_map = parameter.varname_mapper
    compute_tasmean = parameter.compute_tasmean

    ## Adding "tas" to the variable list if compute_tasmean = True and tasmax/tasmin in variable list
    if compute_tasmean and (
        ("tasmin" not in variable_list) or ("tasmax" not in variable_list)
    ):
        print("Must provide tasmax and tasmin to compute tas")
        compute_tasmean = False  # Ignoring
    elif compute_tasmean:
        if "tas" not in variable_list:
            variable_list.append("tas")

    arr = []
    if include_metrics == [
        item for sublist in var_metric_dict.values() for item in sublist
    ]:
        for variable in ordered_vars:
            arr.extend(var_metric_dict[variable])
        for variable in other_vars:
            arr.extend([f"{metric}_{variable}" for metric in var_metric_dict["other"]])
        include_metrics = arr
    else:  # Included metrics should already include desired temp/precip metrics. Just have to fix "other" variable metrics if included
        for metric in var_metric_dict["other"]:
            if metric not in include_metrics:
                continue
            for variable in other_vars:
                include_metrics.append(f"{metric}_{variable}")
            include_metrics.remove(metric)

    if len(include_metrics) < 1:
        raise ValueError("No metric names found")

    for var in other_vars:  ## Appending variable name to the metric names
        var_metric_dict[var] = var_metric_dict["other"]
    del var_metric_dict["other"]

    default_thresh_dict = {
        "tasmin_ge": [Q_(val, "degF") for val in [70, 75, 80, 85, 90]],
        "tasmin_le": [Q_(val, "degF") for val in [0, 32]],
        "monthly_tasmin_le": [Q_(val, "degF") for val in [32]],
        "tasmax_ge": [Q_(val, "degF") for val in [86, 90, 95, 100, 105, 110, 115]],
        "monthly_tasmax_ge": [Q_(val, "degF") for val in [86]],
        "tasmax_le": [Q_(val, "degF") for val in [32]],
        "growing_season": [Q_(val, "degF") for val in [28, 32, 41]],
        "pr_ge": [Q_(val, "inches") for val in [0, 1, 2, 3, 4]],
        "pr_ge_quant": [Q_(val, "%") for val in [90, 95, 99]],
        "tmax_days_above_q": [Q_(val, "%") for val in [99]],
        "tmax_days_below_q": [Q_(val, "%") for val in [1]],
        "tmin_days_above_q": [Q_(val, "%") for val in [99]],
        "tmin_days_below_q": [Q_(val, "%") for val in [1]],
    }

    if not custom_thresholds:
        threshold_dict = default_thresh_dict.copy()
    else:
        threshold_dict = {}
        for key, value in default_thresh_dict.items():
            if key not in custom_thresholds:
                print(f"Using default thresholds for {key}")
                threshold_dict[key] = default_thresh_dict[key]
            else:  # convert user input to default format
                thresh_vals = custom_thresholds[key]["values"]
                units = custom_thresholds[key]["units"]
                threshold_dict[key] = [Q_(val, units) for val in thresh_vals]

    # TODO: Some metrics require a baseline period. Do we use obs for that? Allow two model date ranges?
    msyear = parameter.msyear
    meyear = parameter.meyear
    osyear = parameter.osyear
    oeyear = parameter.oeyear
    generate_sftlf = parameter.generate_sftlf

    # Block extrema related settings
    annual_strict = parameter.annual_strict
    exclude_leap = parameter.exclude_leap
    compute_tasmean = parameter.compute_tasmean
    dec_mode = parameter.dec_mode
    drop_incomplete_djf = parameter.drop_incomplete_djf

    # Region masking
    shp_path = parameter.shp_path
    col = parameter.attribute
    region_name = parameter.region_name
    coords = parameter.coords
    nc_out = parameter.netcdf
    plots = parameter.plot
    mode = parameter.mode

    use_dask = parameter.use_dask
    chunk_time = parameter.chunk_time
    chunk_lat = parameter.chunk_lat
    chunk_lon = parameter.chunk_lon

    if use_dask:  # TODO: Set user options
        from dask.distributed import Client

        Client("tcp://nid004263:8786")  # TODO: Make so user doesn't have to change

        dask.config.set(
            {
                "distributed.worker.memory.target": 0.8,
                "distributed.worker.memory.spill": 0.9,
                "distributed.worker.memory.terminate": 0.98,
                "temporary-directory": "/pscratch/sd/j/jsgoodni/dask-tmp/",
                "array.chunk-size": "192MiB",
                "optimization.fuse.active": True,
                "distributed.scheduler.work.stealing": True,
            }
        )

    # from dask_mpi import initialize
    # initialize(nthreads=16, memory_limit='0', dashboard=True,dashboard_address = ":8787")
    # from dask.distributed import Client
    # client = Client()

    # for v in ["OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_MAX_THREADS"]:
    #     os.environ.setdefault(v, "16")

    if mode.lower() not in ["timeseries", "climatology"]:
        raise ValueError("Mode must be 'timeseries' or 'climatology'")

    mode = mode.lower()  # compatibility with compute_metrics expectations

    # Handling all the cases for possible "include_metrics" arguments. The final result should be a list.
    # Doing this before the chill hours edge case so as to not include all tasmax metrics.

    if ("chill_hours" in include_metrics) and ("tasmax" not in variable_list):
        include_metrics.remove("chill_hours")
        # variable_list = ["tasmax"] + variable_list # So chill hours can be computed
        # ModUnitsAdjust["tasmax"] = ModUnitsAdjust["tasmin"] # assume same conversion for tasmax

    # Helper function for metric computation
    def run_metric(
        metric_name, func, INCLUDED_METRICS=include_metrics, *args, **kwargs
    ):
        if metric_name in INCLUDED_METRICS:
            print(f"Computing {metric_name}")
            return func(*args, **kwargs)
        return {}

    # Check the region masking parameters, if provided
    use_region_mask, region_name, coords = region_utilities.check_region_params(
        shp_path, coords, region_name, col, "land"
    )

    # Verifying output directory
    metrics_output_path = utilities.verify_output_path(metrics_output_path, case_id)

    if isinstance(reference_data_set, list):
        # Fix a command line issue
        reference_data_set = reference_data_set[0]

    # Verify years
    ok_mod = utilities.verify_years(
        msyear,
        meyear,
        msg="Error: Model msyear and meyear must both be set or both be None (unset).",
    )
    ok_obs = utilities.verify_years(
        osyear,
        oeyear,
        msg="Error: Obs osyear and oeyear must both be set or both be None (unset).",
    )

    # Initialize output.json file
    meta = metadata.MetadataFile(metrics_output_path)

    # Initialize Output Path for NetCDF Files
    if nc_out:
        for s in ["annual", "seasonal", "monthly", "quantile"]:
            nc_dir = os.path.join(metrics_output_path, "netcdf")
            nc_subdir = os.path.join(nc_dir, s)
            os.makedirs(nc_subdir, exist_ok=True)

            for v in variable_list:
                var_nc_outdir = os.path.join(nc_subdir, v)
                os.makedirs(var_nc_outdir, exist_ok=True)

    # Initialize Output path for reference files
    ref_dir = os.path.join(metrics_output_path, "reference")
    os.makedirs(ref_dir, exist_ok=True)

    # Initialize Output path for Plots
    if plots:
        for s in ["annual", "seasonal", "monthly", "quantile"]:
            fig_dir = os.path.join(metrics_output_path, "plots")
            plot_subdir = os.path.join(fig_dir, s)
            os.makedirs(plot_subdir, exist_ok=True)

            for v in variable_list:  # Make Subdirectories for each variable
                var_plot_outdir = os.path.join(plot_subdir, v)
                os.makedirs(var_plot_outdir, exist_ok=True)

    # Setting up model realization list
    find_all_realizations, realizations = utilities.set_up_realizations(realization)

    # Only include reference data in loop if it exists
    if reference_data_path is not None:
        model_loop_list = ["Reference"] + model_list
    else:
        model_loop_list = model_list

    # Initialize output JSON structures
    # FYI: if the analysis output JSON is changed, remember to update this function!
    metrics_dict = compute_metrics.init_metrics_dict(
        model_loop_list,
        variable_list,
        dec_mode,
        drop_incomplete_djf,
        annual_strict,
        region_name,
    )
    ##############
    # Run Analysis
    ##############
    ds_tasmax_for_chill_hours = None
    ds_last_freeze = None
    ds_first_freeze = None
    nc_non_zero_pr_ref_file_path = None
    nc_pr_ref_file_path = None
    nc_tmax_ref_file_path = None
    nc_tmin_ref_file_path = None

    # Koppen Utilites
    pr_monthly = None
    tas_monthly = None

    # Loop over models
    for model in model_loop_list:
        if model == "Reference":
            list_of_runs = [str(reference_data_set)]
        elif find_all_realizations:
            tags = {"%(model)": model, "%(model_version)": model, "%(realization)": "*"}
            test_data_full_path = os.path.join(test_data_path, filename_template)
            test_data_full_path = utilities.replace_multi(test_data_full_path, tags)
            ncfiles = glob.glob(test_data_full_path)
            realizations = []
            for ncfile in ncfiles:
                realizations.append(
                    ncfile.split("/")[-1].split(".")[3]
                )  # This is heavily relying on naming conventions
            print("=================================")
            print("model, runs:", model, realizations)
            list_of_runs = realizations
        else:
            list_of_runs = realizations

        metrics_dict["RESULTS"][model] = {}

        # Loop over realizations
        for run in list_of_runs:
            # TODO: For some reason if the reference_data_path was not found, the reference data defaulted to the test data - not sure why
            # Finding land/sea mask

            sftlf_exists = True
            skip_sftlf = False
            if run == reference_data_set:
                if reference_sftlf_template is not None and os.path.exists(
                    reference_sftlf_template
                ):
                    sftlf_filename = reference_sftlf_template
                else:
                    print("No reference sftlf file template provided.")
                    if not generate_sftlf:
                        print("No land/sea mask applied")
                        skip_sftlf = True
                        sftlf_exists = False
                    else:
                        # Set flag to generate sftlf after loading data
                        sftlf_exists = False
            else:
                try:
                    tags = {
                        "%(model)": model,
                        "%(model_version)": model,
                        "%(realization)": run,
                    }
                    sftlf_filename_list = utilities.replace_multi(
                        sftlf_filename_template, tags
                    )
                    sftlf_filename = glob.glob(sftlf_filename_list)[0]
                except (AttributeError, IndexError):
                    print("No sftlf file found for", model, run)
                    if not generate_sftlf:
                        print("No land/sea mask applied")
                        skip_sftlf = True
                        sftlf_exists = False
                    else:
                        # Set flag to generate sftlf after loading data
                        sftlf_exists = False
            if sftlf_exists:
                sftlf = xcdat.open_dataset(sftlf_filename, decode_times=False)
                if use_region_mask:
                    print("\nCreating region mask for land/sea mask.")
                    sftlf = region_utilities.mask_region(
                        sftlf, region_name, coords=coords, shp_path=shp_path, column=col
                    )

            # Initialize results dictionary for this mode/run
            # Presumably we will be populating this will metrics as we go
            metrics_dict["RESULTS"][model][run] = {}

            # In extremes we are looping over different variables. I am really
            # not sure what will be the best way to approach this, if we should loop
            # over variables, take in multiple variables at once, etc.

            for varname in variable_list:
                # Populate the filename templates to get actual data path
                if run == reference_data_set:
                    units_adjust = ObsUnitsAdjust[varname]
                    tags = {
                        "%(variable)": varname,
                    }
                    test_data_full_path = os.path.join(
                        reference_data_path, reference_filename_template
                    )
                    test_data_full_path = utilities.replace_multi(
                        test_data_full_path, tags
                    )
                    # print(test_data_full_path)
                    start_year = osyear
                    end_year = oeyear
                else:
                    if varname != "tas":
                        units_adjust = ModUnitsAdjust[varname]
                    else:
                        units_adjust = ModUnitsAdjust.get(
                            varname, None
                        )  # fallback if needed
                    tags = {
                        "%(variable)": varname,
                        "%(model)": model,
                        "%(model_version)": model,
                        "%(realization)": run,
                    }
                    # some old testing to get the latest version, "/latest/" now works
                    # if test_data_path.endswith('*/'):
                    #     # get latest version
                    #     version = np.sort([vers for vers in os.listdir(utilities.replace_multi(test_data_path.replace("*/", ""), tags)) if vers.startswith('v')])[-1]
                    #     print(version)
                    #     test_data_path_inter = test_data_path.replace("*/", f"{version}/")
                    # else:
                    #     test_data_path_inter = test_data_path

                    test_data_full_path = os.path.join(
                        test_data_path, filename_template
                    )
                    test_data_full_path = utilities.replace_multi(
                        test_data_full_path, tags
                    )
                    start_year = msyear
                    end_year = meyear

                yrs = [str(start_year), str(end_year)]  # for output file names

                # For all variables (including "tas" if not compute_tasmean), check and load file(s)
                if not (varname == "tas" and compute_tasmean):
                    print(test_data_full_path)
                    test_data_full_path = glob.glob(test_data_full_path)

                    test_data_full_path.sort()
                    if len(test_data_full_path) == 0:
                        print("")
                        print("-----------------------")
                        print("Not found: model, run, variable:", model, run, varname)
                        continue
                    else:
                        print("")
                        print("-----------------------")
                        print("model, run, variable:", model, run, varname)
                        print("test_data (model in this case) full_path:")
                        for t in test_data_full_path:
                            print("  ", t)

                # Load and prep data
                if (varname == "tas") and (compute_tasmean):
                    ds = da_tas.to_dataset(name="tas")
                else:
                    ds = utilities.load_dataset(
                        test_data_full_path,
                        varname,
                        var_map,
                        use_dask=use_dask,
                        chunk_time=chunk_time,
                        chunk_lat=chunk_lat,
                        chunk_lon=chunk_lon,
                    )

                    # if varname not in ds.data_vars:
                    #     for v in var_map[varname]:
                    #         if v in ds.data_vars:
                    #             ds = ds.rename({v: varname})
                    #             print(f"[Renamed Variable] {v} -> {varname}")
                    #             break
                    #     else:
                    #         raise ValueError("Variable not found in dataset")

                    if not sftlf_exists and generate_sftlf:
                        print("Generating land sea mask.")
                        sft = create_land_sea_mask(ds)
                        sftlf = ds.copy(data=None)
                        sftlf["sftlf"] = sft
                        if use_region_mask:
                            print("\nCreating region mask for land/sea mask.")
                            sftlf = region_utilities.mask_region(
                                sftlf,
                                region_name,
                                coords=coords,
                                shp_path=shp_path,
                                column=col,
                            )
                    elif skip_sftlf:
                        # Make mask with all ones
                        sftlf = ds.copy(data=None)
                        sftlf["sftlf"] = xarray.ones_like(ds[varname].isel({"time": 0}))
                        if use_region_mask:
                            print("\nCreating region mask for land/sea mask.")
                            sftlf = region_utilities.mask_region(
                                sftlf,
                                region_name,
                                coords=coords,
                                shp_path=shp_path,
                                column=col,
                            )

                    # Mask out Antarctica
                    sflat = get_latitude_key(sftlf)
                    sftlf["sftlf"] = sftlf["sftlf"].where(sftlf[sflat] > -60)

                    if use_region_mask:
                        print("Creating dataset mask")
                        ds = region_utilities.mask_region(
                            ds,
                            region_name,
                            coords=coords,
                            shp_path=shp_path,
                            column=col,
                        )

                    # Get time slice if year parameters exist
                    if start_year is not None:
                        ds = utilities.slice_dataset(ds, start_year, end_year)
                    else:
                        # Get labels for start/end years from dataset
                        yrs = [
                            str(int(ds.time.dt.year[0])),
                            str(int(ds.time.dt.year[-1])),
                        ]

                    if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                        units = ds.time.encoding["units"]
                        ds = ds.convert_calendar("noleap")
                        ds.time.encoding["calendar"] = "noleap"
                        ds.time.encoding["units"] = units

                    if ds[varname].attrs["units"] == "kg m-2 s-1":
                        ds[varname].attrs["units"] = "mm"

                    ds[varname] = compute_metrics.convert_units(
                        ds[varname], units_adjust
                    )
                    data_units = ds[varname].attrs["units"]

                if varname == "pr":  # set all precip data < 1mm/day to 0mm/day
                    ds = compute_metrics.clip_precip(ds)

                # Set up output file names
                if nc_out:
                    # $index will be replaced with index name in metrics function
                    nc_base = os.path.join(nc_dir, "$freq")
                    nc_base = os.path.join(nc_base, "$varname")
                    nc_base = os.path.join(
                        nc_base, "_".join([model, run, "$metric.nc"])
                    )

                    nc_base_for_qthresh = os.path.join(
                        ref_dir, "_".join([model, run, "$index.nc"])
                    )
                else:
                    nc_base = None
                    nc_base_for_qthresh = os.path.join(
                        ref_dir, "_".join([model, run, "$index.nc"])
                    )
                if plots:
                    fig_base = os.path.join(
                        fig_dir, "_".join([model, run, "$index.png"])
                    )
                else:
                    fig_base = None

                # try:
                #     lat_name = get_latitude_key(ds)
                #     lon_name = get_longitude_key(ds)

                #     ds = ds.chunk({"time": 3650, lat_name: 100, lon_name: 100})

                # except Exception as e:
                #     print(e)
                #     pass

                default_args = dict(
                    ds=ds,
                    sftlf=sftlf,
                    dec_mode=dec_mode,
                    drop_incomplete_djf=drop_incomplete_djf,
                    annual_strict=annual_strict,
                    fig_file=fig_base,
                    nc_file=nc_base,
                    mode=mode,
                )
                print(np.unique(ds.time.dt.year.data))
                # Do metrics calculations
                if (varname == "tasmax") and (
                    run == reference_data_set
                ):  # Get the reference dataset we need for model metrics that require a baseline
                    # if compute_tasmean:
                    #     da_tas = ds[varname].copy(deep=True) / 2
                    #     da_tas.attrs = ds[varname].attrs.copy()

                    args = default_args.copy()
                    args["nc_file"] = nc_base_for_qthresh
                    args["start_year"] = osyear
                    args["end_year"] = oeyear
                    args["quantiles"] = (
                        threshold_dict["tmax_days_above_q"]
                        + threshold_dict["tmax_days_below_q"]
                    )

                    del args["fig_file"]

                    result = run_metric(
                        "ref_q_tasmax", compute_metrics.get_ref_tasmax_Q, **args
                    )

                    if isinstance(
                        result, tuple
                    ):  # saves a quantile tasmax netCDF file for later use
                        result_dict, nc_tmax_ref_file_path = result
                    else:
                        result_dict = result

                if (
                    varname == "tasmax"
                ):  # and (run != reference_data_set): # TODO: Do we really need to exclude the reference dataset?
                    if compute_tasmean:
                        da_tas = ds[varname].copy(deep=True) / 2
                        da_tas.attrs = ds[varname].attrs.copy()

                    if (
                        reference_data_set is None
                    ):  # compute quantile thresholds using model dataset itself
                        args = default_args.copy()
                        args["nc_file"] = nc_base_for_qthresh
                        args["start_year"] = osyear
                        args["end_year"] = oeyear
                        args["quantiles"] = (
                            threshold_dict["tmax_days_above_q"]
                            + threshold_dict["tmax_days_below_q"]
                        )
                        del args["fig_file"]

                        result = run_metric(
                            "ref_q_tasmax", compute_metrics.get_ref_tasmax_Q, **args
                        )
                        if isinstance(result, tuple):
                            _, nc_tmax_ref_file_path = result
                        else:
                            _ = result

                    # For computing chill-hours, we need tasmax data. Save tasmax data in a new variable in case we do tasmin as well
                    ds_tasmax_for_chill_hours = ds.copy(deep=True)

                    # Annual Mean Tasmax
                    result_dict = run_metric(
                        "mean_tasmax", compute_metrics.get_mean_tasmax, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Monthly mean tasmax
                    result_dict = run_metric(
                        "monthly_mean_tasmax",
                        compute_metrics.get_monthly_mean_tasmax,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Monthly max tasmax
                    result_dict = run_metric(
                        "monthly_txx", compute_metrics.get_monthly_txx, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # 99.9th Percentile Tasmax
                    result_dict = run_metric(
                        "tasmax_q99p9", compute_metrics.get_tasmax_q99p9, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Median Tasmax
                    result_dict = run_metric(
                        "tasmax_q50", compute_metrics.get_tasmax_q50, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual Max Temperature
                    result_dict = run_metric(
                        "annual_txx", compute_metrics.get_annual_txx, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual-max, 5-day tasmax
                    result_dict = run_metric(
                        "annual_5day_max_tasmax",
                        compute_metrics.get_annual_tasmax_5day,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    for deg in threshold_dict["tasmax_ge"]:
                        args = default_args.copy()
                        args["deg"] = deg
                        result_dict = run_metric(
                            "annual_tasmax_ge",
                            compute_metrics.get_annual_tasmax_ge_XF,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    for deg in threshold_dict["monthly_tasmax_ge"]:
                        args = default_args.copy()
                        args["deg"] = deg
                        result_dict = run_metric(
                            "monthly_tasmax_ge",
                            compute_metrics.get_monthly_tasmax_ge_XF,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    for deg in threshold_dict["tasmax_le"]:
                        args = default_args.copy()
                        args["deg"] = deg
                        result_dict = run_metric(
                            "annual_tasmax_le",
                            compute_metrics.get_annual_tasmax_le_XF,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    # if ("tmax_days")
                    if nc_tmax_ref_file_path is not None:
                        for quantile in threshold_dict["tmax_days_above_q"]:
                            args = default_args.copy()
                            args["file_name_ref_tmax_quant"] = nc_tmax_ref_file_path
                            args["quantile"] = quantile
                            result_dict = run_metric(
                                "tmax_days_above_q",
                                compute_metrics.get_tmax_days_above_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)

                        for quantile in threshold_dict["tmax_days_below_q"]:
                            args = default_args.copy()
                            args["file_name_ref_tmax_quant"] = nc_tmax_ref_file_path
                            args["quantile"] = quantile
                            result_dict = run_metric(
                                "tmax_days_below_q",
                                compute_metrics.get_tmax_days_below_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)
                    else:
                        print(
                            "Skipping tasmax quantile metrics. Make sure ref_q_tasmax is in included_metrics"
                        )
                        pass

                if (varname == "tasmin") and (run == reference_data_set):
                    # if compute_tasmean:
                    #     da_tas = ds[varname].copy(deep=True) / 2
                    #     da_tas.attrs = ds[varname].attrs.copy()
                    args = default_args.copy()
                    args["nc_file"] = nc_base_for_qthresh
                    args["start_year"] = osyear
                    args["end_year"] = oeyear
                    args["quantiles"] = (
                        threshold_dict["tmin_days_above_q"]
                        + threshold_dict["tmin_days_below_q"]
                    )
                    del args["fig_file"]

                    result = run_metric(
                        "ref_q_tasmin", compute_metrics.get_ref_tasmin_Q, **args
                    )
                    if isinstance(result, tuple):
                        result_dict, nc_tmin_ref_file_path = result
                    else:
                        result_dict = result
                # saves a quantile tasmin netCDF file for later use

                if varname == "tasmin":  # and (run != reference_data_set):
                    if compute_tasmean:
                        da_tas += ds[varname].copy(deep=True) / 2
                    if (
                        reference_data_set is None
                    ):  # compute quantile thresholds using model dataset itself
                        args = default_args.copy()
                        args["nc_file"] = nc_base_for_qthresh
                        args["start_year"] = osyear
                        args["end_year"] = oeyear
                        args["quantiles"] = (
                            threshold_dict["tmin_days_above_q"]
                            + threshold_dict["tmin_days_below_q"]
                        )
                        del args["fig_file"]

                        result = run_metric(
                            "ref_q_tasmin", compute_metrics.get_ref_tasmin_Q, **args
                        )
                        if isinstance(result, tuple):
                            result_dict, nc_tmin_ref_file_path = result
                        else:
                            result_dict = result

                    # Annual Minimum Temperature
                    result_dict = run_metric(
                        "annual_tnn", compute_metrics.get_tnn, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual Mean Tasmin
                    result_dict = run_metric(
                        "mean_tasmin", compute_metrics.get_mean_tasmin, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Get monthly mean, tasmin
                    result_dict = run_metric(
                        "monthly_mean_tasmin",
                        compute_metrics.get_monthly_mean_tasmin,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Get monthly min tasmin
                    result_dict = run_metric(
                        "monthly_tnn", compute_metrics.get_monthly_tnn, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Get annual-min, 5-day tasmin
                    result_dict = run_metric(
                        "annual_5day_min_tasmin",
                        compute_metrics.get_annual_min_tasmin_5day,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Get annual-max, 5-day tasmin
                    result_dict = run_metric(
                        "annual_5day_max_tasmin",
                        compute_metrics.get_annual_max_tasmin_5day,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    for deg in threshold_dict["tasmin_le"]:
                        args = default_args.copy()
                        args["deg"] = deg
                        result_dict = run_metric(
                            "annual_tasmin_le",
                            compute_metrics.get_annual_tasmin_le_XF,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    for deg in threshold_dict["monthly_tasmin_le"]:
                        args = default_args.copy()
                        args["deg"] = deg
                        result_dict = run_metric(
                            "monthly_tasmin_le",
                            compute_metrics.get_monthly_tasmin_le_XF,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    for deg in threshold_dict["tasmin_ge"]:
                        args = default_args.copy()
                        args["deg"] = deg
                        result_dict = run_metric(
                            "annual_tasmin_ge",
                            compute_metrics.get_annual_tasmin_ge_XF,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    first_date_dict = {}
                    for deg in threshold_dict["growing_season"]:
                        args = default_args.copy()
                        args["threshold"] = deg
                        result = run_metric(
                            "first_date_below",
                            compute_metrics.get_first_date_belowX,
                            **args,
                        )
                        if isinstance(result, tuple):
                            result_dict, ds_out = result
                            first_date_dict[deg.magnitude] = ds_out
                        else:
                            result_dict = result
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    last_date_dict = {}
                    for deg in threshold_dict["growing_season"]:
                        args = default_args.copy()
                        args["threshold"] = deg
                        result = run_metric(
                            "last_date_below",
                            compute_metrics.get_last_date_belowX,
                            **args,
                        )
                        if isinstance(result, tuple):
                            result_dict, ds_out = result
                            last_date_dict[deg.magnitude] = ds_out

                        else:
                            result_dict = result

                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    if ds_tasmax_for_chill_hours is not None:
                        args = default_args.copy()
                        args["ds_tasmax"] = ds_tasmax_for_chill_hours
                        result_dict = run_metric(
                            "chill_hours", compute_metrics.get_chill_hours, **args
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    if (len(list(first_date_dict.keys())) != 0) and (
                        len(list(last_date_dict.keys())) != 0
                    ):
                        for deg in threshold_dict["growing_season"]:
                            args = default_args.copy()
                            args["ds_first_freeze"] = first_date_dict[deg.magnitude]
                            args["ds_last_freeze"] = last_date_dict[deg.magnitude]
                            args["threshold"] = deg
                            del args["ds"]

                            result_dict = run_metric(
                                "growing_season",
                                compute_metrics.get_growing_season_length,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)

                    if nc_tmin_ref_file_path is not None:
                        for quantile in threshold_dict["tmin_days_above_q"]:
                            args = default_args.copy()
                            args["file_name_ref_tmin_quant"] = nc_tmin_ref_file_path
                            args["quantile"] = quantile
                            result_dict = run_metric(
                                "tmin_days_above_q",
                                compute_metrics.get_tmin_days_above_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)

                        for quantile in threshold_dict["tmin_days_below_q"]:
                            args = default_args.copy()
                            args["file_name_ref_tmin_quant"] = nc_tmin_ref_file_path
                            args["quantile"] = quantile
                            result_dict = run_metric(
                                "tmin_days_below_q",
                                compute_metrics.get_tmin_days_below_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)
                    else:
                        print(
                            "Skipping tasmin quantile metrics. Make sure ref_q_tasmin is in included_metrics"
                        )
                        pass

                if varname == "pr" and run == reference_data_set:
                    args = default_args.copy()
                    args["nc_file"] = nc_base_for_qthresh
                    args["non_zero"] = True

                    args["start_year"] = osyear
                    args["end_year"] = oeyear
                    args["quantiles"] = threshold_dict["pr_ge_quant"]

                    del args["fig_file"]

                    result = run_metric(
                        "ref_pr_Q", compute_metrics.get_ref_pr_Q, **args
                    )
                    if isinstance(result, tuple):
                        result_dict, nc_non_zero_pr_ref_file_path = result
                    else:
                        result_dict = result  # empty dict

                    args["non_zero"] = False
                    result = run_metric(
                        "ref_pr_Q", compute_metrics.get_ref_pr_Q, **args
                    )

                    if isinstance(result, tuple):
                        result_dict, nc_pr_ref_file_path = result
                    else:
                        result_dict = result  # empty dict

                if varname == "pr":  # and (run != reference_data_set):
                    if (
                        reference_data_set is None
                    ):  # compute quantile thresholds using model dataset itself
                        args = default_args.copy()
                        args["nc_file"] = nc_base_for_qthresh
                        args["non_zero"] = True
                        args["start_year"] = osyear
                        args["end_year"] = oeyear
                        args["quantiles"] = threshold_dict["pr_ge_quant"]
                        del args["fig_file"]

                        result = run_metric(
                            "ref_pr_Q", compute_metrics.get_ref_pr_Q, **args
                        )
                        if isinstance(result, tuple):
                            _, nc_non_zero_pr_ref_file_path = result
                        else:
                            _ = result

                        args["non_zero"] = False
                        result = run_metric(
                            "ref_pr_Q", compute_metrics.get_ref_pr_Q, **args
                        )

                        if isinstance(result, tuple):
                            _, nc_pr_ref_file_path = result
                        else:
                            _ = result

                    # Annual/Seasonal  precip
                    result_dict = run_metric(
                        "total_pr", compute_metrics.get_total_pr, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual/Seasonal mean precipitation
                    result_dict = run_metric(
                        "mean_pr", compute_metrics.get_mean_pr, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Monthly mean precipitation
                    result = run_metric(
                        "monthly_pr", compute_metrics.get_monthly_pr, **default_args
                    )

                    if isinstance(result, tuple):
                        result_dict, nc_monthly_pr_path = result
                    else:
                        result_dict = result

                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Max daily precip
                    result_dict = run_metric(
                        "annual_pxx", compute_metrics.get_annual_pxx, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual fraction of days ge X inches. 0-> pr_days a
                    for threshold in threshold_dict["pr_ge"]:
                        args = default_args.copy()
                        args["threshold"] = threshold
                        result_dict = run_metric(
                            "annual_pr_ge", compute_metrics.get_annual_pr_ge_X, **args
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    # TODO: requires 5 years of data
                    # Wettest day in 5 year range

                    if (meyear - msyear) > 5:
                        result_dict = run_metric(
                            "wettest_5yr_total",
                            compute_metrics.get_wettest_5yr,
                            **default_args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Wettest annual N-day period
                    for n in [5, 10, 20, 30]:
                        args = default_args.copy()
                        args["n"] = n
                        result_dict = run_metric(
                            "annual_max_nday_pr",
                            compute_metrics.get_annual_pr_nday,
                            **args,
                        )
                        metrics_dict["RESULTS"][model][run].update(result_dict)

                    # # Consecutive wet days
                    # result_dict = run_metric("annual_cwd", compute_metrics.get_annual_cwd, **default_args)
                    # metrics_dict["RESULTS"][model][run].update(result_dict)

                    # # Consecutive dry days
                    # result_dict = run_metric("annual_cdd", compute_metrics.get_annual_consecDD, **default_args)
                    # metrics_dict["RESULTS"][model][run].update(result_dict)

                    # # Consecutive dry days in JJA
                    # result_dict = run_metric("annual_JJA_cdd", compute_metrics.get_JJA_consecDD, **default_args)
                    # metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Median
                    # This function must come after the consecutive dry days function
                    # Otherwise cdd generates all zeros. Unsure why.

                    result_dict = run_metric(
                        "pr_q50", compute_metrics.get_pr_q50, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # 95 percentile
                    result_dict = run_metric(
                        "pr_q95", compute_metrics.get_pr_q95p0, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # 99.9 percentile
                    result_dict = run_metric(
                        "pr_q99p9", compute_metrics.get_pr_q99p9, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    if nc_pr_ref_file_path != None:
                        for quantile in threshold_dict["pr_ge_quant"]:
                            args = default_args.copy()
                            args["quantile"] = quantile
                            args[
                                "file_name_ref_pr_quant"
                            ] = nc_non_zero_pr_ref_file_path
                            args["non_zero"] = True
                            result_dict = run_metric(
                                "pr_days_above_non_zero_q",
                                compute_metrics.get_pr_days_above_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)

                            args["file_name_ref_pr_quant"] = nc_pr_ref_file_path
                            args["non_zero"] = False
                            result_dict = run_metric(
                                "pr_days_above_q",
                                compute_metrics.get_pr_days_above_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)

                            args["quantile"] = quantile
                            args[
                                "file_name_ref_pr_quant"
                            ] = nc_non_zero_pr_ref_file_path
                            del args["non_zero"]
                            result_dict = run_metric(
                                "pr_sum_above_q",
                                compute_metrics.get_pr_sum_above_Qth,
                                **args,
                            )
                            metrics_dict["RESULTS"][model][run].update(result_dict)
                    else:
                        print(
                            "Skipping precipitation quantile metrics. Make sure ref_q_pr is in included_metrics"
                        )
                        pass

                if varname == "tas":
                    # Mean Average Daily Temperature
                    result_dict = run_metric(
                        "mean_tas", compute_metrics.get_mean_tasmean, **default_args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Monthly Mean Temperature
                    result = run_metric(
                        "monthly_mean_tas",
                        compute_metrics.get_monthly_mean_tas,
                        **default_args,
                    )
                    if isinstance(result, tuple):
                        result_dict, nc_monthly_tas_path = result
                    else:
                        result_dict = result
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual number of cooling degree days
                    result_dict = run_metric(
                        "annual_cooling_deg_days",
                        compute_metrics.get_annual_cooling_degree_days,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual number of heating degree days
                    result_dict = run_metric(
                        "annual_heating_deg_days",
                        compute_metrics.get_annual_heating_degree_days,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual number of growing degree days
                    result_dict = run_metric(
                        "annual_growing_deg_days",
                        compute_metrics.get_annual_growing_degree_days,
                        **default_args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                ## Other Variable with default metric calculations
                if varname not in ["tasmax", "tasmin", "pr", "tas"]:
                    args = default_args.copy()
                    args["varname"] = varname

                    # Annual/Seasonal Mean
                    result_dict = run_metric(
                        f"mean_{varname}", compute_metrics.get_mean_var, **args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual/Seasonal Sum
                    result_dict = run_metric(
                        f"total_{varname}", compute_metrics.get_total_var, **args
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Monthly Mean
                    result_dict = run_metric(
                        f"monthly_mean_{varname}",
                        compute_metrics.get_monthly_mean_var,
                        **args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Monthly Sum
                    result_dict = run_metric(
                        f"monthly_total_{varname}",
                        compute_metrics.get_monthly_total_var,
                        **args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                    # Annual Max
                    result_dict = run_metric(
                        f"annual_max_{varname}",
                        compute_metrics.get_annual_max_var,
                        **args,
                    )
                    metrics_dict["RESULTS"][model][run].update(result_dict)

                if run not in metrics_dict["DIMENSIONS"]["realization"]:
                    metrics_dict["DIMENSIONS"]["realization"].append(run)

        # Output JSON with metrics for single model
        if model != "Reference":
            # Pull out metrics for just this model
            # and write to JSON
            metrics_tmp = metrics_dict.copy()
            metrics_tmp["DIMENSIONS"]["model"] = model
            metrics_tmp["DIMENSIONS"]["realization"] = list_of_runs
            metrics_tmp["RESULTS"] = {model: metrics_dict["RESULTS"][model]}
            metrics_path = "{0}_metrics.json".format(model)
            utilities.write_to_json(metrics_output_path, metrics_path, metrics_tmp)

            meta.update_metrics(
                model,
                os.path.join(metrics_output_path, metrics_path),
                model + " results",
                "Seasonal metrics for single dataset",
            )
            del metrics_tmp

        if ("tas" in variable_list) and (
            "pr" in variable_list
        ):  # and (model != "Reference"):
            if ("monthly_mean_tas" in include_metrics) and (
                "monthly_pr" in include_metrics
            ):
                # Creates a Koppen Map
                compute_metrics.compute_koppen(
                    nc_monthly_tas_path, nc_monthly_pr_path, fig_base
                )

    # Output single file with all models
    model_write_list = model_loop_list.copy()
    if "Reference" in model_write_list:
        model_write_list.remove("Reference")
    metrics_dict["DIMENSIONS"]["model"] = model_write_list
    utilities.write_to_json(
        metrics_output_path, "decision_relevant_metrics.json", metrics_dict
    )
    fname = os.path.join(metrics_output_path, "decision_relevant_metrics.json")
    meta.update_metrics(
        "All",
        fname,
        "All results",
        "Decision relevant climate metrics for all datasets",
    )

    # Update and write metadata file
    try:
        with open(fname, "r") as f:
            tmp = json.load(f)
        meta.update_provenance("environment", tmp["provenance"])
    except Exception:
        # Skip provenance if there's an issue
        print("Error: Could not get provenance from extremes json for output.json.")

    meta.update_provenance("modeldata", test_data_path)
    if reference_data_path is not None:
        meta.update_provenance("obsdata", reference_data_path)
    meta.write()

    # Deleting unused folders at the end #TODO Finish
    # if nc_out:
    #     for s in ["annual", "seasonal", "monthly", "quantile"]:
    #         nc_dir = os.path.join(metrics_output_path, "netcdf")
    #         nc_subdir = os.path.join(nc_dir, s)

    #         for v in variable_list:
    #             var_nc_outdir = os.path.join(nc_subdir, v)
    #             os.makedirs(var_nc_outdir, exist_ok=True)

    # if plots:
    #     for s in ["annual", "seasonal", "monthly", "quantile"]:
    #         fig_dir = os.path.join(metrics_output_path, "plots")
    #         plot_subdir = os.path.join(fig_dir, s)
    #         os.makedirs(plot_subdir, exist_ok=True)

    #         for v in variable_list:  # Make Subdirectories for each variable
    #             var_plot_outdir = os.path.join(plot_subdir, v)
    #             os.makedirs(var_plot_outdir, exist_ok=True)
