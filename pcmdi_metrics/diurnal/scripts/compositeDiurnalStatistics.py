#!/usr/bin/env python

# Curt Covey July 2017
# Jiwoo Lee July 2025 Modernized the code to use xarray


# /export/covey1/CMIP5/Precipitation/DiurnalCycle/HistoricalRuns/compositeDiurnalStatisticsWrapped.py

# This modifiction of ./compositeDiurnalStatistics.py will have the PMP Parser "wrapped" around it,
# so that it can be executed with input parameters in the Unix command line, for example:
# ---> python compositeDiurnalStatisticsWrapped.py -t "sample_data_%(variable)_%(model).nc" -m 7

# These are the models with CMIP5 historical run output at 3h frequency, which this script is designed to process:
# 'ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM',
# 'CCSM4',  'CMCC-CM',      'CNRM-CM5',     'EC-EARTH',
# 'FGOALS-g2', 'GFDL-CM3',  'GFDL-ESM2M', 'GISS-E2-R',
# 'GISS-E2-H', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR',
# 'MIROC4h',   'MIROC5',    'MIROC-ESM',  'MIROC-ESM-CHEM'

from __future__ import division, print_function

import datetime
import glob
import multiprocessing as mp
import os

import cdp
import cftime
import numpy as np
import xarray as xr

from pcmdi_metrics.diurnal.common import (
    INPUT,
    P,
    monthname_d,
    populateStringConstructor,
)
from pcmdi_metrics.io import (
    get_calendar,
    get_latitude,
    get_latitude_key,
    get_longitude,
    get_longitude_key,
    get_time_key,
    xcdat_open,
)


