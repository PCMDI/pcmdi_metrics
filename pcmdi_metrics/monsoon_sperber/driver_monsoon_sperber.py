#!/usr/bin/env python
"""
Calculate monsoon metrics

Code History:
- First implemented by Jiwoo Lee (lee1043@llnl.gov), 2018. 9.
- Updated using xarray/xcdat by Bo Dong (dong12@llnl.gov) and Jiwoo Lee, 2024. 4.

Reference:
Sperber, K. and H. Annamalai, 2014:
The use of fractional accumulated precipitation for the evaluation of the
annual cycle of monsoons. Climate Dynamics, 43:3219-3244,
doi: 10.1007/s00382-014-2099-3

Auspices:
This work was performed under the auspices of the U.S. Department of
Energy by Lawrence Livermore National Laboratory under Contract
DE-AC52-07NA27344. Lawrence Livermore National Laboratory is operated by
Lawrence Livermore National Security, LLC, for the U.S. Department of Energy,
National Nuclear Security Administration under Contract DE-AC52-07NA27344.

Disclaimer:
This document was prepared as an account of work sponsored by an
agency of the United States government. Neither the United States government
nor Lawrence Livermore National Security, LLC, nor any of their employees
makes any warranty, expressed or implied, or assumes any legal liability or
responsibility for the accuracy, completeness, or usefulness of any
information, apparatus, product, or process disclosed, or represents that its
use would not infringe privately owned rights. Reference herein to any specific
commercial product, process, or service by trade name, trademark, manufacturer,
or otherwise does not necessarily constitute or imply its endorsement,
recommendation, or favoring by the United States government or Lawrence
Livermore National Security, LLC. The views and opinions of authors expressed
herein do not necessarily state or reflect those of the United States
government or Lawrence Livermore National Security, LLC, and shall not be used
for advertising or product endorsement purposes.
"""

import copy
import glob
import json
import math
import os
import re
import sys
from argparse import RawTextHelpFormatter
from collections import defaultdict
from shutil import copyfile

import matplotlib
import numpy as np
import pandas as pd
import xarray as xr
import xcdat as xc
from matplotlib import pyplot as plt

from pcmdi_metrics.io import load_regions_specs, region_subset, xcdat_open
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.mean_climate.lib import pmp_parser
from pcmdi_metrics.monsoon_sperber.lib import (
    AddParserArgument,
    YearCheck,
    divide_chunks_advanced,
    model_land_only,
    sperber_metrics,
)
from pcmdi_metrics.utils import create_land_sea_mask, fill_template

matplotlib.use("Agg")


def tree():
    return defaultdict(tree)


def pick_year_last_day(ds):
    eday = 31
    try:
        time_key = xc.axis.get_dim_keys(ds, axis="T")
        if "calendar" in ds[time_key].attrs.keys():
            if "360" in ds[time_key]["calendar"]:
                eday = 30
        else:
            if "360" in ds[time_key][0].values.item().calendar:
                eday = 30
    except Exception:
        pass
    return eday


# How many elements each list should have
n = 5  # pentad

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pmp_parser.PMPParser(
    description="Runs PCMDI Monsoon Sperber Computations",
    formatter_class=RawTextHelpFormatter,
)
P = AddParserArgument(P)
P.add_argument(
    "--cmec",
    dest="cmec",
    default=False,
    action="store_true",
    help="Use to save CMEC format metrics JSON",
)
P.add_argument(
    "--no_cmec",
    dest="cmec",
    default=False,
    action="store_false",
    help="Do not save CMEC format metrics JSON",
)
P.set_defaults(cmec=False)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
fq = param.frequency
realm = param.realm

# On/off switches
nc_out = param.nc_out  # Record NetCDF output
plot = param.plot  # Generate plots
includeOBS = param.includeOBS  # Loop run for OBS or not
cmec = param.cmec  # CMEC formatted JSON

