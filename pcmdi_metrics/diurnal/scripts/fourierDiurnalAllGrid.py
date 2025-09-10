#!/usr/bin/env python

# This modifiction of ./fourierDiurnalAllGrid.py has the PMP Parser "wrapped" around it, so it's executed
# with input parameters in the Unix command line. For example:

# ---> python fourierDiurnalAllGridWrapped.py -m7

# Charles Doutriaux                     September 2017
# Curt Covey                                        January 2017

# -------------------------------------------------------------------------

import glob
import os

import numpy as np
import xarray as xr

from pcmdi_metrics.diurnal.common import P, monthname_d, populateStringConstructor
from pcmdi_metrics.diurnal.fourierFFT import fastAllGridFT
from pcmdi_metrics.io import (
    get_latitude,
    get_latitude_key,
    get_longitude,
    get_longitude_key,
    xcdat_open,
)


def main():
    P.add_argument(
        "-t",
        "--filename_template",
        default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_avg.nc",
        help="template for file names containing diurnal average",
    )
    P.add_argument("--model", default="*")
    P.add_argument(
        "--filename_template_LST",
        default="pr_%(model)_LocalSolarTimes.nc",
        help="template for file names point to Local Solar Time Files",
    )

    args = P.get_parameter()
    month = args.month
    monthname = monthname_d[month]
    startyear = args.firstyear
    finalyear = args.lastyear
    yearrange = f"{startyear}-{finalyear}"

    template = populateStringConstructor(args.filename_template, args)
    template.month = monthname
    template_LST = populateStringConstructor(args.filename_template_LST, args)
    template_LST.month = monthname

    LSTfiles = glob.glob(os.path.join(args.modpath, template_LST()))

    print("modpath ", args.modpath)
    print("filename_template ", args.filename_template)
    print("filename_template_LST ", args.filename_template_LST)

    print("LSTFILES:", LSTfiles)
    print("TMPL", template_LST())
    for LSTfile in LSTfiles:
        print("Reading %s ..." % LSTfile, os.path.basename(LSTfile))
        reverted = template_LST.reverse(os.path.basename(LSTfile))
        model = reverted["model"]
        print("====================")
        print(model)
        print("====================")
        template.model = model
        avgfile = template()
        print("Reading time series of mean diurnal cycle ...")
        ds_f = xcdat_open(LSTfile)
        ds_g = xcdat_open(os.path.join(args.modpath, avgfile))
        LSTs = ds_f["LST"]
        avgs = ds_g["diurnalmean"]
        print("Input shapes: ", LSTs.shape, avgs.shape)
        print("Getting latitude and longitude coordinates.")
        # Any file with grid info will do, so use Local Standard Times file:
        modellats = get_latitude(LSTs)
        modellons = get_longitude(LSTs)
        lon_key = get_longitude_key(LSTs)
        lat_key = get_latitude_key(LSTs)

        print("Taking fast Fourier transform of the mean diurnal cycle ...")
        cycmean, maxvalue, tmax = fastAllGridFT(avgs, LSTs)
        print("  Output:")
        print("    cycmean", cycmean.shape)
        print("    maxvalue", maxvalue.shape)
        print("    tmax", tmax.shape)
        print("    cycmean type:", type(cycmean))
        print("    maxvalue type:", type(maxvalue))
        print("    tmax type:", type(tmax))

        print('"Re-decorating" Fourier harmonics with grid info, etc., ...')
        harmonics = np.arange(3)

        cycmean = xr.DataArray(
            cycmean,
            coords={lat_key: modellats, lon_key: modellons},
            dims=[lat_key, lon_key],
        )
        maxvalue = xr.DataArray(
            maxvalue,
            coords={"harmonic": harmonics, lat_key: modellats, lon_key: modellons},
            dims=["harmonic", lat_key, lon_key],
        )
        tmax = xr.DataArray(
            tmax,
            coords={"harmonic": harmonics, lat_key: modellats, lon_key: modellons},
            dims=["harmonic", lat_key, lon_key],
        )

        cycmean.name = "tmean"
        maxvalue.name = "S"
        tmax.name = "tS"

        cycmean.attrs.update({"units": "mm / day"})
        maxvalue.attrs.update({"units": "mm / day"})
        tmax.attrs.update({"units": "GMT"})

        print("  After decorating:")
        print("    cycmean", cycmean.shape)
        print("    maxvalue", maxvalue.shape)
        print("    tmax", tmax.shape)
        print("    cycmean type:", type(cycmean))
        print("    maxvalue type:", type(maxvalue))
        print("    tmax type:", type(tmax))

        print("... and writing to netCDF.")

        cycmean.to_netcdf(
            os.path.join(
                args.results_dir,
                "pr_" + model + "_" + monthname + "_" + yearrange + "_tmean.nc",
            )
        )
        maxvalue.to_netcdf(
            os.path.join(
                args.results_dir,
                "pr_" + model + "_" + monthname + "_" + yearrange + "_S.nc",
            )
        )
        tmax.to_netcdf(
            os.path.join(
                args.results_dir,
                "pr_" + model + "_" + monthname + "_" + yearrange + "_tS.nc",
            )
        )

        ds_f.close()
        ds_g.close()


if __name__ == "__main__":
    main()
