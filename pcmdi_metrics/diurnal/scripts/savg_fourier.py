#!/usr/bin/env python

# Spatially vector-average pairs of lat/lon fields that store Fourier (amplitude, phase) values for the diurnal
# cycle of preciprecipitation. This version does not explicitly mask out areas where the diurnal cycle is weak,
# but such areas should count for little since the vector amplitudes there
# are small.


# This modifiction of ./savg_fourier.py has the PMP Parser "wrapped" around it, so it's executed with both input and
# output parameters specified in the Unix command line.
# ... but this version is designed to get land-sea masks for any model, not just MIROC5 and CCSM4.

# Charles Doutriaux                                     September 2017
# Curt Covey (from ./savg_fourierWrappedInOutCCSMandMIROC.py) June 2017
# Jiwoo Lee, July 2025, Modernized the code to use xarray


import collections
import glob
import json
import os

import numpy as np
import xarray as xr
import xcdat as xc  # noqa: F401

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.diurnal.common import P, monthname_d, populateStringConstructor
from pcmdi_metrics.io import (
    get_grid,
    get_latitude,
    get_latitude_bounds_key,
    get_latitude_key,
    get_longitude,
    get_longitude_bounds_key,
    get_longitude_key,
    xcdat_open,
)
from pcmdi_metrics.utils import create_land_sea_mask