# Path to reference data
reference_data_name = param.reference_data_name
reference_data_path = param.reference_data_path
reference_data_lf_path = param.reference_data_lf_path

# Path to model data as string template
modpath = param.process_templated_argument("modpath")
modpath_lf = param.process_templated_argument("modpath_lf")
print("modpath = ", modpath)
print("modpath_lf = ", modpath_lf)

# Check given model option
models = param.modnames
print("models:", models)

# list of regions
list_monsoon_regions = param.list_monsoon_regions

if list_monsoon_regions is None:
    list_monsoon_regions = ["AIR", "AUS", "Sahel", "GoG", "NAmo", "SAmo"]

print("list_monsoon_regions:", list_monsoon_regions)

# Include all models if conditioned
if ("all" in [m.lower() for m in models]) or (models == "all"):
    model_index_path = re.split(". |_", modpath.split("/")[-1]).index("%(model)")
    models = [
        re.split(". |_", p.split("/")[-1])[model_index_path]
        for p in glob.glob(
            fill_template(
                modpath, mip=mip, exp=exp, model="*", realization="*", variable="pr"
            )
        )
    ]
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print("number of models:", len(models))

# Realizations
realization = param.realization
print("realization: ", realization)

# Output
outdir = param.process_templated_argument("results_dir")

# Create output directory
for output_type in ["graphics", "diagnostic_results", "metrics_results"]:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# Debug
debug = param.debug
print("debug: ", debug)

# Variables
varModel = param.varModel
varOBS = param.varOBS

# Year
#  model
msyear = param.msyear
meyear = param.meyear
YearCheck(msyear, meyear, P)
#  obs
osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# Units
units = param.units
#  model
ModUnitsAdjust = param.ModUnitsAdjust
#  obs
ObsUnitsAdjust = param.ObsUnitsAdjust

# JSON update
update_json = param.update_json

# =================================================
# Declare dictionary for .json record
# -------------------------------------------------
monsoon_stat_dic = tree()

# Define output json file
json_filename = "_".join(
    ["monsoon_sperber_stat", mip, exp, fq, realm, str(msyear) + "-" + str(meyear)]
)
json_file = os.path.join(outdir(output_type="metrics_results"), json_filename + ".json")
json_file_org = os.path.join(
    outdir(output_type="metrics_results"),
    "_".join([json_filename, "org", str(os.getpid())]) + ".json",
)

# Save pre-existing json file against overwriting
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)
    if update_json:
        fj = open(json_file)
        monsoon_stat_dic = json.loads(fj.read())
        fj.close()

if "REF" not in list(monsoon_stat_dic.keys()):
    monsoon_stat_dic["REF"] = {}
if "RESULTS" not in list(monsoon_stat_dic.keys()):
    monsoon_stat_dic["RESULTS"] = {}

# =================================================
# Load region information
# -------------------------------------------------
regions_specs = load_regions_specs()

# =================================================
# Loop start for given models
# -------------------------------------------------
if includeOBS:
    models.insert(0, "obs")

