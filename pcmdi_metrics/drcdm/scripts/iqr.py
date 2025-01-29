#!/usr/bin/env python
import argparse
import csv
import glob
import json
import os

import numpy as np
import xarray as xr
import xcdat as xc
from xclim import ensembles

from pcmdi_metrics.io.region_from_file import region_from_file


def relative_diff(ds, obs):
    diff = (ds - obs) / obs * 100
    diff = diff.where(~np.isnan(ds)).where(~np.isnan(obs))
    diff = xr.where((diff < 1e200), diff, np.nan)  # remove inf
    diff25 = diff.quantile(0.25, skipna=True).data.item()
    diff50 = diff.quantile(0.5, skipna=True).data.item()
    diff75 = diff.quantile(0.75, skipna=True).data.item()
    diffs = {"0.25": diff25, "0.5": diff50, "0.75": diff75}
    return diffs


def abs_diff(ds, obs):
    diff = ds - obs
    diff = diff.where(~np.isnan(ds)).where(~np.isnan(obs))
    diff = xr.where((diff < 1e200), diff, np.nan)  # remove inf
    diff25 = diff.quantile(0.25, skipna=True).data.item()
    diff50 = diff.quantile(0.5, skipna=True).data.item()
    diff75 = diff.quantile(0.75, skipna=True).data.item()
    diffs = {"0.25": diff25, "0.5": diff50, "0.75": diff75}
    return diffs


def filterLatLon(ds_mod, ds_obs, mod_lat, mod_lon, obs_lat, obs_lon):
    # Given two datasets with "close" but not exact lat/lon coordinates, return the "matched" lat/lon coordinates

    if len(ds_mod[mod_lat].data) >= len(ds_obs[obs_lat].data):
        arr1 = ds_mod[mod_lat].data
        arr2 = ds_obs[obs_lat].data
    else:
        arr1 = ds_obs[obs_lat].data
        arr2 = ds_mod[mod_lat].data

    lat = [i for i in arr1 if any((abs(i - arr2) < 0.01))]  # tolerance

    if len(ds_mod[mod_lon].data) >= len(ds_obs[obs_lon].data):
        arr1 = ds_mod[mod_lon].data
        arr2 = ds_obs[obs_lon].data
    else:
        arr1 = ds_obs[obs_lon].data
        arr2 = ds_mod[mod_lon].data

    lon = [i for i in arr1 if any((abs(i - arr2) < 0.01))]  # tolerance

    return lat, lon


def clean_data(ds_mod, ds_obs, var1):
    """Fixes issue where grid coordinates might not match exactly."""

    try:
        if ds_mod.lon.data[0] < 0:  # convert to a common lon coordinate (0, 360)
            ds_mod["lon"] = ds_mod["lon"] + 360
        mod_lon = "lon"
        mod_lat = "lat"
    except Exception:
        if ds_mod.longitude.data[0] < 0:
            ds_mod["longitude"] = ds_mod["longitude"] + 360
        mod_lon = "longitude"
        mod_lat = "latitude"
    try:
        if ds_obs.lon.data[0] < 0:
            ds_obs["lon"] = ds_obs["lon"] + 360
        obs_lat = "lat"
        obs_lon = "lon"
    except Exception:
        if ds_obs.longitude.data[0] < 0:
            ds_obs["longitude"] = ds_obs["longitude"] + 360
        obs_lat = "latitude"
        obs_lon = "longitude"

    ds_obs[var1] = ds_obs[var1].astype(float)
    ds_mod[var1] = ds_mod[var1].astype(float)

    ds_obs = ds_obs.where(
        ds_obs[var1] is not None, np.nan
    )  # NaNs get stored as None in JSON files, switch back.
    ds_mod = ds_mod.where(ds_mod[var1] is not None, np.nan)

    lat, lon = filterLatLon(
        ds_mod, ds_obs, mod_lat, mod_lon, obs_lat, obs_lon
    )  # the a lat/lon coordinate that is common to both datasets

    try:
        ds_mod = ds_mod.rename(
            {"latitude": "lat", "longitude": "lon"}
        )  # common coordinate names
    except Exception:
        pass

    try:
        ds_obs = ds_obs.rename({"latitude": "lat", "longitude": "lon"})
    except Exception:
        pass

    """
    In some cases, the model/observation lat/lons would be slightly off. For example, a location in the loca2 dataset may have been (25.00N, 270.00N) and the PRISM dataset the same
    grid box would've been (25.0001N, 270.0001N). The code below corrects for those inconsistencies. If we didn't do this xarray would exclude any mismatching coords.
    """

    mod_lat_attrs = ds_mod.lat.attrs  # preserve attrs for later
    mod_lon_attrs = ds_mod.lon.attrs

    ds_mod = ds_mod.sel(lat=lat, lon=lon, method="nearest")
    ds_mod = ds_mod.assign_coords(lat=lat, lon=lon)
    ds_mod = ds_mod.reindex(lat=lat, lon=lon, tolerance=1e-5)  #

    ds_mod.lat.attrs = mod_lat_attrs  # add them back
    ds_mod.lon.attrs = mod_lon_attrs

    obs_lat_attrs = ds_obs.lat.attrs  # preserve attrs for later
    obs_lon_attrs = ds_obs.lon.attrs

    ds_obs = ds_obs.sel(lat=lat, lon=lon, method="nearest")
    ds_obs = ds_obs.assign_coords(lat=lat, lon=lon)
    ds_obs = ds_obs.reindex(
        lat=lat, lon=lon, tolerance=1e-5
    )  # ensures the lat/lon coords are indentical

    ds_obs.lat.attrs = obs_lat_attrs
    ds_obs.lon.attrs = obs_lon_attrs

    if len(list(obs_lon_attrs.keys())) == 0:
        ds_obs.lon.attrs = mod_lon_attrs  # add in the model attributes if the obs didn't originally have any attributes

    return ds_mod, ds_obs


