#!/usr/bin/env python

from __future__ import print_function
from argparse import RawTextHelpFormatter
from genutil import StringConstructor
from subprocess import Popen

from pcmdi_metrics.variability_mode.lib import (
    AddParserArgument, VariabilityModeCheck)

import datetime
import glob
import os
import pcmdi_metrics
import sys

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
P = pcmdi_metrics.driver.pmp_parser.PMPParser(
        description='Runs PCMDI Modes of Variability Computations',
        formatter_class=RawTextHelpFormatter)
P = AddParserArgument(P)
param = P.get_parameter()

# Pre-defined options
mip = param.mip
exp = param.exp
print('mip:', mip)
print('exp:', exp)

# Check given mode of variability
mode = VariabilityModeCheck(param.variability_mode, P)
print('mode:', mode)

# Observation information
obs_name = param.reference_data_name

# Variables
var = param.varModel

# Path to model data as string template
modpath = StringConstructor(param.modpath)

# Check given model option
models = param.modnames

# Include all models if conditioned
if ('all' in [m.lower() for m in models]) or (models == 'all'):
    models = ([p.split('.')[1] for p in glob.glob(modpath(
                mip=mip, exp=exp, model='*', realization='*', variable=var))])
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print('models:', models)
print('number of models:', len(models))

# Realizations
realization = param.realization
if ('all' in [r.lower() for r in realization]) or (realization == 'all'):
    realization = '*'
print('realization: ', realization)

# case id
case_id = param.case_id
print('case_id:', case_id)

# Output
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)',
    mip=mip, exp=exp, variability_mode=mode, reference_data_name=obs_name)))

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
param_file = '../doc/myParam_'+mode+'_'+mip+'.py'

if debug:
    param_file = '../doc/myParam_test.py'
    print('number of models (debug mode):', len(models))

cmds_list = []
for m, model in enumerate(models):
    cmd = ['python', 'variability_modes_driver.py',
           '-p', param_file,
           '--case_id', case_id]
    if m > 0:
        cmd += ['--no_nc_out_obs', '--no_plot_obs']
    cmd += ['--modnames', model]
    cmds_list.append(cmd)

# =================================================
# Run subprocesses in parallel
# -------------------------------------------------
# log dir
case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
log_dir = "./log_"+case_id

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# number of tasks to submit at the same time
num_workers = 10
#num_workers = 30

print("Start : %s" % time.ctime())

# submit tasks and wait for subset of tasks to complete
procs_list = []
for p, cmd in enumerate(cmds_list):
    print(p, cmd)
    model = cmd[-1]
    log_filename = '_'.join(['log_variability_mode', mode, mip, exp, model, case_id])
    log_file = os.path.join(log_dir, log_filename)
    with open(log_file+"_stdout.txt", "wb") as out, open(log_file+"_stderr.txt", "wb") as err:
        procs_list.append(Popen(cmd, stdout=out, stderr=err))
    if ((p > 0 and p % num_workers == 0) or (p == len(cmds_list)-1)):
        print('wait...')
        for proc in procs_list:
            proc.wait()
        print("Tasks end : %s" % time.ctime())
        procs_list = []

# tasks done
print("End : %s" % time.ctime())
sys.exit('DONE')