for model in models:
    print(f"====  model: {model} ======================================")
    try:
        # Conditions depending obs or model
        if model == "obs":
            var = varOBS
            UnitsAdjust = ObsUnitsAdjust
            syear = osyear
            eyear = oeyear
            # variable data
            model_path_list = [reference_data_path]
            # land fraction
            model_lf_path = reference_data_lf_path
            # dict for output JSON
            if reference_data_name not in list(monsoon_stat_dic["REF"].keys()):
                monsoon_stat_dic["REF"][reference_data_name] = {}
            # dict for plottng
            dict_obs_composite = {}
            dict_obs_composite[reference_data_name] = {}
        else:  # for rest of models
            var = varModel
            UnitsAdjust = ModUnitsAdjust
            syear = msyear
            eyear = meyear
            # variable data
            model_path_list = glob.glob(
                modpath(model=model, exp=exp, realization=realization, variable=var)
            )
            if debug:
                print(
                    "model: ",
                    model,
                    "   exp: ",
                    exp,
                    "  realization: ",
                    realization,
                    "  variable: ",
                    var,
                )
                print("debug: model_path_list: ", model_path_list)
            # land fraction
            model_lf_path = modpath_lf(model=model)
            print("model_lf_path = ", model_lf_path)
            if os.path.isfile(model_lf_path):
                pass
            else:
                model_lf_path = modpath_lf(model=model.upper())
            # dict for output JSON
            if model not in list(monsoon_stat_dic["RESULTS"].keys()):
                monsoon_stat_dic["RESULTS"][model] = {}

            dict_obs_composite = {}
            dict_obs_composite[reference_data_name] = {}

        # Read land fraction
        if model_lf_path is not None:
            if os.path.isfile(model_lf_path):
                try:
                    ds_lf = xcdat_open(model_lf_path)
                except Exception:
                    ds_lf = None

        if not ds_lf:
            lf_array = create_land_sea_mask(ds_lf, method="pcmdi")
            ds_lf = lf_array.to_dataset().compute()
            ds_lf = ds_lf.rename_vars({"lsmask": "sftlf"})

        if model in ["EC-EARTH"]:  # , "BNU-ESM" ]:
            ds_lf = ds_lf.isel(lat=slice(None, None, -1))
        lf = ds_lf.sftlf.sel(lat=slice(-90, 90))  # land frac file must be global

        # -------------------------------------------------
        # Loop start - Realization
        # -------------------------------------------------
        for model_path in model_path_list:
            try:
                if model == "obs":
                    run = "obs"
                else:
                    if realization in ["all", "All", "ALL", "*"]:
                        run_index = modpath.split(".").index("%(realization)")
                        run = model_path.split("/")[-1].split(".")[run_index]
                    else:
                        run = realization
                    if run not in monsoon_stat_dic["RESULTS"][model]:
                        monsoon_stat_dic["RESULTS"][model][run] = {}

                print(f" --- {run} ---")

                # Get time coordinate information
                print("model_path =   ", model_path)

                dc = xcdat_open(model_path, decode_times=True)
                dc["time"].attrs["axis"] = "T"
                dc["time"].attrs["standard_name"] = "time"
                dc = xr.decode_cf(dc, decode_times=True)
                dc = dc.bounds.add_missing_bounds("X")
                dc = dc.bounds.add_missing_bounds("Y")
                dc = dc.bounds.add_missing_bounds("T")

                dc = dc.assign_coords({"lon": lf.lon, "lat": lf.lat})
                c = xc.center_times(dc)
                eday = pick_year_last_day(dc)

                # Get starting and ending year and month
                startYear = c.time.values[0].year
                startMonth = c.time.values[0].month
                endYear = c.time.values[-1].year
                endMonth = c.time.values[-1].month

                # Adjust years to consider only when they
                # have entire calendar months
                if startMonth > 1:
                    startYear += 1
                if endMonth < 12:
                    endYear -= 1

                # Final selection of starting and ending years
                startYear = max(syear, startYear)
                endYear = min(eyear, endYear)

                # Check calendar (just checking..)

                if debug:
                    print("debug: startYear: ", type(startYear), startYear)
                    print("debug: startMonth: ", type(startMonth), startMonth)
                    print("debug: endYear: ", type(endYear), endYear)
                    print("debug: endMonth: ", type(endMonth), endMonth)
                    endYear = startYear + 1

                # Prepare archiving individual year pentad time series for composite
                list_pentad_time_series = {}
                list_pentad_time_series_cumsum = {}  # Cumulative time series
                for region in list_monsoon_regions:
                    list_pentad_time_series[region] = []
                    list_pentad_time_series_cumsum[region] = []

                # Write individual year time series for each monsoon domain
                # in a netCDF file
                output_filename = "{}_{}_{}_{}_{}_{}-{}".format(
                    mip, model, exp, run, "monsoon_sperber", startYear, endYear
                )
                if nc_out:
                    output_filename = "{}_{}_{}_{}_{}_{}-{}".format(
                        mip, model, exp, run, "monsoon_sperber", startYear, endYear
                    )

                    file_path = os.path.join(
                        outdir(output_type="diagnostic_results"),
                        output_filename + ".nc",
                    )
                    try:
                        fout = xr.open_dataset(
                            file_path, mode="a"
                        )  # 'a' stands for append mode
                    except FileNotFoundError:
                        fout = xr.Dataset()

                # Plotting setup
                if plot:
                    ax = {}
                    if len(list_monsoon_regions) > 1:
                        nrows = math.ceil(len(list_monsoon_regions) / 2.0)
                        ncols = 2
                    else:
                        nrows = 1
                        ncols = 1

                    fig = plt.figure(figsize=[6.4, 6.4])
                    plt.subplots_adjust(hspace=0.25)

                    for i, region in enumerate(list_monsoon_regions):
                        ax[region] = plt.subplot(nrows, ncols, i + 1)
                        ax[region].set_ylim(0, 1)
                        # ax[region].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
                        # ax[region].set_xticks([0, 10, 20, 30, 40, 50, 60, 70])
                        ax[region].margins(x=0)
                        print(
                            "plot: region",
                            region,
                            "nrows",
                            nrows,
                            "ncols",
                            ncols,
                            "index",
                            i + 1,
                        )
                        if nrows > 1 and math.ceil((i + 1) / float(ncols)) < nrows:
                            ax[region].set_xticklabels([])
                        if ncols > 1 and (i + 1) % 2 == 0:
                            ax[region].set_yticklabels([])

                    fig.text(0.5, 0.04, "pentad count", ha="center")
                    fig.text(
                        0.03,
                        0.5,
                        "accumulative pentad precip fraction",
                        va="center",
                        rotation="vertical",
                    )

                # -------------------------------------------------
                # Loop start - Year
                # -------------------------------------------------
                temporary = {}
                print("\n")
                # year loop, endYear+1 to include last year
                for year in range(startYear, endYear + 1):
                    print("\n")
                    print(" year = ", year)
                    print("\n")
                    d = dc.pr.sel(
                        time=slice(
                            str(year) + "-01-01 00:00:00",
                            str(year) + f"-12-{eday} 23:59:59",
                        ),
                        lat=slice(-90, 90),
                    )
                    # unit adjust
                    if UnitsAdjust[0]:
                        """Below two lines are identical to following:
                        d = MV2.multiply(d, 86400.)
                        d.units = 'mm/d'
                        """
                        d.values = d.values * 86400.0
                        d["units"] = units

                    # variable for over land only
                    d_land = model_land_only(model, d, lf, debug=debug)

                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Loop start - Monsoon region
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    for region in list_monsoon_regions:
                        print(" region = ", region)
                        # extract for monsoon region
                        if region in ["GoG", "NAmo"]:
                            # all grid point rainfall
                            d_sub_ds = region_subset(
                                dc, region, data_var="pr", regions_specs=regions_specs
                            )
                            # must be entire calendar years
                            d_sub_pr = d_sub_ds.pr.sel(
                                time=slice(
                                    str(year) + "-01-01 00:00:00",
                                    str(year) + f"-12-{eday} 23:59:59",
                                )
                            )

                            d_sub_pr.values = d_sub_pr.values * 86400.0
                            d_sub_pr["units"] = units

                        else:
                            # land-only rainfall
                            d_sub_ds = region_subset(
                                dc, region, data_var="pr", regions_specs=regions_specs
                            )
                            d_sub_pr = d_sub_ds.pr.sel(
                                time=slice(
                                    str(year) + "-01-01 00:00:00",
                                    str(year) + f"-12-{eday} 23:59:59",
                                )
                            )

                            lf_sub_ds = region_subset(
                                ds_lf,
                                region,
                                data_var="sftlf",
                                regions_specs=regions_specs,
                            )
                            lf_sub = lf_sub_ds.sftlf
                            d_sub_pr = model_land_only(
                                model, d_sub_pr, lf_sub, debug=debug
                            )

                            d_sub_pr.values = d_sub_pr.values * 86400.0
                            d_sub_pr["units"] = units

                        # Area average
                        ds_sub_pr = d_sub_pr.to_dataset().compute()
                        dc = dc.bounds.add_missing_bounds("X")
                        ds_sub_pr = ds_sub_pr.bounds.add_missing_bounds("X")
                        ds_sub_pr = ds_sub_pr.bounds.add_missing_bounds("Y")
                        ds_sub_pr = ds_sub_pr.bounds.add_missing_bounds("T")

                        if "lat_bnds" not in ds_sub_pr.variables:
                            lat_bnds = dc["lat_bnds"].sel(lat=ds_sub_pr["lat"])
                            ds_sub_pr["lat_bnds"] = lat_bnds

                        ds_sub_aave = ds_sub_pr.spatial.average(
                            "pr", axis=["X", "Y"], weights="generate"
                        ).compute()
                        d_sub_aave = ds_sub_aave.pr

                        if debug:
                            print("debug: region:", region)

                        # Southern Hemisphere monsoon domain
                        # set time series as 7/1~6/30
                        if region in ["AUS", "SAmo"]:
                            if year == startYear:
                                start_t = str(year) + "-07-01 00:00:00"
                                end_t = str(year) + f"-12-{eday} 23:59:59"
                                temporary[region] = d_sub_aave.sel(
                                    time=slice(start_t, end_t)
                                )

                                continue
                            else:
                                # n-1 year 7/1~12/31
                                part1 = copy.copy(temporary[region])
                                # n year 1/1~6/30
                                part2 = d_sub_aave.sel(
                                    time=slice(
                                        str(year) + "-01-01 00:00:00",
                                        str(year) + "-06-30 23:59:59",
                                    )
                                )
                                start_t = str(year) + "-07-01 00:00:00"
                                end_t = str(year) + f"-12-{eday} 23:59:59"
                                temporary[region] = d_sub_aave.sel(
                                    time=slice(start_t, end_t)
                                )

                                d_sub_aave = xr.concat([part1, part2], dim="time")

                                if debug:
                                    print(
                                        "debug: ",
                                        region,
                                        year,
                                    )
                        # get pentad time series
                        list_d_sub_aave_chunks = list(
                            divide_chunks_advanced(d_sub_aave, n, debug=debug)
                        )

                        pentad_time_series = []
                        time_coords = np.array([], dtype="datetime64")

                        for d_sub_aave_chunk in list_d_sub_aave_chunks:
                            # ignore when chunk length is shorter than defined
                            if d_sub_aave_chunk.shape[0] >= n:
                                aa = d_sub_aave_chunk.to_numpy()
                                aa_mean = np.mean(aa)
                                ave_chunk = d_sub_aave_chunk.mean(
                                    axis=0, skipna=True
                                ).compute()
                                pentad_time_series.append(float(ave_chunk))
                                datetime_str = str(d_sub_aave_chunk["time"][0].values)
                                datetime = pd.to_datetime([datetime_str[:10]])
                                time_coords = np.concatenate([time_coords, datetime])
                                time_coords = pd.to_datetime(time_coords)

                        pentad_time_series = xr.DataArray(
                            pentad_time_series,
                            dims="time",
                            coords={"time": time_coords},
                        )

                        if debug:
                            print(
                                "debug: pentad_time_series length: ",
                                len(pentad_time_series),
                            )

                        # Keep pentad time series length in consistent
                        ref_length = int(365 / n)
                        if len(pentad_time_series) < ref_length:
                            pentad_time_series = pentad_time_series.interp(
                                time=pd.date_range(
                                    time_coords[0], time_coords[-1], periods=ref_length
                                )
                            )

                            time_coords = pentad_time_series.coords["time"]

                        pentad_time_series_cumsum = np.cumsum(pentad_time_series)
                        pentad_time_series = xr.DataArray(
                            pentad_time_series,
                            dims="time",
                            name=region + "_" + str(year),
                        )
                        pentad_time_series.attrs["units"] = str(d.units.values)

                        pentad_time_series_cumsum = xr.DataArray(
                            pentad_time_series_cumsum,
                            dims="time",
                            name=region + "_" + str(year) + "_cumsum",
                        )
                        pentad_time_series_cumsum.attrs["units"] = str(d.units.values)
                        pentad_time_series_cumsum.coords["time"] = time_coords

                        if nc_out:
                            # Archive individual year time series in netCDF file
                            pentad_time_series.to_netcdf(file_path, mode="a")
                            pentad_time_series_cumsum.to_netcdf(file_path, mode="a")

                        """
                        if plot:
                            # Add grey line for individual year in plot
                            if year == startYear:
                                label = 'Individual yr'
                            else:
                                label = ''
                            ax[region].plot(
                                np.array(pentad_time_series_cumsum),
                                c='grey', label=label)
                        """

                        # Append individual year: save for following composite
                        list_pentad_time_series[region].append(pentad_time_series)
                        list_pentad_time_series_cumsum[region].append(
                            pentad_time_series_cumsum
                        )

                    # --- Monsoon region loop end
                # --- Year loop end
                dc.close()

                # -------------------------------------------------
                # Loop start: Monsoon region without year: Composite
                # -------------------------------------------------
                if debug:
                    print("debug: composite start")

                for region in list_monsoon_regions:
                    # Get composite for each region

                    composite_pentad_time_series = np.array(
                        list_pentad_time_series[region]
                    ).mean(axis=0)

                    # Get accumulation ts from the composite
                    composite_pentad_time_series_cumsum = np.cumsum(
                        composite_pentad_time_series
                    )

                    # Maintain axis information

                    # - - - - - - - - - - -
                    # Metrics for composite
                    # - - - - - - - - - - -

                    metrics_result = sperber_metrics(
                        composite_pentad_time_series_cumsum, region, debug=debug
                    )

                    # Normalized cummulative pentad time series
                    composite_pentad_time_series_cumsum_normalized = metrics_result[
                        "frac_accum"
                    ]

                    composite_pentad_time_series = xr.DataArray(
                        composite_pentad_time_series, dims="time", name=region + "_comp"
                    )
                    composite_pentad_time_series.attrs["units"] = str(d.units)
                    composite_pentad_time_series.coords["time"] = time_coords

                    composite_pentad_time_series_cumsum = xr.DataArray(
                        composite_pentad_time_series_cumsum,
                        dims="time",
                        name=region + "_comp_cumsum",
                    )
                    composite_pentad_time_series_cumsum.attrs["units"] = str(d.units)
                    composite_pentad_time_series_cumsum.coords["time"] = time_coords

                    composite_pentad_time_series_cumsum_normalized = xr.DataArray(
                        composite_pentad_time_series_cumsum_normalized,
                        dims="time",
                        name=region + "_comp_cumsum_fraction",
                    )
                    composite_pentad_time_series_cumsum_normalized.attrs["units"] = str(
                        d.units
                    )
                    composite_pentad_time_series_cumsum_normalized.coords[
                        "time"
                    ] = time_coords

                    if model == "obs":
                        dict_obs_composite[reference_data_name][region] = {}
                        dict_obs_composite[reference_data_name][
                            region
                        ] = composite_pentad_time_series_cumsum_normalized

                    # Archive as dict for JSON
                    if model == "obs":
                        dict_head = monsoon_stat_dic["REF"][reference_data_name]
                    else:
                        dict_head = monsoon_stat_dic["RESULTS"][model][run]
                    # generate key if not there
                    if region not in list(dict_head.keys()):
                        dict_head[region] = {}
                    # generate keys and save for statistics
                    dict_head[region]["onset_index"] = metrics_result["onset_index"]
                    dict_head[region]["decay_index"] = metrics_result["decay_index"]
                    dict_head[region]["slope"] = metrics_result["slope"]
                    dict_head[region]["duration"] = metrics_result["duration"]

                    # Archice in netCDF file
                    if nc_out:
                        composite_pentad_time_series.to_netcdf(file_path, mode="a")
                        composite_pentad_time_series_cumsum.to_netcdf(
                            file_path, mode="a"
                        )
                        composite_pentad_time_series_cumsum_normalized.to_netcdf(
                            file_path, mode="a"
                        )

                        if region == list_monsoon_regions[-1]:
                            fout.close()

                    # Add line in plot
                    if plot:
                        if model != "obs":
                            # model
                            ax[region].plot(
                                np.array(
                                    composite_pentad_time_series_cumsum_normalized
                                ),
                                c="red",
                                label=model,
                            )
                            for idx in [
                                metrics_result["onset_index"],
                                metrics_result["decay_index"],
                            ]:
                                ax[region].axvline(
                                    x=idx,
                                    ymin=0,
                                    ymax=composite_pentad_time_series_cumsum_normalized[
                                        idx
                                    ].item(),
                                    c="red",
                                    ls="--",
                                )

                        # obs
                        if model == "obs":
                            ax[region].plot(
                                np.array(
                                    dict_obs_composite[reference_data_name][region]
                                ),
                                c="blue",
                                label=reference_data_name,
                            )
                            for idx in [
                                monsoon_stat_dic["REF"][reference_data_name][region][
                                    "onset_index"
                                ],
                                monsoon_stat_dic["REF"][reference_data_name][region][
                                    "decay_index"
                                ],
                            ]:
                                ax[region].axvline(
                                    x=idx,
                                    ymin=0,
                                    ymax=dict_obs_composite[reference_data_name][
                                        region
                                    ][idx].item(),
                                    c="blue",
                                    ls="--",
                                )
                        # title
                        ax[region].set_title(region)
                        if region == list_monsoon_regions[0]:
                            ax[region].legend(loc=2)
                        if region == list_monsoon_regions[-1]:
                            if model == "obs":
                                data_name = "OBS: " + reference_data_name
                            else:
                                data_name = ", ".join([mip.upper(), model, exp, run])
                            fig.suptitle(
                                "Precipitation pentad time series\n"
                                + "Monsoon domain composite accumulations\n"
                                + ", ".join(
                                    [data_name, str(startYear) + "-" + str(endYear)]
                                )
                            )
                            plt.subplots_adjust(top=0.85)
                            plt.savefig(
                                os.path.join(
                                    outdir(output_type="graphics"),
                                    output_filename + ".png",
                                )
                            )
                            plt.close()

                # =================================================
                # Write dictionary to json file
                # (let the json keep overwritten in model loop)
                # -------------------------------------------------
                JSON = Base(outdir(output_type="metrics_results"), json_filename)
                JSON.write(
                    monsoon_stat_dic,
                    json_structure=["model", "realization", "monsoon_region", "metric"],
                    sort_keys=True,
                    indent=4,
                    separators=(",", ": "),
                )
                if cmec:
                    JSON.write_cmec(indent=4, separators=(",", ": "))

            except Exception as err:
                if debug:
                    raise
                else:
                    print("warning: faild for ", model, run, err)
                    pass
        # --- Realization loop end
    except Exception as err:
        if debug:
            raise
        else:
            print("warning: faild for ", model, err)
            pass
# --- Model loop end

if not debug:
    sys.exit(0)
