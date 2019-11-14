#!/usr/bin/env python

from __future__ import print_function
from genutil import StringConstructor
from pcmdi_metrics.variability_mode.lib import dict_merge

import glob
import json
import os

# -------------------------------
mode = 'NAM'
eof = 'EOF1'
mip = 'cmip5'
exp = 'historical'
case_id = 'v20191114'
obs = 'NOAA-CIRES_20CR'
syear = 1900
eyear = 2005
# -------------------------------

pmprdir = '/work/lee1043/imsi/result_test'
json_file_dir_template = 'metrics_results/variability_modes/%(mip)/%(exp)/%(case_id)/%(mode)/%(obs)'
json_file_dir_template = StringConstructor(json_file_dir_template)
json_file_dir = os.path.join(
    pmprdir,
    json_file_dir_template(mip=mip, exp=exp, case_id=case_id, mode=mode, obs=obs))

json_file_template = 'var_mode_%(mode)_%(eof)_stat_%(mip)_%(exp)_mo_atm_%(model)_%(run)_%(syear)-%(eyear).json'
json_file_template = StringConstructor(json_file_template)

# Search for individual JSONs
json_files = sorted(glob.glob(
    os.path.join(
        json_file_dir,
        json_file_template(mode=mode, eof=eof, mip=mip, exp=exp, model='*', run='*', syear='*', eyear='*'))))

print('json_files:', json_files)

# Load individual JSON and merge to one big dictionary
for j, json_file in enumerate(json_files):
    print(j, json_file)
    f = open(json_file)
    dict_tmp = json.loads(f.read())
    if j == 0:
        dict_final = dict_tmp.copy()
    else:
        dict_merge(dict_final, dict_tmp)
    f.close()

# Dump final dictionary to JSON
final_json_filename = json_file_template(
    mode=mode, eof=eof, mip=mip, exp=exp, model='allModels', run='allRuns', syear=str(syear), eyear=str(eyear))
final_json_file = os.path.join(json_file_dir, final_json_filename)

with open(final_json_file, 'w') as fp:
    json.dump(dict_final, fp, sort_keys=True, indent=4)
