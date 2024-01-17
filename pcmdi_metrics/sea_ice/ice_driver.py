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
from sea_ice_parser import create_sea_ice_parser

from pcmdi_metrics.io import xcdat_openxml
from pcmdi_metrics.io.base import Base
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


def sea_ice_regions(ds, var, xvar, yvar):
    # Two sets of region definitions are provided, one for
    # -180:180 and one for 0:360 longitude ranges
    data_arctic = ds[var].where(ds[yvar] > 0, 0)
    data_antarctic = ds[var].where(ds[yvar] < 0, 0)
    if (ds[xvar] > 180).any():  # 0 to 360
        data_ca1 = ds[var].where(
            (
                (ds[yvar] > 80)
                & (ds[yvar] <= 87.2)
                & ((ds[xvar] > 240) | (ds[xvar] <= 90))
            ),
            0,
        )
        data_ca2 = ds[var].where(
            ((ds[yvar] > 65) & (ds[yvar] < 87.2))
            & ((ds[xvar] > 90) & (ds[xvar] <= 240)),
            0,
        )
        data_ca = data_ca1 + data_ca2
        data_np = ds[var].where(
            (ds[yvar] > 35) & (ds[yvar] <= 65) & ((ds[xvar] > 90) & (ds[xvar] <= 240)),
            0,
        )
        data_na = ds[var].where(
            (ds[yvar] > 45) & (ds[yvar] <= 80) & ((ds[xvar] > 240) | (ds[xvar] <= 90)),
            0,
        )
        data_na = data_na - data_na.where(
            (ds[yvar] > 45) & (ds[yvar] <= 50) & (ds[xvar] > 30) & (ds[xvar] <= 60),
            0,
        )
        data_sa = ds[var].where(
            (ds[yvar] > -90)
            & (ds[yvar] <= -40)
            & ((ds[xvar] > 300) | (ds[xvar] <= 20)),
            0,
        )
        data_sp = ds[var].where(
            (ds[yvar] > -90)
            & (ds[yvar] <= -40)
            & ((ds[xvar] > 90) & (ds[xvar] <= 300)),
            0,
        )
        data_io = ds[var].where(
            (ds[yvar] > -90) & (ds[yvar] <= -40) & (ds[xvar] > 20) & (ds[xvar] <= 90),
            0,
        )
    else:  # -180 to 180
        data_ca1 = ds[var].where(
            (
                (ds[yvar] > 80)
                & (ds[yvar] <= 87.2)
                & (ds[xvar] > -120)
                & (ds[xvar] <= 90)
            ),
            0,
        )
        data_ca2 = ds[var].where(
            ((ds[yvar] > 65) & (ds[yvar] < 87.2))
            & ((ds[xvar] > 90) | (ds[xvar] <= -120)),
            0,
        )
        data_ca = data_ca1 + data_ca2
        data_np = ds[var].where(
            (ds[yvar] > 35) & (ds[yvar] <= 65) & ((ds[xvar] > 90) | (ds[xvar] <= -120)),
            0,
        )
        data_na = ds[var].where(
            (ds[yvar] > 45) & (ds[yvar] <= 80) & (ds[xvar] > -120) & (ds[xvar] <= 90),
            0,
        )
        data_na = data_na - data_na.where(
            (ds[yvar] > 45) & (ds[yvar] <= 50) & (ds[xvar] > 30) & (ds[xvar] <= 60),
            0,
        )
        data_sa = ds[var].where(
            (ds[yvar] > -90) & (ds[yvar] <= -40) & (ds[xvar] > -60) & (ds[xvar] <= 20),
            0,
        )
        data_sp = ds[var].where(
            (ds[yvar] > -90)
            & (ds[yvar] <= -40)
            & ((ds[xvar] > 90) | (ds[xvar] <= -60)),
            0,
        )
        data_io = ds[var].where(
            (ds[yvar] > -90) & (ds[yvar] <= -40) & (ds[xvar] > 20) & (ds[xvar] <= 90),
            0,
        )

    regions_dict = {
        "arctic": data_arctic.copy(deep=True),
        "ca": data_ca.copy(deep=True),
        "np": data_np.copy(deep=True),
        "na": data_na.copy(deep=True),
        "antarctic": data_antarctic.copy(deep=True),
        "sa": data_sa.copy(deep=True),
        "sp": data_sp.copy(deep=True),
        "io": data_io.copy(deep=True),
    }
    return regions_dict


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


