#!/usr/bin/env python

# From a high frequency (hourly, 3-hourly, ...) time series, compute daily means for one month over one or more years at
# each gridpoint, then their standard deviation. This version processes
# CMIP5 historical precipitation for years 1999-2005.

# Charles Doutriaux     September 2017
# Curt Covey            July 2017   (from ./old_computeDailyMeans.py)
# Jiwoo Lee             July 2025   Modernized the code to use xarray

# This version has the PMP Parser "wrapped" around it, so it can be executed with input parameters in the command line
# ---> computeStdDailyMeansWrapped.py -i data -m7 --realization="r1i1p1" -t "sample_data_%(variable)_%(model).nc"

import datetime
import glob
import multiprocessing as mp
import os

import cftime
import xarray as xr

from pcmdi_metrics.diurnal.common import (
    INPUT,
    P,
    monthname_d,
    populateStringConstructor,
)
from pcmdi_metrics.io import (
    get_calendar,
    get_latitude_key,
    get_longitude_key,
    xcdat_open,
)
from pcmdi_metrics.utils import cdp_run


def main():
    def compute(params, debug=False):
        fileName = params.fileName
        startyear = params.args.firstyear
        finalyear = params.args.lastyear
        month = params.args.month
        monthname = params.monthname
        varbname = params.varname
        template = populateStringConstructor(args.filename_template, args)
        template.variable = varbname

        dataname = params.args.model
        if dataname is None or dataname.find("*") != -1:
            # model not passed or passed as *
            reverted = template.reverse(os.path.basename(fileName))
            dataname = reverted["model"]
        print(f"Data source: {dataname}")
        print(f"Opening {fileName}")
        if dataname not in args.skip:
            try:
                print(f"Data source: {dataname}")
                print(f"Opening {fileName}")
                ds = xcdat_open(fileName)

                # Find calendar type of ds
                cftime_class = get_cftime_class(ds)
                iYear = 0
                dmean = None
                for year in range(startyear, finalyear + 1):
                    print(f"Year {year}:")
                    startTime = cftime_class(year, month, 1)
                    print("Start time:", startTime)
                    # Last possible second to get all tpoints
                    finishtime = add_one_month(startTime)
                    print("Finish time:", finishtime)
                    print(
                        f"Reading {varbname} from {fileName} for time interval {startTime} to {finishtime}"
                    )
                    # variable stores data for current year's month.
                    ds_year = ds.sel(
                        time=(ds.time >= startTime) & (ds.time < finishtime)
                    )
                    # *HARD-CODES conversion from kg/m2/sec to mm/day.
                    tvarb = ds_year[varbname] * 86400
                    # The following tasks need to be done only once, extracting
                    # metadata from first-year file:
                    tc = tvarb.time.values
                    current = tc[0]
                    if debug:
                        print("Current time:", current)
                        print("Current month:", current.month)
                        print("month:", month)

                    while current.month == month:
                        end = add_one_day(current)
                        if debug:
                            print("in the while loop, current:", current)
                            print("End time:", end)

                        sub = tvarb.sel(
                            time=(tvarb.time >= current) & (tvarb.time < end)
                        )
                        if debug:
                            print("Subsetting time:", current, "to", end)
                            print("sub.time.values:\n", sub.time.values)
                            print("sub.shape", sub.shape)

                        # Compute mean over the first dimension (i.e., 'time')
                        tmp = sub.mean(dim=sub.dims[0], skipna=True)

                        # Add a new 'time' dimension of size 1
                        tmp = tmp.expand_dims(dim={"time": [current]})

                        # Append to dmean
                        if dmean is None:
                            dmean = tmp
                        else:
                            dmean = xr.concat([dmean, tmp], dim="time")

                        current = end
                    iYear += 1

                print("type(dmean):", type(dmean))
                print("dmean.shape:", dmean.shape)

                # Compute standard deviation over time dimension
                # Assuming 'time' is the first dimension of dmean
                stdvalues = dmean.std(dim="time", skipna=True)
                stdvalues.name = "dailySD"  # Equivalent to stdvalues.id

                # Assign units (optional metadata)
                stdvalues.attrs["units"] = "mm/d"

                # Build output file path
                stdoutfile = f"{varbname}_{dataname}_{monthname}_{startyear}-{finalyear}_std_of_dailymeans.nc"
                output_path = os.path.join(args.results_dir, stdoutfile)

                # Ensure output directory exists
                os.makedirs(args.results_dir, exist_ok=True)

                # Write to NetCDF
                write_to_netcdf(stdvalues, ds, output_path)

                print(f"Output written to {output_path}")

            except Exception as err:
                print(f"Failed for model: {dataname} with error: {err}")

    args = P.get_parameter()
    month = args.month
    startyear = args.firstyear
    finalyear = args.lastyear
    directory = args.modpath  # Input  directory for model data
    # These models have been processed already (or tried and found wanting,
    # e.g. problematic time coordinates):
    skipMe = args.skip
    print("SKIPPING:", skipMe)

    # Choose only one ensemble member per model, with the following ensemble-member code (for definitions, see
    # http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf):

    # NOTE--These models do not supply 3hr data from the 'r1i1p1' ensemble member,
    #       but do supply it from other ensemble members:
    #       bcc-csm1-1 (3hr data is from r2i1p1)
    #       CCSM4      (3hr data is from r6i1p1)
    #       GFDL-CM3   (3hr data is from r2i1p1, r3i1p1, r4i1p1, r5i1p1)
    #       GISS-E2-H  (3hr data is from r6i1p1, r6i1p3)
    #       GISS-E2-R  (3hr data is from r6i1p2)

    varbname = "pr"

    #           Note that CMIP5 specifications designate (01:30, 04:30, 07:30, ..., 22:30) GMT for 3hr flux fields, but
    # *WARNING* some GMT timepoints are actually (0, 3, 6,..., 21) in submitted CMIP5 data, despite character strings in
    #           file names (and time axis metadata) to the contrary. See CMIP5 documentation and errata! Overrides to
    #           correct these problems are given below:
    # Include 00Z as a possible starting time, to accomodate (0, 3, 6,...,
    # 21)GMT in the input data.
    # startime = -1.5     # Subtract 1.5h from (0, 3, 6,..., 21)GMT input
    # data. This is needed for BNU-ESM, CCSM4 and CNRM-CM5.
    # Subtract 1.5h from (0, 3, 6,..., 21)GMT input data. This is needed for
    # CMCC-CM.

    # -------------------------------------

    monthname = monthname_d[month]  # noqa: F841
    nYears = finalyear - startyear + 1  # noqa: F841
    # Character strings for starting and ending day/GMT (*HARD-CODES
    # particular GMT timepoints*):
    # *WARNING* GMT timepoints are actually (0, 3, 6,..., 21) in the original TRMM/Obs4MIPs data, despite character
    # strings in file names (and time axis metadata). See CMIP5 documentation and
    # errata!

    template = populateStringConstructor(args.filename_template, args)
    template.variable = varbname

    fileList = glob.glob(os.path.join(directory, template()))
    print("FILES:", fileList)

    params = [INPUT(args, name, template) for name in fileList]
    print("PARAMS:", params)

    cdp_run.multiprocess(compute, params, num_workers=args.num_workers)


