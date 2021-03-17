#!/usr/bin/env python
# =================================================
# Dependencies
# -------------------------------------------------
from __future__ import print_function

import cdms2
import glob
import json
import os
import pkg_resources
import sys

from genutil import StringConstructor
from PMPdriver_lib import AddParserArgument
from PMPdriver_lib import metrics_to_json
from PMPdriver_lib import sort_human
from PMPdriver_lib import find_realm, get_file
from EnsoMetrics.EnsoCollectionsLib import CmipVariables, defCollection, ReferenceObservations
from EnsoMetrics.EnsoComputeMetricsLib import ComputeCollection

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
        try: var_in_file = dict_var[var]['var_name']
        except:
            print('\033[95m' + str(var) + " is not available for " + str(obs) + " or unscripted" + '\033[0m')
        else:
            if isinstance(var_in_file, list):
                var0 = var_in_file[0]
            else:
                var0 = var_in_file

            try:
                # finding file for 'obs', 'var'
                file_name = param.reference_data_path[obs].replace('VAR', var0)
                file_areacell = None ## temporary for now
                try:
                    file_landmask = param.reference_data_lf_path[obs]
                except:
                    file_landmask = None
                try:
                    areacell_in_file = dict_var['areacell']['var_name']
                except:
                    areacell_in_file = None
                try:
                    landmask_in_file = dict_var['landmask']['var_name']
                except:
                    landmask_in_file = None
                # if var_in_file is a list (like for thf) all variables should be read from the same realm
                if isinstance(var_in_file, list):
                    list_files = list()
                    list_files = [param.reference_data_path[obs].replace('VAR', var1) for var1 in var_in_file]
                    list_areacell = [file_areacell for var1 in var_in_file]
                    list_name_area = [areacell_in_file for var1 in var_in_file]
                    try:
                        list_landmask = [param.reference_data_lf_path[obs] for var1 in var_in_file]
                    except:
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
            except:
                print('\033[95m' + 'Observation dataset' + str(obs) + " is not given for variable " + str(var) + '\033[0m')

print('PMPdriver: dict_obs readin end')

# =================================================
# Loop for Models 
# -------------------------------------------------
# finding file and variable name in file for each observations dataset
dict_metric, dict_dive = dict(), dict()
dict_var = CmipVariables()['variable_name_in_file']

print('models:', models)

