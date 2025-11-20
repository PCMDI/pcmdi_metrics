#!/usr/bin/env python
import glob
import json
import logging
import os

import numpy as np
import xarray
import xcdat as xc

from pcmdi_metrics.io import xcdat_open
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.io.xcdat_dataset_io import get_latitude_key, get_longitude_key
from pcmdi_metrics.sea_ice.lib import create_sea_ice_parser
from pcmdi_metrics.sea_ice.lib import sea_ice_figures as fig
from pcmdi_metrics.sea_ice.lib import sea_ice_lib as lib
from pcmdi_metrics.utils import create_land_sea_mask, fix_tuple

if __name__ == "__main__":
    logging.getLogger("xcdat").setLevel(logging.ERROR)

    parser = create_sea_ice_parser()
    parameter = parser.get_parameter(argparse_vals_only=False)

    # Parameters
    # I/O settings
    case_id = parameter.case_id
    realization = parameter.realization
    var = parameter.var
    filename_template = parameter.filename_template
    sft_filename_template = parameter.sft_filename_template
    test_data_path = parameter.test_data_path
    model_list = parameter.test_data_set
    reference_data_path_nh = parameter.reference_data_path_nh
    reference_data_path_sh = parameter.reference_data_path_sh
    reference_data_set = parameter.reference_data_set
    metrics_output_path = parameter.metrics_output_path
    area_template = parameter.area_template
    area_var = parameter.area_var
    AreaUnitsAdjust = parameter.AreaUnitsAdjust
    obs_area_var = parameter.obs_area_var
    obs_var = parameter.obs_var
    obs_area_template_nh = parameter.obs_area_template_nh
    obs_area_template_sh = parameter.obs_area_template_sh
    obs_cell_area = parameter.obs_cell_area
    ObsAreaUnitsAdjust = parameter.ObsAreaUnitsAdjust
    ModUnitsAdjust = parameter.ModUnitsAdjust
    ObsUnitsAdjust = parameter.ObsUnitsAdjust
    msyear = parameter.msyear
    meyear = parameter.meyear
    osyear = parameter.osyear
    oeyear = parameter.oeyear
    plot = parameter.plot
    pole = parameter.pole
    to_nc = parameter.netcdf
    generate_mask = parameter.generate_mask
    no_mask = parameter.no_mask

    print("Model list:", model_list)
    model_list.sort()
    # Verifying output directory
    metrics_output_path = lib.verify_output_path(metrics_output_path, case_id)

    if isinstance(reference_data_set, list):
        # Fix a command line issue
        reference_data_set = reference_data_set[0]

    # Verify years
    ok_mod = lib.verify_years(
        msyear,
        meyear,
        msg="Error: Model msyear and meyear must both be set or both be None (unset).",
    )
    ok_obs = lib.verify_years(
        osyear,
        oeyear,
        msg="Error: Obs osyear and oeyear must both be set or both be None (unset).",
    )

    # Fix issues that can come from command line tuples
    ModUnitsAdjust = fix_tuple(ModUnitsAdjust)
    AreaUnitsAdjust = fix_tuple(AreaUnitsAdjust)
    ObsUnitsAdjust = fix_tuple(ObsUnitsAdjust)
    ObsAreaUnitsAdjust = fix_tuple(ObsAreaUnitsAdjust)

    # Initialize output.json file
    meta = lib.MetadataFile(metrics_output_path)

    # Setting up model realization list
    find_all_realizations, realizations = lib.set_up_realizations(realization)
    print("Find all realizations:", find_all_realizations)

    # --------------------------
    # Process observations first
    # --------------------------
    # This section is hard-coded to work with the
    # OSI-SAF data in obs4mips.

    # ~~~~~~
    # Arctic
    # ~~~~~~
    print("OBS: Arctic")

    arctic_clims = {}
    arctic_means = {}

    nh_files = glob.glob(reference_data_path_nh)
    obs = xcdat_open(nh_files, chunks=None)  # obs is an xarray dataset
    xvar = lib.find_lon(obs)
    yvar = lib.find_lat(obs)
    coord_i, coord_j = lib.get_xy_coords(obs, xvar)
    if osyear is not None:
        obs = obs.sel(
            time=slice(f"{osyear}-01-01", f"{oeyear}-12-31")
        )  # .compute() is not always needed; remove for lazy evaluation
    obs[obs_var] = lib.adjust_units(obs[obs_var], ObsUnitsAdjust)
    if obs_area_var is not None:
        obs[obs_area_var] = lib.adjust_units(obs[obs_area_var], ObsAreaUnitsAdjust)
        area_val = obs[obs_area_var]
    else:
        area_val = obs_cell_area
    # Remove land areas (including lakes)
    mask = create_land_sea_mask(obs, lon_key=xvar, lat_key=yvar)
    obs[obs_var] = obs[obs_var].where(mask < 1)
    # Get regions
    clims, means = lib.process_by_region(obs, obs_var, area_val, pole)
    nh_obs_area = lib.get_ocean_area_for_regions(obs, obs_var, area_val, pole)
    print("nh_obs_area:", nh_obs_area)
    arctic_clims = {
        "arctic": clims["arctic"],
        "ca": clims["ca"],
        "np": clims["np"],
        "na": clims["na"],
    }

    arctic_means = {
        "arctic": means["arctic"],
        "ca": means["ca"],
        "np": means["np"],
        "na": means["na"],
    }

    # Get climatology
    print("Start get clim")
    nc_climo = lib.get_clim(obs, obs_var, ds=None)
    print("End get clim")

    # Generate netcdf files of climatologies
    nc_dir = os.path.join(metrics_output_path, "netcdf")
    os.makedirs(nc_dir, exist_ok=True)
    print("Writing climatology netcdf")
    fname_nh = f"sic_clim_{reference_data_set}_nh_{osyear}_{oeyear}.nc"
    fname_nh = os.path.join(nc_dir, fname_nh)
    nc_climo.to_netcdf(fname_nh, "w")
    del nc_climo
    obs.close()

    # ~~~~~~~~~
    # Antarctic
    # ~~~~~~~~~
    print("OBS: Antarctic")
    antarctic_clims = {}
    antarctic_means = {}
    sh_files = glob.glob(reference_data_path_sh)
    obs = xcdat_open(sh_files)
    xvar = lib.find_lon(obs)
    yvar = lib.find_lat(obs)
    coord_i, coord_j = lib.get_xy_coords(obs, xvar)
    if osyear is not None:
        obs = obs.sel(
            time=slice(f"{osyear}-01-01", f"{oeyear}-12-31")
        )  # .compute() is not always needed; remove for lazy evaluation
    obs[obs_var] = lib.adjust_units(obs[obs_var], ObsUnitsAdjust)
    if obs_area_var is not None:
        obs[obs_area_var] = lib.adjust_units(obs[obs_area_var], ObsAreaUnitsAdjust)
        area_val = obs[obs_area_var]
    else:
        area_val = obs_cell_area
    # Remove land areas (including lakes)
    mask = create_land_sea_mask(obs, lon_key="lon", lat_key="lat")
    obs[obs_var] = obs[obs_var].where(mask < 1)
    clims, means = lib.process_by_region(obs, obs_var, area_val, pole)
    sh_obs_area = lib.get_ocean_area_for_regions(obs, obs_var, area_val, pole)
    print(sh_obs_area)
    antarctic_clims = {
        "antarctic": clims["antarctic"],
        "io": clims["io"],
        "sp": clims["sp"],
        "sa": clims["sa"],
    }

    antarctic_means = {
        "antarctic": means["antarctic"],
        "io": means["io"],
        "sp": means["sp"],
        "sa": means["sa"],
    }

    # Get climatology
    nc_climo = lib.get_clim(obs, obs_var, ds=None)

    # Generate netcdf files of climatologies
    nc_dir = os.path.join(metrics_output_path, "netcdf")
    os.makedirs(nc_dir, exist_ok=True)
    print("Writing climatology netcdf")
    fname_sh = f"sic_clim_{reference_data_set}_sh_{osyear}_{oeyear}.nc"
    fname_sh = os.path.join(nc_dir, fname_sh)
    nc_climo.to_netcdf(fname_sh, "w")
    del nc_climo
    obs.close()

    obs_clims = {reference_data_set: {}}
    obs_means = {reference_data_set: {}}
    for item in antarctic_clims:
        obs_clims[reference_data_set][item] = antarctic_clims[item]
        obs_means[reference_data_set][item] = antarctic_means[item]
    for item in arctic_clims:
        obs_clims[reference_data_set][item] = arctic_clims[item]
        obs_means[reference_data_set][item] = arctic_means[item]

    # -----------------------------
    # Model (or non-reference) data
    # -----------------------------

    # Needs to weigh months by length for metrics later
    clim_wts = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    clim_wts = [x / 365 for x in clim_wts]
    # Initialize JSON data
    mse = {}
    mse_wgt = {}
    df = {
        "Reference": {
            "arctic": {reference_data_set: {}},
            "ca": {reference_data_set: {}},
            "na": {reference_data_set: {}},
            "np": {reference_data_set: {}},
            "antarctic": {reference_data_set: {}},
            "sp": {reference_data_set: {}},
            "sa": {reference_data_set: {}},
            "io": {reference_data_set: {}},
        }
    }
    metrics = {
        "DIMENSIONS": {
            "json_structure": [
                "region",
                "realization",
                "obs",
                "index",
                "statistic",
            ],
            "region": ["arctic", "ca", "na", "np", "antarctic", "io", "sa", "sp"],
            "index": {
                "monthly_clim": "Monthly climatology of extent",
                "total_extent": "Sum of ice coverage where concentration > 15%",
            },
            "statistic": {"mse": "Mean Square Error (10^12 km^4)"},
            "model": model_list,
        },
        "RESULTS": {},
        "model_year_range": {},
    }
    data_file = {
        "DIMENSIONS": {
            "json_structure": ["region", "realization", "data"],
        },
        "RESULTS": {},
    }
    print("Model list:", model_list)

    # Loop over models and realizations to generate metrics
    for model in model_list:
        start_year = msyear
        end_year = meyear

        real_clim = {
            "arctic": {"model_mean": {}},
            "ca": {"model_mean": {}},
            "na": {"model_mean": {}},
            "np": {"model_mean": {}},
            "antarctic": {"model_mean": {}},
            "sp": {"model_mean": {}},
            "sa": {"model_mean": {}},
            "io": {"model_mean": {}},
        }
        real_mean = {
            "arctic": {"model_mean": 0},
            "ca": {"model_mean": 0},
            "na": {"model_mean": 0},
            "np": {"model_mean": 0},
            "antarctic": {"model_mean": 0},
            "sp": {"model_mean": 0},
            "sa": {"model_mean": 0},
            "io": {"model_mean": 0},
        }
        mse[model] = {
            "arctic": {"model_mean": {reference_data_set: {}}},
            "ca": {"model_mean": {reference_data_set: {}}},
            "na": {"model_mean": {reference_data_set: {}}},
            "np": {"model_mean": {reference_data_set: {}}},
            "antarctic": {"model_mean": {reference_data_set: {}}},
            "sp": {"model_mean": {reference_data_set: {}}},
            "sa": {"model_mean": {reference_data_set: {}}},
            "io": {"model_mean": {reference_data_set: {}}},
        }
        df[model] = {
            "arctic": {},
            "ca": {},
            "na": {},
            "np": {},
            "antarctic": {},
            "sp": {},
            "sa": {},
            "io": {},
        }

        tags = {
            "%(variable)": var,
            "%(model)": model,
            "%(model_version)": model,
            "%(realization)": "*",
        }
        if find_all_realizations:
            print("finding all realizations")
            test_data_full_path_tmp = os.path.join(test_data_path, filename_template)
            test_data_full_path_tmp = lib.replace_multi(test_data_full_path_tmp, tags)
            ncfiles = glob.glob(test_data_full_path_tmp)
            realizations = []
            for ncfile in ncfiles:
                basename = ncfile.split("/")[-1]
                if len(basename.split(".")) <= 2:
                    if basename.split("_")[4] not in realizations:
                        realizations.append(basename.split("_")[4])
                else:
                    if basename.split(".")[3] not in realizations:
                        realizations.append(basename.split(".")[3])

            print("\n=================================")
            print("model, runs:", model, realizations)
            list_of_runs = realizations
        else:
            list_of_runs = realizations
        print(list_of_runs)

        # Model grid area
        print(lib.replace_multi(area_template, tags))
        area = xcdat_open(glob.glob(lib.replace_multi(area_template, tags))[0])
        area[area_var] = lib.adjust_units(area[area_var], AreaUnitsAdjust)

        if len(list_of_runs) > 0:
            # Loop over realizations
            for run_ind, run in enumerate(list_of_runs):
                # Find model data, determine number of files, check if they exist
                tags = {
                    "%(variable)": var,
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
                }
                test_data_tmp = lib.replace_multi(test_data_path, tags)
                if "*" in test_data_tmp:
                    # Get the most recent version for last wildcard
                    ind = test_data_tmp.split("/")[::-1].index("*")
                    tmp1 = "/".join(test_data_tmp.split("/")[0:-ind])
                    globbed = glob.glob(tmp1)
                    globbed.sort()
                    test_data_tmp = globbed[-1]
                test_data_full_path = os.path.join(test_data_tmp, filename_template)
                test_data_full_path = lib.replace_multi(test_data_full_path, tags)
                test_data_full_path = glob.glob(test_data_full_path)
                test_data_full_path.sort()
                if len(test_data_full_path) == 0:
                    print("")
                    print("-----------------------")
                    print("Not found: model, run, variable:", model, run, var)
                    break
                else:
                    print("")
                    print("-----------------------")
                    print("model, run, variable:", model, run, var)
                    print("test_data (model in this case) full_path:")
                    for t in test_data_full_path:
                        print("  ", t)

                # Load and prep data
                ds = xcdat_open(test_data_full_path)
                ds[var] = lib.adjust_units(ds[var], ModUnitsAdjust)
                xvar = lib.find_lon(ds)
                yvar = lib.find_lat(ds)
                if xvar is None or yvar is None:
                    print("Could not get latitude or longitude variables")
                    break
                if (ds[xvar] < -180).any():
                    ds[xvar] = ds[xvar].where(ds[xvar] >= -180, ds[xvar] + 360)

                if ds.time.encoding["calendar"] == "360_day":
                    day360 = True
                else:
                    day360 = False

                # Get time slice if year parameters exist
                if start_year is not None:
                    if day360:
                        final_day = 30
                    else:
                        final_day = 31
                    ds = ds.sel(
                        time=slice(
                            f"{start_year}-01-01",
                            f"{end_year}-12-{final_day}",
                        )
                    )
                    yr_range = [str(start_year), str(end_year)]
                else:
                    # Get labels for start/end years from dataset
                    yr_range = [
                        str(int(ds.time.dt.year[0])),
                        str(int(ds.time.dt.year[-1])),
                    ]

                # Update year list info in metrics JSON structure
                metrics["model_year_range"][model] = yr_range

                # Land/sea mask
                try:
                    tags = {
                        "%(model)": model,
                        "%(model_version)": model,
                        "%(realization)": run,
                    }
                    sft_filename_list = lib.replace_multi(sft_filename_template, tags)
                    sft_filename = glob.glob(sft_filename_list)[0]
                    sft_exists = True
                except (AttributeError, IndexError):
                    print("No land/sea mask file found for", model, run)
                    # Set flag to generate sftlf after loading data
                    sft_exists = False

                if ~sft_exists and no_mask:
                    # Make mask with all zeros, effectively no masking.
                    print("--no_mask is True. No land/sea mask applied.")
                    mask = xarray.zeros_like(ds[var].isel({"time": 0}))
                elif sft_exists:
                    sft = xcdat_open(sft_filename)
                    # SFTOF and siconc don't always have same coordinate
                    # names in CMIP data
                    ds_lat = get_latitude_key(ds)
                    ds_lon = get_longitude_key(ds)
                    sft_lat = get_latitude_key(sft)
                    sft_lon = get_longitude_key(sft)
                    sft = sft.rename({sft_lon: ds_lon, sft_lat: ds_lat})
                    if "sftlf" in sft.keys():
                        mask = sft["sftlf"]
                    elif "sftof" in sft.keys():
                        # SFTOF uses 100 for ocean, 0 for land
                        mask = xarray.where(
                            sft["sftof"] > 0, 1 - sft["sftof"] / 100.0, 1
                        )
                    else:
                        print(
                            "Invalid land/sea mask. Land/sea mask must contain variable 'sftlf' or 'sftof'"
                        )
                        continue
                    if np.max(mask) > 50:
                        mask = mask / 100
                else:
                    print("Creating land/sea mask.")
                    mask = create_land_sea_mask(ds, lon_key=xvar, lat_key=yvar)
                ds[var] = ds[var].where(mask < 1)
                # Option to weigh sea ice coverage by fraction of cell that is ocean.
                # area[area_var] = area[area_var] * (1 - mask)

                # Generate netcdf files of climatologies
                nc_dir = os.path.join(metrics_output_path, "netcdf")
                if not os.path.exists(nc_dir):
                    os.mkdir(nc_dir)
                nc_climo = lib.get_clim(ds, var, ds=None)
                fname = f"sic_clim_{model}_{run}_{yr_range[0]}_{yr_range[1]}.nc"
                fname = os.path.join(nc_dir, fname)
                print("Writing climatology netcdf", fname)
                nc_climo.to_netcdf(fname, "w")
                del nc_climo

                # Get regions
                print("Getting regional areas for run")
                clims, means = lib.process_by_region(ds, var, area[area_var].data, pole)

                ds.close()
                # Running sum of all realizations
                for rgn in clims:
                    real_clim[rgn][run] = clims[rgn]
                    real_mean[rgn][run] = means[rgn]

            # --------------------
            # Get regional metrics
            # --------------------
            print("\n-------------------------------------------")
            print("Calculating model regional average metrics \nfor ", model)
            print("--------------------------------------------")

            for rgn in real_clim:
                print(rgn)
                # Get model mean for real_clim
                datalist = [real_clim[rgn][r][var].data for r in list_of_runs]
                real_clim[rgn]["model_mean"][var] = np.nanmean(
                    np.array(datalist), axis=0
                )
                print("datalist clims:", datalist)
                print(
                    "real_clim[rgn]['model_mean'][var]:",
                    real_clim[rgn]["model_mean"][var],
                )

                # Get model mean for real_mean
                datalist = [real_mean[rgn][r] for r in list_of_runs]
                real_mean[rgn]["model_mean"] = np.nanmean(np.array(datalist))
                print("datalist means:", datalist)
                print("real_mean[rgn]['model_mean']:", real_mean[rgn]["model_mean"])

                for run in real_clim[rgn]:
                    # Set up metrics dictionary
                    if run not in mse[model][rgn]:
                        mse[model][rgn][run] = {}
                    if run not in df[model][rgn]:
                        df[model][rgn][run] = {}
                    mse[model][rgn][run].update(
                        {
                            reference_data_set: {
                                "monthly_clim": {"mse": None},
                                "total_extent": {"mse": None},
                            }
                        }
                    )

                    # Organize the clims and mean for writing to file
                    df[model][rgn][run].update(
                        {
                            "monthly_climatology": [],
                            "time_mean_extent": real_mean[rgn][run] * 1e-6,
                        }
                    )
                    if isinstance(
                        real_clim[rgn][run][var], xarray.core.dataarray.DataArray
                    ):
                        df_list = list(real_clim[rgn][run][var].compute().data)
                    else:
                        df_list = list(real_clim[rgn][run][var].data)
                    df[model][rgn][run]["monthly_climatology"] = [
                        x * 1e-6 for x in df_list
                    ]

                    # Get errors, convert to 1e12 km^-4
                    if day360:
                        weights = None
                    else:
                        weights = clim_wts
                    mse[model][rgn][run][reference_data_set]["monthly_clim"]["mse"] = (
                        lib.mse_t(
                            real_clim[rgn][run][var] - real_mean[rgn][run],
                            obs_clims[reference_data_set][rgn][obs_var]
                            - obs_means[reference_data_set][rgn],
                            weights=weights,
                        )
                        * 1e-12
                    )
                    mse[model][rgn][run][reference_data_set]["total_extent"]["mse"] = (
                        lib.mse_model(
                            real_mean[rgn][run], obs_means[reference_data_set][rgn]
                        )
                        * 1e-12
                    )
            # --------------------------
            # Get sector weighted metric
            # --------------------------
            run_list = [x for x in real_clim["arctic"]]
            if "model_mean" in run_list:
                run_list.remove("model_mean")
            wgted_nh_te = 0
            wgted_nh_clim = 0
            wgted_sh_te = 0
            wgted_sh_clim = 0
            n_nh = len(run_list)
            n_sh = len(run_list)
            print("run_list:", run_list)
            print("before loop: n_nh:", n_nh, "n_sh:", n_sh)
            for r in run_list:
                # Skip run if regions are missing
                if ~np.isnan(
                    mse[model]["arctic"][r][reference_data_set]["total_extent"]["mse"]
                ):
                    for rgn in ["ca", "na", "np"]:
                        # Take the mse for the region and weigh by relative area of sector
                        wgted_nh_te += (
                            mse[model][rgn][r][reference_data_set]["total_extent"][
                                "mse"
                            ]
                            * nh_obs_area[rgn]
                            / nh_obs_area["arctic"]
                        )
                        wgted_nh_clim += (
                            mse[model][rgn][r][reference_data_set]["monthly_clim"][
                                "mse"
                            ]
                            * nh_obs_area[rgn]
                            / nh_obs_area["arctic"]
                        )
                else:
                    n_nh -= 1

                if ~np.isnan(
                    mse[model]["antarctic"][r][reference_data_set]["total_extent"][
                        "mse"
                    ]
                ):
                    for rgn in ["sa", "io", "sp"]:
                        wgted_sh_te += (
                            mse[model][rgn][r][reference_data_set]["total_extent"][
                                "mse"
                            ]
                            * sh_obs_area[rgn]
                            / sh_obs_area["antarctic"]
                        )
                        wgted_sh_clim += (
                            mse[model][rgn][r][reference_data_set]["monthly_clim"][
                                "mse"
                            ]
                            * sh_obs_area[rgn]
                            / sh_obs_area["antarctic"]
                        )
                else:
                    n_sh -= 1

                # Error values for single realization
                mse[model]["arctic"][r][reference_data_set]["total_extent"][
                    "sector_mse"
                ] = wgted_nh_te
                mse[model]["arctic"][r][reference_data_set]["monthly_clim"][
                    "sector_mse"
                ] = wgted_nh_clim
                mse[model]["antarctic"][r][reference_data_set]["total_extent"][
                    "sector_mse"
                ] = wgted_sh_te
                mse[model]["antarctic"][r][reference_data_set]["monthly_clim"][
                    "sector_mse"
                ] = wgted_sh_clim

            print("after loop: n_nh:", n_nh, "n_sh:", n_sh)

            # Error values averaged over all realizations
            mse[model]["arctic"]["model_mean"][reference_data_set]["total_extent"][
                "sector_mse"
            ] = (wgted_nh_te / n_nh)
            mse[model]["arctic"]["model_mean"][reference_data_set]["monthly_clim"][
                "sector_mse"
            ] = (wgted_nh_clim / n_nh)
            mse[model]["antarctic"]["model_mean"][reference_data_set]["total_extent"][
                "sector_mse"
            ] = (wgted_sh_te / n_sh)
            mse[model]["antarctic"]["model_mean"][reference_data_set]["monthly_clim"][
                "sector_mse"
            ] = (wgted_sh_clim / n_sh)

        else:
            for rgn in mse[model]:
                # Set up metrics dictionary
                mse[model][rgn]["model_mean"][reference_data_set] = {
                    "monthly_clim": {"mse": None},
                    "total_extent": {"mse": None},
                }
                metrics["model_year_range"][model] = ["", ""]

    # -------------------
    # Update metrics JSON
    # -------------------
    metrics["RESULTS"] = mse

    metricsfile = os.path.join(metrics_output_path, "sea_ice_metrics.json")
    JSON = Base(metrics_output_path, "sea_ice_metrics.json")
    json_structure = metrics["DIMENSIONS"]["json_structure"]
    JSON.write(
        metrics,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    meta.update_metrics(
        "metrics",
        metricsfile,
        "metrics_JSON",
        "JSON file containing regional sea ice metrics",
    )

    # ----------------------
    # Update supporting data
    # ----------------------
    # Write obs data to dict
    for rgn in df["Reference"]:
        df["Reference"][rgn][reference_data_set].update(
            {
                "monthly_climatology": [],
                "time_mean_extent": obs_means[reference_data_set][rgn] * 1e-6,
            }
        )
        if isinstance(
            obs_clims[reference_data_set][rgn][obs_var], xarray.core.dataarray.DataArray
        ):
            df_list = list(obs_clims[reference_data_set][rgn][obs_var].compute().data)
        else:
            df_list = list(obs_clims[reference_data_set][rgn][obs_var].data)
        df["Reference"][rgn][reference_data_set]["monthly_climatology"] = [
            x * 1e-6 for x in df_list
        ]

    # Write data to file
    data_file["RESULTS"] = df
    datafile = os.path.join(metrics_output_path, "sea_ice_data.json")
    JSONDF = Base(metrics_output_path, "sea_ice_data.json")
    json_structure = data_file["DIMENSIONS"]["json_structure"]
    JSONDF.write(
        data_file,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    meta.update_data(
        "supporting_data",
        datafile,
        "supporting_data",
        "JSON file containig regional sea ice data",
    )

    # ------------
    # Make figures
    # ------------
    if plot:
        fig_dir = os.path.join(metrics_output_path, "plot")
        os.makedirs(fig_dir, exist_ok=True)

        # Make metrics bar chart for all models
        print("Creating metrics bar chart.")
        meta = fig.metrics_bar_chart(
            model_list, metrics, reference_data_set, fig_dir, meta
        )

        # Make annual cycle line plots for all models
        print("Creating annual cycle figures.")
        meta = fig.annual_cycle_plots(df, fig_dir, reference_data_set, meta)

        # Make maps
        print("Creating maps.")
        if os.path.exists(fname_nh) and os.path.exists(fname_sh):
            obs_nh = xc.open_dataset(fname_nh)
            obs_sh = xc.open_dataset(fname_sh)
        else:
            obs_nh = None
            obs_sh = None
        nc_dir = os.path.join(metrics_output_path, "netcdf/*")
        count = 0
        for file in glob.glob(nc_dir):
            model = os.path.basename(file).split("_")[2]
            run = os.path.basename(file).split("_")[3]
            nc_climo = xc.open_dataset(file)
            if model == reference_data_set:
                continue
            try:
                tmp_model = "_".join([model, run])
                tmp_title = f"{yr_range[0]}-{yr_range[1]} Arctic sea ice"
                meta = fig.create_arctic_map(
                    nc_climo,
                    obs_nh,
                    var,
                    obs_var,
                    fig_dir,
                    meta,
                    tmp_model,
                    tmp_title,
                )
                meta = fig.create_summary_maps_arctic(
                    nc_climo, var, fig_dir, meta, tmp_model
                )
                meta = fig.create_annual_mean_map_arctic(
                    nc_climo, var, fig_dir, meta, tmp_model
                )
                tmp_title = f"{yr_range[0]}-{yr_range[1]} Antarctic sea ice"
                meta = fig.create_antarctic_map(
                    nc_climo,
                    obs_sh,
                    var,
                    obs_var,
                    fig_dir,
                    meta,
                    tmp_model,
                    tmp_title,
                )
                meta = fig.create_summary_maps_antarctic(
                    nc_climo, var, fig_dir, meta, tmp_model
                )
                meta = fig.create_annual_mean_map_antarctic(
                    nc_climo, var, fig_dir, meta, tmp_model
                )
            except Exception as e:
                print("Error making figures for model", model, "realization", run)
                print("  ", e)

        # Model Mean maps
        for model in model_list:
            count = 0
            nc_dir = os.path.join(metrics_output_path, "netcdf/*" + model + "_*")
            for file in glob.glob(nc_dir):
                nc_climo = xc.open_dataset(file)
                if count == 0:
                    nc_climo_mean = nc_climo.copy(deep=True)
                else:
                    nc_climo_mean[var] = nc_climo_mean[var] + nc_climo[var]
            nc_climo_mean[var] = nc_climo_mean[var] / (count + 1)
            tmp_model = "_".join([model, "model_mean"])
            tmp_title = f"{yr_range[0]}-{yr_range[1]} Arctic sea ice"
            meta = fig.create_arctic_map(
                nc_climo_mean, obs_nh, var, obs_var, fig_dir, meta, tmp_model, tmp_title
            )
            tmp_title = f"{yr_range[0]}-{yr_range[1]} Antarctic sea ice"
            meta = fig.create_antarctic_map(
                nc_climo_mean, obs_sh, var, obs_var, fig_dir, meta, tmp_model, tmp_title
            )

            meta = fig.create_summary_maps_arctic(
                nc_climo_mean, var, fig_dir, meta, tmp_model
            )
            meta = fig.create_summary_maps_antarctic(
                nc_climo_mean, var, fig_dir, meta, tmp_model
            )

            meta = fig.create_annual_mean_map_arctic(
                nc_climo_mean, var, fig_dir, meta, tmp_model
            )
            meta = fig.create_annual_mean_map_antarctic(
                nc_climo_mean, var, fig_dir, meta, tmp_model
            )

    # --------------------------------
    # Delete netcdf files if unwanted
    # --------------------------------
    if not to_nc:
        print("Cleaning up.")
        print("Deleting netcdf files.")
        nc_dir = os.path.join(metrics_output_path, "netcdf/*")
        for file in glob.glob(nc_dir):
            os.remove(file)
        try:
            os.rmdir(os.path.join(metrics_output_path, "netcdf"))
        except OSError as e:
            print(
                "Could not delete netcdf directory ",
                os.path.join(metrics_output_path, "netcdf"),
            )
            print(e)

    # -----------------
    # Update and write
    # metadata file
    # -----------------
    try:
        with open(os.path.join(metricsfile), "r") as f:
            tmp = json.load(f)
        meta.update_provenance("environment", tmp["provenance"])
    except Exception:
        # Skip provenance if there's an issue
        print("Error: Could not get provenance from metrics json for output.json.")

    print("Writing metadata file.")
    meta.update_provenance("modeldata", test_data_path)
    if reference_data_path_nh is not None:
        meta.update_provenance("obsdata_nh", reference_data_path_nh)
        meta.update_provenance("obsdata_sh", reference_data_path_sh)
    meta.write()
