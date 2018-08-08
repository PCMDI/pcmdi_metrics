""" Calculate monsoon metrics

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

from __future__ import print_function

import cdms2
import cdtime
import cdutil
import json
import math
import matplotlib.pyplot as plt
import MV2
import numpy as np
import os
import pcmdi_metrics
import sys
import time

from argparse import RawTextHelpFormatter
from collections import defaultdict
from genutil import StringConstructor
from shutil import copyfile
from pcmdi_metrics.monsoon_sperber import AddParserArgument, YearCheck, model_land_only, divide_chunks_advanced, divide_chunks, interp1d

""" NOTE FOR ISSUES
*1. syear/eyear given by parameter file need to be refered in the code
*2. ocean mask for land only is not complete; refer placeholder
*3. pathin need to be fully replaced by modpath
4. reference data (obs) is yet to be used
*5. 72 pentad to 73 pentad interpolation need to be added for HadGEM2 models 
*6. Adding of custom domain maybe needed to test Indian region as in Sperber & Annamalai 2014 Clim Dyn
   (or define the domain in the share/default_regions.py)
7. Make the results_dir aknowledge the tree structure
8. use unit adjust parameter in the code
*9. leaf year
*10. start from July 1st for SH region
*11. add pentad time series to cumulative and archive it in netCDF
*12. calculate metrics based on cumulative pentad time series
*13. add time checker
"""

# =================================================
# Hard coded options... will be moved out later
# -------------------------------------------------
list_monsoon_regions = ['AIR']  # Will be added later
list_monsoon_regions = ['AIR', 'AUS', 'Sahel', 'GoG', 'NAmo', 'SAmo']  # Will be added later

# How many elements each
# list should have
n = 5  # pentad

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pcmdi_metrics.driver.pmp_parser.PMPParser(
        description='Runs PCMDI Monsoon Sperber Computations',
        formatter_class=RawTextHelpFormatter)
P = AddParserArgument(P)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
fq = param.frequency
realm = param.realm

# On/off switches
nc_out = param.nc_out  # Record NetCDF output
plot = param.plot # Generate plots

# Path to model data as string template
modpath = StringConstructor(param.modpath)
modpath_lf = StringConstructor(param.modpath_lf)

# Check given model option
models = param.modnames
print('models:', models)

# Realizations
realization = param.realization
print('realization: ', realization)

# Output
outdir = param.results_dir
print('outdir: ', outdir)

# Create output directory
if not os.path.exists(outdir):
    os.makedirs(outdir)

# Debug
debug = param.debug
print('debug: ', debug)

# Variables
var = param.varModel

# Year
syear = param.msyear
eyear = param.meyear
YearCheck(syear, eyear, P)

osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# =================================================
# Declare dictionary for .json record
# -------------------------------------------------
def tree():
    return defaultdict(tree)

monsoon_stat_dic = tree()

# Define output json file ---
json_filename = '_'.join(['monsoon_sperber_stat', 
                          mip, exp, fq, realm, str(syear)+'-'+str(eyear)])
json_file = os.path.join(outdir, json_filename + '.json')
json_file_org = os.path.join(
    outdir, '_'.join([json_filename, 'org', str(os.getpid())])+'.json')

# Save pre-existing json file against overwriting ---
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)

    update_json = param.update_json

    if update_json:
        fj = open(json_file)
        monsoon_stat_dic = json.loads(fj.read())
        fj.close()

if 'REF' not in list(monsoon_stat_dic.keys()):
    monsoon_stat_dic['REF'] = {}
if 'RESULTS' not in list(monsoon_stat_dic.keys()):
    monsoon_stat_dic['RESULTS'] = {}

# =================================================
# Loop start - Model
# -------------------------------------------------
regions_specs = {}
exec(compile(open(os.path.join(sys.prefix, "share", "pmp", "default_regions.py") ).read(),
             os.path.join(sys.prefix, "share", "pmp" ,"default_regions.py"), 'exec'))

for model in models:
    print(' ----- ', model, ' ---------------------')

    if model not in list(monsoon_stat_dic['RESULTS'].keys()):
        monsoon_stat_dic['RESULTS'][model] = {}

    model_path_list = os.popen(
        'ls '+modpath(model=model, exp=exp,
        realization=realization, variable=var)).readlines() 

    if debug:
        print('debug: model_path_list: ', model_path_list)

    model_lf_path = modpath_lf(model=model)
    if os.path.isfile(model_lf_path):
        pass
    else:
        model_lf_path = modpath_lf(model=model.upper())
    print(model_lf_path)

    # Read model's land fraction
    f_lf = cdms2.open(model_lf_path)
    lf = f_lf('sftlf', latitude=(-90, 90))
 
    # -------------------------------------------------
    # Loop start - Realization
    # -------------------------------------------------
    for model_path in model_path_list:

        timechk1 = time.time()
        try:
            run = model_path.split('/')[-1].split('.')[3]
            print(' --- ', run, ' ---')
            print(model_path)

            if run not in list(monsoon_stat_dic['RESULTS'][model].keys()):
                monsoon_stat_dic['RESULTS'][model][run] = {}

            # Get time coordinate information
            fc = cdms2.open(model_path)
            d = fc[var]  # NOTE: square brackets does not bring data into memory, only coordinates!
            t = d.getTime()
            c = t.asComponentTime()

            startYear = max(syear, c[0].year)
            endYear = min(eyear, c[-1].year)
            startMonth = c[0].month
            endMonth = c[-1].month

            # Consider year only when entire calendar available
            if startMonth > 1:
                startYear += 1
            if endMonth < 12:
                endYear -= 1

            # Check calendar (just checking..)
            calendar = d.getTime().calendar
            print('check: calendar: ', calendar)

            if debug:
                print('debug: startYear: ', type(startYear), startYear)
                print('debug: startMonth: ', type(startMonth), startMonth)
                print('debug: endYear: ', type(endYear), endYear)
                print('debug: endMonth: ', type(endMonth), endMonth)
                #endYear = startYear + 4
                endYear = startYear + 1

            list_pentad_time_series = {}  # Archive individual year pentad time series for composite
            list_pentad_time_series_cumsum = {} # For cumulative time series
            for region in list_monsoon_regions:
                list_pentad_time_series[region] = []
                list_pentad_time_series_cumsum[region] =[]

            if nc_out:
                output_file_name = '_'.join([mip, model, exp, run,
                    'monsoon_sperber', str(startYear), str(endYear)])
                fout = cdms2.open(os.path.join(outdir, output_file_name+'.nc'), 'w')

            # -------------------------------------------------
            # Plotting tool
            # -------------------------------------------------
            if plot:
                ax = {}
                if len(list_monsoon_regions) > 1:
                    nrows = math.ceil(len(list_monsoon_regions)/2.)
                    ncols = 2
                else:
                    nrows = 1
                    ncols = 1
            
                fig = plt.figure()
                plt.subplots_adjust(hspace = 0.25)
            
                for i, region in enumerate(list_monsoon_regions):
                    ax[region] = plt.subplot(nrows, ncols, i+1)
                    print('plot: region', region, 'nrows', nrows, 'ncols', ncols, 'index', i+1)
                    if nrows > 1 and math.ceil((i+1)/float(ncols)) < nrows:
                        ax[region].set_xticks([])
            
                fig.text(0.5, 0.04, 'pentad count', ha='center')
                fig.text(0.03, 0.5, 'pentad precip mm/d', va='center', rotation='vertical')
            
            # -------------------------------------------------
            # Loop start - Year
            # -------------------------------------------------
            temporary = {}

            for year in range(startYear, endYear+1):  # year loop, endYear+1 to include last year
                d = fc(var,
                       time=(cdtime.comptime(year),cdtime.comptime(year+1)),
                       latitude=(-90,90))

                # unit change
                d = MV2.multiply(d, 86400.)
                d.units = 'mm/d'

                # land only
                #d_land = model_land_only(model, d, model_lf_path, debug=debug)
                d_land = model_land_only(model, d, lf, debug=debug)

                print('check: year, d.shape: ', year, d.shape)

                # - - - - - - - - - - - - - - - - - - - - - - - - -
                # Loop start - Monsoon region
                # - - - - - - - - - - - - - - - - - - - - - - - - -
                for region in list_monsoon_regions:
                    # extract for monsoon region
                    if region in ['GoG', 'NAmo']:  # all grid point rainfall
                        d_sub = d(regions_specs[region]['domain'])
                    else:  # land-only rainfall
                        d_sub = d_land(regions_specs[region]['domain'])
                    # area average
                    d_sub_aave = cdutil.averager(d_sub, axis='xy', weights='weighted')

                    if debug: 
                        print('debug: region: ', region)
                        print('debug: d_sub.shape: ', d_sub.shape)
                        print('debug: d_sub_aave.shape: ', d_sub_aave.shape)

                    # Southern Hemisphere monsoon domain -- set time series as 7/1~6/30
                    if region in ['AUS', 'SAmo']:
                        if year == startYear:
                            temporary[region] = d_sub_aave(time=(cdtime.comptime(year,7,1),cdtime.comptime(year+1)))
                            continue
                        else:
                            part1 = temporary[region] # n-1 year 7/1~12/31
                            part2 = d_sub_aave(time=(cdtime.comptime(year),cdtime.comptime(year,7,1))) # n year 1/1~6/30
                            temporary[region] = d_sub_aave(time=(cdtime.comptime(year,7,1),cdtime.comptime(year+1)))
                            d_sub_aave = MV2.concatenate([part1,part2],axis=0)
                            if debug:
                                print('debug: ', region, year, d_sub_aave.getTime().asComponentTime())

                    # get pentad time series
                    list_d_sub_aave_chunks = list(divide_chunks_advanced(d_sub_aave, n, debug=debug)) 
                    pentad_time_series = []
                    for d_sub_aave_chunk in list_d_sub_aave_chunks:
                        if d_sub_aave_chunk.shape[0] >= n:  # ignore when chunk length is shorter than defined
                            ave_chunk = MV2.average(d_sub_aave_chunk, axis=0)
                            pentad_time_series.append(float(ave_chunk))
                    if debug:
                        print('debug: pentad_time_series length: ', len(pentad_time_series))

                    # Keep pentad time series length in consistent
                    ref_length = int(365/n)
                    if len(pentad_time_series) < ref_length:
                        pentad_time_series = interp1d(pentad_time_series, ref_length, debug=debug) 

                    pentad_time_series = MV2.array(pentad_time_series)
                    pentad_time_series.units = d.units
                    pentad_time_series_cumsum = np.cumsum(pentad_time_series)

                    if nc_out:
                        fout.write(pentad_time_series, id=region+'_'+str(year))
                        fout.write(pentad_time_series_cumsum, id=region+'_'+str(year)+'_cumsum')
                    if plot:
                        if year == startYear:
                            label = 'Individual yr'
                        else:
                            label = ''
                        #ax[region].plot(np.array(pentad_time_series), c='grey', label=label)
                        ax[region].plot(np.array(pentad_time_series_cumsum), c='grey', label=label)

                    # Archive for composite
                    list_pentad_time_series[region].append(pentad_time_series)
                    list_pentad_time_series_cumsum[region].append(pentad_time_series_cumsum)

                # --- Monsoon region loop end
            # --- Year loop end
            fc.close()

            # --- Monsoon region loop start without year loop
            # Get composite for each region
            if debug:
                print('debug: composite start')

            for region in list_monsoon_regions:
                composite_pentad_time_series = cdutil.averager(
                    MV2.array(list_pentad_time_series[region]),
                    axis=0,
                    weights='unweighted')
                composite_pentad_time_series.setAxis(
                    0, pentad_time_series.getAxis(0))
                composite_pentad_time_series_cumsum = np.cumsum(composite_pentad_time_series)
                composite_pentad_time_series_cumsum.setAxis(
                    0, pentad_time_series.getAxis(0))

                # Metrics for composite
                metrics_result = sperber_metrics(composite_pentad_time_series_cumsum, region, debug=debug)

                if region not in list(monsoon_stat_dic['RESULTS'][model][run].keys()):
                    monsoon_stat_dic['RESULTS'][model][run][region] = {}

                monsoon_stat_dic['RESULTS'][model][run][region]['onset_index'] = metrics_result['onset_index']
                monsoon_stat_dic['RESULTS'][model][run][region]['decay_index'] = metrics_result['decay_index']
                monsoon_stat_dic['RESULTS'][model][run][region]['slope'] = metrics_result['slope']

                if nc_out:
                    fout.write(composite_pentad_time_series, id=region+'_comp')
                    fout.write(composite_pentad_time_series_cumsum, id=region+'_comp_cumsum')
                    fout.write(metrics_result['frac_accum'], id=region+'_comp_cumsum_frac')
                if plot:
                    ax[region].plot(
                        #np.array(composite_pentad_time_series),
                        np.array(composite_pentad_time_series_cumsum),
                        c='red',
                        label='Composite')
                    ax[region].set_title(region)
                    if region == list_monsoon_regions[0]:
                        ax[region].legend(loc=2)

            if nc_out:
                fout.close()
            if plot:
                fig.suptitle(
                    'Precipitation pentad time series\n'
                    + ', '.join([mip, model, exp, run, str(startYear)+'-'+str(endYear)]))
                plt.subplots_adjust(top=0.85)
                plt.savefig(os.path.join(outdir, output_file_name+'.png'))
                plt.close()

            # =================================================
            # Write dictionary to json file
            # (let the json keep overwritten in model loop)
            # -------------------------------------------------
            JSON = pcmdi_metrics.io.base.Base(outdir, json_filename)
            JSON.write(monsoon_stat_dic,
                       json_structure=["data",
                                       "model",
                                       "realization",
                                       "monsoon_region",
                                       "metric"],
                       sort_keys=True,
                       indent=4,
                       separators=(',', ': '))

        except Exception as err:
            if debug:
                raise
            else:
                print('warning: faild for ', model, run, err, ',')
                pass

        timechk2 = time.time()
        timechk = timechk2 - timechk1
        print('timechk: ', model, run, timechk)
    # --- Realization loop end

    f_lf.close()
# --- Model loop end

if not debug:
    sys.exit('done')