for mod in models:
    print(' ----- model: ', mod, ' ---------------------')
    print('PMPdriver: var loop start for model ', mod)
    dict_mod = {mod: {}}
    dict_metric[mod], dict_dive[mod] = dict(), dict()

    model_path_list = glob.glob(
        modpath(mip=mip, exp=exp, realm='atmos', model=mod, realization=realization, variable='ts'))

    model_path_list = sort_human(model_path_list)
    if debug:
        print('model_path_list:', model_path_list)

    # Find where run can be gripped from given filename template for modpath
    print('realization:', realization)
    try:
        run_in_modpath = modpath(mip=mip, exp=exp, realm='atmos',  model=mod, realization=realization,
            variable='ts').split('/')[-1].split('.').index(realization)
        print('run_in_modpath:', run_in_modpath)
        # Collect available runs
        runs_list = [model_path.split('/')[-1].split('.')[run_in_modpath] for model_path in model_path_list]
    except:
        if realization not in ["all", "*"]:
            runs_list = [realization]

    if debug:
        print('runs_list:', runs_list)

    # =================================================
    # Loop for Realizations
    # -------------------------------------------------
    for run in runs_list:

        print(' --- run: ', run, ' ---')
        mod_run = '_'.join([mod, run])
        dict_mod = {mod_run: {}}

        if debug:
            print('list_variables:', list_variables)
    
        try:
            for var in list_variables:
                print(' --- var: ', var, ' ---')
                # finding variable name in file
                var_in_file = dict_var[var]['var_name']
                print('var_in_file:', var_in_file)
                if isinstance(var_in_file, list):
                    var0 = var_in_file[0]
                else:
                    var0 = var_in_file
                # finding variable type (atmos or ocean)
                areacell_in_file, realm = find_realm(var0)
                if realm == 'Amon':
                    realm2 = 'atmos'
                elif realm == 'Omon':
                    realm2 = 'ocean'
                else:
                    realm2 = realm
                print('var, areacell_in_file, realm:', var, areacell_in_file, realm)
                #
                # finding file for 'mod', 'var'
                #
                file_name = get_file(modpath(mip=mip, realm=realm, exp=exp, model=mod, realization=run, variable=var0))
                file_areacell = get_file(modpath_lf(mip=mip, realm=realm2, model=mod, variable=areacell_in_file))
                if not os.path.isfile(file_areacell):
                    file_areacell = None
                file_landmask = get_file(modpath_lf(mip=mip, realm=realm2, model=mod, variable=dict_var['landmask']['var_name']))
                # -- TEMPORARY --
                if mip == 'cmip6':
                    if mod in ['IPSL-CM6A-LR', 'CNRM-CM6-1']:
                        file_landmask = '/work/lee1043/ESGF/CMIP6/CMIP/'+mod+'/sftlf_fx_'+mod+'_historical_r1i1p1f1_gr.nc'
                    elif mod in ['GFDL-ESM4']:
                        file_landmask = modpath_lf(mip=mip, realm="atmos", model='GFDL-CM4', variable=dict_var['landmask']['var_name'])
                if mip == 'cmip5':
                    if mod == "BNU-ESM":
                        # Incorrect latitude in original sftlf fixed
                        file_landmask = "/work/lee1043/ESGF/CMIP5/BNU-ESM/sftlf_fx_BNU-ESM_historical_r0i0p0.nc"
                    elif mod == "HadCM3":
                        # Inconsistent lat/lon between sftlf and other variables
                        file_landmask = None 
                        # Inconsistent grid between areacella and tauu (probably staggering grid system)
                        file_areacell = None
                # -- TEMPORARY END --
                """
                try:
                    areacell_in_file = dict_var['areacell']['var_name']
                except:
                    areacell_in_file = None
                """
                try:
                    landmask_in_file = dict_var['landmask']['var_name']
                except:
                    landmask_in_file = None
        
                if isinstance(var_in_file, list):
                    list_areacell, list_files, list_landmask, list_name_area, list_name_land = \
                        list(), list(), list(), list(), list()
                    for var1 in var_in_file:
                        areacell_in_file, realm = find_realm(var1)
                        modpath_tmp = get_file(modpath(mip=mip, exp=exp, realm=realm, model=mod, realization=realization, variable=var1))
                        #modpath_lf_tmp = get_file(modpath_lf(mip=mip, realm=realm2, model=mod, variable=dict_var['landmask']['var_name']))
                        if not os.path.isfile(modpath_tmp):
                            modpath_tmp = None
                        #if not os.path.isfile(modpath_lf_tmp):
                        #    modpath_lf_tmp = None
                        file_areacell_tmp = get_file(modpath_lf(mip=mip, realm=realm2, model=mod, variable=areacell_in_file))
                        print("file_areacell_tmp:", file_areacell_tmp)
                        if not os.path.isfile(file_areacell_tmp):
                            file_areacell_tmp = None
                        list_files.append(modpath_tmp)
                        list_areacell.append(file_areacell_tmp)
                        list_name_area.append(areacell_in_file)
                        #list_landmask.append(modpath_lf_tmp)
                        list_landmask.append(file_landmask)
                        list_name_land.append(landmask_in_file)
                else:
                    if not os.path.isfile(file_name):
                        file_name = None
                    if file_landmask is not None:
                        if not os.path.isfile(file_landmask):
                            file_landmask = None
                    list_files = file_name
                    list_areacell = file_areacell
                    list_name_area = areacell_in_file
                    list_landmask = file_landmask
                    list_name_land = landmask_in_file

                # Variable from ocean grid
                if var in ['ssh']:
                    list_landmask = None
                    # Temporay control of areacello for models with zos on gr instead on gn
                    if mod in ['BCC-ESM1', 'CESM2', 'CESM2-FV2', 'CESM2-WACCM', 'CESM2-WACCM-FV2',
                               'GFDL-CM4', 'GFDL-ESM4', 'MRI-ESM2-0',  # cmip6
                               #'BCC-CSM1-1', 'BCC-CSM1-1-M', 'EC-EARTH', 'GFDL-CM3', 'GISS-E2-R',
                               'BCC-CSM1-1', 'BCC-CSM1-1-M', 'GFDL-CM3', 'GISS-E2-R',
                               'MRI-CGCM3']:  # cmip5
                        list_areacell = None

                dict_mod[mod_run][var] = {
                    'path + filename': list_files, 'varname': var_in_file,
                    'path + filename_area': list_areacell, 'areaname': list_name_area,
                    'path + filename_landmask': list_landmask, 'landmaskname': list_name_land}

                print('PMPdriver: var loop end')
            
            # dictionary needed by EnsoMetrics.ComputeMetricsLib.ComputeCollection
            dictDatasets = {'model': dict_mod, 'observations': dict_obs}
            print('dictDatasets:')
            print(json.dumps(dictDatasets, indent=4, sort_keys=True))

            # regridding dictionary (only if you want to specify the regridding)
            dict_regrid = {}
            """
            # Usage of dict_regrid (select option as below):
            dict_regrid = {
                'regridding': {
                    'model_orand_obs': 2, 'regridder': 'cdms', 'regridTool': 'esmf', 'regridMethod': 'linear',
                    'newgrid_name': 'generic 1x1deg'},
            }
            """

            # Prepare netcdf file setup
            json_name = json_name_template(mip=mip, exp=exp, metricsCollection=mc_name, case_id=case_id, model=mod, realization=run)
            netcdf_name = netcdf_name_template(mip=mip, exp=exp, metricsCollection=mc_name, case_id=case_id, model=mod, realization=run)
            netcdf = os.path.join(netcdf_path, netcdf_name)

            if debug:
                print('file_name:', file_name)
                print('list_files:', list_files)
                print('netcdf_name:', netcdf_name)
                print('json_name:', json_name)

            # Computes the metric collection
            print("\n### Compute the metric collection ###\n")
            cdms2.setAutoBounds('on')
            dict_metric[mod][run], dict_dive[mod][run] = ComputeCollection(mc_name, dictDatasets, mod_run, netcdf=param.nc_out,
                                                     netcdf_name=netcdf, debug=debug)
            if debug:
                print('file_name:', file_name)
                print('list_files:', list_files)
                print('netcdf_name:', netcdf_name)
                print('dict_metric:')
                print(json.dumps(dict_metric, indent=4, sort_keys=True))

            # OUTPUT METRICS TO JSON FILE (per simulation)
            metrics_to_json(mc_name, dict_obs, dict_metric, dict_dive, egg_pth, outdir, json_name, mod=mod, run=run)

        except Exception as e: 
            print('failed for ', mod, run)
            print(e)
            if not debug:
                pass

print('PMPdriver: model loop end')

# =================================================
# OUTPUT METRICS TO JSON FILE (for all simulations)
# -------------------------------------------------
#json_name = json_name_template(mip=mip, exp=exp, metricsCollection=mc_name, model='all', realization='all')
#metrics_to_json(mc_name, dict_obs, dict_metric, dict_dive, egg_pth, outdir, json_name)
