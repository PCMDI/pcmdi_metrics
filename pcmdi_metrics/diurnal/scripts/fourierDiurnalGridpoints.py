#!/usr/bin/env python

# For a few selected gridpoints, read previously computed composite-mean and standard deviation of the diurnal
# cycle, compute Fourier harmonics and write output in a form suitable for Mathematica. The Fourier output of
# this script should match the output fields of
# ./fourierDiurnalAllGrid*.py at the selected gridpoints

# Curt Covey, June 2017
# Jiwoo Lee, July 2025, Modernized the code to use xarray


# (from ~/CMIP5/Tides/OtherFields/Models/CMCC-CM_etal/old_fourierDiurnalGridpoints.py)
# -------------------------------------------------------------------------

import glob
import os

import numpy as np

from pcmdi_metrics.diurnal.common import P, monthname_d, populateStringConstructor
from pcmdi_metrics.diurnal.fourierFFT import fastFT
from pcmdi_metrics.io import get_latitude_key, get_longitude_key, xcdat_open


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
    P.add_argument(
        "--filename_template_std",
        default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_std.nc",
        help="template for file names containing diurnal std",
    )
    P.add_argument(
        "-l",
        "--lats",
        nargs="*",
        default=[31.125, 31.125, 36.4, 5.125, 45.125, 45.125],
        help="latitudes",
    )
    P.add_argument(
        "-L",
        "--lons",
        nargs="*",
        default=[-83.125, 111.145, -97.5, 147.145, -169.145, -35.145],
        help="longitudes",
    )
    P.add_argument(
        "-A",
        "--outnameasc",
        type=str,
        dest="outnameasc",
        default="pr_%(month)_%(firstyear)-%(lastyear)_fourierDiurnalGridPoints.asc",
        help="Output name for ascs",
    )
    args = P.get_parameter()
    month = args.month
    monthname = monthname_d[month]
    # startyear = args.firstyear
    # finalyear = args.lastyear
    # yearrange = "%s-%s" % (startyear, finalyear)  # noqa: F841

    template = populateStringConstructor(args.filename_template, args)
    template.month = monthname
    template_std = populateStringConstructor(args.filename_template_std, args)
    template_std.month = monthname
    template_LST = populateStringConstructor(args.filename_template_LST, args)
    template_LST.month = monthname

    LSTfiles = glob.glob(os.path.join(args.modpath, template_LST()))
    print("LSTFILES:", LSTfiles)
    print("TMPL", template_LST())

    ascFile = populateStringConstructor(args.outnameasc, args)
    ascFile.month = monthname
    ascname = os.path.join(os.path.abspath(args.results_dir), ascFile())

    os.makedirs(os.path.dirname(ascname), exist_ok=True)
    fasc = open(ascname, "w")

    gridptlats = [float(x) for x in args.lats]
    gridptlons = [float(x) for x in args.lons]
    nGridPoints = len(gridptlats)
    assert len(gridptlons) == nGridPoints

    # gridptlats = [-29.125, -5.125,   45.125,  45.125]
    # gridptlons = [-57.125, 75.125, -169.145, -35.145]
    # Gridpoints for JULY    samples in Figure 4 of Covey et al., JClimate 29: 4461 (2016):
    # nGridPoints = 6
    # gridptlats = [ 31.125,  31.125,  36.4,   5.125,   45.125,  45.125]
    # gridptlons = [-83.125, 111.145, -97.5, 147.145, -169.145, -35.145]

    N = 8  # Number of timepoints in a 24-hour cycle
    for LSTfile in LSTfiles:
        print(f"Reading {LSTfile} ... {os.path.basename(LSTfile)}", file=fasc)
        reverted = template_LST.reverse(os.path.basename(LSTfile))
        model = reverted["model"]
        print("====================", file=fasc)
        print(model, file=fasc)
        print("====================", file=fasc)
        template.model = model
        avgfile = template()
        template_std.model = model
        stdfile = template_std()
        print("Reading time series of mean diurnal cycle ...", file=fasc)

        ds_f = xcdat_open(LSTfile)
        ds_g = xcdat_open(os.path.join(args.modpath, avgfile))
        ds_h = xcdat_open(os.path.join(args.modpath, stdfile))
        LSTs = ds_f["LST"]

        print("Input shapes: ", LSTs.shape, file=fasc)

        lat_key = get_latitude_key(LSTs)
        lon_key = get_longitude_key(LSTs)

        # Gridpoints selected above may be offset slightly from points in full
        # grid ...
        closestlats = np.zeros(nGridPoints)
        closestlons = np.zeros(nGridPoints)
        pointLSTs = np.zeros((nGridPoints, N))
        avgvalues = np.zeros((nGridPoints, N))
        stdvalues = np.zeros((nGridPoints, N))
        # ... in which case, just pick the closest full-grid point:
        for i in range(nGridPoints):
            print(
                f"   (lat, lon) = ({gridptlats[i]:8.3f}, {gridptlons[i]:8.3f})",
                file=fasc,
            )
            closestlats[i] = gridptlats[i]
            closestlons[i] = gridptlons[i] % 360
            print(
                f"   Closest (lat, lon) for gridpoint = ({closestlats[i]:8.3f}, {closestlons[i]:8.3f})",
                file=fasc,
            )
            # Time series for selected grid point:
            avgvalues[i] = ds_g["diurnalmean"].sel(
                {lat_key: closestlats[i], lon_key: closestlons[i]}, method="nearest"
            )
            stdvalues[i] = ds_h["diurnalstd"].sel(
                {lat_key: closestlats[i], lon_key: closestlons[i]}, method="nearest"
            )
            pointLSTs[i] = ds_f["LST"].sel(
                {lat_key: closestlats[i], lon_key: closestlons[i]}, method="nearest"
            )
            print(" ", file=fasc)
        ds_f.close()
        ds_g.close()
        ds_h.close()
        # Print results for input to Mathematica.
        if monthname == "Jan":
            # In printed output, numbers for January data follow 0-5 for July data,
            # hence begin with 6.
            deltaI = 6
        else:
            deltaI = 0
        prefix = args.modpath
        for i in range(nGridPoints):
            print(
                f"For gridpoint {i} at {gridptlats[i]:5.1f} deg latitude, {gridptlons[i]:6.1f} deg longitude ...",
                file=fasc,
            )
            print("   Local Solar Times are:", file=fasc)
            print(f"{prefix}LST{i + deltaI} = {{", file=fasc)
            print(", ".join(f"{v:5.3f}" for v in pointLSTs[i]), end="", file=fasc)
            print("};", file=fasc)
            print("   Mean values for each time-of-day are:", file=fasc)
            print(f"{prefix}mean{i + deltaI} = {{", file=fasc)
            print(", ".join(f"{v:5.3f}" for v in avgvalues[i]), end="", file=fasc)
            print("};", file=fasc)
            print("   Standard deviations for each time-of-day are:", file=fasc)
            print(f"{prefix}std{i + deltaI} = {{", file=fasc)
            print(", ".join(f"{v:6.4f}" for v in stdvalues[i]), end="", file=fasc)
            print("};", file=fasc)
            print(" ", file=fasc)

        # Take fast Fourier transform of the overall multi-year mean diurnal cycle.
        print("**************   ", avgvalues[0][0], file=fasc)
        cycmean, maxvalue, tmax = fastFT(avgvalues, pointLSTs)
        print("**************   ", avgvalues[0][0], file=fasc)
        # Print Fourier harmonics:
        for i in range(nGridPoints):
            print(
                f"For gridpoint {i} at {gridptlats[i]:5.1f} deg latitude, {gridptlons[i]:6.1f} deg longitude ...",
                file=fasc,
            )
            print(f"  Mean value over cycle = {cycmean[i]:6.2f}", file=fasc)
            print(
                f"  Diurnal     maximum   = {maxvalue[i, 0]:6.2f} at {tmax[i, 0] % 24:6.2f} hr Local Solar Time.",
                file=fasc,
            )
            print(
                f"  Semidiurnal maximum   = {maxvalue[i, 1]:6.2f} at {tmax[i, 1] % 24:6.2f} hr Local Solar Time.",
                file=fasc,
            )
            print(
                f"  Terdiurnal  maximum   = {maxvalue[i, 2]:6.2f} at {tmax[i, 2] % 24:6.2f} hr Local Solar Time.",
                file=fasc,
            )

    print("Results sent to:", ascname)


if __name__ == "__main__":
    main()
