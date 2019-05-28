#!/usr/bin/env python
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
import copy
import json
import math
import matplotlib.pyplot as plt
import MV2
import numpy as np
import os
import pcmdi_metrics
import pkg_resources
import sys
import time

from argparse import RawTextHelpFormatter
from collections import defaultdict
from shutil import copyfile
from pcmdi_metrics.monsoon_sperber import AddParserArgument, YearCheck
from pcmdi_metrics.monsoon_sperber import model_land_only
from pcmdi_metrics.monsoon_sperber import divide_chunks_advanced, interp1d
from pcmdi_metrics.monsoon_sperber import sperber_metrics

# =================================================
# Hard coded options... will be moved out later
# -------------------------------------------------
list_monsoon_regions = ['AIR', 'AUS', 'Sahel', 'GoG', 'NAmo', 'SAmo']

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
plot = param.plot  # Generate plots
includeOBS = param.includeOBS  # Loop run for OBS or not

# Path to reference data
reference_data_name = param.reference_data_name
reference_data_path = param.reference_data_path
reference_data_lf_path = param.reference_data_lf_path

# Path to model data as string template
modpath = param.process_templated_argument("modpath")
modpath_lf = param.process_templated_argument("modpath_lf")

# Check given model option
models = param.modnames
print('models:', models)

# Realizations
realization = param.realization
print('realization: ', realization)

# Output
outdir = param.process_templated_argument("results_dir")

# Create output directory
for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# Debug
debug = param.debug
print('debug: ', debug)

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
def tree():
    return defaultdict(tree)

monsoon_stat_dic = tree()

# Define output json file
json_filename = '_'.join(['monsoon_sperber_stat',
                          mip, exp, fq, realm, str(msyear)+'-'+str(meyear)])
json_file = os.path.join(outdir(output_type='metrics_results'), json_filename + '.json')
json_file_org = os.path.join(
    outdir(output_type='metrics_results'), '_'.join([json_filename, 'org', str(os.getpid())])+'.json')

# Save pre-existing json file against overwriting
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)
    if update_json:
        fj = open(json_file)
        monsoon_stat_dic = json.loads(fj.read())
        fj.close()

if 'REF' not in list(monsoon_stat_dic.keys()):
    monsoon_stat_dic['REF'] = {}
if 'RESULTS' not in list(monsoon_stat_dic.keys()):
    monsoon_stat_dic['RESULTS'] = {}

# =================================================
# Loop start for given models
# -------------------------------------------------
"""
regions_specs = {}
exec(compile(open(os.path.join(sys.prefix, "share",
                               "pmp", "default_regions.py")).read(),
             os.path.join(sys.prefix, "share", "pmp",
                          "default_regions.py"), 'exec'))
"""
regions_specs = {}
egg_pth = pkg_resources.resource_filename(
    pkg_resources.Requirement.parse("pcmdi_metrics"), 
    "share/pmp")
exec(compile(open(os.path.join(egg_pth, "default_regions.py")).read(),
os.path.join(egg_pth, "default_regions.py"), 'exec'))

if includeOBS:
    models.insert(0, 'obs')

