#!/usr/bin/env python

import datetime
import glob
import json
import os
import sys

import dask
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import xcdat as xc

from pcmdi_metrics.io import xcdat_openxml
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.sea_ice.lib import create_sea_ice_parser
from pcmdi_metrics.utils import create_land_sea_mask


class MetadataFile:
    # This class organizes the contents for the CMEC
    # metadata file called output.json, which describes
    # the other files in the output bundle.

    def __init__(self, metrics_output_path):
        self.outfile = os.path.join(metrics_output_path, "output.json")
        self.json = {
            "provenance": {
                "environment": "",
                "modeldata": "",
                "obsdata": "",
                "log": "",
            },
            "metrics": {},
            "data": {},
            "plots": {},
        }

    def update_metrics(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["metrics"].update({kw: tmp})
        return

    def update_data(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["data"].update({kw: tmp})
        return

    def update_plots(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["plots"].update({kw: tmp})

    def update_provenance(self, kw, data):
        self.json["provenance"].update({kw: data})
        return

    def update_index(self, val):
        self.json["index"] = val
        return

    def write(self):
        with open(self.outfile, "w") as f:
            json.dump(self.json, f, indent=4)


def central_arctic(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_ca1 = ds[ds_var].where(
            (
                (ds[yvar] > 80)
                & (ds[yvar] <= 87.2)
                & ((ds[xvar] > 240) | (ds[xvar] <= 90))
            ),
            0,
        )
        data_ca2 = ds[ds_var].where(
            ((ds[yvar] > 65) & (ds[yvar] < 87.2))
            & ((ds[xvar] > 90) & (ds[xvar] <= 240)),
            0,
        )
        data_ca = data_ca1 + data_ca2
    else:  # -180 to 180
        data_ca1 = ds[ds_var].where(
            (
                (ds[yvar] > 80)
                & (ds[yvar] <= 87.2)
                & (ds[xvar] > -120)
                & (ds[xvar] <= 90)
            ),
            0,
        )
        data_ca2 = ds[ds_var].where(
            ((ds[yvar] > 65) & (ds[yvar] < 87.2))
            & ((ds[xvar] > 90) | (ds[xvar] <= -120)),
            0,
        )
        data_ca = data_ca1 + data_ca2
    return data_ca


def north_pacific(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_np = ds[ds_var].where(
            (ds[yvar] > 35) & (ds[yvar] <= 65) & ((ds[xvar] > 90) & (ds[xvar] <= 240)),
            0,
        )
    else:
        data_np = ds[ds_var].where(
            (ds[yvar] > 35) & (ds[yvar] <= 65) & ((ds[xvar] > 90) | (ds[xvar] <= -120)),
            0,
        )
    return data_np


def north_atlantic(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_na = ds[ds_var].where(
            (ds[yvar] > 45) & (ds[yvar] <= 80) & ((ds[xvar] > 240) | (ds[xvar] <= 90)),
            0,
        )
        data_na = data_na - data_na.where(
            (ds[yvar] > 45) & (ds[yvar] <= 50) & (ds[xvar] > 30) & (ds[xvar] <= 60),
            0,
        )
    else:
        data_na = ds[ds_var].where(
            (ds[yvar] > 45) & (ds[yvar] <= 80) & (ds[xvar] > -120) & (ds[xvar] <= 90),
            0,
        )
        data_na = data_na - data_na.where(
            (ds[yvar] > 45) & (ds[yvar] <= 50) & (ds[xvar] > 30) & (ds[xvar] <= 60),
            0,
        )
    return data_na


def south_atlantic(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_sa = ds[ds_var].where(
            (ds[yvar] > -90)
            & (ds[yvar] <= -40)
            & ((ds[xvar] > 300) | (ds[xvar] <= 20)),
            0,
        )
    else:  # -180 to 180
        data_sa = ds[ds_var].where(
            (ds[yvar] > -90) & (ds[yvar] <= -55) & (ds[xvar] > -60) & (ds[xvar] <= 20),
            0,
        )
    return data_sa


def south_pacific(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_sp = ds[ds_var].where(
            (ds[yvar] > -90)
            & (ds[yvar] <= -40)
            & ((ds[xvar] > 90) & (ds[xvar] <= 300)),
            0,
        )
    else:
        data_sp = ds[ds_var].where(
            (ds[yvar] > -90)
            & (ds[yvar] <= -55)
            & ((ds[xvar] > 90) | (ds[xvar] <= -60)),
            0,
        )
    return data_sp


def indian_ocean(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_io = ds[ds_var].where(
            (ds[yvar] > -90) & (ds[yvar] <= -40) & (ds[xvar] > 20) & (ds[xvar] <= 90),
            0,
        )
    else:  # -180 to 180
        data_io = ds[ds_var].where(
            (ds[yvar] > -90) & (ds[yvar] <= -55) & (ds[xvar] > 20) & (ds[xvar] <= 90),
            0,
        )
    return data_io


def arctic(ds, ds_var, xvar, yvar):
    data_arctic = ds[ds_var].where(ds[yvar] > 0, 0)
    return data_arctic


def antarctic(ds, ds_var, xvar, yvar):
    data_antarctic = ds[ds_var].where(ds[yvar] < 0, 0)
    return data_antarctic


def choose_region(region, ds, ds_var, xvar, yvar):
    if region == "arctic":
        return arctic(ds, ds_var, xvar, yvar)
    elif region == "na":
        return north_atlantic(ds, ds_var, xvar, yvar)
    elif region == "ca":
        return central_arctic(ds, ds_var, xvar, yvar)
    elif region == "np":
        return north_pacific(ds, ds_var, xvar, yvar)
    elif region == "antarctic":
        return antarctic(ds, ds_var, xvar, yvar)
    elif region == "sa":
        return south_atlantic(ds, ds_var, xvar, yvar)
    elif region == "sp":
        return south_pacific(ds, ds_var, xvar, yvar)
    elif region == "io":
        return indian_ocean(ds, ds_var, xvar, yvar)


def get_total_extent(data, ds_area):
    xvar = find_lon(data)
    coord_i, coord_j = get_xy_coords(data, xvar)
    total_extent = (data.where(data > 0.15) * ds_area).sum(
        (coord_i, coord_j), skipna=True
    )
    if isinstance(total_extent.data, dask.array.core.Array):
        te_mean = total_extent.mean("time", skipna=True).data.compute().item()
    else:
        te_mean = total_extent.mean("time", skipna=True).data.item()
    return total_extent, te_mean


def get_clim(total_extent, ds, ds_var):
    clim = to_ice_con_ds(total_extent, ds, ds_var).temporal.climatology(
        ds_var, freq="month"
    )
    return clim


def process_by_region(ds, ds_var, ds_area):
    regions_list = ["arctic", "antarctic", "ca", "na", "np", "sa", "sp", "io"]
    clims = {}
    means = {}
    for region in regions_list:
        xvar = find_lon(ds)
        yvar = find_lat(ds)
        data = choose_region(region, ds, ds_var, xvar, yvar)
        total_extent, te_mean = get_total_extent(data, ds_area)
        clim = get_clim(total_extent, ds, ds_var)
        clims[region] = clim
        means[region] = te_mean
        del data
    return clims, means


def find_lon(ds):
    for key in ds.coords:
        if key in ["lon", "longitude"]:
            return key
    for key in ds.keys():
        if key in ["lon", "longitude"]:
            return key
    return None


def find_lat(ds):
    for key in ds.coords:
        if key in ["lat", "latitude"]:
            return key
    for key in ds.keys():
        if key in ["lat", "latitude"]:
            return key
    return None


def mse_t(dm, do, weights=None):
    """Computes mse"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Temporal Mean Square Error",
            "Abstract": "Compute Temporal Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if weights is None:
        stat = np.sum(((dm.data - do.data) ** 2)) / len(dm, axis=0)
    else:
        stat = np.sum(((dm.data - do.data) ** 2) * weights, axis=0)
    if isinstance(stat, dask.array.core.Array):
        stat = stat.compute()
    return stat


def mse_model(dm, do, var=None):
    """Computes mse"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Square Error",
            "Abstract": "Compute Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if var is not None:  # dataset
        stat = (dm[var].data - do[var].data) ** 2
    else:  # dataarray
        stat = (dm - do) ** 2
    if isinstance(stat, dask.array.core.Array):
        stat = stat.compute()
    return stat


def to_ice_con_ds(da, ds, obs_var):
    # Convert sea ice data array to dataset using
    # coordinates from another dataset
    ds = xr.Dataset(
        data_vars={obs_var: da, "time_bnds": ds.time_bnds}, coords={"time": ds.time}
    )
    return ds


def adjust_units(ds, adjust_tuple):
    action_dict = {"multiply": "*", "divide": "/", "add": "+", "subtract": "-"}
    if adjust_tuple[0]:
        print("Converting units by ", adjust_tuple[1], adjust_tuple[2])
        cmd = " ".join(["ds", str(action_dict[adjust_tuple[1]]), str(adjust_tuple[2])])
        ds = eval(cmd)
    return ds


def verify_output_path(metrics_output_path, case_id):
    if metrics_output_path is None:
        metrics_output_path = datetime.datetime.now().strftime("v%Y%m%d")
    if case_id is not None:
        metrics_output_path = metrics_output_path.replace("%(case_id)", case_id)
    if not os.path.exists(metrics_output_path):
        print("\nMetrics output path not found.")
        print("Creating metrics output directory", metrics_output_path)
        try:
            os.makedirs(metrics_output_path)
        except Exception as e:
            print("\nError: Could not create metrics output path", metrics_output_path)
            print(e)
            print("Exiting.")
            sys.exit()
    return metrics_output_path


def verify_years(start_year, end_year, msg="Error: Invalid start or end year"):
    if start_year is None and end_year is None:
        return
    elif start_year is None or end_year is None:
        # If only one of the two is set, exit.
        print(msg)
        print("Exiting")
        sys.exit()


def set_up_realizations(realization):
    find_all_realizations = False
    if realization is None:
        realization = ""
        realizations = [realization]
    elif isinstance(realization, str):
        if realization.lower() in ["all", "*"]:
            find_all_realizations = True
            realizations = [""]
        else:
            realizations = [realization]
    elif isinstance(realization, list):
        realizations = realization

    return find_all_realizations, realizations


def load_dataset(filepath):
    # Load an xarray dataset from the given filepath.
    # If list of netcdf files, opens mfdataset.
    # If list of xmls, open last file in list.
    if filepath[-1].endswith(".xml"):
        # Final item of sorted list would have most recent version date
        ds = xcdat_openxml.xcdat_openxml(filepath[-1])
    elif len(filepath) > 1:
        ds = xc.open_mfdataset(filepath, chunks=None)
    else:
        ds = xc.open_dataset(filepath[0])
    return ds


def replace_multi(string, rdict):
    # Replace multiple keyworks in a string template
    # based on key-value pairs in 'rdict'.
    for k in rdict.keys():
        string = string.replace(k, rdict[k])
    return string


def get_xy_coords(ds, xvar):
    if len(ds[xvar].dims) == 2:
        lon_j, lon_i = ds[xvar].dims
    elif len(ds[xvar].dims) == 1:
        lon_j = find_lon(ds)
        lon_i = find_lat(ds)
    return lon_i, lon_j


if __name__ == "__main__":
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

    print(model_list)
    model_list.sort()
    # Verifying output directory
    metrics_output_path = verify_output_path(metrics_output_path, case_id)

    if isinstance(reference_data_set, list):
        # Fix a command line issue
        reference_data_set = reference_data_set[0]

    # Verify years
    ok_mod = verify_years(
        msyear,
        meyear,
        msg="Error: Model msyear and meyear must both be set or both be None (unset).",
    )
    ok_obs = verify_years(
        osyear,
        oeyear,
        msg="Error: Obs osyear and oeyear must both be set or both be None (unset).",
    )

    # Initialize output.json file
    meta = MetadataFile(metrics_output_path)

    # Setting up model realization list
    find_all_realizations, realizations = set_up_realizations(realization)
    print("Find all realizations:", find_all_realizations)

    #### Do Obs part
    arctic_clims = {}
    arctic_means = {}

    print("OBS: Arctic")
    nh_files = glob.glob(reference_data_path_nh)
    obs = load_dataset(nh_files)
    xvar = find_lon(obs)
    yvar = find_lat(obs)
    coord_i, coord_j = get_xy_coords(obs, xvar)
    if osyear is not None:
        obs = obs.sel(
            {
                "time": slice(
                    "{0}-01-01".format(osyear),
                    "{0}-12-31".format(oeyear),
                )
            }
        ).compute()  # TODO: won't always need to compute
    obs[obs_var] = adjust_units(obs[obs_var], ObsUnitsAdjust)
    if obs_area_var is not None:
        obs[obs_area_var] = adjust_units(obs[obs_area_var], ObsAreaUnitsAdjust)
        area_val = obs[obs_area_var]
    else:
        area_val = obs_cell_area
    # Remove land areas (including lakes)
    mask = create_land_sea_mask(obs, lon_key=xvar, lat_key=yvar)
    obs[obs_var] = obs[obs_var].where(mask < 1)
    # Get regions
    clims, means = process_by_region(obs, obs_var, area_val)

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
    obs = load_dataset(sh_files)
    xvar = find_lon(obs)
    yvar = find_lat(obs)
    coord_i, coord_j = get_xy_coords(obs, xvar)
    if osyear is not None:
        obs = obs.sel(
            {
                "time": slice(
                    "{0}-01-01".format(osyear),
                    "{0}-12-31".format(oeyear),
                )
            }
        ).compute()
    obs[obs_var] = adjust_units(obs[obs_var], ObsUnitsAdjust)
    if obs_area_var is not None:
        obs[obs_area_var] = adjust_units(obs[obs_area_var], ObsAreaUnitsAdjust)
        area_val = obs[obs_area_var]
    else:
        area_val = obs_cell_area
    # Remove land areas (including lakes)
    mask = create_land_sea_mask(obs, lon_key="lon", lat_key="lat")
    obs[obs_var] = obs[obs_var].where(mask < 1)
    clims, means = process_by_region(obs, obs_var, area_val)
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
    metrics = {
        "DIMENSIONS": {
            "json_structure": [
                "model",
                "realization",
                "obs",
                "region",
                "index",
                "statistic",
            ],
            "region": {},
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
    print("Model list:", model_list)

    # Loop over models and realizations to generate metrics
    for model in model_list:
        start_year = msyear
        end_year = meyear

        real_clim = {
            "arctic": {"model_mean": None},
            "ca": {"model_mean": None},
            "na": {"model_mean": None},
            "np": {"model_mean": None},
            "antarctic": {"model_mean": None},
            "sp": {"model_mean": None},
            "sa": {"model_mean": None},
            "io": {"model_mean": None},
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

        tags = {
            "%(variable)": var,
            "%(model)": model,
            "%(model_version)": model,
            "%(realization)": "*",
        }
        if find_all_realizations:
            test_data_full_path_tmp = os.path.join(test_data_path, filename_template)
            test_data_full_path_tmp = replace_multi(test_data_full_path_tmp, tags)
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
        print(replace_multi(area_template, tags))
        area = xc.open_dataset(glob.glob(replace_multi(area_template, tags))[0])
        area[area_var] = adjust_units(area[area_var], AreaUnitsAdjust)

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
                test_data_full_path = replace_multi(test_data_full_path, tags)
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
                ds = load_dataset(test_data_full_path)
                ds[var] = adjust_units(ds[var], ModUnitsAdjust)
                xvar = find_lon(ds)
                yvar = find_lat(ds)
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

                # Get regions
                clims, means = process_by_region(ds, var, area[area_var].data)

                ds.close()
                # Running sum of all realizations
                for rgn in clims:
                    real_clim[rgn][run] = clims[rgn]
                    if real_clim[rgn]["model_mean"] is None:
                        real_clim[rgn]["model_mean"] = clims[rgn]
                    else:
                        real_clim[rgn]["model_mean"][var] = (
                            real_clim[rgn]["model_mean"][var] + clims[rgn][var]
                        )
                    real_mean[rgn][run] = means[rgn]
                    real_mean[rgn]["model_mean"] = (
                        real_mean[rgn]["model_mean"] + means[rgn]
                    )

            print("\n-------------------------------------------")
            print("Calculating model regional average metrics \nfor ", model)
            print("--------------------------------------------")
            for rgn in real_clim:
                print(rgn)
                # Get model mean
                real_clim[rgn]["model_mean"][var] = real_clim[rgn]["model_mean"][
                    var
                ] / len(list_of_runs)
                real_mean[rgn]["model_mean"] = real_mean[rgn]["model_mean"] / len(
                    list_of_runs
                )

                for run in real_clim[rgn]:
                    # Set up metrics dictionary
                    if run not in mse[model][rgn]:
                        mse[model][rgn][run] = {}
                    mse[model][rgn][run].update(
                        {
                            reference_data_set: {
                                "monthly_clim": {"mse": None},
                                "total_extent": {"mse": None},
                            }
                        }
                    )
                    # Get errors, convert to 1e12 km^-4
                    mse[model][rgn][run][reference_data_set]["monthly_clim"][
                        "mse"
                    ] = str(
                        mse_t(
                            real_clim[rgn][run][var],
                            obs_clims[reference_data_set][rgn][obs_var],
                            weights=clim_wts,
                        )
                        * 1e-12
                    )
                    mse[model][rgn][run][reference_data_set]["total_extent"][
                        "mse"
                    ] = str(
                        mse_model(
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

    # ----------------
    # Make figure
    # ----------------
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
                    metrics["RESULTS"][model][rgn]["model_mean"][reference_data_set][
                        "monthly_clim"
                    ]["mse"]
                )
            )
            mse_ext.append(
                float(
                    metrics["RESULTS"][model][rgn]["model_mean"][reference_data_set][
                        "total_extent"
                    ]["mse"]
                )
            )
            # Get spread, only if there are multiple realizations
            if len(metrics["RESULTS"][model][rgn].keys()) > 2:
                for r in metrics["RESULTS"][model][rgn]:
                    if r != "model_mean":
                        clim_err_x.append(ind[nmod])
                        clim_err_y.append(
                            float(
                                metrics["RESULTS"][model][rgn][r][reference_data_set][
                                    "monthly_clim"
                                ]["mse"]
                            )
                        )
                        ext_err_y.append(
                            float(
                                metrics["RESULTS"][model][rgn][r][reference_data_set][
                                    "total_extent"
                                ]["mse"]
                            )
                        )

        # plot data
        if len(model_list) < 4:
            mark_size = 9
        elif len(model_list) < 12:
            mark_size = 3
        else:
            mark_size = 1
        ax7[inds].bar(ind - width / 2.0, mse_clim, width, color="b", label="Ann. Cycle")
        ax7[inds].bar(ind, mse_ext, width, color="r", label="Ann. Mean")
        if len(clim_err_x) > 0:
            ax7[inds].scatter(
                [x - width / 2.0 for x in clim_err_x],
                clim_err_y,
                marker="D",
                s=mark_size,
                color="k",
            )
            ax7[inds].scatter(clim_err_x, ext_err_y, marker="D", s=mark_size, color="k")
        # xticks
        if inds == len(sector_list) - 1:
            ax7[inds].set_xticks(ind + width / 2.0, mlabels, rotation=90, size=7)
        else:
            ax7[inds].set_xticks(ind + width / 2.0, labels="")
        # yticks
        if len(clim_err_y) > 0:
            datamax = np.max(np.array(clim_err_y))
        else:
            datamax = np.max(np.array(mse_clim))
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

    # Update and write metadata file
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