def add_one_month(t):
    # Add one month manually (cftime has no direct DateOffset)
    # We'll use the cftime constructor
    year = t.year + (t.month // 12)
    month = (t.month % 12) + 1
    return t.replace(year=year, month=month)


def add_one_day(t):
    return t + datetime.timedelta(days=1)


def get_cftime_class(ds):
    # Find calendar type of ds
    if not hasattr(ds, "time"):
        raise ValueError("Dataset does not have a 'time' variable.")

    calendar = get_calendar(ds)
    print(f"Calendar type: {calendar}")

    # Create the correct cftime class based on calendar
    cftime_class = cftime.datetime  # Default

    if calendar == "360_day":
        cftime_class = cftime.Datetime360Day
    elif calendar == "noleap":
        cftime_class = cftime.DatetimeNoLeap
    else:
        cftime_class = cftime.DatetimeGregorian

    return cftime_class


def write_to_netcdf(stdvalues, ds, output_path):
    # Convert DataArray to Dataset
    std_ds = stdvalues.to_dataset()

    # Preserve global attributes from original dataset
    std_ds.attrs = ds.attrs.copy()

    # Preserve bounds variables for lat and lon only
    lat_key = get_latitude_key(ds)
    lon_key = get_longitude_key(ds)

    for coord in [lat_key, lon_key]:
        if coord in ds.coords and "bounds" in ds[coord].attrs:
            bounds_name = ds[coord].attrs["bounds"]
            if bounds_name in ds.variables:
                std_ds[bounds_name] = ds[bounds_name]

    # Write to NetCDF
    std_ds.to_netcdf(output_path)


# Good practice to place contents of script under this check
if __name__ == "__main__":
    # Related to script being installed as executable
    mp.freeze_support()

    main()