def stats_dif(ds, obs, shp):
    tmpstats = {}
    region_list = [
        "Northeast",
        "Northwest",
        "Southeast",
        "Southwest",
        "Northern Great Plains",
        "Southern Great Plains",
        "Midwest",
    ]

    for region in region_list:
        tmpstats[region] = {}
        ds1 = region_from_file(ds, shp, "NAME", region).compute()
        obs1 = region_from_file(obs, shp, "NAME", region).compute()
        for varname in ["ANN", "DJF", "MAM", "JJA", "SON", "q50", "q99p9", "q99p0"]:
            if varname in obs1.keys():
                print(varname)
                ds2, obs2 = clean_data(ds1, obs1, varname)
                rg_dict = {}
                rg_dict["diff"] = dict(
                    {"absolute": abs_diff(ds2[varname], obs2[varname])}
                )
                rg_dict["diff"]["relative"] = relative_diff(ds2[varname], obs2[varname])
                tmpstats[region][varname] = rg_dict
    return tmpstats


def fix_ds(ds):
    # Fixes some issues in the quantile fields
    # that aren't saved with a time axis
    # and the NaN encoding seems to have issues
    for var in ["time_bnds", "lat_bnds", "lon_bnds"]:
        if var in ds:
            ds = ds.drop_vars(var)
    ds = ds.expand_dims(dim="time")
    ds = ds.bounds.add_missing_bounds()
    for var in ["q50", "q99p0", "q99p9"]:
        if var in ds:
            ds = ds.where(ds[var] < 1000)
    return ds