def main():
    P.add_argument(
        "-j",
        "--outnamejson",
        type=str,
        dest="outnamejson",
        default="pr_%(month)_%(firstyear)-%(lastyear)_savg_DiurnalFourier.json",
        help="Output name for jsons",
    )

    P.add_argument("--lat1", type=float, default=-50.0, help="First latitude")
    P.add_argument("--lat2", type=float, default=50.0, help="Last latitude")
    P.add_argument("--lon1", type=float, default=0.0, help="First longitude")
    P.add_argument("--lon2", type=float, default=360.0, help="Last longitude")
    P.add_argument(
        "--region_name",
        type=str,
        default="TRMM",
        help="name for the region of interest",
    )

    P.add_argument(
        "-t",
        "--filename_template",
        default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_S.nc",
        help="template for getting at amplitude files",
    )
    P.add_argument(
        "--filename_template_tS",
        default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_tS.nc",
        help="template for phase files",
    )
    P.add_argument(
        "--filename_template_sftlf",
        default="cmip5.%(model).%(experiment).r0i0p0.fx.atm.fx.sftlf.%(version).latestX.xml",
        help="template for sftlf file names",
    )
    P.add_argument("--model", default="*")
    P.add_argument(
        "--cmec",
        dest="cmec",
        action="store_true",
        default=False,
        help="Use to save metrics in CMEC JSON format",
    )
    P.add_argument(
        "--no_cmec",
        dest="cmec",
        action="store_false",
        default=False,
        help="Use to disable saving metrics in CMEC JSON format",
    )

    args = P.get_parameter()
    month = args.month
    monthname = monthname_d[month]
    # startyear = args.firstyear
    # finalyear = args.lastyear
    # years = "%s-%s" % (startyear, finalyear)  # noqa: F841
    cmec = args.cmec

    print("Specifying latitude / longitude domain of interest ...")
    # TRMM (observed) domain:
    latrange = (args.lat1, args.lat2)
    lonrange = (args.lon1, args.lon2)

    # region = cdutil.region.domain(latitude=latrange, longitude=lonrange)

    if args.region_name == "":
        region_name = f"{latrange[0]:g}_{latrange[1]:g}&{lonrange[0]:g}_{lonrange[1]:g}"
    else:
        region_name = args.region_name
    region = f"lat {latrange[0]:g} to {latrange[1]:g} and lon {lonrange[0]:g} to {lonrange[1]:g}"
    # Amazon basin:
    # latrange = (-15.0,  -5.0)
    # lonrange = (285.0, 295.0)

    # Functions to convert phase between angle-in-radians and hours, for
    # either a 12- or 24-hour clock, i.e. for clocktype = 12 or 24:

    def hrs_to_rad(hours, clocktype):
        return 2 * np.pi * hours / clocktype

    def rad_to_hrs(phase, clocktype):
        return phase * clocktype / 2 / np.pi

    def vectoravg(hr1, hr2, clocktype):
        "Function to test vector-averaging of two time values:"
        sin_avg = (
            np.sin(hrs_to_rad(hr1, clocktype)) + np.sin(hrs_to_rad(hr2, clocktype))
        ) / 2
        cos_avg = (
            np.cos(hrs_to_rad(hr1, clocktype)) + np.cos(hrs_to_rad(hr2, clocktype))
        ) / 2
        return rad_to_hrs(np.arctan2(sin_avg, cos_avg), clocktype)

    def spacevavg(tvarb1, tvarb2, sftlf, model):
        """
        Given a "root filename" and month/year specifications, vector-average lat/lon arrays in an (amplitude, phase)
        pair of input data files. Each input data file contains diurnal (24h), semidiurnal (12h) and terdiurnal (8h)
        Fourier harmonic components of the composite mean day/night cycle.

        Vector-averaging means we consider the input data to be readings on an 8-, 12- or 24-hour clock and separately
        average the Cartesian components (called "cosine" and "sine" below). Then the averaged components are combined
        back into amplitude and phase values and returned.

        Space-averaging is done globally, as well as separately for land and ocean areas.
        """

        glolf = spatial_average(sftlf)
        lat = get_latitude(sftlf)
        lon = get_longitude(sftlf)
        print("  Global mean land fraction = %5.3f" % glolf)
        outD = {}  # Output dictionary to be returned by this function
        harmonics = [1, 2, 3]
        for harmonic in harmonics:
            ampl = tvarb1[harmonic - 1]
            tmax = tvarb2[harmonic - 1]
            # print ampl[:, :]
            # print tmax[:, :]
            clocktype = 24 / harmonic
            cosine = np.cos(hrs_to_rad(tmax, clocktype)) * ampl  # X-component
            sine = np.sin(hrs_to_rad(tmax, clocktype)) * ampl  # Y-component

            print("Area-averaging globally, over land only, and over ocean only ...")
            # Average Cartesian components ...
            cos_avg_glo = spatial_average(cosine, lat=lat, lon=lon)
            sin_avg_glo = spatial_average(sine, lat=lat, lon=lon)
            cos_avg_lnd = spatial_average(cosine * sftlf.to_numpy(), lat=lat, lon=lon)
            sin_avg_lnd = spatial_average(sine * sftlf.to_numpy(), lat=lat, lon=lon)
            cos_avg_ocn = cos_avg_glo - cos_avg_lnd
            sin_avg_ocn = sin_avg_glo - sin_avg_lnd
            # ... normalized by land-sea fraction:
            cos_avg_lnd /= glolf
            sin_avg_lnd /= glolf
            cos_avg_ocn /= 1 - glolf
            sin_avg_ocn /= 1 - glolf
            # Amplitude and phase:
            # * 86400 Convert kg/m2/s -> mm/d?
            amp_avg_glo = np.sqrt(sin_avg_glo**2 + cos_avg_glo**2)
            # * 86400 Convert kg/m2/s -> mm/d?
            amp_avg_lnd = np.sqrt(sin_avg_lnd**2 + cos_avg_lnd**2)
            # * 86400 Convert kg/m2/s -> mm/d?
            amp_avg_ocn = np.sqrt(sin_avg_ocn**2 + cos_avg_ocn**2)
            pha_avg_glo = np.remainder(
                rad_to_hrs(np.arctan2(sin_avg_glo, cos_avg_glo), clocktype), clocktype
            )
            pha_avg_lnd = np.remainder(
                rad_to_hrs(np.arctan2(sin_avg_lnd, cos_avg_lnd), clocktype), clocktype
            )
            pha_avg_ocn = np.remainder(
                rad_to_hrs(np.arctan2(sin_avg_ocn, cos_avg_ocn), clocktype), clocktype
            )
            if "CMCC-CM" in model:
                # print '** Correcting erroneous time recording in ', rootfname
                pha_avg_lnd -= 3.0
                pha_avg_lnd = np.remainder(pha_avg_lnd, clocktype)
            elif "BNU-ESM" in model or "CCSM4" in model or "CNRM-CM5" in model:
                # print '** Correcting erroneous time recording in ', rootfname
                pha_avg_lnd -= 1.5
                pha_avg_lnd = np.remainder(pha_avg_lnd, clocktype)
            print(
                "Converting singleton transient variables to plain floating-point numbers ..."
            )
            amp_avg_glo = float(amp_avg_glo)
            pha_avg_glo = float(pha_avg_glo)
            amp_avg_lnd = float(amp_avg_lnd)
            pha_avg_lnd = float(pha_avg_lnd)
            amp_avg_ocn = float(amp_avg_ocn)
            pha_avg_ocn = float(pha_avg_ocn)
            print(
                f"{monthname} {harmonic}-harmonic amplitude, phase = {amp_avg_glo:7.3f} mm/d, {pha_avg_glo:7.3f} hrsLST averaged globally"
            )
            print(
                f"{monthname} {harmonic}-harmonic amplitude, phase = {amp_avg_lnd:7.3f} mm/d, {pha_avg_lnd:7.3f} hrsLST averaged over land"
            )
            print(
                f"{monthname} {harmonic}-harmonic amplitude, phase = {amp_avg_ocn:7.3f} mm/d, {pha_avg_ocn:7.3f} hrsLST averaged over ocean"
            )
            # Sub-dictionaries, one for each harmonic component:
            outD["harmonic" + str(harmonic)] = {}
            outD["harmonic" + str(harmonic)]["amp_avg_lnd"] = amp_avg_lnd
            outD["harmonic" + str(harmonic)]["pha_avg_lnd"] = pha_avg_lnd
            outD["harmonic" + str(harmonic)]["amp_avg_ocn"] = amp_avg_ocn
            outD["harmonic" + str(harmonic)]["pha_avg_ocn"] = pha_avg_ocn
        return outD

    print("Preparing to write output to JSON file ...")
    os.makedirs(args.results_dir, exist_ok=True)
    jsonFile = populateStringConstructor(args.outnamejson, args)
    jsonFile.month = monthname

    jsonname = os.path.join(os.path.abspath(args.results_dir), jsonFile())

    if not os.path.exists(jsonname) or args.append is False:
        print("Initializing dictionary of statistical results ...")
        stats_dic = {}
        metrics_dictionary = collections.OrderedDict()
    else:
        with open(jsonname) as f:
            metrics_dictionary = json.load(f)
            stats_dic = metrics_dictionary["RESULTS"]

    OUT = pcmdi_metrics.io.base.Base(
        os.path.abspath(args.results_dir), os.path.basename(jsonname)
    )
    egg_pth = resources.resource_path()
    disclaimer = open(os.path.join(egg_pth, "disclaimer.txt")).read()
    metrics_dictionary["DISCLAIMER"] = disclaimer
    metrics_dictionary["REFERENCE"] = (
        "The statistics in this file are based on Covey et al., J Climate 2016"
    )

    # Accumulate output from each model (or observed) data source in the
    # Python dictionary.
    template_S = populateStringConstructor(args.filename_template, args)
    template_S.month = monthname
    template_tS = populateStringConstructor(args.filename_template_tS, args)
    template_tS.month = monthname
    template_sftlf = populateStringConstructor(args.filename_template_sftlf, args)
    template_sftlf.month = monthname

    print("TEMPLATE:", template_S())
    files_S = glob.glob(os.path.join(args.modpath, template_S()))
    print(files_S)
    for file_S in files_S:
        print(f"Reading Amplitude from {file_S} ...")
        reverted = template_S.reverse(os.path.basename(file_S))
        model = reverted["model"]
        try:
            template_tS.model = model
            template_sftlf.model = model

            ds_S = xcdat_open(file_S).bounds.add_missing_bounds()
            ds_S_region = ds_S.sel(
                {
                    get_latitude_key(ds_S): slice(latrange[0], latrange[1]),
                    get_longitude_key(ds_S): slice(lonrange[0], lonrange[1]),
                }
            )
            S = ds_S_region["S"]

            print(f"Reading Phase from {os.path.join(args.modpath, template_tS())} ...")

            ts_S = xcdat_open(
                os.path.join(args.modpath, template_tS())
            ).bounds.add_missing_bounds()
            ts_S_region = ts_S.sel(
                {
                    get_latitude_key(ts_S): slice(latrange[0], latrange[1]),
                    get_longitude_key(ts_S): slice(lonrange[0], lonrange[1]),
                }
            )
            tS = ts_S_region["tS"]

            print(
                f"Reading sftlf from {os.path.join(args.modpath, template_sftlf())} ..."
            )
            try:
                sftlf_fnm = glob.glob(os.path.join(args.modpath, template_sftlf()))[0]
                sftlf_ds = xcdat_open(sftlf_fnm)
                # if max of sftlf is 100, convert to fraction:
                if sftlf_ds["sftlf"].max() > 100:
                    print("Converting sftlf to fraction ...")
                    sftlf = sftlf_ds["sftlf"] / 100.0
                else:
                    print("sftlf is already in fraction ...")
                    sftlf = sftlf_ds["sftlf"]

            except BaseException as err:
                print(f"Failed reading sftlf from file (error was: {err})")
                print("Creating one for you")
                sftlf = generate_landsea_mask(ds_S)

            # Select the region of interest
            sftlf_region = sftlf.sel(
                {
                    get_latitude_key(sftlf): slice(latrange[0], latrange[1]),
                    get_longitude_key(sftlf): slice(lonrange[0], lonrange[1]),
                }
            )

            if model not in stats_dic:
                stats_dic[model] = {region_name: spacevavg(S, tS, sftlf_region, model)}
            else:
                stats_dic[model].update(
                    {region_name: spacevavg(S, tS, sftlf_region, model)}
                )
            print(stats_dic)
        except Exception as err:
            print(f"Failed for model {model} with error: {err}")

    # Write output to JSON file.
    metrics_dictionary["RESULTS"] = stats_dic
    rgmsk = metrics_dictionary.get("RegionalMasking", {})
    nm = region_name
    # region.id = nm
    rgmsk[nm] = {"id": nm, "domain": region}
    metrics_dictionary["RegionalMasking"] = rgmsk
    OUT.write(
        metrics_dictionary,
        json_structure=["model", "domain", "harmonic", "statistic"],
        indent=4,
        separators=(",", ": "),
    )
    if cmec:
        print("Writing cmec file")
        OUT.write_cmec(indent=4, separators=(",", ": "))
    print("done")


