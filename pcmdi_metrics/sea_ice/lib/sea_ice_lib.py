#!/usr/bin/env python
import datetime
import json
import os
import sys

import dask
import numpy as np
import xarray as xr
import xcdat as xc

from pcmdi_metrics.io import xcdat_dataset_io, xcdat_openxml


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


# ------------------------------------
# Define region coverage in functions
# ------------------------------------
def central_arctic(ds, ds_var, xvar, yvar, pole):
    if (ds[xvar] > 180).any():  # 0 to 360
        data_ca1 = ds[ds_var].where(
            (
                (ds[yvar] > 80)
                & (ds[yvar] <= pole)
                & ((ds[xvar] > 240) | (ds[xvar] <= 90))
            ),
            0,
        )
        data_ca2 = ds[ds_var].where(
            ((ds[yvar] > 65) & (ds[yvar] < pole))
            & ((ds[xvar] > 90) & (ds[xvar] <= 240)),
            0,
        )
        data_ca = data_ca1 + data_ca2
    else:  # -180 to 180
        data_ca1 = ds[ds_var].where(
            (
                (ds[yvar] > 80)
                & (ds[yvar] <= pole)
                & (ds[xvar] > -120)
                & (ds[xvar] <= 90)
            ),
            0,
        )
        data_ca2 = ds[ds_var].where(
            ((ds[yvar] > 65) & (ds[yvar] < pole))
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


def arctic(ds, ds_var, xvar, yvar, pole):
    data_arctic = ds[ds_var].where((ds[yvar] > 0) & (ds[yvar] < pole), 0)
    return data_arctic


def antarctic(ds, ds_var, xvar, yvar):
    data_antarctic = ds[ds_var].where(ds[yvar] < 0, 0)
    return data_antarctic


def choose_region(region, ds, ds_var, xvar, yvar, pole):
    if region == "arctic":
        return arctic(ds, ds_var, xvar, yvar, pole)
    elif region == "na":
        return north_atlantic(ds, ds_var, xvar, yvar)
    elif region == "ca":
        return central_arctic(ds, ds_var, xvar, yvar, pole)
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


def get_clim(total_extent, ds_var, ds=None):
    # ds is a dataset that contains the dimensions
    # needed to turn total_extent into a dataset
    if ds is None:
        ds_new = total_extent
    else:
        ds_new = to_ice_con_ds(total_extent, ds, ds_var)
    try:
        clim = ds_new.temporal.climatology(ds_var, freq="month")
    except IndexError:  # Issue with time bounds
        tbkey = xcdat_dataset_io.get_time_bounds_key(ds_new)
        ds_new = ds_new.drop_vars(tbkey)
        ds_new = ds_new.bounds.add_missing_bounds()
        clim = ds_new.temporal.climatology(ds_var, freq="month")
    return clim


def process_by_region(ds, ds_var, ds_area, pole):
    regions_list = ["arctic", "antarctic", "ca", "na", "np", "sa", "sp", "io"]
    clims = {}
    means = {}
    for region in regions_list:
        xvar = find_lon(ds)
        yvar = find_lat(ds)
        data = choose_region(region, ds, ds_var, xvar, yvar, pole)
        total_extent, te_mean = get_total_extent(data, ds_area)
        clim = get_clim(total_extent, ds_var, ds)
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
        stat = np.sum(((dm.data - do.data) ** 2)) / len(dm)
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
    tbkey = xcdat_dataset_io.get_time_bounds_key(ds)
    ds = xr.Dataset(data_vars={obs_var: da, tbkey: ds[tbkey]}, coords={"time": ds.time})
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