def main():
    def compute(params):
        fileName = params.fileName
        startyear = params.args.firstyear
        finalyear = params.args.lastyear
        month = params.args.month
        monthname = params.monthname
        varbname = params.varname
        template = populateStringConstructor(args.filename_template, args)
        template.variable = varbname
        # Units on output (*may be converted below from the units of input*)
        outunits = "mm/d"
        startime = 1.5  # GMT value for starting time-of-day

        dataname = params.args.model
        if dataname is None or dataname.find("*") != -1:
            # model not passed or passed as *
            reverted = template.reverse(os.path.basename(fileName))
            print("REVERYING", reverted, dataname)
            dataname = reverted["model"]
        if dataname not in args.skip:
            try:
                print(f"Data source: {dataname}")
                print(f"Opening {fileName}")
                ds = xcdat_open(fileName)
                modellons = get_longitude(ds).values
                modellats = get_latitude(ds).values
                lon_key = get_longitude_key(ds)
                lat_key = get_latitude_key(ds)
                time_key = get_time_key(ds)

                # Find calendar type of ds
                cftime_class = get_cftime_class(ds)

                # Composite-mean and composite-s.d diurnal cycle for month and year(s):
                iYear = 0
                for year in range(startyear, finalyear + 1):
                    print(f"Year {year}:")
                    startTime = cftime_class(year, month, 1)
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
                    print("Shape:", tvarb.shape)
                    # The following tasks need to be done only once, extracting
                    # metadata from first-year file:
                    if year == startyear:
                        tc = tvarb.time.values
                        print("DATA FROM:", tc[0], "to", tc[-1])
                        day1 = tc[0]
                        firstday = tvarb.sel(
                            time=(tvarb.time >= day1) & (tvarb.time < add_one_day(day1))
                        )
                        dimensions = firstday.shape
                        print("Shape = ", dimensions)
                        # Number of time points in the selected month for one year
                        N = dimensions[0]
                        nlats = dimensions[1]
                        nlons = dimensions[2]
                        deltaH = 24.0 / N
                        dayspermo = tvarb.shape[0] // N
                        print(
                            f"  {N} timepoints per day, {deltaH} hr intervals between timepoints"
                        )
                        comptime = firstday.time.values
                        # Longitude values are needed later to compute Local Solar Times.
                        lons = modellons[:]
                        print("  Creating temporary storage and output fields ...")
                        # Sorts tvarb into separate GMTs for one year
                        tvslice = np.zeros((N, dayspermo, nlats, nlons))
                        # Concatenates tvslice over all years
                        concatenation = np.zeros((N, dayspermo * nYears, nlats, nlons))
                        LSTs = np.zeros((N, nlats, nlons))
                        for iGMT in range(N):
                            hour = iGMT * deltaH + startime
                            print(
                                f"  Computing Local Standard Times for GMT {hour:5.2f} ..."
                            )
                            for j in range(nlats):
                                for k in range(nlons):
                                    LSTs[iGMT, j, k] = (hour + lons[k] / 15) % 24
                    for iGMT in range(N):
                        hour = iGMT * deltaH + startime
                        print(f"  Choosing timepoints with GMT {hour:5.2f} ...")
                        print("days per mo :", dayspermo)
                        # Transient-variable slice: every Nth tpoint gets all of
                        # the current GMT's tpoints for current year:
                        tvslice[iGMT] = tvarb[iGMT::N]
                        concatenation[
                            iGMT, iYear * dayspermo : (iYear + 1) * dayspermo
                        ] = tvslice[iGMT]
                    iYear += 1
                ds.close()

                # For each GMT, take mean and standard deviation over all years for
                # the chosen month:
                avgvalues = np.zeros((N, nlats, nlons))
                stdvalues = np.zeros((N, nlats, nlons))
                for iGMT in range(N):
                    hour = iGMT * deltaH + startime
                    print(
                        f"Computing mean and standard deviation over all GMT {hour:5.2f} timepoints ..."
                    )
                    # Assumes first dimension of input ("axis#0") is time
                    avgvalues[iGMT] = np.average(concatenation[iGMT], axis=0)
                    stdvalues[iGMT] = np.std(concatenation[iGMT], axis=0)

                # Write output files
                avgoutfile = f"{varbname}_{dataname}_{monthname}_{args.firstyear}-{args.lastyear}_diurnal_avg.nc"
                stdoutfile = f"{varbname}_{dataname}_{monthname}_{args.firstyear}-{args.lastyear}_diurnal_std.nc"
                LSToutfile = f"{varbname}_{dataname}_LocalSolarTimes.nc"
                os.makedirs(args.results_dir, exist_ok=True)

                print("netcdf writing starts")
                required_keys = (time_key, lat_key, lon_key)
                axes = {time_key: comptime, lat_key: modellats, lon_key: modellons}
                write_numpy_to_netcdf(
                    avgvalues,
                    axes,
                    os.path.join(args.results_dir, avgoutfile),
                    var_name="diurnalmean",
                    attrs={"units": outunits},
                    ds_org=ds,
                    required_keys=required_keys,
                )
                print("avgvalues written")
                write_numpy_to_netcdf(
                    stdvalues,
                    axes,
                    os.path.join(args.results_dir, stdoutfile),
                    var_name="diurnalstd",
                    attrs={"units": outunits},
                    ds_org=ds,
                    required_keys=required_keys,
                )
                print("stdvalues written")
                write_numpy_to_netcdf(
                    LSTs,
                    axes,
                    os.path.join(args.results_dir, LSToutfile),
                    var_name="LST",
                    attrs={"units": "hr", "long_name": "Local Solar Time"},
                    ds_org=ds,
                    required_keys=required_keys,
                )
                print("LSTs written")
                print("netcdf writing done")
            except Exception as err:
                print(f"Failed for model {dataname} with error: {err}")

    print("done")
    args = P.get_parameter()

    month = args.month  # noqa: F841
    monthname = monthname_d[args.month]  # noqa: F841

    # -------------------------------------HARD-CODED INPUT (add to command line later?):

    # These models have been processed already (or tried and found wanting,
    # e.g. problematic time coordinates):
    skipMe = args.skip  # noqa: F841

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
    # startGMT =  '0:0:0.0' # Include 00Z as a possible starting time, to accomodate (0, 3, 6,..., 21)GMT in the input
    # data.
    # startime = -1.5 # Subtract 1.5h from (0, 3, 6,..., 21)GMT input data. This is needed for BNU-ESM, CCSM4 and
    # CNRM-CM5.
    # startime = -3.0 # Subtract 1.5h from (0, 3, 6,..., 21)GMT input
    # data. This is needed for CMCC-CM.

    # -------------------------------------

    nYears = args.lastyear - args.firstyear + 1

    template = populateStringConstructor(args.filename_template, args)
    template.variable = varbname

    print("TEMPLATE:", template())
    fileList = glob.glob(os.path.join(args.modpath, template()))
    print("FILES:", fileList)
    params = [INPUT(args, name, template) for name in fileList]
    print("PARAMS:", params)
    cdp.cdp_run.multiprocess(compute, params, num_workers=args.num_workers)


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


