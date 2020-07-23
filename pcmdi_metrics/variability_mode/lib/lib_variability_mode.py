from __future__ import print_function
from collections import defaultdict
from datetime import datetime
from time import gmtime, strftime
import cdms2
import cdtime
import cdutil
import copy
import MV2
import pcmdi_metrics
import re


def tree():
    return defaultdict(tree)


def write_nc_output(output_file_name,
                    eofMap, pc, frac, slopeMap, interceptMap):
    fout = cdms2.open(output_file_name+'.nc', 'w')
    # 1-d timeseries having time dimension: write time first
    fout.write(pc, id='pc')
    # 2-d maps having no time axis
    fout.write(eofMap, id='eof')
    fout.write(slopeMap, id='slope')
    fout.write(interceptMap, id='intercept')
    # single number having no axis
    fout.write(frac, id='frac')
    fout.close()


def get_domain_range(mode, regions_specs):
    if mode == 'NPGO':
        mode_origin_domain = 'PDO'
    elif mode == 'NPO':
        mode_origin_domain = 'PNA'
    else:
        mode_origin_domain = mode

    region_subdomain = regions_specs[mode_origin_domain]['domain']
    return region_subdomain


def read_data_in(
        path, var_in_data, var_to_consider,
        start_time, end_time,
        UnitsAdjust, LandMask, debug=False):

    f = cdms2.open(path)
    data_timeseries = f(var_in_data, time=(start_time, end_time), latitude=(-90, 90))
    cdutil.setTimeBoundsMonthly(data_timeseries)

    # missing data check
    check_missing_data(data_timeseries)

    if UnitsAdjust[0]:
        data_timeseries = getattr(MV2, UnitsAdjust[1])(
            data_timeseries, UnitsAdjust[2])

    if var_to_consider == 'ts' and LandMask:
        # Replace temperature below -1.8 C to -1.8 C (sea ice)
        data_timeseries = sea_ice_adjust(data_timeseries)

    # Check available time window and adjust if needed
    data_stime = data_timeseries.getTime().asComponentTime()[0]
    data_etime = data_timeseries.getTime().asComponentTime()[-1]

    data_syear = data_stime.year
    data_smonth = data_stime.month
    data_eyear = data_etime.year
    data_emonth = data_etime.month

    if data_smonth > 1:
        data_syear = data_syear + 1
    if data_emonth < 12:
        data_eyear = data_eyear - 1

    debug_print(
        'data_syear: '+str(data_syear)+' data_eyear: '+str(data_eyear),
        debug)

    data_timeseries = data_timeseries(time=(
        cdtime.comptime(data_syear, 1, 1, 0, 0, 0),
        cdtime.comptime(data_eyear, 12, 31, 23, 59, 59)))

    f.close()

    return data_timeseries, data_syear, data_eyear


def check_missing_data(d):
    time = d.getTime().asComponentTime()
    num_tstep = d.shape[0]
    months_between = diff_month(datetime(time[-1].year, time[-1].month, 1),
                                datetime(time[0].year, time[0].month, 1))
    if num_tstep < months_between:
        raise ValueError("ERROR: check_missing_data: num_data_timestep, expected_num_timestep:",
                         num_tstep, months_between)


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def debug_print(string, debug):
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print('debug: '+nowtime+' '+string)


def sort_human(input_list):
    lst = copy.copy(input_list)

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]

    lst.sort(key=alphanum)
    return lst


def sea_ice_adjust(data_array):
    """
    Note: Replace temperature below -1.8 C to -1.8 C (sea-ice adjustment)
    input
    - data_array: cdms2 array
    output
    - data_array: cdms2 array (adjusted)
    """
    data_mask = copy.copy(data_array.mask)
    data_array[data_array < -1.8] = -1.8
    data_array.mask = data_mask
    return data_array


def mov_metrics_to_json(outdir, json_filename, result_dict, model=None, run=None):
    # Open JSON
    JSON = pcmdi_metrics.io.base.Base(
        outdir(output_type='metrics_results'),
        json_filename)
    # Dict for JSON
    if (model is None and run is None):
        result_dict_to_json = result_dict
    else:
        # Preserve only needed dict branch
        result_dict_to_json = result_dict.copy()
        models_in_dict = list(result_dict_to_json['RESULTS'].keys())
        for m in models_in_dict:
            if m == model:
                runs_in_model_dict = list(result_dict_to_json['RESULTS'][m].keys())
                for r in runs_in_model_dict:
                    if r != run:
                        del result_dict_to_json['RESULTS'][m][r]
            else:
                del result_dict_to_json['RESULTS'][m]
    # Write selected dict to JSON
    JSON.write(
        result_dict_to_json,
        json_structure=[
            "model", "realization", "reference",
            "mode", "season", "method", "statistic"],
        sort_keys=True, indent=4, separators=(',', ': '))