def get_varnames(ds):
    varlist = []
    for item in ["ANN", "DJF", "MAM", "JJA", "SON", "q50", "q99p0", "q99p9"]:
        if item in ds:
            varlist.append(item)
    return varlist


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="iqr.py", description="Create interquartile range table"
    )
    parser.add_argument(
        "--filename_template",
        dest="filename_template",
        type=str,
        help="Filename template of model data",
    )
    parser.add_argument(
        "--reference_template",
        dest="reference_template",
        type=str,
        help="Filename template of observation data",
    )
    parser.add_argument(
        "--shapefile_path",
        dest="shapefile_path",
        type=str,
        help="Path to regions shapefile",
    )
    parser.add_argument(
        "--output_path",
        dest="output_path",
        default=".",
        type=str,
        help="The directory at which to write figure file",
    )
    parser.add_argument(
        "--obs_name",
        dest="obs_name",
        type=str,
        help="The name of the observation dataset",
    )
    parser.add_argument(
        "--model_name",
        dest="model_name",
        type=str,
        help="The name of the model dataset",
    )
    args = parser.parse_args()

    filename_template = args.filename_template
    reference_template = args.reference_template
    shapefile_path = args.shapefile_path
    output_path = args.output_path
    obs_name = args.obs_name
    model_name = args.model_name

    flist = {
        "pr": [
            "_annual_pxx.nc",
            "_annualmean_pr.nc",
            "_pr_q50.nc",
            "_pr_q99p0.nc",
            "_pr_q99p9.nc",
            "_seasonalmean_pr.nc",
            "_annual_cdd.nc",
            "_annual_cwd.nc",
            "_wettest_5yr.nc",
        ],
        "tasmax": [
            "_annual_txx.nc",
            "_mean_tasmax.nc",
            "_tasmax_q50.nc",
            "_tasmax_q99p9.nc",
            "_annual_tasmax_ge_86F.nc",
            "_annual_tasmax_ge_90F.nc",
            "_annual_tasmax_ge_95F.nc",
            "_annual_tasmax_ge_100F.nc",
            "_annual_tasmax_ge_105F.nc",
            "_annual_tasmax_ge_110F.nc",
            "_annual_tasmax_ge_115F.nc",
        ],
        "tasmin": [
            "_annual_tnn.nc",
            "_annualmean_tasmin.nc",
            "_annual_tasmin_ge_70F.nc",
            "_annual_tasmin_ge_75F.nc",
            "_annual_tasmin_ge_80F.nc",
            "_annual_tasmin_ge_85F.nc",
            "_annual_tasmin_ge_90F.nc",
            "_annual_tasmin_le_0F.nc",
            "_annual_tasmin_le_32F.nc",
        ],
    }

    # First get all the model-obs differences for each run
    # and write to file.
    print("\nGenerating regional difference JSONs\n")
    for variable in ["pr", "tasmin", "tasmax"]:
        for suffix in flist[variable]:
            try:
                # Open obs
                reference_path_tmp = reference_template.replace("%(variable)", variable)
                reference_path_tmp = os.path.join(
                    reference_path_tmp, "netcdf/Reference_None" + suffix
                )
                obs = xc.open_dataset(reference_path_tmp)
                if "time" not in obs:
                    obs = fix_ds(obs)
                # Open model ensemble
                filename_template_tmp = filename_template.replace(
                    "%(variable)", variable
                )
                filelist = os.path.join(
                    filename_template_tmp, "netcdf/*{0}".format(suffix)
                )
                filelist = glob.glob(filelist)
                ens = ensembles.create_ensemble(filelist).load()
                # Get the model-obs differences
                varnames = get_varnames(ens)
                print(variable, obs_name, suffix)
                for item in varnames:
                    filename_out = os.path.join(
                        output_path,
                        "{0}{1}_{2}_{3}_{4}.json".format(
                            variable, suffix.split(".")[0], item, model_name, obs_name
                        ),
                    )
                    if "time" in ens:
                        ens_mean = ens.mean(["realization", "time"])
                    else:
                        ens_mean = ens.mean(["realization"])
                    obs2 = obs.regridder.horizontal(
                        item, ens_mean, tool="xesmf", method="nearest_s2d"
                    )
                    if "time" in obs2:
                        obs2 = obs2.mean("time")
                    if suffix in [
                        "_annual_txx.nc",  # convert units F to C
                        "_mean_tasmax.nc",
                        "_tasmax_q50.nc",
                        "_tasmax_q99p9.nc",
                        "_annual_tnn.nc",
                        "_annualmean_tasmin.nc",
                    ]:
                        ens_mean[item] = (ens_mean[item] - 32) * 5 / 9
                        obs2[item] = (obs2[item] - 32) * 5 / 9
                    tmp = stats_dif(ens_mean, obs2, shapefile_path)
                    with open(filename_out, "w") as json_out:
                        json.dump(tmp, json_out, indent=4)
            except Exception as e:
                print("Could not get stats")
                print(e)

    # Once all the differences are written to file, compile into the IQR table
    print("\nGenerating IQR CSV\n")
    metrics_dict = {
        "annualmean_pr (%)": (
            "pr_annualmean_pr_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "seasonalmean_pr (DJF)(%)": (
            "pr_seasonalmean_pr_DJF_{0}_{1}.json".format(model_name, obs_name),
            "DJF",
        ),
        "seasonalmean_pr (MAM)(%)": (
            "pr_seasonalmean_pr_MAM_{0}_{1}.json".format(model_name, obs_name),
            "MAM",
        ),
        "seasonalmean_pr (JJA)(%)": (
            "pr_seasonalmean_pr_JJA_{0}_{1}.json".format(model_name, obs_name),
            "JJA",
        ),
        "seasonalmean_pr (SON)(%)": (
            "pr_seasonalmean_pr_SON_{0}_{1}.json".format(model_name, obs_name),
            "SON",
        ),
        "pr_q50 (%)": (
            "pr_pr_q50_q50_{0}_{1}.json".format(model_name, obs_name),
            "q50",
        ),
        "pr_q99p9 (%)": (
            "pr_pr_q99p9_q99p9_{0}_{1}.json".format(model_name, obs_name),
            "q99p9",
        ),
        "annual_pxx (%)": (
            "pr_annual_pxx_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "annualmean_tasmax (C)": (
            "tasmax_mean_tasmax_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "seasonalmean_tasmax (DJF)(C)": (
            "tasmax_mean_tasmax_DJF_{0}_{1}.json".format(model_name, obs_name),
            "DJF",
        ),
        "seasonalmean_tasmax (MAM)(C)": (
            "tasmax_mean_tasmax_MAM_{0}_{1}.json".format(model_name, obs_name),
            "MAM",
        ),
        "seasonalmean_tasmax (JJA)(C)": (
            "tasmax_mean_tasmax_JJA_{0}_{1}.json".format(model_name, obs_name),
            "JJA",
        ),
        "seasonalmean_tasmax (SON)(C)": (
            "tasmax_mean_tasmax_SON_{0}_{1}.json".format(model_name, obs_name),
            "SON",
        ),
        "tasmax_q50 (C)": (
            "tasmax_tasmax_q50_q50_{0}_{1}.json".format(model_name, obs_name),
            "q50",
        ),
        "tasmax_q99p9 (C)": (
            "tasmax_tasmax_q99p9_q99p9_{0}_{1}.json".format(model_name, obs_name),
            "q99p9",
        ),
        "annual_tasmax_ge_95F (%)": (
            "tasmax_annual_tasmax_ge_95F_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "annual_tasmax_ge_100F (%)": (
            "tasmax_annual_tasmax_ge_100F_ANN_{0}_{1}.json".format(
                model_name, obs_name
            ),
            "ANN",
        ),
        "annual_tasmax_ge_105F (%)": (
            "tasmax_annual_tasmax_ge_105F_ANN_{0}_{1}.json".format(
                model_name, obs_name
            ),
            "ANN",
        ),
        "annual_txx (C)": (
            "tasmax_annual_txx_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "annualmean_tasmin (C)": (
            "tasmin_annualmean_tasmin_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "annual_tasmin_le_32F (C)": (
            "tasmin_annual_tasmin_le_32F_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
        "annual_tnn (C)": (
            "tasmin_annual_tnn_ANN_{0}_{1}.json".format(model_name, obs_name),
            "ANN",
        ),
    }
    regions_list = [
        "Midwest",
        "Northeast",
        "Northern Great Plains",
        "Northwest",
        "Southeast",
        "Southern Great Plains",
        "Southwest",
    ]
    regions_dict = {}
    for item in regions_list:
        regions_dict[item + " 25th"] = ""
        regions_dict[item + " 50th"] = ""
        regions_dict[item + " 75th"] = ""
    header_list = [x for x in regions_dict]
    table_dict = {}
    for item in metrics_dict:
        table_dict[item] = regions_dict.copy()
    for item in metrics_dict:
        filepath = os.path.join(output_path, metrics_dict[item][0])
        with open(filepath, "r") as data_in:
            data = json.load(data_in)
        for region in regions_list:
            if item.endswith("(%)"):
                table_dict[item][region + " 25th"] = round(
                    float(
                        data[region][metrics_dict[item][1]]["diff"]["relative"]["0.25"]
                    ),
                    2,
                )
                table_dict[item][region + " 50th"] = round(
                    float(
                        data[region][metrics_dict[item][1]]["diff"]["relative"]["0.5"]
                    ),
                    2,
                )
                table_dict[item][region + " 75th"] = round(
                    float(
                        data[region][metrics_dict[item][1]]["diff"]["relative"]["0.75"]
                    ),
                    2,
                )
            elif item.endswith("(C)"):
                table_dict[item][region + " 25th"] = round(
                    float(
                        data[region][metrics_dict[item][1]]["diff"]["absolute"]["0.25"]
                    ),
                    2,
                )
                table_dict[item][region + " 50th"] = round(
                    float(
                        data[region][metrics_dict[item][1]]["diff"]["absolute"]["0.5"]
                    ),
                    2,
                )
                table_dict[item][region + " 75th"] = round(
                    float(
                        data[region][metrics_dict[item][1]]["diff"]["absolute"]["0.75"]
                    ),
                    2,
                )
    csv_file = os.path.join(
        output_path, "iqr_table_{0}_{1}.csv".format(model_name, obs_name)
    )
    print("Writing", csv_file)
    with open(csv_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Metric"] + header_list)
        writer.writeheader()
        for name, details in table_dict.items():
            row = {"Metric": name}
            row.update(details)
            writer.writerow(row)
