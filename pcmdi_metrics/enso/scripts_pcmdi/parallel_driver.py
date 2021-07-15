#!/usr/bin/env python

"""
Usage example:
1. First realization per model
./parallel_driver.py -p my_Param_ENSO.py --mip cmip6 --modnames all --realization r1i1p1f1 --metricsCollection ENSO_perf
2. All realizations of individual models
./parallel_driver.py -p my_Param_ENSO.py --mip cmip6 --modnames all --realization all --metricsCollection ENSO_perf
"""

from __future__ import print_function
from genutil import StringConstructor

from pcmdi_metrics.enso.lib import AddParserArgument, find_realm
from pcmdi_metrics.variability_mode.lib import sort_human
from pcmdi_metrics.misc.scripts import parallel_submitter

import glob
import os

# =================================================
# Collect user defined options
# -------------------------------------------------
param = AddParserArgument()

# Pre-defined options
mip = param.mip
exp = param.exp
print('mip:', mip)
print('exp:', exp)

# Path to model data as string template
modpath = param.process_templated_argument("modpath")

# Check given model option
models = param.modnames
print('models:', models)

# Include all models if conditioned
if mip == "CLIVAR_LE":
    inline_separator = '_'
else:
    inline_separator = '.'

if ('all' in [m.lower() for m in models]) or (models == 'all'):
    model_index_path = param.modpath.split('/')[-1].split(inline_separator).index("%(model)")
    models = ([p.split('/')[-1].split(inline_separator)[model_index_path] for p in glob.glob(modpath(
                mip=mip, exp=exp, model='*', realization='*', variable='ts'))])
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print('models:', models)
print('number of models:', len(models))

# Realizations
realization = param.realization
if ('all' in [r.lower() for r in realization]) or (realization == 'all'):
    realization = '*'
print('realization: ', realization)

# Metrics Collection
mc_name = param.metricsCollection

# case id
case_id = param.case_id
print('case_id:', case_id)

# Output
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)',
    mip=mip, exp=exp, metricsCollection=mc_name, case_id=case_id)))

# Debug
debug = param.debug
print('debug:', debug)

# =================================================
# Create output directories
# -------------------------------------------------
for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# =================================================
# Generates list of command
# -------------------------------------------------
if mip == "obs2obs":
    param_file = '../param/my_Param_ENSO_obs2obs.py'
if mip == "CLIVAR_LE":
    # param_file = '../param/my_Param_ENSO_PCMDIobs_CLIVAR_LE-CESM1-CAM5.py'
    param_file = '../param/my_Param_ENSO_PCMDIobs_CLIVAR_LE_CanESM2.py'
else:
    param_file = '../param/my_Param_ENSO_PCMDIobs.py'

cmds_list = []
logfilename_list = []
for model in models:
    print(' ----- model: ', model, ' ---------------------')
    # Find all xmls for the given model
    realm, areacell_in_file = find_realm('ts', mip)
    model_path_list = glob.glob(
        modpath(mip=mip, exp=exp, realm=realm, model=model, realization="*", variable='ts'))
    # sort in nice way
    model_path_list = sort_human(model_path_list)
    if debug:
        print('model_path_list:', model_path_list)
    try:
        # Find where run can be gripped from given filename template for modpath
        run_in_modpath = modpath(mip=mip, exp=exp, realm=realm, model=model, realization=realization,
                                 variable='ts').split('/')[-1].split(inline_separator).index(realization)
        if debug:
            print('run_in_modpath:', run_in_modpath)
        # Collect available runs
        runs_list = [model_path.split('/')[-1].split(inline_separator)[run_in_modpath]
                     for model_path in model_path_list]
    except Exception:
        if realization not in ["*", "all"]:
            runs_list = [realization]
    if debug:
        print('runs_list (all):', runs_list)
    # Check if given run member is included. If not for all runs and given run member is not included,
    # take alternative run
    if realization != "*":
        if realization in runs_list:
            runs_list = [realization]
        else:
            runs_list = runs_list[0:1]
        if debug:
            print('runs_list (revised):', runs_list)
    for run in runs_list:
        # command line for queue
        cmd = ['enso_driver.py',
               '-p', param_file,
               '--mip', mip, '--metricsCollection', mc_name,
               '--case_id', case_id,
               '--modnames', model,
               '--realization', run]
        cmds_list.append(' '.join(cmd))
        # log file for each process
        logfilename = '_'.join(['log_enso', mc_name, mip, exp, model, run, case_id])
        logfilename_list.append(logfilename)

print(' --- jobs to submit ---')
for cmd in cmds_list:
    print(cmd)
print(' --- end of jobs to submit ---')

# =================================================
# Run subprocesses in parallel
# -------------------------------------------------
# log dir
log_dir = outdir(output_type='log')
os.makedirs(log_dir, exist_ok=True)

# number of tasks to submit at the same time
# num_workers = 7
# num_workers = 10
num_workers = 15
# num_workers = 30
# num_workers = 25

parallel_submitter(cmds_list, log_dir=log_dir,
                   logfilename_list=logfilename_list,
                   num_workers=num_workers)
