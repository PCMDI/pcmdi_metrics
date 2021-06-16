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
from subprocess import Popen

from pcmdi_metrics.enso.lib import AddParserArgument, find_realm
from pcmdi_metrics.variability_mode.lib import sort_human

import glob
import os
import sys
import time

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Must be done before any CDAT library is called.
# https://github.com/CDAT/cdat/issues/2213
if 'UVCDAT_ANONYMOUS_LOG' not in os.environ:
    os.environ['UVCDAT_ANONYMOUS_LOG'] = 'no'

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
        cmd = ['enso_driver.py',
               '-p', param_file,
               '--mip', mip, '--metricsCollection', mc_name,
               '--case_id', case_id,
               '--modnames', model,
               '--realization', run]
        cmds_list.append(cmd)

if debug:
    for cmd in cmds_list:
        print(' '.join(cmd))

# =================================================
# Run subprocesses in parallel
# -------------------------------------------------
# log dir
log_dir = os.path.join("log", case_id, mc_name)

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# number of tasks to submit at the same time
# num_workers = 7
# num_workers = 10
num_workers = 15
# num_workers = 30
# num_workers = 25

print("Start : %s" % time.ctime())

# submit tasks and wait for subset of tasks to complete
procs_list = []
for p, cmd in enumerate(cmds_list):
    timenow = time.ctime()
    print(timenow, p, ' '.join(cmd))
    model = cmd[-3]
    run = cmd[-1]
    log_filename = '_'.join(['log_enso', mc_name, mip, exp, model, run, case_id])
    log_file = os.path.join(log_dir, log_filename)
    with open(log_file+"_stdout.txt", "wb") as out, open(log_file+"_stderr.txt", "wb") as err:
        procs_list.append(Popen(cmd, stdout=out, stderr=err))
        time.sleep(1)
    if ((p > 0 and p % num_workers == 0) or (p == len(cmds_list)-1)):
        print('wait...')
        for proc in procs_list:
            proc.wait()
        print("Tasks end : %s" % time.ctime())
        procs_list = []

# tasks done
print("End : %s" % time.ctime())
sys.exit('DONE')
