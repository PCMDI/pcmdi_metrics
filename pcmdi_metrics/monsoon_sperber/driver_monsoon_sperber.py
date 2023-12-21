#!/usr/bin/env python
"""
Calculate monsoon metrics

Jiwoo Lee (lee1043@llnl.gov)

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

import xcdat as xc
import xarray as xr

#from __future__ import print_function

import copy
import json
import math
import os
import sys
import time
from argparse import RawTextHelpFormatter
from collections import defaultdict
from glob import glob
from shutil import copyfile

import cdms2
# import cdtime
# import cdutil
import matplotlib.pyplot as plt
# import MV2
import numpy as np

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.mean_climate.lib import pmp_parser
from pcmdi_metrics.monsoon_sperber.lib import (
    AddParserArgument,
    YearCheck,
    divide_chunks_advanced,
    interp1d,
    model_land_only,
    sperber_metrics,
)
from pcmdi_metrics.io import load_regions_specs, region_subset

print("=========!!!!!!!!!change to xCDAT!!!!!!!!!!!=========")

def tree():
    return defaultdict(tree)


# =================================================
# Hard coded options... will be moved out later
# -------------------------------------------------
#list_monsoon_regions = ["AIR", "AUS", "Sahel", "GoG", "NAmo", "SAmo"]
list_monsoon_regions = ["AUS", "Sahel"]

# How many elements each
# list should have
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

# Check given model option
models = param.modnames
print("models:", models)

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
# Loop start for given models
# -------------------------------------------------
regions_specs = {}
egg_pth = resources.resource_path()
exec(
    compile(
        open(os.path.join(egg_pth, "default_regions.py")).read(),
        os.path.join(egg_pth, "default_regions.py"),
        "exec",
    )
)

# =================================================
# Loop start for given models
# -------------------------------------------------
if includeOBS:
    models.insert(0, "obs")

for model in models:
    print(" ----- ", model, " ---------------------")
    print(" xxxxxxxxxxxxxxxxxx ")
    #try:
    if 1:
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
            model_path_list = glob(
                modpath(model=model, exp=exp, realization=realization, variable=var)
            )
            if debug:
                print("debug: model_path_list: ", model_path_list)
            # land fraction
            model_lf_path = modpath_lf(model=model)
            if os.path.isfile(model_lf_path):
                pass
            else:
                model_lf_path = modpath_lf(model=model.upper())
            # dict for output JSON
            if model not in list(monsoon_stat_dic["RESULTS"].keys()):
                monsoon_stat_dic["RESULTS"][model] = {}

        # Read land fraction
        print("model_lf_path: ", model_lf_path)
        print(" xxxxxxxxxxx.  ")
        #f_lf = cdms2.open(model_lf_path)
        #lf = f_lf("sftlf", latitude=(-90, 90))
        #f_lf.close()
        
        ds_lf = xc.open_mfdataset(model_lf_path)#, add_bounds=True)
        lf = ds_lf.sftlf.sel(lat=slice(-90,90))
        print('YYYYYYYYYYYYY')
        print(lf)

        # -------------------------------------------------
        # Loop start - Realization
        # -------------------------------------------------
        for model_path in model_path_list:
            print('\n')
            print('model_path = ',model_path)
            print('\n')
            timechk1 = time.time()
            #try:
            if 1:
                if model == "obs":
                    run = "obs"
                else:
                    if realization in ["all", "All", "ALL", "*"]:
                        run_index = modpath.split(".").index("%(realization)")
                        run = model_path.split("/")[-1].split(".")[run_index]
                    else:
                        run = realization
                    # dict
                    if run not in monsoon_stat_dic["RESULTS"][model]:
                        monsoon_stat_dic["RESULTS"][model][run] = {}
                print(" --- ", run, " ---")
                print(" xxxxxxxxxxxxxxx ")
                print("model_path ", model_path)

                # Get time coordinate information
#                 fc = cdms2.open(model_path)
#                 print("xxx what is fc, ", fc)
#                 print("xxx var = ", var)
#                 # NOTE: square brackets does not bring data into memory
#                 # only coordinates!
#                 d = fc[var]
#                 print("d = fc[var]   ",d)
#                 t = d.getTime()
#                 print("t = d.getTime()   ",t)
#                 c = t.asComponentTime()
#                 print("c = t.asComponentTime()",c)
                
                dc = xc.open_mfdataset(model_path)# xCDAT
                dc = dc.assign_coords({'lon':lf.lon,'lat':lf.lat})
       
                #c = dc[var].getTime().asComponentTime()
                c = xc.center_times(dc)
                print("c = t.asComponentTime() --> xc.center_times(dc) =   ",c)
                

                # Get starting and ending year and month
                #startYear = c[0].year
                #startMonth = c[0].month
                #endYear = c[-1].year
                #endMonth = c[-1].month
                startYear = c.time.values[0].year
                startMonth = c.time.values[0].month
                endYear = c.time.values[-1].year
                endMonth = c.time.values[-1].month
                print("start year, ",startYear)
                print("end year, ",endYear)
                print("start month, ",startMonth)
                print("end month, ",endMonth)

                # Adjust years to consider only when they
                # have entire calendar months
                if startMonth > 1:
                    startYear += 1
                if endMonth < 12:
                    endYear -= 1

                print("start year, ",startYear)
                print("end year, ",endYear)
                
                # Final selection of starting and ending years
                startYear = max(syear, startYear)
                endYear = min(eyear, endYear)

                
                print("start year, ",startYear)
                print("end year, ",endYear)
                
                # Check calendar (just checking..)
#                 calendar = t.calendar
#                 print("check: calendar: ", calendar)

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
                    print('\n')
                    print('region = ',region)
                    print('\n')
                    list_pentad_time_series[region] = []
                    list_pentad_time_series_cumsum[region] = []
           
                timechk2 = time.time()
                timechk = timechk2 - timechk1
                print("timechk line 380: ", model, run, timechk)
                        
                # Write individual year time series for each monsoon domain
                # in a netCDF file
                output_filename = "{}_{}_{}_{}_{}_{}-{}".format(
                    mip, model, exp, run, "monsoon_sperber", startYear, endYear
                )
                if nc_out:
                    output_filename = "{}_{}_{}_{}_{}_{}-{}".format(
                        mip, model, exp, run, "monsoon_sperber", startYear, endYear
                    )
                    
                    fout = cdms2.open(
                        os.path.join(
                            outdir(output_type="diagnostic_results"),
                            output_filename + ".nc",
                        ),
                        "w",
                    )
                print(" xxxxxxxxxxx output_filename = .  ", output_filename)
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

                    timechk2 = time.time()
                    timechk = timechk2 - timechk1
                    print("timechk line 443: ", model, run, timechk)
                # -------------------------------------------------
                # Loop start - Year
                # -------------------------------------------------
                temporary = {}

                # year loop, endYear+1 to include last year
                for year in range(startYear, endYear + 1):
                    print('\n')
                    print("RRRRRRRRR. YEAR =  ", year)
                    print('\n')
#                    d = fc(
#                        var,
#                        time=(
#                            cdtime.comptime(year, 1, 1, 0, 0, 0),
#                            cdtime.comptime(year, 12, 31, 23, 59, 59),
#                        ),
#                        latitude=(-90, 90),
#                    )
                    d = dc.pr.sel(time=slice(str(year)+"-01-01 00:00:00",str(year)+"-12-31 23:59:59"), lat=slice(-90,90))
                    print("xxx d =, ",d)
                    print("type d type,", type(d))
                    # unit adjust
                    if UnitsAdjust[0]:
                        """Below two lines are identical to following:
                        d = MV2.multiply(d, 86400.)
                        d.units = 'mm/d'
                        """
#                        d = getattr(MV2, UnitsAdjust[1])(d, UnitsAdjust[2])
                        d.values = d.values * 86400.
                        #d.units = units
                        d["units"] = units
                        print("xxx d =, ",d)
                        print("xxx d type =, ",type(d))
                    
                        timechk2 = time.time()
                        timechk = timechk2 - timechk1
                        print("timechk line 479: ", model, run, timechk)####?????
                
                    # variable for over land only
                    d_land = model_land_only(model, d, lf, debug=debug)
                    #d_land = model_land_only(model, d, ds_lf, debug=debug)# xCDAT 
                    #d_land = ds_lf
                    print('ZZZZZZZZZZZ')
                    print('xxx lf = ', lf)
                    print('xxx d_land = ', d_land)
                    print('model = ', model)

                    print("check: year, d.shape: ", year, d.shape)
                    
                    timechk2 = time.time()
                    timechk = timechk2 - timechk1
                    print("timechk line 492: ", model, run, timechk)###???????

                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Loop start - Monsoon region
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    
                    regions_specs = load_regions_specs()
                    
                    for region in list_monsoon_regions:
                        print('\n')
                        print('region = ',region)
                        print('\n')
                        # extract for monsoon region
                        if region in ["GoG", "NAmo"]:
                            # all grid point rainfall
                            #d_sub = d(regions_specs[region]["domain"])
                            d_sub_ds = region_subset(dc, regions_specs, region=region)
                            d_sub_pr = d_sub_ds.pr.sel(time=slice(str(year)+"-01-01 00:00:00",
                                                      str(year)+"-12-31 23:59:59"))
                            
                        else:
                            # land-only rainfall
                            #d_sub = d_land(regions_specs[region]["domain"])
                            
                            d_sub_ds = region_subset(dc, regions_specs, region=region)
                            d_sub_pr = d_sub_ds.pr.sel(time=slice(str(year)+"-01-01 00:00:00",
                                                                  str(year)+"-12-31 23:59:59"))
                            lf_sub_ds = region_subset(ds_lf, regions_specs, region=region)
                            lf_sub = lf_sub_ds.sftlf
                            print('yyyyyyy dc = ', dc)
                            print('yyyyyyy lf sub = ', lf_sub)
                            print('yyyyyyy lf = ', lf)
                            print('yyyyyyy d_sub_pr = ', d_sub_pr)
                            print("timechk line 531: ", time.time()-timechk1)
                            d_sub_pr = model_land_only(model, d_sub_pr, lf_sub, debug=debug)
                            print("timechk line 533: ", time.time()-timechk1)
                            
                        # Area average
                        #d_sub_aave = cdutil.averager(
                        #    d_sub, axis="xy", weights="weighted"
                        #)
                        
                        ds_sub_pr = d_sub_pr.to_dataset().compute()
                        #ds_sub_pr['time_bnds'] = ds_sub.time_bnds
                        #ds_sub['lat_bnds'] = d_sub_ds.lat_bnds
                        #ds_sub['lon_bnds'] = d_sub_ds.lon_bnds
                        #ds_sub_pr.bounds.add_bounds("X")
                        #ds_sub_pr.bounds.add_bounds("Y")
                        ds_sub_pr = ds_sub_pr.bounds.add_missing_bounds('X')
                        ds_sub_pr = ds_sub_pr.bounds.add_missing_bounds('Y')

                        print("timechk line 543: ", time.time()-timechk1)
                        #ds_sub_aave = ds_sub_pr.spatial.average("pr", axis=["X", "Y"]).compute()#, weights="generated")
                        ds_sub_aave = ds_sub_pr.spatial.average("pr", axis=["X", "Y"],weights="generate").compute()
                        #ds_sub_aave = ds_sub_pr.spatial.spatial_avg("pr", axis=["X", "Y"],weights="generate").compute()
                        print("timechk line 549: ", time.time()-timechk1)
                        d_sub_aave = ds_sub_aave.pr
                        print('d_sub_aave, =    ', d_sub_aave)
                        print('len data  ', len(d_sub_aave))

                        if debug:
                            print("debug: region:", region)
                            print("debug: d_sub.shape:", d_sub.shape)
                            print("debug: d_sub_aave.shape:", d_sub_aave.shape)                         
                            


                        # Southern Hemisphere monsoon domain
                        # set time series as 7/1~6/30
                        if region in ["AUS", "SAmo"]:
                            if year == startYear:
                                #start_t = cdtime.comptime(year, 7, 1)
                                #end_t = cdtime.comptime(year, 12, 31, 23, 59, 59)
                                start_t = str(year)+"-07-01 00:00:00"
                                end_t = str(year)+"-12-31 23:59:59"
                                #temporary[region] = d_sub_aave(time=(start_t, end_t))
                                temporary[region] = d_sub_aave.sel(time=slice(start_t, end_t))

                                continue
                            else:
                                # n-1 year 7/1~12/31
                                part1 = copy.copy(temporary[region])
                                # n year 1/1~6/30
                                #part2 = d_sub_aave(
                                #    time=(
                                #        cdtime.comptime(year),
                                #        cdtime.comptime(year, 6, 30, 23, 59, 59),
                                #    )
                                #)
                                part2 = d_sub_aave.sel(time=slice(str(year)+"-01-01 00:00:00",str(year)+"-06-30 23:59:59"))
                                #start_t = cdtime.comptime(year, 7, 1)
                                #end_t = cdtime.comptime(year, 12, 31, 23, 59, 59)
                                start_t = str(year)+"-07-01 00:00:00"
                                end_t = str(year)+"-12-31 23:59:59"
                                #temporary[region] = d_sub_aave(time=(start_t, end_t))
                                temporary[region] = d_sub_aave.sel(time=slice(start_t, end_t))
                                
                                print('part1 =    ', part1)
                                print('part2 =    ', part2)
                                
                                #d_sub_aave = MV2.concatenate([part1, part2], axis=0)
                                d_sub_aave = xr.concat([part1, part2], dim='time')
                                
                                

                                print('d_sub_aave, =    ', d_sub_aave)
                                
                                
                                if debug:
                                    print(
                                        "debug: ",
                                        region,
                                        year,
                                        #d_sub_aave.getTime().asComponentTime(),
                                        d_sub_aave.time,
                                    )
                                    
                        timechk2 = time.time()
                        timechk = timechk2 - timechk1
                        print("timechk line 597: ", model, run, timechk)##?>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

                        # get pentad time series
                        list_d_sub_aave_chunks = list(
                            divide_chunks_advanced(d_sub_aave, n, debug=debug)
                        )
                        #print('list_d_sub_aave_chunks  = ', list_d_sub_aave_chunks)
                        print("timechk line 603: ", time.time()-timechk1)
                        print('CCCCCCCCCCCCCCCCCC')
                        
                        pentad_time_series = []
                        print('d_sub_aave_chunk 1st  =  ', list_d_sub_aave_chunks[0])
                        for d_sub_aave_chunk in list_d_sub_aave_chunks:
                            # ignore when chunk length is shorter than defined
                            if d_sub_aave_chunk.shape[0] >= n:
                                #ave_chunk = MV2.average(d_sub_aave_chunk, axis=0)
                                #d_sub_aave_chunk.to_netcdf('d_sub_aave_chunk.nc')
                                aa = d_sub_aave_chunk.to_numpy()
                                print("timechk line 611: ", time.time()-timechk1)
                                aa_mean = np.mean(aa)
                                
                                print("timechk line 612: ", time.time()-timechk1)
                                ave_chunk = d_sub_aave_chunk.mean(axis=0, skipna=True).compute()
                                #print('ave_chunk =.  ', ave_chunk)
                                print("timechk line 613: ", time.time()-timechk1)
                                pentad_time_series.append(float(ave_chunk))
                                print("timechk line 614: ", time.time()-timechk1)
                                
                        print('d_sub_aave_chunk  = ', d_sub_aave_chunk)
                        print("timechk line 615: ", time.time()-timechk1)
                        if debug:
                            print(
                                "debug: pentad_time_series length: ",
                                len(pentad_time_series),
                            )
                        timechk2 = time.time()
                        timechk = timechk2 - timechk1
                        print("timechk line 624: ", model, run, timechk)###?????????????????????????????????????????????
                            
                            
                        # Keep pentad time series length in consistent
                        ref_length = int(365 / n)
                        if len(pentad_time_series) < ref_length:
                            pentad_time_series = interp1d(
                                pentad_time_series, ref_length, debug=debug
                            )
                            
                        print('DDDDDDDDDDDDDDDD')
                        print('pentad_time_series = ',pentad_time_series)
                        
                        pentad_time_series_cumsum = np.cumsum(pentad_time_series)
                        pentad_time_series = xr.DataArray(pentad_time_series)
                        pentad_time_series.attrs['units'] = d.units
                        
                        
                        print('EEEEEEEEEEEEEEEEEE')

                        if nc_out:
                            # Archive individual year time series in netCDF file
                            fout.write(pentad_time_series, id=region + "_" + str(year))
                            fout.write(
                                pentad_time_series_cumsum,
                                id=region + "_" + str(year) + "_cumsum",
                            )

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
                        
                        print('FFFFFFFFFFFFFFFFFF')
                        print('list_pentad_time_series[region]  = ', list_pentad_time_series[region])
                        print('list_pentad_time_series_cumsum[region]  = ', list_pentad_time_series_cumsum[region])

                    # --- Monsoon region loop end
                # --- Year loop end
                #fc.close()
                dc.close()

                print('loop DONE!!!!!~   dc.close() ')
                
                
                timechk2 = time.time()
                timechk = timechk2 - timechk1
                print("timechk line 684: ", model, run, timechk)                
                
                
                # -------------------------------------------------
                # Loop start: Monsoon region without year: Composite
                # -------------------------------------------------
                if debug:
                    print("debug: composite start")
                    
                print('list_monsoon_regions   =. ',list_monsoon_regions)

                for region in list_monsoon_regions:
                    # Get composite for each region
#                     composite_pentad_time_series = cdutil.averager(
#                         MV2.array(list_pentad_time_series[region]),
#                         axis=0,
#                         weights="unweighted",
#                     )
                    composite_pentad_time_series = np.array(list_pentad_time_series[region]).mean(axis=0)

                    # Get accumulation ts from the composite
                    composite_pentad_time_series_cumsum = np.cumsum(
                        composite_pentad_time_series
                    )

                    # Maintain axis information
#                     axis0 = pentad_time_series.getAxis(0)
#                     composite_pentad_time_series.setAxis(0, axis0)
#                     composite_pentad_time_series_cumsum.setAxis(0, axis0)

                    # - - - - - - - - - - -
                    # Metrics for composite
                    # - - - - - - - - - - -
            
                    timechk2 = time.time()
                    timechk = timechk2 - timechk1
                    print("timechk line 720: ", model, run, timechk)            
            
                    metrics_result = sperber_metrics(
                        composite_pentad_time_series_cumsum, region, debug=debug
                    )

                
                    timechk2 = time.time()
                    timechk = timechk2 - timechk1
                    print("timechk line 728: ", model, run, timechk)                
                

                    # Normalized cummulative pentad time series
                    composite_pentad_time_series_cumsum_normalized = metrics_result[
                        "frac_accum"
                    ]
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
                        fout.write(composite_pentad_time_series, id=region + "_comp")
                        fout.write(
                            composite_pentad_time_series_cumsum,
                            id=region + "_comp_cumsum",
                        )
                        fout.write(
                            composite_pentad_time_series_cumsum_normalized,
                            id=region + "_comp_cumsum_fraction",
                        )
                        if region == list_monsoon_regions[-1]:
                            fout.close()

                    # Add line in plot
                    if plot:
                        if model != "obs":
                            # model
                            ax[region].plot(
                                # np.array(composite_pentad_time_series),
                                # np.array(composite_pentad_time_series_cumsum),
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
                                    ],
                                    c="red",
                                    ls="--",
                                )
                        # obs
                        ax[region].plot(
                            np.array(dict_obs_composite[reference_data_name][region]),
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
                                ymax=dict_obs_composite[reference_data_name][region][
                                    idx
                                ],
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
                JSON = pcmdi_metrics.io.base.Base(
                    outdir(output_type="metrics_results"), json_filename
                )
                JSON.write(
                    monsoon_stat_dic,
                    json_structure=["model", "realization", "monsoon_region", "metric"],
                    sort_keys=True,
                    indent=4,
                    separators=(",", ": "),
                )
                if cmec:
                    JSON.write_cmec(indent=4, separators=(",", ": "))

            """
            except Exception as err:
                if debug:
                    raise
                else:
                    print("warning: faild for ", model, run, err)
                    pass
            """
            timechk2 = time.time()
            timechk = timechk2 - timechk1
            print("timechk: ", model, run, timechk)
        # --- Realization loop end
    """
    except Exception as err:
        if debug:
            raise
        else:
            print("warning: faild for ", model, err)
            pass
    """
# --- Model loop end

if not debug:
    sys.exit(0)