def to_ice_con_ds(da, ds):
    # Convert sea ice data array to dataset using
    # coordinates from another dataset
    ds = xr.Dataset(
        data_vars={"ice_con": da, "time_bnds": ds.time_bnds}, coords={"time": ds.time}
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
    reference_data_path = parameter.reference_data_path
    reference_data_set = parameter.reference_data_set
    metrics_output_path = parameter.metrics_output_path
    area_template = parameter.area_template
    area_var = parameter.area_var
    AreaUnitsAdjust = parameter.AreaUnitsAdjust
    ModUnitsAdjust = parameter.ModUnitsAdjust
    ObsUnitsAdjust = parameter.ObsUnitsAdjust
    # plots = parameter.plots
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

    # if plots:
    #    plot_dir_maps = os.path.join(metrics_output_path, "plots", "maps")
    #    os.makedirs(plot_dir_maps, exist_ok=True)

    # Setting up model realization list
    find_all_realizations, realizations = set_up_realizations(realization)
    print("Find all realizations:", find_all_realizations)

    #### Do Obs part
    ObsUnitsAdjust = (True, "multiply", 1e-2)
    ObsAreaUnitsAdjust = (False, 0, 0)

    f_nt_n = "/home/ordonez4/seaice/data/icecon_ssmi_nt_n_edited.nc"
    f_nt_s = "/home/ordonez4/seaice/data/icecon_ssmi_nt_s_edited.nc"
    f_bt_n = "/home/ordonez4/seaice/data/icecon_ssmi_bt_n_edited.nc"
    f_bt_s = "/home/ordonez4/seaice/data/icecon_ssmi_bt_s_edited.nc"

    arctic_clims = {}
    arctic_means = {}
    arctic_files = {"nt": f_nt_n, "bt": f_bt_n}
    obs_var = "ice_con"

    print("OBS: Arctic")
    for source in arctic_files:
        obs = xc.open_dataset(arctic_files[source])
        obs[obs_var] = adjust_units(obs[obs_var], ObsUnitsAdjust)
        obs["area"] = adjust_units(obs["area"], ObsAreaUnitsAdjust)
        # Remove land areas (including lakes)
        mask = create_land_sea_mask(obs, lon_key="lon", lat_key="lat")
        obs[obs_var] = obs[obs_var].where(mask < 1)
        # Get regions
        rgn_dict = sea_ice_regions(obs, obs_var, "lon", "lat")
        """data_arctic = obs[obs_var].where((obs.lat > 0), 0)
        data_ca1 = obs[obs_var].where(
            ((obs.lat > 80) & (obs.lat <= 87.2) & (obs.lon > -120) & (obs.lon <= 90)), 0
        )
        data_ca2 = obs[obs_var].where(
            ((obs.lat > 65) & (obs.lat < 87.2)) & ((obs.lon > 90) | (obs.lon <= -120)),
            0,
        )
        data_ca = obs[obs_var].where((data_ca1 > 0) | (data_ca2 > 0), 0)
        data_np = obs[obs_var].where(
            (obs.lat > 35) & (obs.lat <= 65) & ((obs.lon > 90) | (obs.lon <= -120)), 0
        )
        data_na = obs[obs_var].where(
            (obs.lat > 45) & (obs.lat <= 80) & (obs.lon > -120) & (obs.lon <= 90), 0
        )
        data_na = data_na - data_na.where(
            (obs.lat > 45) & (obs.lat <= 50) & (obs.lon > 30) & (obs.lon <= 60), 0
        )"""

        # Get ice extent
        total_extent_arctic_obs = (
            rgn_dict["arctic"].where(rgn_dict["arctic"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)
        total_extent_ca_obs = (
            rgn_dict["ca"].where(rgn_dict["ca"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)
        total_extent_np_obs = (
            rgn_dict["np"].where(rgn_dict["np"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)
        total_extent_na_obs = (
            rgn_dict["na"].where(rgn_dict["na"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)

        clim_arctic_obs = to_ice_con_ds(
            total_extent_arctic_obs, obs
        ).temporal.climatology(obs_var, freq="month")
        clim_ca_obs = to_ice_con_ds(total_extent_ca_obs, obs).temporal.climatology(
            obs_var, freq="month"
        )
        clim_np_obs = to_ice_con_ds(total_extent_np_obs, obs).temporal.climatology(
            obs_var, freq="month"
        )
        clim_na_obs = to_ice_con_ds(total_extent_na_obs, obs).temporal.climatology(
            obs_var, freq="month"
        )

        arctic_clims[source] = {
            "arctic": clim_arctic_obs,
            "ca": clim_ca_obs,
            "np": clim_np_obs,
            "na": clim_na_obs,
        }

        arctic_means[source] = {
            "arctic": total_extent_arctic_obs.mean("time", skipna=True).data.item(),
            "ca": total_extent_ca_obs.mean("time", skipna=True).data.item(),
            "np": total_extent_np_obs.mean("time", skipna=True).data.item(),
            "na": total_extent_na_obs.mean("time", skipna=True).data.item(),
        }
        obs.close()

    antarctic_clims = {}
    antarctic_means = {}
    antarctic_files = {"nt": f_nt_s, "bt": f_bt_s}
    print("OBS: Antarctic")
    for source in antarctic_files:
        obs = xc.open_dataset(antarctic_files[source])
        obs[obs_var] = adjust_units(obs[obs_var], ObsUnitsAdjust)
        obs["area"] = adjust_units(obs["area"], ObsAreaUnitsAdjust)
        # Remove land areas (including lakes)
        mask = create_land_sea_mask(obs, lon_key="lon", lat_key="lat")
        obs[obs_var] = obs[obs_var].where(mask < 1)
        rgn_dict = sea_ice_regions(obs, obs_var, "lon", "lat")
        """data_antarctic = obs[obs_var].where((obs.lat < 0), 0)
        data_sa = obs[obs_var].where(
            (obs.lat > -90) & (obs.lat <= -55) & (obs.lon > -60) & (obs.lon <= 20), 0
        )
        data_sp = obs[obs_var].where(
            (obs.lat > -90) & (obs.lat <= -55) & ((obs.lon > 90) | (obs.lon <= -60)), 0
        )
        data_io = obs[obs_var].where(
            (obs.lat > -90) & (obs.lat <= -55) & (obs.lon > 20) & (obs.lon <= 90), 0
        )"""

        total_extent_antarctic_obs = (
            rgn_dict["antarctic"].where(rgn_dict["antarctic"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)
        total_extent_sa_obs = (
            rgn_dict["sa"].where(rgn_dict["sa"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)
        total_extent_sp_obs = (
            rgn_dict["sp"].where(rgn_dict["sp"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)
        total_extent_io_obs = (
            rgn_dict["io"].where(rgn_dict["io"] > 0.15) * obs.area
        ).sum(("x", "y"), skipna=True)

        clim_antarctic_obs = to_ice_con_ds(
            total_extent_antarctic_obs, obs
        ).temporal.climatology(obs_var, freq="month")
        clim_sa_obs = to_ice_con_ds(total_extent_sa_obs, obs).temporal.climatology(
            obs_var, freq="month"
        )
        clim_sp_obs = to_ice_con_ds(total_extent_sp_obs, obs).temporal.climatology(
            obs_var, freq="month"
        )
        clim_io_obs = to_ice_con_ds(total_extent_io_obs, obs).temporal.climatology(
            obs_var, freq="month"
        )

        antarctic_clims[source] = {
            "antarctic": clim_antarctic_obs,
            "io": clim_io_obs,
            "sp": clim_sp_obs,
            "sa": clim_sa_obs,
        }

        antarctic_means[source] = {
            "antarctic": total_extent_antarctic_obs.mean(
                "time", skipna=True
            ).data.item(),
            "io": total_extent_io_obs.mean("time", skipna=True).data.item(),
            "sp": total_extent_sp_obs.mean("time", skipna=True).data.item(),
            "sa": total_extent_sa_obs.mean("time", skipna=True).data.item(),
        }
        obs.close()

    obs_clims = {"nt": {}, "bt": {}}
    obs_means = {"nt": {}, "bt": {}}
    for item in antarctic_clims["nt"]:
        obs_clims["nt"][item] = antarctic_clims["nt"][item]
        obs_means["nt"][item] = antarctic_means["nt"][item]
        obs_clims["bt"][item] = antarctic_clims["bt"][item]
        obs_means["bt"][item] = antarctic_means["bt"][item]
    for item in arctic_clims["nt"]:
        obs_clims["nt"][item] = arctic_clims["nt"][item]
        obs_means["nt"][item] = arctic_means["nt"][item]
        obs_clims["bt"][item] = arctic_clims["bt"][item]
        obs_means["bt"][item] = arctic_means["bt"][item]

    # Get climatology
    # get errors for climo and mean

    #### Do model part
    # Loop over models

    clim_wts = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    clim_wts = [x / 365 for x in clim_wts]
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
    print(model_list)

    for model in model_list:
        start_year = msyear
        end_year = meyear

        # totals_dict = {
        #    "arctic": 0,
        #    "ca": 0,
        #    "na": 0,
        #    "np": 0,
        #    "antarctic": 0,
        #    "sp": 0,
        #    "sa": 0,
        #    "io": 0,
        # }
        real_dict = {
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
            "arctic": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "ca": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "na": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "np": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "antarctic": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "sp": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "sa": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
            "io": {"model_mean": {"nasateam": {}, "bootstrap": {}}},
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
                regions_dict = sea_ice_regions(ds, var, xvar, yvar)

                ds.close()
                # Running sum of all realizations
                for rgn in regions_dict:
                    data = regions_dict[rgn]
                    # coordinates aren't always the same as lat/lon names,
                    # especially if lat/lon are 2D
                    if len(data[xvar].dims) == 2:
                        lon_j, lon_i = data[xvar].dims
                    elif len(data[xvar].dims) == 1:
                        lon_j = xvar
                        lon_i = yvar
                    # area data doesn't always use same coordinates as siconc data in CMIP6
                    # so we multiply by area.data, dropping the coordinates
                    rgn_total = (data.where(data > 0.15, 0) * area[area_var].data).sum(
                        (lon_j, lon_i), skipna=True
                    )
                    real_dict[rgn][run] = rgn_total
                    # totals_dict[rgn] = totals_dict[rgn] + rgn_total
                    real_dict[rgn]["model_mean"] = (
                        real_dict[rgn]["model_mean"] + rgn_total
                    )

            print("\n-------------------------------------------")
            print("Calculating model regional average metrics \nfor ", model)
            print("--------------------------------------------")
            for rgn in real_dict:
                print(rgn)

                # Average all realizations, fix bounds, get climatologies and totals
                # total_rgn = (totals_dict[rgn] / len(list_of_runs)).to_dataset(name=var)
                real_dict[rgn]["model_mean"] = real_dict[rgn]["model_mean"] / len(
                    list_of_runs
                )

                for run in real_dict[rgn]:
                    # Set up metrics dictionary
                    if run not in mse[model][rgn]:
                        mse[model][rgn][run] = {}
                    for key in ["nasateam", "bootstrap"]:
                        mse[model][rgn][run].update(
                            {
                                key: {
                                    "monthly_clim": {"mse": None},
                                    "total_extent": {"mse": None},
                                }
                            }
                        )

                    run_data = real_dict[rgn][run].to_dataset(name=var)
                    # total_rgn.time.attrs.pop("bounds")
                    # total_rgn = total_rgn.bounds.add_missing_bounds()
                    run_data = run_data.bounds.add_missing_bounds()
                    clim_extent = run_data.temporal.climatology(var, freq="month")
                    total = run_data.mean("time")[var].data

                    # Get errors, convert to 1e12 km^-4
                    mse[model][rgn][run]["nasateam"]["monthly_clim"]["mse"] = str(
                        mse_t(
                            clim_extent[var],
                            obs_clims["nt"][rgn]["ice_con"],
                            weights=clim_wts,
                        )
                        * 1e-12
                    )
                    mse[model][rgn][run]["bootstrap"]["monthly_clim"]["mse"] = str(
                        mse_t(
                            clim_extent[var],
                            obs_clims["bt"][rgn]["ice_con"],
                            weights=clim_wts,
                        )
                        * 1e-12
                    )
                    mse[model][rgn][run]["nasateam"]["total_extent"]["mse"] = str(
                        mse_model(total, obs_means["nt"][rgn]) * 1e-12
                    )
                    mse[model][rgn][run]["bootstrap"]["total_extent"]["mse"] = str(
                        mse_model(total, obs_means["bt"][rgn]) * 1e-12
                    )

            # Update year list
            metrics["model_year_range"][model] = [str(start_year), str(end_year)]
        else:
            for rgn in mse[model]:
                # Set up metrics dictionary
                for key in ["nasateam", "bootstrap"]:
                    mse[model][rgn]["model_mean"][key] = {
                        "monthly_clim": {"mse": None},
                        "total_extent": {"mse": None},
                    }
                metrics["model_year_range"][model] = ["", ""]

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
    mlabels = model_list + ["bootstrap"]
    ind = np.arange(len(mlabels))  # the x locations for the groups
    # ind = np.arange(len(mods)+1)  # the x locations for the groups
    width = 0.3
    n = len(ind) - 1
    for inds, sector in enumerate(sector_list):
        # Assemble data
        mse_clim = []
        mse_ext = []
        rgn = sector_short[inds]
        for model in model_list:
            mse_clim.append(
                float(
                    metrics["RESULTS"][model][rgn]["model_mean"]["nasateam"][
                        "monthly_clim"
                    ]["mse"]
                )
            )
            mse_ext.append(
                float(
                    metrics["RESULTS"][model][rgn]["model_mean"]["nasateam"][
                        "total_extent"
                    ]["mse"]
                )
            )
        mse_clim.append(
            mse_t(
                obs_clims["bt"][rgn]["ice_con"],
                obs_clims["nt"][rgn]["ice_con"],
                weights=clim_wts,
            )
            * 1e-12
        )
        mse_ext.append(mse_model(obs_means["bt"][rgn], obs_means["nt"][rgn]) * 1e-12)

        # Make figure
        ax7[inds].bar(ind, mse_clim, width, color="b")
        ax7[inds].bar(ind, mse_ext, width, color="r")
        # ax7[inds].errorbar(ind, mse_clim, yerr=clim_err, fmt="o", color="r")
        # ax7[inds].errorbar(ind, mse_ext, yerr=ext_err, fmt="o", color="r")
        # ax7[inds].bar(ind[n], obs[sector_short[inds]]**2, width, color="b")
        if inds == len(sector_list) - 1:
            ax7[inds].set_xticks(ind + width / 2.0, mlabels, rotation=90, size=5)
        else:
            ax7[inds].set_xticks(ind + width / 2.0, labels="")
        datamax = np.max(mse_clim)
        ymax = (datamax) * 1.3
        ax7[inds].set_ylim(0.0, ymax)
        if ymax < 1:
            ticks = np.linspace(0, 1, 5)
            labels = [str(round(x, 1)) for x in ticks]
        elif ymax < 4:
            ticks = np.linspace(0, round(ymax), num=round(ymax / 2) * 4 + 1)
            labels = [str(round(x, 1)) for x in ticks]
        elif ymax > 10:
            ticks = range(0, round(ymax), 5)
            labels = [str(round(x, 0)) for x in ticks]
        else:
            ticks = range(0, round(ymax))
            labels = [str(round(x, 0)) for x in ticks]

        ax7[inds].set_yticks(ticks, labels, fontsize=6)

        ax7[inds].set_ylabel("10${^12}$km${^4}$", size=6)
        ax7[inds].grid(True, linestyle=":")
        ax7[inds].annotate(
            sector,
            (0.35, 0.8),
            xycoords="axes fraction",
            size=8,
        )
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
    if reference_data_path is not None:
        meta.update_provenance("obsdata", reference_data_path)
    meta.write()
