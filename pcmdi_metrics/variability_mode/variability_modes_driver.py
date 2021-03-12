#!/usr/bin/env python

"""
# Modes of Variability Metrics
- Calculate metrics for modes of varibility from archive of CMIP models
- Author: Jiwoo Lee (lee1043@llnl.gov), PCMDI, LLNL

## EOF1 based variability modes
- NAM: Northern Annular Mode
- NAO: Northern Atlantic Oscillation
- SAM: Southern Annular Mode
- PNA: Pacific North American Pattern
- PDO: Pacific Decadal Oscillation

## EOF2 based variability modes
- NPO: North Pacific Oscillation (2nd EOFs of PNA domain)
- NPGO: North Pacific Gyre Oscillation (2nd EOFs of PDO domain)

## Reference:
Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019:
Quantifying the Agreement Between Observed and Simulated Extratropical Modes of
Interannual Variability. Climate Dynamics.
https://doi.org/10.1007/s00382-018-4355-4

## Auspices:
This work was performed under the auspices of the U.S. Department of
Energy by Lawrence Livermore National Laboratory under Contract
DE-AC52-07NA27344. Lawrence Livermore National Laboratory is operated by
Lawrence Livermore National Security, LLC, for the U.S. Department of Energy,
National Nuclear Security Administration under Contract DE-AC52-07NA27344.

## Disclaimer:
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
from argparse import RawTextHelpFormatter
from genutil import StringConstructor
from shutil import copyfile
from pcmdi_metrics.variability_mode.lib import (
    AddParserArgument, VariabilityModeCheck, YearCheck,
    calc_stats_save_dict, calcTCOR, calcSTD,
    eof_analysis_get_variance_mode,
    linear_regression_on_globe_for_teleconnection,
    gain_pseudo_pcs, gain_pcs_fraction, adjust_timeseries,
    model_land_mask_out,
    tree, write_nc_output, get_domain_range, read_data_in, debug_print, sort_human,
    variability_metrics_to_json,
    plot_map)
import cdtime
import cdutil
import glob
import json
import MV2
import os
import pcmdi_metrics
import pkg_resources
import sys

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Must be done before any CDAT library is called.
# https://github.com/CDAT/cdat/issues/2213
if 'UVCDAT_ANONYMOUS_LOG' not in os.environ:
    os.environ['UVCDAT_ANONYMOUS_LOG'] = 'no'

regions_specs = {}
egg_pth = pkg_resources.resource_filename(
    pkg_resources.Requirement.parse("pcmdi_metrics"),
    "share/pmp")
exec(compile(open(os.path.join(egg_pth, "default_regions.py")).read(),
             os.path.join(egg_pth, "default_regions.py"), 'exec'))

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
fq = param.frequency
realm = param.realm
print('mip:', mip)
print('exp:', exp)
print('fq:', fq)
print('realm:', realm)

# On/off switches
obs_compare = True  # Statistics against observation
CBF = param.CBF  # Conduct CBF analysis
ConvEOF = param.ConvEOF  # Conduct conventional EOF analysis

EofScaling = param.EofScaling  # If True, consider EOF with unit variance
RmDomainMean = param.RemoveDomainMean  # If True, remove Domain Mean of each time step
LandMask = param.landmask  # If True, maskout land region thus consider only over ocean

print('EofScaling:', EofScaling)
print('RmDomainMean:', RmDomainMean)
print('LandMask:', LandMask)

nc_out_obs = param.nc_out_obs  # Record NetCDF output
plot_obs = param.plot_obs  # Generate plots
nc_out_model = param.nc_out  # Record NetCDF output
plot_model = param.plot  # Generate plots
update_json = param.update_json

print('nc_out_obs, plot_obs:', nc_out_obs, plot_obs)
print('nc_out_model, plot_model:', nc_out_model, plot_model)

cmec = False
if hasattr(param, 'cmec'):
    cmec = param.cmec  # Generate CMEC compliant json
print('CMEC:' + str(cmec))

# Check given mode of variability
mode = VariabilityModeCheck(param.variability_mode, P)
print('mode:', mode)

# Variables
var = param.varModel

# Check dependency for given season option
seasons = param.seasons
print('seasons:', seasons)

# Observation information
obs_name = param.reference_data_name
obs_path = param.reference_data_path
obs_var = param.varOBS

# Path to model data as string template
modpath = StringConstructor(param.modpath)
if LandMask:
    modpath_lf = StringConstructor(param.modpath_lf)

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
print('realization: ', realization)

# EOF ordinal number
eofn_obs = int(param.eofn_obs)
eofn_mod = int(param.eofn_mod)

# case id
case_id = param.case_id

# Output
outdir_template = param.process_templated_argument("results_dir")
outdir = StringConstructor(str(outdir_template(
    output_type='%(output_type)',
    mip=mip, exp=exp, variability_mode=mode, reference_data_name=obs_name, case_id=case_id)))

# Debug
debug = param.debug

# Year
msyear = param.msyear
meyear = param.meyear
YearCheck(msyear, meyear, P)

osyear = param.osyear
oeyear = param.oeyear
YearCheck(osyear, oeyear, P)

# Units adjustment
ObsUnitsAdjust = param.ObsUnitsAdjust
ModUnitsAdjust = param.ModUnitsAdjust

# lon1g and lon2g is for global map plotting
if mode in ['PDO', 'NPGO']:
    lon1g = 0
    lon2g = 360
else:
    lon1g = -180
    lon2g = 180

# parallel
parallel = param.parallel
print('parallel:', parallel)

# =================================================
# Time period adjustment
# -------------------------------------------------
start_time = cdtime.comptime(msyear, 1, 1, 0, 0)
end_time = cdtime.comptime(meyear, 12, 31, 23, 59)

try:
    # osyear and oeyear variables were defined.
    start_time_obs = cdtime.comptime(osyear, 1, 1, 0, 0)
    end_time_obs = cdtime.comptime(oeyear, 12, 31, 23, 59)
except NameError:
    # osyear, oeyear variables were NOT defined
    start_time_obs = start_time
    end_time_obs = end_time

# =================================================
# Region control
# -------------------------------------------------
region_subdomain = get_domain_range(mode, regions_specs)

# =================================================
# Create output directories
# -------------------------------------------------
for output_type in ['graphics', 'diagnostic_results', 'metrics_results']:
    if not os.path.exists(outdir(output_type=output_type)):
        os.makedirs(outdir(output_type=output_type))
    print(outdir(output_type=output_type))

# =================================================
# Set dictionary for .json record
# -------------------------------------------------
result_dict = tree()

# Set metrics output JSON file
json_filename = '_'.join(['var', 'mode', mode, 'EOF'+str(eofn_mod), 'stat',
                          mip, exp, fq, realm, str(msyear)+'-'+str(meyear)])

json_file = os.path.join(outdir(output_type='metrics_results'), json_filename + '.json')
json_file_org = os.path.join(
    outdir(output_type='metrics_results'), '_'.join([json_filename, 'org', str(os.getpid())])+'.json')

# Archive if there is pre-existing JSON: preventing overwriting
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0:
    copyfile(json_file, json_file_org)
    if update_json:
        fj = open(json_file)
        result_dict = json.loads(fj.read())
        fj.close()

if 'REF' not in list(result_dict.keys()):
    result_dict['REF'] = {}
if 'RESULTS' not in list(result_dict.keys()):
    result_dict['RESULTS'] = {}

# =================================================
# Observation
# -------------------------------------------------
if obs_compare:

    # read data in
    obs_timeseries, osyear, oeyear = read_data_in(
        obs_path, obs_var, var,
        start_time_obs, end_time_obs,
        ObsUnitsAdjust, LandMask, debug=debug)

    # Save global grid information for regrid below
    ref_grid_global = obs_timeseries.getGrid()

    # Declare dictionary variables to keep information from observation
    eof_obs = {}
    pc_obs = {}
    frac_obs = {}
    solver_obs = {}
    reverse_sign_obs = {}
    eof_lr_obs = {}
    stdv_pc_obs = {}

    # Dictonary for json archive
    if 'obs' not in list(result_dict['REF'].keys()):
        result_dict['REF']['obs'] = {}
    if 'defaultReference' not in list(result_dict['REF']['obs'].keys()):
        result_dict['REF']['obs']['defaultReference'] = {}
    if ('source' not in list(
            result_dict['REF']['obs']['defaultReference'].keys())):
        result_dict['REF']['obs']['defaultReference']['source'] = {}
    if(mode not in list(
            result_dict['REF']['obs']['defaultReference'].keys())):
        result_dict['REF']['obs']['defaultReference'][mode] = {}

    result_dict['REF']['obs']['defaultReference']['source'] = obs_path
    result_dict['REF']['obs']['defaultReference']['reference_eofs'] = eofn_obs
    result_dict['REF']['obs']['defaultReference']['period'] = str(osyear)+'-'+str(oeyear)

    # -------------------------------------------------
    # Season loop
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    debug_print('obs season loop starts', debug)

    for season in seasons:
        debug_print('season: '+season, debug)

        if (season not in list(
                result_dict['REF']['obs']['defaultReference'][mode].keys())):
            result_dict['REF']['obs']['defaultReference'][mode][season] = {}

        dict_head_obs = result_dict['REF']['obs']['defaultReference'][mode][season]

        # Time series adjustment (remove annual cycle, seasonal mean (if needed),
        # and subtracting domain (or global) mean of each time step)
        debug_print('time series adjustment', debug)
        obs_timeseries_season = adjust_timeseries(obs_timeseries, mode, season, region_subdomain, RmDomainMean)

        # Extract subdomain
        obs_timeseries_season_subdomain = obs_timeseries_season(region_subdomain)

        # EOF analysis
        debug_print('EOF analysis', debug)
        eof_obs[season], pc_obs[season], frac_obs[season], reverse_sign_obs[season], \
            solver_obs[season] = eof_analysis_get_variance_mode(
                mode, obs_timeseries_season_subdomain, eofn=eofn_obs,
                debug=debug, EofScaling=EofScaling)

        # Calculate stdv of pc time series
        debug_print('calculate stdv of pc time series', debug)
        stdv_pc_obs[season] = calcSTD(pc_obs[season])

        # Linear regression to have extended global map; teleconnection purpose
        eof_lr_obs[season], slope_obs, intercept_obs = linear_regression_on_globe_for_teleconnection(
            pc_obs[season], obs_timeseries_season, stdv_pc_obs[season],
            RmDomainMean, EofScaling, debug=debug)

        # - - - - - - - - - - - - - - - - - - - - - - - - -
        # Record results
        # . . . . . . . . . . . . . . . . . . . . . . . . .
        debug_print('record results', debug)

        # Set output file name for NetCDF and plot
        output_filename_obs = '_'.join([
            mode, var, 'EOF'+str(eofn_obs), season, 'obs',
            str(osyear)+'-'+str(oeyear)])
        if EofScaling:
            output_filename_obs += '_EOFscaled'

        # Save global map, pc timeseries, and fraction in NetCDF output
        if nc_out_obs:
            output_nc_file_obs = os.path.join(
                outdir(output_type='diagnostic_results'),
                output_filename_obs)
            write_nc_output(
                output_nc_file_obs, eof_lr_obs[season], pc_obs[season],
                frac_obs[season], slope_obs, intercept_obs)

        # Plotting
        if plot_obs:
            output_img_file_obs = os.path.join(
                outdir(output_type='graphics'),
                output_filename_obs)
            # plot_map(mode, '[REF] '+obs_name, osyear, oeyear, season,
            #          eof_obs[season], frac_obs[season],
            #          output_img_file_obs+'_org_eof')
            plot_map(mode, '[REF] '+obs_name, osyear, oeyear, season,
                     eof_lr_obs[season](region_subdomain),
                     frac_obs[season], output_img_file_obs)
            plot_map(mode+'_teleconnection', '[REF] '+obs_name, osyear,
                     oeyear, season,
                     eof_lr_obs[season](longitude=(lon1g, lon2g)),
                     frac_obs[season], output_img_file_obs+'_teleconnection')
            debug_print('obs plotting end', debug)

        # Save stdv of PC time series in dictionary
        dict_head_obs['stdv_pc'] = stdv_pc_obs[season]
        dict_head_obs['frac'] = float(frac_obs[season])

        # Mean
        mean_obs = cdutil.averager(eof_obs[season], axis='yx', weights='weighted')
        mean_glo_obs = cdutil.averager(eof_lr_obs[season], axis='yx', weights='weighted')
        dict_head_obs['mean'] = float(mean_obs)
        dict_head_obs['mean_glo'] = float(mean_glo_obs)
        debug_print('obs mean end', debug)

        # North test -- make this available as option later...
        # execfile('../north_test.py')

    debug_print('obs end', debug)

# =================================================
# Model
# -------------------------------------------------
for model in models:
    print(' ----- ', model, ' ---------------------')

    if model not in list(result_dict['RESULTS'].keys()):
        result_dict['RESULTS'][model] = {}

    model_path_list = glob.glob(
        modpath(mip=mip, exp=exp, model=model, realization=realization, variable=var))

    model_path_list = sort_human(model_path_list)

    debug_print('model_path_list: '+str(model_path_list), debug)

    # Find where run can be gripped from given filename template for modpath
    if realization == "*":
        run_in_modpath = modpath(
            mip=mip, exp=exp, model=model, realization=realization,
            variable=var).split('/')[-1].split('.').index(realization)

    # -------------------------------------------------
    # Run
    # -------------------------------------------------
    for model_path in model_path_list:

        try:
            if realization == "*":
                run = (model_path.split('/')[-1]).split('.')[run_in_modpath]
            else:
                run = realization
            print(' --- ', run, ' ---')

            if run not in list(result_dict['RESULTS'][model].keys()):
                result_dict['RESULTS'][model][run] = {}
            if ('defaultReference' not in list(
                    result_dict['RESULTS'][model][run].keys())):
                result_dict['RESULTS'][model][run]['defaultReference'] = {}
            if (mode not in list(
                    result_dict['RESULTS'][model][run]['defaultReference'].keys())):
                result_dict['RESULTS'][model][run]['defaultReference'][mode] = {}
            result_dict['RESULTS'][model][run]['defaultReference'][mode]['target_model_eofs'] = eofn_mod

            # read data in
            model_timeseries, msyear, meyear = read_data_in(
                model_path, var, var,
                start_time, end_time,
                ModUnitsAdjust, LandMask, debug=debug)

            # landmask if required
            if LandMask:
                model_lf_path = modpath_lf(mip=mip, exp=exp, model=model)
                # Extract SST (land region mask out)
                model_timeseries = model_land_mask_out(
                    model, model_timeseries, model_lf_path)

            debug_print('msyear: '+str(msyear)+' meyear: '+str(meyear), debug)

            # -------------------------------------------------
            # Season loop
            # - - - - - - - - - - - - - - - - - - - - - - - - -
            for season in seasons:
                debug_print('season: '+season, debug)

                if (season not in list(
                        result_dict['RESULTS'][model][run]['defaultReference'][mode].keys())):
                    result_dict['RESULTS'][model][run]['defaultReference'][mode][season] = {}
                result_dict['RESULTS'][model][run]['defaultReference'][mode][season]['period'] = (
                        str(msyear)+'-'+str(meyear))

                # Time series adjustment (remove annual cycle, seasonal mean (if needed),
                # and subtracting domain (or global) mean of each time step)
                debug_print('time series adjustment', debug)
                model_timeseries_season = adjust_timeseries(
                        model_timeseries, mode, season, region_subdomain, RmDomainMean)

                # Extract subdomain
                debug_print('extract subdomain', debug)
                model_timeseries_season_subdomain = model_timeseries_season(region_subdomain)

                # -------------------------------------------------
                # Common Basis Function Approach
                # - - - - - - - - - - - - - - - - - - - - - - - - -
                if CBF and obs_compare:

                    if ('cbf' not in list(
                            result_dict['RESULTS'][model][run]['defaultReference'][mode][season].keys())):
                        result_dict['RESULTS'][model][run]['defaultReference'][mode][season]['cbf'] = {}
                    dict_head = result_dict['RESULTS'][model][run]['defaultReference'][mode][season]['cbf']
                    debug_print('CBF approach start', debug)

                    # Regrid (interpolation, model grid to ref grid)
                    model_timeseries_season_regrid = model_timeseries_season.regrid(
                        ref_grid_global, regridTool='regrid2', mkCyclic=True)
                    model_timeseries_season_regrid_subdomain = model_timeseries_season_regrid(region_subdomain)

                    # Matching model's missing value location to that of observation
                    # Save axes for preserving
                    axes = model_timeseries_season_regrid_subdomain.getAxisList()
                    # 1) Replace model's masked grid to 0, so theoritically won't affect to result
                    model_timeseries_season_regrid_subdomain = MV2.array(
                        model_timeseries_season_regrid_subdomain.filled(0.))
                    # 2) Give obs's mask to model field, so enable projecField functionality below
                    model_timeseries_season_regrid_subdomain.mask = eof_obs[season].mask
                    # Preserve axes
                    model_timeseries_season_regrid_subdomain.setAxisList(axes)

                    # CBF PC time series
                    cbf_pc = gain_pseudo_pcs(
                        solver_obs[season],
                        model_timeseries_season_regrid_subdomain,
                        eofn_obs,
                        reverse_sign_obs[season],
                        EofScaling=EofScaling)

                    # Calculate stdv of cbf pc time series
                    stdv_cbf_pc = calcSTD(cbf_pc)

                    # Linear regression to have extended global map; teleconnection purpose
                    eof_lr_cbf, slope_cbf, intercept_cbf = linear_regression_on_globe_for_teleconnection(
                        cbf_pc, model_timeseries_season, stdv_cbf_pc,
                        # cbf_pc, model_timeseries_season_regrid, stdv_cbf_pc,
                        RmDomainMean, EofScaling, debug=debug)

                    # Extract subdomain for statistics
                    eof_lr_cbf_subdomain = eof_lr_cbf(region_subdomain)

                    # Calculate fraction of variance explained by cbf pc
                    frac_cbf = gain_pcs_fraction(
                        # model_timeseries_season_regrid_subdomain,  # regridded model anomaly space
                        model_timeseries_season_subdomain,  # native grid model anomaly space
                        eof_lr_cbf_subdomain,
                        cbf_pc/stdv_cbf_pc, debug=debug)

                    # SENSITIVITY TEST ---
                    # Calculate fraction of variance explained by cbf pc (on regrid domain)
                    frac_cbf_regrid = gain_pcs_fraction(
                        model_timeseries_season_regrid_subdomain,
                        eof_lr_cbf_subdomain,
                        cbf_pc/stdv_cbf_pc, debug=debug)
                    dict_head['frac_cbf_regrid'] = float(frac_cbf_regrid)

                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Record results
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    # Metrics results -- statistics to JSON
                    dict_head, eof_lr_cbf = calc_stats_save_dict(
                            dict_head, eof_lr_cbf_subdomain, eof_lr_cbf, slope_cbf,
                            cbf_pc, stdv_cbf_pc, frac_cbf,
                            region_subdomain,
                            eof_obs[season], eof_lr_obs[season], stdv_pc_obs[season],
                            obs_compare=obs_compare, method='cbf', debug=debug)

                    # Set output file name for NetCDF and plot images
                    output_filename = '_'.join([
                            mode, var, 'EOF'+str(eofn_mod), season, mip,
                            model, exp, run, fq, realm,
                            str(msyear)+'-'+str(meyear)])
                    if EofScaling:
                        output_filename += '_EOFscaled'

                    # Diagnostics results -- data to NetCDF
                    # Save global map, pc timeseries, and fraction in NetCDF output
                    output_nc_file = os.path.join(
                            outdir(output_type='diagnostic_results'),
                            output_filename)
                    if nc_out_model:
                        write_nc_output(
                            output_nc_file+'_cbf', eof_lr_cbf,
                            cbf_pc, frac_cbf, slope_cbf, intercept_cbf)

                    # Graphics -- plot map image to PNG
                    output_img_file = os.path.join(
                        outdir(output_type='graphics'),
                        output_filename)
                    if plot_model:
                        plot_map(mode,
                                 mip.upper()+' '+model+' ('+run+')'+' - CBF',
                                 msyear, meyear, season,
                                 eof_lr_cbf(region_subdomain), frac_cbf,
                                 output_img_file+'_cbf')
                        plot_map(mode+'_teleconnection',
                                 mip.upper()+' '+model+' ('+run+')'+' - CBF',
                                 msyear, meyear, season,
                                 eof_lr_cbf(longitude=(lon1g, lon2g)), frac_cbf,
                                 output_img_file+'_cbf_teleconnection')

                    debug_print('cbf pcs end', debug)

                # -------------------------------------------------
                # Conventional EOF approach as supplementary
                # - - - - - - - - - - - - - - - - - - - - - - - - -
                if ConvEOF:

                    eofn_mod_max = 3

                    # EOF analysis
                    debug_print('conventional EOF analysis start', debug)
                    eof_list, pc_list, frac_list, reverse_sign_list, solver = \
                        eof_analysis_get_variance_mode(
                            mode,
                            model_timeseries_season_subdomain,
                            eofn=eofn_mod, eofn_max=eofn_mod_max,
                            debug=debug, EofScaling=EofScaling,
                            save_multiple_eofs=True)
                    debug_print('conventional EOF analysis done', debug)

                    # -------------------------------------------------
                    # For multiple EOFs (e.g., EOF1, EOF2, EOF3, ...)
                    # - - - - - - - - - - - - - - - - - - - - - - - - -
                    rms_list = []
                    cor_list = []
                    tcor_list = []

                    for n in range(0, eofn_mod_max):
                        eofs = 'eof'+str(n+1)
                        if (eofs not in list(
                                result_dict['RESULTS'][model][run]['defaultReference'][mode][season].keys())):
                            result_dict['RESULTS'][model][run]['defaultReference'][mode][season][eofs] = {}
                            dict_head = result_dict['RESULTS'][model][run]['defaultReference'][mode][season][eofs]

                        # Component for each EOFs
                        eof = eof_list[n]
                        pc = pc_list[n]
                        frac = frac_list[n]

                        # Calculate stdv of pc time series
                        stdv_pc = calcSTD(pc)

                        # Linear regression to have extended global map:
                        eof_lr, slope, intercept = linear_regression_on_globe_for_teleconnection(
                            pc, model_timeseries_season, stdv_pc,
                            RmDomainMean, EofScaling, debug=debug)

                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        # Record results
                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        # Metrics results -- statistics to JSON
                        if obs_compare:
                            dict_head, eof_lr = calc_stats_save_dict(
                                dict_head, eof, eof_lr, slope, pc, stdv_pc, frac,
                                region_subdomain,
                                eof_obs=eof_obs[season], eof_lr_obs=eof_lr_obs[season], stdv_pc_obs=stdv_pc_obs[season],
                                obs_compare=obs_compare, method='eof', debug=debug)
                        else:
                            dict_head, eof_lr = calc_stats_save_dict(
                                dict_head, eof, eof_lr, slope, pc, stdv_pc, frac,
                                region_subdomain,
                                obs_compare=obs_compare, method='eof', debug=debug)

                        # Temporal correlation between CBF PC timeseries and usual model PC timeseries
                        if CBF:
                            tc = calcTCOR(cbf_pc, pc)
                            debug_print('cbf tc end', debug)
                            dict_head['tcor_cbf_vs_eof_pc'] = tc

                        # Set output file name for NetCDF and plot images
                        output_filename = '_'.join([
                            mode, var, 'EOF'+str(n+1), season, mip,
                            model, exp, run, fq, realm,
                            str(msyear)+'-'+str(meyear)])
                        if EofScaling:
                            output_filename += '_EOFscaled'

                        # Diagnostics results -- data to NetCDF
                        # Save global map, pc timeseries, and fraction in NetCDF output
                        output_nc_file = os.path.join(
                            outdir(output_type='diagnostic_results'),
                            output_filename)
                        if nc_out_model:
                            write_nc_output(
                                output_nc_file, eof_lr, pc, frac, slope, intercept)

                        # Graphics -- plot map image to PNG
                        output_img_file = os.path.join(
                            outdir(output_type='graphics'),
                            output_filename)
                        if plot_model:
                            # plot_map(mode,
                            #          mip.upper()+' '+model+' ('+run+')',
                            #          msyear, meyear, season,
                            #          eof, frac,
                            #          output_img_file+'_org_eof')
                            plot_map(mode,
                                     mip.upper()+' '+model+' ('+run+') - EOF'+str(n+1),
                                     msyear, meyear, season,
                                     eof_lr(region_subdomain), frac,
                                     output_img_file)
                            plot_map(mode+'_teleconnection',
                                     mip.upper()+' '+model+' ('+run+') - EOF'+str(n+1),
                                     msyear, meyear, season,
                                     eof_lr(longitude=(lon1g, lon2g)), frac,
                                     output_img_file+'_teleconnection')

                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        # EOF swap diagnosis
                        # - - - - - - - - - - - - - - - - - - - - - - - - -
                        rms_list.append(dict_head['rms'])
                        cor_list.append(dict_head['cor'])
                        if CBF:
                            tcor_list.append(dict_head['tcor_cbf_vs_eof_pc'])

                    # Find best matching eofs with different criteria
                    best_matching_eofs_rms = rms_list.index(min(rms_list))+1
                    best_matching_eofs_cor = cor_list.index(max(cor_list))+1
                    if CBF:
                        best_matching_eofs_tcor = tcor_list.index(max(tcor_list))+1

                    # Save the best matching information to JSON
                    dict_head = result_dict['RESULTS'][model][run]['defaultReference'][mode][season]
                    dict_head['best_matching_model_eofs__rms'] = best_matching_eofs_rms
                    dict_head['best_matching_model_eofs__cor'] = best_matching_eofs_cor
                    if CBF:
                        dict_head['best_matching_model_eofs__tcor_cbf_vs_eof_pc'] = best_matching_eofs_tcor

                    debug_print('conventional eof end', debug)

            # =================================================================
            # Dictionary to JSON: individual JSON during model_realization loop
            # -----------------------------------------------------------------
            json_filename_tmp = '_'.join(['var', 'mode', mode, 'EOF'+str(eofn_mod), 'stat',
                                          mip, exp, fq, realm, model, run, str(msyear)+'-'+str(meyear)])
            variability_metrics_to_json(outdir, json_filename_tmp, result_dict, model=model, run=run, cmec_flag=cmec)

        except Exception as err:
            if debug:
                raise
            else:
                print('warning: failed for ', model, run, err)
                pass

# ========================================================================
# Dictionary to JSON: collective JSON at the end of model_realization loop
# ------------------------------------------------------------------------
if not parallel and (len(models) > 1):
    json_filename_all = '_'.join(['var', 'mode', mode, 'EOF'+str(eofn_mod), 'stat',
                                  mip, exp, fq, realm, 'allModels', 'allRuns', str(msyear)+'-'+str(meyear)])
    variability_metrics_to_json(outdir, json_filename_all, result_dict, cmec_flag=cmec)

if not debug:
    sys.exit(0)