def spatial_average(data, lat=None, lon=None):
    if isinstance(data, xr.DataArray):
        # if data type is xarray.DataArray, da= data
        da = data
    else:
        # if data type is numpy.ndarray, convert it to xarray.DataArray
        # This requires lat and lon coordinates
        if lat is None or lon is None:
            raise ValueError("lat and lon must be provided for numpy.ndarray input")
        coords = {lat.name: lat, lon.name: lon}
        da = xr.DataArray(data, coords=coords, dims=[lat.name, lon.name])

    # if da does not have name, set it to 'data'
    if da.name is None:
        da.name = "data"
    ds = da.to_dataset()
    ds = ds.bounds.add_missing_bounds()
    ds_avg = ds.spatial.average(da.name)
    return ds_avg[da.name]


def generate_landsea_mask(ds):
    """
    Generate a land-sea mask for the given dataset.
    """
    # Ensure the dataset has the correct latitude and longitude keys
    ds_tmp = ds.copy(deep=True)
    if get_latitude_key(ds_tmp) != "lat":
        ds_tmp = ds_tmp.rename({get_latitude_key(ds_tmp): "lat"})
    if get_longitude_key(ds_tmp) != "lon":
        ds_tmp = ds_tmp.rename({get_longitude_key(ds_tmp): "lon"})
    if get_latitude_bounds_key(ds_tmp) != "lat_bounds":
        ds_tmp = ds_tmp.rename({get_latitude_bounds_key(ds_tmp): "lat_bounds"})
        ds_tmp["lat"].attrs["bounds"] = "lat_bounds"
    if get_longitude_bounds_key(ds_tmp) != "lon_bounds":
        ds_tmp = ds_tmp.rename({get_longitude_bounds_key(ds_tmp): "lon_bounds"})
        ds_tmp["lon"].attrs["bounds"] = "lon_bounds"

    grid = get_grid(ds_tmp)
    sftlf = create_land_sea_mask(grid, method="pcmdi")

    return sftlf


if __name__ == "__main__":
    main()
