#!/usr/bin/env python
import glob
import json
import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import xarray
import xcdat as xc

from pcmdi_metrics.io.base import Base
from pcmdi_metrics.sea_ice.lib import create_sea_ice_parser
from pcmdi_metrics.sea_ice.lib import sea_ice_lib as lib
from pcmdi_metrics.utils import create_land_sea_mask

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

    # Initialize output.json file
    meta = lib.MetadataFile(metrics_output_path)

    # Setting up model realization list
    find_all_realizations, realizations = lib.set_up_realizations(realization)
    print("Find all realizations:", find_all_realizations)

    #### Do Obs part
    arctic_clims = {}
    arctic_means = {}

    print("OBS: Arctic")
    nh_files = glob.glob(reference_data_path_nh)
    obs = lib.load_dataset(nh_files)
    xvar = lib.find_lon(obs)
    yvar = lib.find_lat(obs)
    coord_i, coord_j = lib.get_xy_coords(obs, xvar)
    if osyear is not None:
        obs = obs.sel(
            {
                "time": slice(
                    "{0}-01-01".format(osyear),
                    "{0}-12-31".format(oeyear),
                )
            }
        ).compute()  # TODO: won't always need to compute
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
    obs.close()

    antarctic_clims = {}
    antarctic_means = {}
    print("OBS: Antarctic")
    sh_files = glob.glob(reference_data_path_sh)
    obs = lib.load_dataset(sh_files)
    xvar = lib.find_lon(obs)
    yvar = lib.find_lat(obs)
    coord_i, coord_j = lib.get_xy_coords(obs, xvar)
    if osyear is not None:
        obs = obs.sel(
            {
                "time": slice(
                    "{0}-01-01".format(osyear),
                    "{0}-12-31".format(oeyear),
                )
            }
        ).compute()
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
    obs.close()

    obs_clims = {reference_data_set: {}}
    obs_means = {reference_data_set: {}}
    for item in antarctic_clims:
        obs_clims[reference_data_set][item] = antarctic_clims[item]
        obs_means[reference_data_set][item] = antarctic_means[item]
    for item in arctic_clims:
        obs_clims[reference_data_set][item] = arctic_clims[item]
        obs_means[reference_data_set][item] = arctic_means[item]

    #### Do model part

    # Needs to weigh months by length for metrics later
    clim_wts = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    clim_wts = [x / 365 for x in clim_wts]
    # Initialize JSON data
    mse = {}
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

        # Model grid area
        print(lib.replace_multi(area_template, tags))
        area = xc.open_dataset(glob.glob(lib.replace_multi(area_template, tags))[0])
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
                test_data_full_path = os.path.join(test_data_path, filename_template)
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
                ds = lib.load_dataset(test_data_full_path)
                ds[var] = lib.adjust_units(ds[var], ModUnitsAdjust)
                xvar = lib.find_lon(ds)
                yvar = lib.find_lat(ds)
                if xvar is None or yvar is None:
                    print("Could not get latitude or longitude variables")
                    break
                if (ds[xvar] < -180).any():
                    ds[xvar] = ds[xvar].where(ds[xvar] >= -180, ds[xvar] + 360)

                # Get time slice if year parameters exist
                if start_year is not None:
                    ds = ds.sel(
                        {
                            "time": slice(
                                "{0}-01-01".format(start_year),
                                "{0}-12-31".format(end_year),
                            )
                        }
                    )
                    yr_range = [str(start_year), str(end_year)]
                else:
                    # Get labels for start/end years from dataset
                    yr_range = [
                        str(int(ds.time.dt.year[0])),
                        str(int(ds.time.dt.year[-1])),
                    ]

                mask = create_land_sea_mask(ds, lon_key=xvar, lat_key=yvar)
                ds[var] = ds[var].where(mask < 1)

                # Get regions
                clims, means = lib.process_by_region(ds, var, area[area_var].data, pole)

                ds.close()
                # Running sum of all realizations
                for rgn in clims:
                    real_clim[rgn][run] = clims[rgn]
                    real_mean[rgn][run] = means[rgn]

            print("\n-------------------------------------------")
            print("Calculating model regional average metrics \nfor ", model)
            print("--------------------------------------------")
            for rgn in real_clim:
                print(rgn)
                # Get model mean
                datalist = [real_clim[rgn][r][var].data for r in list_of_runs]
                real_clim[rgn]["model_mean"][var] = np.nanmean(
                    np.array(datalist), axis=0
                )
                datalist = [real_mean[rgn][r] for r in list_of_runs]
                real_mean[rgn]["model_mean"] = np.nanmean(np.array(datalist))

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
                            "time_mean_extent": str(real_mean[rgn][run] * 1e-6),
                        }
                    )
                    if isinstance(
                        real_clim[rgn][run][var], xarray.core.dataarray.DataArray
                    ):
                        df_list = list(real_clim[rgn][run][var].compute().data)
                    else:
                        df_list = list(real_clim[rgn][run][var].data)
                    df[model][rgn][run]["monthly_climatology"] = [
                        str(x * 1e-6) for x in df_list
                    ]

                    # Get errors, convert to 1e12 km^-4
                    mse[model][rgn][run][reference_data_set]["monthly_clim"][
                        "mse"
                    ] = str(
                        lib.mse_t(
                            real_clim[rgn][run][var] - real_mean[rgn][run],
                            obs_clims[reference_data_set][rgn][obs_var]
                            - obs_means[reference_data_set][rgn],
                            weights=clim_wts,
                        )
                        * 1e-12
                    )

                    mse[model][rgn][run][reference_data_set]["total_extent"][
                        "mse"
                    ] = str(
                        lib.mse_model(
                            real_mean[rgn][run], obs_means[reference_data_set][rgn]
                        )
                        * 1e-12
                    )

            # Update year list
            metrics["model_year_range"][model] = [str(start_year), str(end_year)]
        else:
            for rgn in mse[model]:
                # Set up metrics dictionary
                mse[model][rgn]["model_mean"][reference_data_set] = {
                    "monthly_clim": {"mse": None},
                    "total_extent": {"mse": None},
                }
                metrics["model_year_range"][model] = ["", ""]

    # -----------------
    # Update metrics
    # -----------------
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
        "JSON file containig regional sea ice metrics",
    )

    # -----------------
    # Update supporting data
    # -----------------
    # Write obs data to dict
    for rgn in df["Reference"]:
        df["Reference"][rgn][reference_data_set].update(
            {
                "monthly_climatology": [],
                "time_mean_extent": str(obs_means[reference_data_set][rgn] * 1e-6),
            }
        )
        if isinstance(
            obs_clims[reference_data_set][rgn][obs_var], xarray.core.dataarray.DataArray
        ):
            df_list = list(obs_clims[reference_data_set][rgn][obs_var].compute().data)
        else:
            df_list = list(obs_clims[reference_data_set][rgn][obs_var].data)
        df["Reference"][rgn][reference_data_set]["monthly_climatology"] = [
            str(x * 1e-6) for x in df_list
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

    # ----------------
    # Make figure
    # ----------------
    if plot:
        sector_list = [
            "Central Arctic Sector",
            "North Atlantic Sector",
            "North Pacific Sector",
            "Indian Ocean Sector",
            "South Atlantic Sector",
            "South Pacific Sector",
        ]
        sector_short = ["ca", "na", "np", "io", "sa", "sp"]
        fig7, ax7 = plt.subplots(6, 1, figsize=(5, 9))
        mlabels = model_list
        ind = np.arange(len(mlabels))  # the x locations for the groups
        width = 0.3
        n = len(ind)
        for inds, sector in enumerate(sector_list):
            # Assemble data
            mse_clim = []
            mse_ext = []
            clim_range = []
            ext_range = []
            clim_err_x = []
            clim_err_y = []
            ext_err_y = []
            rgn = sector_short[inds]
            for nmod, model in enumerate(model_list):
                mse_clim.append(
                    float(
                        metrics["RESULTS"][model][rgn]["model_mean"][
                            reference_data_set
                        ]["monthly_clim"]["mse"]
                    )
                )
                mse_ext.append(
                    float(
                        metrics["RESULTS"][model][rgn]["model_mean"][
                            reference_data_set
                        ]["total_extent"]["mse"]
                    )
                )
                # Get spread, only if there are multiple realizations
                if len(metrics["RESULTS"][model][rgn].keys()) > 2:
                    for r in metrics["RESULTS"][model][rgn]:
                        if r != "model_mean":
                            clim_err_x.append(ind[nmod])
                            clim_err_y.append(
                                float(
                                    metrics["RESULTS"][model][rgn][r][
                                        reference_data_set
                                    ]["monthly_clim"]["mse"]
                                )
                            )
                            ext_err_y.append(
                                float(
                                    metrics["RESULTS"][model][rgn][r][
                                        reference_data_set
                                    ]["total_extent"]["mse"]
                                )
                            )

            # plot data
            if len(model_list) < 4:
                mark_size = 9
            elif len(model_list) < 12:
                mark_size = 3
            else:
                mark_size = 1
            ax7[inds].bar(
                ind - width / 2.0, mse_clim, width, color="b", label="Ann. Cycle"
            )
            ax7[inds].bar(ind, mse_ext, width, color="r", label="Ann. Mean")
            if len(clim_err_x) > 0:
                ax7[inds].scatter(
                    [x - width / 2.0 for x in clim_err_x],
                    clim_err_y,
                    marker="D",
                    s=mark_size,
                    color="k",
                )
                ax7[inds].scatter(
                    clim_err_x, ext_err_y, marker="D", s=mark_size, color="k"
                )
            # xticks
            if inds == len(sector_list) - 1:
                ax7[inds].set_xticks(ind + width / 2.0, mlabels, rotation=90, size=7)
            else:
                ax7[inds].set_xticks(ind + width / 2.0, labels="")
            # yticks
            if len(clim_err_y) > 0:
                datamax = np.max(
                    np.concatenate((np.array(clim_err_y), np.array(ext_err_y)))
                )
            else:
                datamax = np.max(
                    np.concatenate((np.array(mse_clim), np.array(mse_ext)))
                )
            ymax = (datamax) * 1.3
            ax7[inds].set_ylim(0.0, ymax)
            if ymax < 0.1:
                ticks = np.linspace(0, 0.1, 6)
                labels = [str(round(x, 3)) for x in ticks]
            elif ymax < 1:
                ticks = np.linspace(0, 1, 5)
                labels = [str(round(x, 1)) for x in ticks]
            elif ymax < 4:
                ticks = np.linspace(0, round(ymax), num=round(ymax / 2) * 2 + 1)
                labels = [str(round(x, 1)) for x in ticks]
            elif ymax > 10:
                ticks = range(0, round(ymax), 5)
                labels = [str(round(x, 0)) for x in ticks]
            else:
                ticks = range(0, round(ymax))
                labels = [str(round(x, 0)) for x in ticks]

            ax7[inds].set_yticks(ticks, labels, fontsize=8)
            # labels etc
            ax7[inds].set_ylabel("10${^1}{^2}$km${^4}$", size=8)
            ax7[inds].grid(True, linestyle=":")
            ax7[inds].annotate(
                sector,
                (0.35, 0.8),
                xycoords="axes fraction",
                size=9,
            )
        # Add legend, save figure
        ax7[0].legend(loc="upper right", fontsize=6)
        plt.suptitle("Mean Square Error relative to " + reference_data_set, y=0.91)
        figfile = os.path.join(metrics_output_path, "MSE_bar_chart.png")
        plt.savefig(figfile)
        meta.update_plots(
            "bar_chart", figfile, "regional_bar_chart", "Bar chart of regional MSE"
        )

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

    meta.update_provenance("modeldata", test_data_path)
    if reference_data_path_nh is not None:
        meta.update_provenance("obsdata_nh", reference_data_path_nh)
        meta.update_provenance("obsdata_sh", reference_data_path_sh)
    meta.write()