for model in models:
    print(' ----- ', model, ' ---------------------')
    try:
        # Conditions depending obs or model
        if model == 'obs':
            var = varOBS
            UnitsAdjust = ObsUnitsAdjust
            syear = osyear
            eyear = oeyear
            # variable data
            model_path_list = [reference_data_path]
            # land fraction
            model_lf_path = reference_data_lf_path
            # dict for output JSON
            if reference_data_name not in list(monsoon_stat_dic['REF'].keys()):
                monsoon_stat_dic['REF'][reference_data_name] = {}
            # dict for plottng
            dict_obs_composite = {}
            dict_obs_composite[reference_data_name] = {}
        else:  # for rest of models
            var = varModel
            UnitsAdjust = ModUnitsAdjust
            syear = msyear
            eyear = meyear
            # variable data
            model_path_list = os.popen(
                'ls '+modpath(model=model, exp=exp, realization=realization,
                 variable=var)).readlines()
            if debug: print('debug: model_path_list: ', model_path_list)
            # land fraction
            model_lf_path = modpath_lf(model=model)
            if os.path.isfile(model_lf_path):
                pass
            else:
                model_lf_path = modpath_lf(model=model.upper())
            # dict for output JSON
            if model not in list(monsoon_stat_dic['RESULTS'].keys()):
                monsoon_stat_dic['RESULTS'][model] = {}

        # Read land fraction
        print('lf_path: ',  model_lf_path)
        f_lf = cdms2.open(model_lf_path)
        lf = f_lf('sftlf', latitude=(-90, 90))
        f_lf.close()

        # -------------------------------------------------
        # Loop start - Realization
        # -------------------------------------------------
        for model_path in model_path_list:
            timechk1 = time.time()
            try:
                if model == 'obs':
                    run = 'obs'
                else:
                    run = model_path.split('/')[-1].split('.')[3]
                    # dict
                    if run not in monsoon_stat_dic['RESULTS'][model]:
                        monsoon_stat_dic['RESULTS'][model][run] = {}
                print(' --- ', run, ' ---')
                print(model_path)

                # Get time coordinate information
                fc = cdms2.open(model_path)
                # NOTE: square brackets does not bring data into memory
                # only coordinates!
                d = fc[var]
                t = d.getTime()
                c = t.asComponentTime()

                # Get starting and ending year and month
                startYear = c[0].year
                startMonth = c[0].month
                endYear = c[-1].year
                endMonth = c[-1].month

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
                calendar = t.calendar
                print('check: calendar: ', calendar)

                if debug:
                    print('debug: startYear: ', type(startYear), startYear)
                    print('debug: startMonth: ', type(startMonth), startMonth)
                    print('debug: endYear: ', type(endYear), endYear)
                    print('debug: endMonth: ', type(endMonth), endMonth)
                    endYear = startYear + 1

                # Prepare archiving individual year pentad time series for composite
                list_pentad_time_series = {}
                list_pentad_time_series_cumsum = {}  # Cumulative time series
                for region in list_monsoon_regions:
                    list_pentad_time_series[region] = []
                    list_pentad_time_series_cumsum[region] = []

                # Write individual year time series for each monsoon domain
                # in a netCDF file
                if nc_out:
                    output_filename = "{}_{}_{}_{}_{}_{}_{}".format(
                        mip, model, exp,
                        run, 'monsoon_sperber', startYear, endYear)
                    fout = cdms2.open(os.path.join(
                        outdir(output_type='diagnostic_results'),
                        output_filename+'.nc'), 'w')

                # Plotting setup
                if plot:
                    ax = {}
                    if len(list_monsoon_regions) > 1:
                        nrows = math.ceil(len(list_monsoon_regions)/2.)
                        ncols = 2
                    else:
                        nrows = 1
                        ncols = 1

                    fig = plt.figure(figsize=[6.4, 6.4])
                    plt.subplots_adjust(hspace=0.25)

                    for i, region in enumerate(list_monsoon_regions):
                        ax[region] = plt.subplot(nrows, ncols, i+1)
                        ax[region].set_ylim(0,1) 
                        ax[region].margins(x=0)
                        print('plot: region', region, 'nrows',
                              nrows, 'ncols', ncols, 'index', i+1)
                        if nrows > 1 and math.ceil((i+1)/float(ncols)) < nrows:
                            ax[region].set_xticklabels([])
                        if ncols > 1 and (i+1) % 2 == 0:
                            ax[region].set_yticklabels([])

                    fig.text(0.5, 0.04, 'pentad count', ha='center')
                    fig.text(0.03, 0.5, 'accumulative pentad precip fraction',
                             va='center', rotation='vertical')

                # -------------------------------------------------
                # Loop start - Year
                # -------------------------------------------------
                temporary = {}

                # year loop, endYear+1 to include last year
                for year in range(startYear, endYear+1):
                    d = fc(var,
                           time=(cdtime.comptime(year, 1, 1, 0, 0, 0),
                                 cdtime.comptime(year, 12, 31, 23, 59, 59)),
                           latitude=(-90, 90))
                    # unit adjust
                    if UnitsAdjust[0]:
                        """ Below two lines are identical to following:
                        d = MV2.multiply(d, 86400.)
                        d.units = 'mm/d'
                        """
                        d = getattr(MV2, UnitsAdjust[1])(d, UnitsAdjust[2])
                        d.units = units
                    # variable for over land only
                    d_land = model_land_only(model, d, lf, debug=debug)

                    print('check: year, d.shape: ', year, d.shape)

                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Loop start - Monsoon region
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    for region in list_monsoon_regions:
                        # extract for monsoon region
                        if region in ['GoG', 'NAmo']:
                            # all grid point rainfall
                            d_sub = d(regions_specs[region]['domain'])
                        else:
                            # land-only rainfall
                            d_sub = d_land(regions_specs[region]['domain'])
                        # Area average
                        d_sub_aave = cdutil.averager(
                            d_sub, axis='xy', weights='weighted')

                        if debug:
                            print('debug: region:', region)
                            print('debug: d_sub.shape:', d_sub.shape)
                            print('debug: d_sub_aave.shape:', d_sub_aave.shape)

                        # Southern Hemisphere monsoon domain
                        # set time series as 7/1~6/30
                        if region in ['AUS', 'SAmo']:
                            if year == startYear:
                                start_t = cdtime.comptime(year, 7, 1)
                                end_t = cdtime.comptime(
                                    year, 12, 31, 23, 59, 59)
                                temporary[region] = d_sub_aave(
                                    time=(start_t, end_t))
                                continue
                            else:
                                # n-1 year 7/1~12/31
                                part1 = copy.copy(temporary[region])
                                # n year 1/1~6/30
                                part2 = d_sub_aave(time=(cdtime.comptime(
                                    year), cdtime.comptime(year, 6, 30, 23,
                                                           59, 59)))
                                start_t = cdtime.comptime(year, 7, 1)
                                end_t = cdtime.comptime(
                                    year, 12, 31, 23, 59, 59)
                                temporary[region] = d_sub_aave(
                                    time=(start_t, end_t))
                                d_sub_aave = MV2.concatenate(
                                    [part1, part2], axis=0)
                                if debug:
                                    print('debug: ', region, year,
                                          d_sub_aave.getTime().asComponentTime())

                        # get pentad time series
                        list_d_sub_aave_chunks = list(
                            divide_chunks_advanced(d_sub_aave, n, debug=debug))
                        pentad_time_series = []
                        for d_sub_aave_chunk in list_d_sub_aave_chunks:
                            # ignore when chunk length is shorter than defined
                            if d_sub_aave_chunk.shape[0] >= n:
                                ave_chunk = MV2.average(
                                    d_sub_aave_chunk, axis=0)
                                pentad_time_series.append(float(ave_chunk))
                        if debug:
                            print('debug: pentad_time_series length: ',
                                  len(pentad_time_series))

                        # Keep pentad time series length in consistent
                        ref_length = int(365/n)
                        if len(pentad_time_series) < ref_length:
                            pentad_time_series = interp1d(
                                pentad_time_series, ref_length, debug=debug)

                        pentad_time_series = MV2.array(pentad_time_series)
                        pentad_time_series.units = d.units
                        pentad_time_series_cumsum = np.cumsum(
                            pentad_time_series)

                        if nc_out:
                            # Archive individual year time series in netCDF file
                            fout.write(pentad_time_series,
                                       id=region+'_'+str(year))
                            fout.write(pentad_time_series_cumsum,
                                       id=region+'_'+str(year)+'_cumsum')

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
                        list_pentad_time_series[region].append(
                            pentad_time_series)
                        list_pentad_time_series_cumsum[region].append(
                            pentad_time_series_cumsum)

                    # --- Monsoon region loop end
                # --- Year loop end
                fc.close()

                # -------------------------------------------------
                # Loop start: Monsoon region without year: Composite
                # -------------------------------------------------
                if debug:
                    print('debug: composite start')

                for region in list_monsoon_regions:
                    # Get composite for each region
                    composite_pentad_time_series = cdutil.averager(
                        MV2.array(list_pentad_time_series[region]),
                        axis=0,
                        weights='unweighted')

                    # Get accumulation ts from the composite
                    composite_pentad_time_series_cumsum = np.cumsum(
                        composite_pentad_time_series)

                    # Maintain axis information
                    axis0 = pentad_time_series.getAxis(0)
                    composite_pentad_time_series.setAxis(0, axis0)
                    composite_pentad_time_series_cumsum.setAxis(0, axis0)

                    # - - - - - - - - - - -
                    # Metrics for composite
                    # - - - - - - - - - - -
                    metrics_result = sperber_metrics(
                        composite_pentad_time_series_cumsum, region, debug=debug)

                    # Normalized cummulative pentad time series
                    composite_pentad_time_series_cumsum_normalized = metrics_result['frac_accum']
                    if model == 'obs':
                        dict_obs_composite[reference_data_name][region] = {}
                        dict_obs_composite[reference_data_name][region] = composite_pentad_time_series_cumsum_normalized

                    # Archive as dict for JSON
                    if model == 'obs':
                        dict_head = monsoon_stat_dic['REF'][reference_data_name]
                    else:
                        dict_head = monsoon_stat_dic['RESULTS'][model][run]
                    # generate key if not there
                    if region not in list(dict_head.keys()):
                        dict_head[region] = {}
                    # generate keys and save for statistics
                    dict_head[region]['onset_index'] = metrics_result['onset_index']
                    dict_head[region]['decay_index'] = metrics_result['decay_index']
                    dict_head[region]['slope'] = metrics_result['slope']
                    dict_head[region]['duration'] = metrics_result['duration']

                    # Archice in netCDF file
                    if nc_out:
                        fout.write(composite_pentad_time_series,
                                   id=region+'_comp')
                        fout.write(composite_pentad_time_series_cumsum,
                                   id=region+'_comp_cumsum')
                        fout.write(composite_pentad_time_series_cumsum_normalized,
                                   id=region+'_comp_cumsum_fraction')
                        if region == list_monsoon_regions[-1]:
                            fout.close()

                    # Add line in plot
                    if plot:
                        if model != 'obs':
                            # model
                            ax[region].plot(
                                #np.array(composite_pentad_time_series),
                                #np.array(composite_pentad_time_series_cumsum),
                                np.array(composite_pentad_time_series_cumsum_normalized),
                                c='red',
                                label=model)
                                #label='Composite')
                            for idx in [metrics_result['onset_index'], metrics_result['decay_index']]:
                                ax[region].axvline(
                                    x=idx,
                                    ymin=0,
                                    ymax=composite_pentad_time_series_cumsum_normalized[idx],
                                    c='red', ls='--')
                        # obs
                        ax[region].plot(
                            np.array(dict_obs_composite[reference_data_name][region]),
                            c='blue',
                            label=reference_data_name)
                        for idx in [
                            monsoon_stat_dic['REF'][reference_data_name][region]['onset_index'], 
                            monsoon_stat_dic['REF'][reference_data_name][region]['decay_index']]:
                            ax[region].axvline(
                                x=idx,
                                ymin=0,
                                ymax=dict_obs_composite[reference_data_name][region][idx],
                                c='blue', ls='--')
                        # title
                        ax[region].set_title(region)
                        if region == list_monsoon_regions[0]:
                            ax[region].legend(loc=2)
                        if region == list_monsoon_regions[-1]:
                            if model == 'obs':
                                data_name = 'OBS: '+reference_data_name
                            else:
                                data_name = ', '.join([mip.upper(), model, exp, run])
                            fig.suptitle(
                                'Precipitation pentad time series\n' +
                                'Monsoon domain composite accumulations\n' +
                                ', '.join([data_name, str(startYear)+'-'+str(endYear)]))
                            plt.subplots_adjust(top=0.85)
                            plt.savefig(os.path.join(
                                outdir(output_type='graphics'), output_filename+'.png'))
                            plt.close()

                # =================================================
                # Write dictionary to json file
                # (let the json keep overwritten in model loop)
                # -------------------------------------------------
                JSON = pcmdi_metrics.io.base.Base(outdir(output_type='metrics_results'), json_filename)
                JSON.write(monsoon_stat_dic,
                           json_structure=["model",
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
                    print('warning: faild for ', model, run, err)
                    pass

            timechk2 = time.time()
            timechk = timechk2 - timechk1
            print('timechk: ', model, run, timechk)
        # --- Realization loop end

    except Exception as err:
        if debug:
            raise
        else:
            print('warning: faild for ', model, err)
            pass
# --- Model loop end

if not debug:
    sys.exit('done')
