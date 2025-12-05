#!/usr/bin/env python
import datetime
import json
import os
import sys

import dask
import numpy as np
import xarray as xr

from pcmdi_metrics.io import get_latitude_key, get_longitude_key, get_time_bounds_key
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


# ------------------------------------
# Define region coverage in functions
# ------------------------------------

# NH


def central_arctic(ds, ds_var, xvar, yvar, pole):
    if (ds[xvar] > 180).any():  # 0 to 360 longitude
        mask = (
            (ds[yvar] > 80) & (ds[yvar] <= pole) & ((ds[xvar] > 240) | (ds[xvar] <= 90))
        ) | (
            (ds[yvar] > 65) & (ds[yvar] < pole) & ((ds[xvar] > 90) & (ds[xvar] <= 240))
        )
    else:  # -180 to 180 longitude
        mask = (
            (ds[yvar] > 80) & (ds[yvar] <= pole) & (ds[xvar] > -120) & (ds[xvar] <= 90)
        ) | (
            (ds[yvar] > 65) & (ds[yvar] < pole) & ((ds[xvar] > 90) | (ds[xvar] <= -120))
        )
    data_ca = ds[ds_var].where(mask, np.nan)
    return data_ca


def north_pacific(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360 longitude
        # North Pacific region: lat 45–65, lon 90–240
        mask = (ds[yvar] > 45) & (ds[yvar] <= 65) & (ds[xvar] > 90) & (ds[xvar] <= 240)
    else:  # -180 to 180 longitude
        # North Pacific region: lat 45–65, lon 90 to 180 and -180 to -120
        mask = (
            (ds[yvar] > 45) & (ds[yvar] <= 65) & ((ds[xvar] > 90) | (ds[xvar] <= -120))
        )
    data_np = ds[ds_var].where(mask, np.nan)
    return data_np


def north_atlantic(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360 longitude
        # Inclusion mask for North Atlantic
        mask_incl = (
            (ds[yvar] > 45) & (ds[yvar] <= 80) & ((ds[xvar] > 240) | (ds[xvar] <= 90))
        )
        # Exclusion mask for the small region
        mask_excl = (
            (ds[yvar] > 45) & (ds[yvar] <= 50) & (ds[xvar] > 30) & (ds[xvar] <= 60)
        )
    else:  # -180 to 180 longitude
        mask_incl = (
            (ds[yvar] > 45) & (ds[yvar] <= 80) & (ds[xvar] > -120) & (ds[xvar] <= 90)
        )
        mask_excl = (
            (ds[yvar] > 45) & (ds[yvar] <= 50) & (ds[xvar] > 30) & (ds[xvar] <= 60)
        )

    # Final mask: include North Atlantic, exclude small region
    final_mask = mask_incl & ~mask_excl
    data_na = ds[ds_var].where(final_mask, np.nan)
    return data_na


# SH


def south_atlantic(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360 longitude
        # South Atlantic: lat -90 to -55, lon 300–360 or 0–20
        mask = (
            (ds[yvar] > -90) & (ds[yvar] <= -55) & ((ds[xvar] > 300) | (ds[xvar] <= 20))
        )
    else:  # -180 to 180 longitude
        # South Atlantic: lat -90 to -55, lon -60 to 20
        mask = (
            (ds[yvar] > -90) & (ds[yvar] <= -55) & (ds[xvar] > -60) & (ds[xvar] <= 20)
        )
    data_sa = ds[ds_var].where(mask, np.nan)
    return data_sa


def south_pacific(ds, ds_var, xvar, yvar):
    if (ds[xvar] > 180).any():  # 0 to 360 longitude
        # South Pacific: lat -90 to -55, lon 90–300
        mask = (
            (ds[yvar] > -90) & (ds[yvar] <= -55) & (ds[xvar] > 90) & (ds[xvar] <= 300)
        )
    else:  # -180 to 180 longitude
        # South Pacific: lat -90 to -55, lon 90 to 180 and -180 to -60
        mask = (
            (ds[yvar] > -90) & (ds[yvar] <= -55) & ((ds[xvar] > 90) | (ds[xvar] <= -60))
        )
    data_sp = ds[ds_var].where(mask, np.nan)
    return data_sp


def indian_ocean(ds, ds_var, xvar, yvar):
    # Indian Ocean: lat -90 to -55, lon 20–90 (same for both conventions)
    mask = (ds[yvar] > -90) & (ds[yvar] <= -55) & (ds[xvar] > 20) & (ds[xvar] <= 90)
    data_io = ds[ds_var].where(mask, np.nan)
    return data_io


# Global


def arctic(ds, ds_var, xvar, yvar, pole=90.1):
    # Arctic region: lat > 45 up to the pole (default pole = 90.1)
    mask = (ds[yvar] > 45) & (ds[yvar] < pole)
    data_arctic = ds[ds_var].where(mask, np.nan)
    return data_arctic


def antarctic(ds, ds_var, xvar, yvar):
    # Antarctic region: lat <= -55
    mask = ds[yvar] <= -55
    data_antarctic = ds[ds_var].where(mask, np.nan)
    return data_antarctic


# Choose region function


def choose_region(region, ds, ds_var, xvar, yvar, pole=90.1):
    """
    Chooses region based on input region string.

    Parameters
    ----------
    region : str
        Region name. Options are: "arctic", "na", "ca", "np", "antarctic", "sa", "sp", "io".
    ds : xarray.Dataset
        Input dataset containing sea ice data.
    ds_var : str
        Variable name in the dataset representing sea ice data.
    xvar : str
        Name of the longitude coordinate variable.
    yvar : str
        Name of the latitude coordinate variable.
    pole : float
        Latitude value representing the pole (default is 90.1 for Arctic).

    Returns
    -------
    data_region : xarray.DataArray
        DataArray containing data for the specified region.
    """
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
    else:
        raise ValueError(f"Unknown region: {region}")


# ------------------------------------
# Define other functions
# ------------------------------------
def get_mask(ds, lon_key="lon", lat_key="lat"):
    mask = create_land_sea_mask(ds, lon_key=lon_key, lat_key=lat_key)
    # In mask, 0:ocean 1:land
    ds_mask = mask.to_dataset()
    return ds_mask


def get_total_extent(data, ds_area):
    xvar = get_longitude_key(data)
    coord_i, coord_j = get_xy_coords(data, xvar)
    total_extent = (data.where(data > 0.15) * ds_area).sum(
        (coord_i, coord_j), skipna=True
    )
    return total_extent


def get_clim(total_extent, ds_var, ds=None):
    # ds is a dataset that contains the dimensions
    # needed to turn total_extent into a dataset
    if ds is None:
        ds_new = total_extent
        ds_new = ds_new.unify_chunks()
    else:
        ds_new = to_ice_con_ds(total_extent, ds, ds_var)

    try:
        clim = ds_new.temporal.climatology(ds_var, freq="month")
    except IndexError:  # Issue with time bounds
        tbkey = get_time_bounds_key(ds_new)
        ds_new = ds_new.drop_vars(tbkey)
        ds_new = ds_new.bounds.add_missing_bounds()
        clim = ds_new.temporal.climatology(ds_var, freq="month")
    return clim


def get_mean(total_extent, ds_var, ds=None):
    # ds is a dataset that contains the dimensions
    # needed to turn total_extent into a dataset
    if ds is None:
        ds_new = total_extent
        ds_new = ds_new.unify_chunks()
    else:
        ds_new = to_ice_con_ds(total_extent, ds, ds_var)

    try:
        te_mean = ds_new.temporal.average(ds_var, weighted=True)
    except IndexError:  # Issue with time bounds
        tbkey = get_time_bounds_key(ds_new)
        ds_new = ds_new.drop_vars(tbkey)
        ds_new = ds_new.bounds.add_missing_bounds()
        te_mean = ds_new.temporal.average(ds_var, weighted=True)

    if isinstance(te_mean[ds_var].data, dask.array.core.Array):
        return te_mean[ds_var].data.compute().item()
    else:
        return te_mean[ds_var].data.item()


def process_by_region(ds, ds_var, ds_area, pole, debug_tag):
    regions_list = ["arctic", "antarctic", "ca", "na", "np", "sa", "sp", "io"]
    clims = {}
    means = {}
    xvar = get_longitude_key(ds)
    yvar = get_latitude_key(ds)
    for region in regions_list:
        data = choose_region(region, ds, ds_var, xvar, yvar, pole)
        data.to_netcdf("tmp/debug_sea_ice_region_" + region + "_" + debug_tag + ".nc")
        total_extent = get_total_extent(data, ds_area)
        clim = get_clim(total_extent, ds_var, ds)
        te_mean = get_mean(total_extent, ds_var, ds)
        clims[region] = clim
        means[region] = te_mean
        del data
    return clims, means


def get_area(data, ds_area):
    xvar = get_longitude_key(data)
    coord_i, coord_j = get_xy_coords(data, xvar)
    total_area = (data * ds_area).sum((coord_i, coord_j), skipna=True)
    if isinstance(total_area.data, dask.array.core.Array):
        ta_mean = total_area.data.compute().item()
    else:
        ta_mean = total_area.data.item()
    return ta_mean


def get_ocean_area_for_regions(ds_org, ds_var, area_val, pole):
    # Invert land/sea mask: 0:land 1:ocean
    ds = ds_org.copy()
    ds[ds_var] = 1 - ds[ds_var]

    regions_list = ["arctic", "antarctic", "ca", "na", "np", "sa", "sp", "io"]
    areas = {}
    # Only want spatial slice
    if "time" in ds:
        print("len(ds.time):", len(ds.time))
        ds = ds.isel({"time": 0})
        # ds = ds.isel({"time": 5})
    xvar = get_longitude_key(ds)
    yvar = get_latitude_key(ds)
    for region in regions_list:
        data = choose_region(region, ds, ds_var, xvar, yvar, pole)
        tmp = get_area(data, area_val)
        areas[region] = tmp
        if tmp > 0:
            print(f"Area of {region}: {tmp} (area_val: {area_val})")
        del data
    return areas


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
    tbkey = get_time_bounds_key(ds)
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
    else:
        raise ValueError("Error: realization must be a string or list of strings")

    return find_all_realizations, realizations


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
        lon_j = get_longitude_key(ds)
        lon_i = get_latitude_key(ds)
    else:
        raise ValueError("Unexpected number of dimensions for coordinate variable")
    return lon_i, lon_j