def write_numpy_to_netcdf(
    data, axes, filename, var_name="data", attrs=None, ds_org=None, required_keys=None
):
    """
    Convert a 3D NumPy array to an xarray.DataArray and write it to a NetCDF file.

    Parameters
    ----------
    data : np.ndarray
        A 3D NumPy array with shape (time, lat, lon).
    axes : dict
        Dictionary containing 1D coordinate arrays or xarray.DataArrays with keys:
        - 'time': shape (time,)
        - 'lat' : shape (lat,)
        - 'lon' : shape (lon,)
    filename : str
        Output path to the NetCDF file (e.g., 'output.nc').
    var_name : str, optional
        Name of the variable in the NetCDF file (default is 'data').
    attrs : dict, optional
        Attributes to attach to the variable (e.g., {'units': 'K', 'long_name': 'Temperature'}).
    ds_org : xr.Dataset, optional
        Original dataset to preserve global attributes and bounds variables from.
    required_keys : tuple of str, optional
        Keys for the coordinate dimensions. Defaults to ('time', 'lat', 'lon').

    Raises
    ------
    ValueError
        If data is not 3D, or if axes are missing or do not match data dimensions.

    Examples
    --------
    >>> data = np.random.rand(10, 90, 180)
    >>> axes = {
    ...     'time': pd.date_range("2024-01-01", periods=10),
    ...     'lat': np.linspace(-90, 90, 90),
    ...     'lon': np.linspace(-180, 180, 180)
    ... }
    >>> write_numpy_to_netcdf(data, axes, "output.nc", var_name="temperature",
    ...                        attrs={"units": "K", "long_name": "Air Temperature"})
    """
    if data.ndim != 3:
        raise ValueError("Input data must be a 3D NumPy array (time, lat, lon).")

    if required_keys is None:
        required_keys = ("time", "lat", "lon")

    if not all(k in axes for k in required_keys):
        raise ValueError(f"Axes dictionary must contain keys: {required_keys}")

    time_key, lat_key, lon_key = required_keys
    time_dim, lat_dim, lon_dim = data.shape

    if (
        len(axes[time_key]) != time_dim
        or len(axes[lat_key]) != lat_dim
        or len(axes[lon_key]) != lon_dim
    ):
        raise ValueError(
            f"Axis lengths must match data dimensions ({time_key}, {lat_key}, {lon_key})."
        )

    # Create DataArray
    da = xr.DataArray(
        data,
        dims=required_keys,
        coords={
            time_key: axes[time_key],
            lat_key: axes[lat_key],
            lon_key: axes[lon_key],
        },
        name=var_name,
        attrs=attrs or {},
    )

    ds_new = da.to_dataset()

    if ds_org:
        # Copy global attributes
        ds_new.attrs = ds_org.attrs.copy()

        # Preserve lat/lon bounds variables if available
        for coord_key in [lat_key, lon_key]:
            if coord_key in ds_org.coords:
                bounds_attr = ds_org[coord_key].attrs.get("bounds")
                if bounds_attr and bounds_attr in ds_org.variables:
                    ds_new[bounds_attr] = ds_org[bounds_attr]

    # Save to file
    ds_new.to_netcdf(path=filename)
    print(f"Saved to NetCDF: {filename}")


# Good practice to place contents of script under this check
if __name__ == "__main__":
    # Related to script being installed as executable
    mp.freeze_support()

    main()
