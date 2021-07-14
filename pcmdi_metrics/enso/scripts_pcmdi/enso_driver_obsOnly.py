#!/usr/bin/env python
# =================================================
# Dependencies
# -------------------------------------------------
from __future__ import print_function

import glob
import json
import os
import pkg_resources
import sys

from genutil import StringConstructor
from pcmdi_metrics.enso.lib import AddParserArgument
from pcmdi_metrics.enso.lib import metrics_to_json
from EnsoMetrics.EnsoCollectionsLib import defCollection, ReferenceObservations
# from EnsoMetrics.EnsoComputeMetricsLib import ComputeCollection
from EnsoMetrics.EnsoComputeMetricsLib import ComputeCollection_ObsOnly

# To avoid below error when using multi cores
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

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
modpath_lf = param.process_templated_argument("modpath_lf")

# Check given model option
models = param.modnames

# Include all models if conditioned
if ('all' in [m.lower() for m in models]) or (models == 'all'):
    model_index_path = param.modpath.split('/')[-1].split('.').index("%(model)")
    models = ([p.split('/')[-1].split('.')[model_index_path] for p in glob.glob(modpath(
                mip=mip, exp=exp, model='*', realization='*', variable='ts'))])
    # remove duplicates
    models = sorted(list(dict.fromkeys(models)), key=lambda s: s.lower())

print('models:', models)

# Realizations
realization = param.realization
print('realization: ', realization)

# Metrics Collection
mc_name = param.metricsCollection
dict_mc = defCollection(mc_name)
list_metric = sorted(dict_mc['metrics_list'].keys())
print('mc_name:', mc_name)

# case id
case_id = param.case_id

# Output
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)',
    mip=mip, exp=exp, metricsCollection=mc_name, case_id=case_id)))
netcdf_path = outdir(output_type='diagnostic_results')
json_name_template = param.process_templated_argument("json_name")
netcdf_name_template = param.process_templated_argument("netcdf_name")

print('outdir:', str(outdir_template(
    output_type='%(output_type)',
    mip=mip, exp=exp, metricsCollection=mc_name)))
print('netcdf_path:', netcdf_path)

# Switches
debug = param.debug
print('debug:', debug)

# =================================================
# Prepare loop iteration
# -------------------------------------------------
# Environmental setup
try:
    egg_pth = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse("pcmdi_metrics"), "share/pmp")
except Exception:
    egg_pth = os.path.join(sys.prefix, "share", "pmp")
print('egg_pth:', egg_pth)

# Create output directory
for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# list of variables
list_variables = list()
for metric in list_metric:
    listvar = dict_mc['metrics_list'][metric]['variables']
    for var in listvar:
        if var not in list_variables:
            list_variables.append(var)
list_variables = sorted(list_variables)
print(list_variables)

# list of observations
list_obs = list()
for metric in list_metric:
    dict_var_obs = dict_mc['metrics_list'][metric]['obs_name']
    for var in dict_var_obs.keys():
        for obs in dict_var_obs[var]:
            if obs not in list_obs:
                list_obs.append(obs)
list_obs = sorted(list_obs)

#
# finding file and variable name in file for each observations dataset
#
dict_obs = dict()

for obs in list_obs:
    # be sure to add your datasets to EnsoCollectionsLib.ReferenceObservations if needed
    dict_var = ReferenceObservations(obs)['variable_name_in_file']
    dict_obs[obs] = dict()
    for var in list_variables:
        #
        # finding variable name in file
        #
        try:
            var_in_file = dict_var[var]['var_name']
        except Exception:
            print('\033[95m' + str(var) + " is not available for " + str(obs) + " or unscripted" + '\033[0m')
        else:
            if isinstance(var_in_file, list):
                var0 = var_in_file[0]
            else:
                var0 = var_in_file

            try:
                # finding file for 'obs', 'var'
                file_name = param.reference_data_path[obs].replace('VAR', var0)
                file_areacell = None  # temporary for now
                try:
                    file_landmask = param.reference_data_lf_path[obs]
                except Exception:
                    file_landmask = None
                try:
                    areacell_in_file = dict_var['areacell']['var_name']
                except Exception:
                    areacell_in_file = None
                try:
                    landmask_in_file = dict_var['landmask']['var_name']
                except Exception:
                    landmask_in_file = None
                # if var_in_file is a list (like for thf) all variables should be read from the same realm
                if isinstance(var_in_file, list):
                    list_files = list()
                    list_files = [param.reference_data_path[obs].replace('VAR', var1) for var1 in var_in_file]
                    list_areacell = [file_areacell for var1 in var_in_file]
                    list_name_area = [areacell_in_file for var1 in var_in_file]
                    try:
                        list_landmask = [param.reference_data_lf_path[obs] for var1 in var_in_file]
                    except Exception:
                        list_landmask = None
                    list_name_land = [landmask_in_file for var1 in var_in_file]
                else:
                    list_files = file_name
                    list_areacell = file_areacell
                    list_name_area = areacell_in_file
                    list_landmask = file_landmask
                    list_name_land = landmask_in_file
                dict_obs[obs][var] = {'path + filename': list_files, 'varname': var_in_file,
                                      'path + filename_area': list_areacell, 'areaname': list_name_area,
                                      'path + filename_landmask': list_landmask, 'landmaskname': list_name_land}
            except Exception:
                print('\033[95m' + 'Observation dataset' + str(obs) +
                      " is not given for variable " + str(var) + '\033[0m')

print('PMPdriver: dict_obs readin end')

# Prepare computing the metric collection (OBS to OBS)
dictDatasets = {'observations': dict_obs}
netcdf_path = "/work/lee1043/imsi/result_test/enso_metric/test_obs2obs_yann"
netcdf_name = 'YANN_PLANTON_' + mc_name + "_OBSNAME"
netcdf = os.path.join(netcdf_path, netcdf_name)
if debug:
    print('file_name:', file_name)
    print('list_files:', list_files)
    print('netcdf_name:', netcdf_name)
    print('dict_obs:')
    print(json.dumps(dict_obs, indent=4, sort_keys=True))
    with open("dict_obs_" + mc_name + ".json", "w") as f_dict_obs:
        json.dump(dict_obs, f_dict_obs, indent=4, sort_keys=True)

# Compute the metric collection (OBS to OBS)
dict_metric, dict_dive = ComputeCollection_ObsOnly(mc_name, dictDatasets, debug=True, netcdf=True, netcdf_name=netcdf)
if debug:
    print('dict_metric:')
    print(json.dumps(dict_metric, indent=4, sort_keys=True))

# OUTPUT METRICS TO JSON FILE (per simulation)
outdir = netcdf_path
json_name = netcdf_name
metrics_to_json(mc_name, dict_obs, dict_metric, dict_dive, egg_pth, outdir, json_name, mod='obs', run='test')
