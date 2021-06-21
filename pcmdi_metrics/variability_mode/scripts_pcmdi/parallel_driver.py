#!/usr/bin/env python

from __future__ import print_function
from argparse import RawTextHelpFormatter
from genutil import StringConstructor

from pcmdi_metrics.variability_mode.lib import AddParserArgument
from pcmdi_metrics.variability_mode.lib import VariabilityModeCheck
from pcmdi_metrics.variability_mode.lib import sort_human
from pcmdi_metrics.misc.scripts import parallel_submitter

import glob
import os
import pcmdi_metrics

# =================================================
# Collect user defined options
# -------------------------------------------------
P = pcmdi_metrics.driver.pmp_parser.PMPParser(
        description='Runs PCMDI Modes of Variability Computations',
        formatter_class=RawTextHelpFormatter)
P = AddParserArgument(P)
P.add_argument("--param_dir",
               type=str,
               default=None,
               help="directory for parameter files")
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
    model_index_path = param.modpath.split('/')[-1].split('.').index("%(model)")
    models = ([p.split('/')[-1].split('.')[model_index_path] for p in glob.glob(modpath(
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
param_dir = param.param_dir
if param_dir is None:
    param_dir = '../../../sample_setups/pcmdi_parameter_files/variability_modes'
param_filename = 'myParam_'+mode+'_'+mip+'.py'

if debug:
    param_filename = 'myParam_test.py'
    print('number of models (debug mode):', len(models))

param_file = os.path.join(param_dir, param_filename)

cmds_list = list()
logfilename_list = list()
for m, model in enumerate(models):
    print(' ----- model: ', model, ' ---------------------')
    # Find all xmls for the given model
    model_path_list = glob.glob(
        modpath(mip=mip, exp=exp, model=model, realization="*", variable=var))
    # sort in nice way
    model_path_list = sort_human(model_path_list)
    if debug:
        print('model_path_list:', model_path_list)
    # Find where run can be gripped from given filename template for modpath
    run_in_modpath = modpath(mip=mip, exp=exp, model=model, realization=realization,
                             variable=var).split('/')[-1].split('.').index(realization)
    # Collect available runs
    runs_list = [model_path.split('/')[-1].split('.')[run_in_modpath] for model_path in model_path_list]
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
    for r, run in enumerate(runs_list):
        # command line for queue
        cmd = ['python', '../variability_modes_driver.py',
               '-p', param_file,
               '--case_id', case_id,
               '--mip', mip,
               '--exp', exp,
               '--modnames', model,
               '--realization', run,
               '--parallel', 'True']
        if m > 0 or r > 0:
            cmd += ['--no_nc_out_obs', '--no_plot_obs']
        cmds_list.append(' '.join(cmd))
        # log file for each process
        logfilename = '_'.join(['log_variability_mode', mode, mip, exp, model, run, case_id, obs_name])
        logfilename_list.append(logfilename)

if debug:
    for cmd in cmds_list:
        print(' '.join(cmd))

# =================================================
# Run subprocesses in parallel
# -------------------------------------------------
# log dir
log_dir = outdir(output_type='log')
os.makedirs(log_dir, exist_ok=True)

# number of tasks to submit at the same time
num_workers = 3
# num_workers = 5
# num_workers = 10
# num_workers = 30

parallel_submitter(cmds_list, log_dir=log_dir,
                   logfilename_list=logfilename_list,
                   num_workers=num_workers)
