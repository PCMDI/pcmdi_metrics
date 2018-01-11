"""
Calculate mode of varibility from archive of CMIP5 models

NAM: Northern Annular Mode
NAO: Northern Atlantic Oscillation
SAM: Southern Annular Mode
PNA: Pacific North American Pattern
PDO: Pacific Decadal Oscillation

Ji-Woo Lee
"""
from shutil import copyfile 
import cdms2 as cdms
import cdutil, cdtime
import genutil
import json
import pcmdi_metrics
import string
import sys, os
import time
import MV2
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser
from collections import defaultdict

libfiles = ['argparse_functions.py',
            'eof_analysis.py',
            'calc_stat.py',
            'landmask.py',
            'write_nc_output.py',
            'plot_map.py']

libfiles_share = ['default_regions.py']

for lib in libfiles + libfiles_share:
  execfile(os.path.join('./lib/',lib))

#=================================================
# Pre-defined options
#-------------------------------------------------
mip = 'cmip5'
#exp = 'piControl'
exp = 'historical'
fq = 'mo'
realm = 'atm'

#=================================================
# Collect user defined options
#-------------------------------------------------
P = PMPParser()
param = P.get_parameter()

# Statistics against observation --
obs_compare = True

# pseudo model PC time series analysis --
pseudo = True  ## CBF

# NetCDF output --
nc_out = param.nc_out

# Plot figures --
plot = param.plot

# options......
EofScaling = param.EofScaling
RemoveDomainMean = param.RemoveDomainMean

# Check given mode of variability option ---
mode = VariabilityModeCheck(param.mode)
#mode = param.mode
print 'mode:', mode

# Check dependency for given season option ---
seasons = param.seasons
print 'seasons:', seasons

# Check given model option ---
models = param.modnames
print 'models:', models

# Realizations
run = param.run
print 'run: ', run

# EOF ordinal number ---
eofn_obs = param.eofn_obs
eofn_mod = param.eofn_mod

# Output ---
outdir = param.outdir
print 'outdir: ', outdir

# Create output directory ---
if not os.path.exists(outdir): os.makedirs(outdir)

# Debug ---
debug = param.debug
print 'debug: ', debug

# Variables ---
var = param.varModel

# Year
syear = param.msyear
eyear = param.meyear

osyear = param.osyear
oeyear = param.oeyear

# lon1g and lon2g is for global map plotting ---
if mode == 'PDO':
  lon1g = 0
  lon2g = 360
else:
  lon1g = -180
  lon2g = 180

#=================================================
# Time period control
#-------------------------------------------------
start_time = cdtime.comptime(syear,1,1)
end_time = cdtime.comptime(eyear,12,31)

try:
  osyear
  oeyear
except NameError:
  # Variables were NOT defined
  start_time_obs = start_time
  end_time_obs = end_time
else:
  # Variables were defined.
  start_time_obs = cdtime.comptime(osyear,1,1)
  end_time_obs = cdtime.comptime(oeyear,12,31)
  
#=================================================
# Declare dictionary for .json record 
#-------------------------------------------------
def tree(): return defaultdict(tree)
var_mode_stat_dic = tree()

# Define output json file ---
json_filename = 'var_mode_'+mode+'_EOF'+str(eofn_mod)+'_stat_'+mip+'_'+exp+'_'+fq+'_'+realm+'_'+str(syear)+'-'+str(eyear)

json_file = outdir + '/' + json_filename + '.json'
json_file_org = outdir + '/' + json_filename + '_org_'+str(os.getpid())+'.json'

# Save pre-existing json file against overwriting ---
if os.path.isfile(json_file) and os.stat(json_file).st_size > 0 :
  copyfile(json_file, json_file_org)

  update_json = param.update_json

  if update_json == True:
    fj = open(json_file)
    var_mode_stat_dic = json.loads(fj.read())
    fj.close()

if 'REF' not in var_mode_stat_dic.keys():
  var_mode_stat_dic['REF']={}
if 'RESULTS' not in var_mode_stat_dic.keys():
  var_mode_stat_dic['RESULTS']={}

#=================================================
# Observation
#-------------------------------------------------
if obs_compare:

  obs_name = param.obs_name
  obs_path = param.obs_path
  obs_var = param.varOBS
  ObsUnitsAdjust = param.ObsUnitsAdjust

  fo = cdms.open(obs_path)
  obs_timeseries = fo(obs_var, time=(start_time_obs,end_time_obs), latitude=(-90,90))
  
  if ObsUnitsAdjust[0]:
    obs_timeseries = getattr(MV2, ObsUnitsAdjust[1])(obs_timeseries, ObsUnitsAdjust[2])   

  if var == 'ts' and param.LandMask == 0:
    # Replace area where temperature below -1.8 C to -1.8 C (Sea ice adjust) ---
    obs_mask = obs_timeseries.mask
    obs_timeseries[obs_timeseries<-1.8] = -1.8
    obs_timeseries.mask = obs_mask

  cdutil.setTimeBoundsMonthly(obs_timeseries)

  # Check available time window and adjust if needed ---
  ostime = obs_timeseries.getTime().asComponentTime()[0]
  oetime = obs_timeseries.getTime().asComponentTime()[-1]

  osyear = ostime.year; osmonth = ostime.month
  oeyear = oetime.year; oemonth = oetime.month

  if osmonth > 1: osyear = osyear + 1
  if oemonth < 12: oeyear = oeyear - 1

  osyear = max(syear, osyear)
  oeyear = min(eyear, oeyear)

  if debug: print 'osyear:', osyear, 'oeyear:', oeyear

  # Save global grid information for regrid below ---
  ref_grid_global = obs_timeseries.getGrid()

  # Declare dictionary variables to keep information obtained from the observation ---
  eof_obs={}
  pc_obs={}
  frac_obs={}
  solver_obs={}
  reverse_sign_obs={}
  eof_lr_obs={}
  stdv_pc_obs={}

  # Dictonary for json archive ---
  if 'obs' not in var_mode_stat_dic['REF'].keys(): 
    var_mode_stat_dic['REF']['obs']={}
  if 'defaultReference' not in var_mode_stat_dic['REF']['obs'].keys(): 
    var_mode_stat_dic['REF']['obs']['defaultReference']={}
  if 'source' not in var_mode_stat_dic['REF']['obs']['defaultReference'].keys():
    var_mode_stat_dic['REF']['obs']['defaultReference']['source'] = {}
  if mode not in var_mode_stat_dic['REF']['obs']['defaultReference'].keys():
    var_mode_stat_dic['REF']['obs']['defaultReference'][mode]={}

  var_mode_stat_dic['REF']['obs']['defaultReference']['source'] = obs_path
  var_mode_stat_dic['REF']['obs']['defaultReference']['reference_eof_mode'] = eofn_obs
  
  #-------------------------------------------------
  # Season loop
  #- - - - - - - - - - - - - - - - - - - - - - - - -
  obs_timeseries_season_subdomain = {}

  if debug: print 'obs season loop starts'

  for season in seasons:

    if debug: print season

    if season not in var_mode_stat_dic['REF']['obs']['defaultReference'][mode].keys():
      var_mode_stat_dic['REF']['obs']['defaultReference'][mode][season]={}

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Time series adjustment
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    if debug: print 'Time series adjustment'

    # Reomove annual cycle (for all modes) and get its seasonal mean time series (except PDO) ---
    obs_timeseries_ano = get_anomaly_timeseries(obs_timeseries, mode, season)

    # Calculate residual by subtracting domain average (or global mean) ---
    obs_timeseries_season = get_residual_timeseries(obs_timeseries_ano, mode, param.RemoveDomainMean)

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Extract subdomain ---
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    if debug: print 'Extract subdomain'

    obs_timeseries_season_subdomain[season] = obs_timeseries_season(regions_specs[mode]['domain'])

    # EOF analysis ---
    if debug: print 'EOF analysis'
    eof_obs[season], pc_obs[season], frac_obs[season], solver_obs[season], reverse_sign_obs[season] = \
           eof_analysis_get_variance_mode(mode, obs_timeseries_season_subdomain[season], eofn_obs)

    # Calculate stdv of pc time series
    if debug: print 'Calculate stdv of pc time series'
    stdv_pc_obs[season] = calcSTD(pc_obs[season])

    # Linear regression to have extended global map; teleconnection purpose ---
    if debug: print 'Linear regression'
    if debug: print pc_obs[season].shape, obs_timeseries_season.shape
    if RemoveDomainMean:
      slope_obs, intercept_obs = linear_regression(pc_obs[season], obs_timeseries_season)
      eof_lr_obs[season] = MV2.add(MV2.multiply(slope_obs, stdv_pc_obs[season]), intercept_obs)
    else:
      slope_obs, intercept_obs = linear_regression(pc_obs[season], obs_timeseries_season)
      if not EofScaling:
        eof_lr_obs[season] = MV2.add(MV2.multiply(slope_obs, stdv_pc_obs[season]),intercept_obs)
      else:
        eof_lr_obs[season] = MV2.add(slope_obs, intercept_obs)

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Record results 
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    if debug: print 'Record results'

    # Set output file name for NetCDF and plot ---
    output_filename_obs = outdir + '/' + mode+'_'+var+'_EOF'+str(eofn_obs)+'_'+season+'_obs_'+str(osyear)+'-'+str(oeyear)

    # Save global map, pc timeseries, and fraction in NetCDF output ---
    if nc_out:
      write_nc_output(output_filename_obs, eof_lr_obs[season], pc_obs[season], frac_obs[season], slope_obs, intercept_obs)

    # Plotting ---
    if plot:
      #plot_map(mode, 'obs: '+obs_name, osyear, oeyear, season, eof_obs[season], frac_obs[season], output_filename_obs+'_org')
      plot_map(mode, 'obs: '+obs_name, osyear, oeyear, season, 
               eof_lr_obs[season](regions_specs[mode]['domain']), frac_obs[season], output_filename_obs)
      plot_map(mode+'_teleconnection', 'obs-lr: '+obs_name, osyear, oeyear, season, 
               eof_lr_obs[season](longitude=(lon1g,lon2g)), frac_obs[season], output_filename_obs+'_teleconnection')

    # Save stdv of PC time series in dictionary ---
    var_mode_stat_dic['REF']['obs']['defaultReference'][mode][season]['stdv_pc'] = float(stdv_pc_obs[season])
    var_mode_stat_dic['REF']['obs']['defaultReference'][mode][season]['frac'] = float(frac_obs[season])

    if debug: print 'obs plotting end'

    #execfile('../north_test.py')

#=================================================
# Model
#-------------------------------------------------
for model in models:
  print ' ----- ', model,' ---------------------'

  if model not in var_mode_stat_dic['RESULTS'].keys():
    var_mode_stat_dic['RESULTS'][model]={}
  
  model_path_list = os.popen('ls '+param.modpath.replace('MOD',model).replace('RUN',run).replace('VAR',var)).readlines()
  if debug: print model_path_list

  for model_path in model_path_list:

    try:
      run = string.split((string.split(model_path,'/')[-1]),'.')[3]
      print ' --- ', run,' ---'
  
      if run not in var_mode_stat_dic['RESULTS'][model].keys():
        var_mode_stat_dic['RESULTS'][model][run]={}
      if 'defaultReference' not in var_mode_stat_dic['RESULTS'][model][run].keys():
        var_mode_stat_dic['RESULTS'][model][run]['defaultReference']={}
      if mode not in var_mode_stat_dic['RESULTS'][model][run]['defaultReference'].keys():
        var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode]={}
        var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode]['model_eof_mode'] = int(eofn_mod)
  
      f = cdms.open(model_path)
      model_timeseries = f(var,time=(start_time,end_time),latitude=(-90,90))
    
      ModUnitsAdjust = param.ModUnitsAdjust
      if ModUnitsAdjust[0]:
        model_timeseries = getattr(MV2, ModUnitsAdjust[1])(model_timeseries, ModUnitsAdjust[2])
    
      if var == 'ts' and param.LandMask == 0:
        # Replace area where temperature below -1.8 C to -1.8 C (sea ice) ---
        model_timeseries[model_timeseries<-1.8] = -1.8
  
      cdutil.setTimeBoundsMonthly(model_timeseries)

      # Check available time window and adjust if needed ---
      mstime = model_timeseries.getTime().asComponentTime()[0]
      metime = model_timeseries.getTime().asComponentTime()[-1]
    
      msyear = mstime.year; msmonth = mstime.month
      meyear = metime.year; memonth = metime.month
    
      msyear = max(syear, msyear)
      meyear = min(eyear, meyear)

      if debug: print 'msyear:', msyear, 'meyear:', meyear
  
      #-------------------------------------------------
      # Season loop
      #- - - - - - - - - - - - - - - - - - - - - - - - -
      for season in seasons:

        if debug: print season

        if season not in var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode].keys():
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]={}
    
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # Time series adjustment
        #. . . . . . . . . . . . . . . . . . . . . . . . . 
        if debug: print 'Time series adjustment'

        if param.LandMask == 0:
          # Extract SST (land region mask out) ---
          model_timeseries = model_land_mask_out(mip,model,model_timeseries)

        # Reomove annual cycle (for all modes) and get its seasonal mean time series if needed ---
        model_timeseries_ano = get_anomaly_timeseries(model_timeseries, mode, season)
  
        # Calculate residual by subtracting domain average (or global mean) ---
        model_timeseries_season = get_residual_timeseries(model_timeseries_ano, mode, param.RemoveDomainMean)
  
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # Extract subdomain ---
        #. . . . . . . . . . . . . . . . . . . . . . . . .
        model_timeseries_season_subdomain = model_timeseries_season(regions_specs[mode]['domain'])

        #-------------------------------------------------
        # Usual EOF approach
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        if param.ConvEOF:

          if debug: print 'Usual EOF approach'
  
          # EOF analysis ---
          eof, pc, frac, solver, reverse_sign = \
                eof_analysis_get_variance_mode(mode, model_timeseries_season_subdomain, eofn_mod)
          if debug: print 'eof analysis'
      
          # Calculate stdv of pc time series ---
          stdv_pc = calcSTD(pc)
  
          # Linear regression to have extended global map:
          # -- Reconstruct EOF fist mode including teleconnection purpose as well
          # -- Have confirmed that "eof_lr" is identical to "eof" over EOF domain (i.e., "subdomain")
          # -- Note that eof_lr has global field ---
          if RemoveDomainMean:
            slope, intercept = linear_regression(pc, model_timeseries_season)
            eof_lr = MV2.add(MV2.multiply(slope, stdv_pc), intercept)
          else:
            slope, intercept = linear_regression(pc, model_timeseries_season)
            if not EofScaling:
              eof_lr = MV2.add(MV2.multiply(slope, stdv_pc), intercept)
            else:
              eof_lr = MV2.add(slope, intercept)
          if debug: print 'linear regression'
  
          # Add to dictionary for json output ---
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['frac_eof'] = float(frac)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['stdv_eof_pc'] = float(stdv_pc)
      
          #- - - - - - - - - - - - - - - - - - - - - - - - -
          # OBS statistics (only over EOF domain), save as dictionary ---
          #. . . . . . . . . . . . . . . . . . . . . . . . .
          if obs_compare:
      
            # Regrid (interpolation, model grid to ref grid) ---
            if debug: print 'regrid (global) start'
            eof_lr_regrid_global = eof_lr.regrid(ref_grid_global, regridTool='regrid2', mkCyclic=True)
            if debug: print 'regrid end'
      
            # Extract subdomain ---
            eof_regrid = eof_lr_regrid_global(regions_specs[mode]['domain'])
  
            # Spatial correlation weighted by area ('generate' option for weights) ---
            cor = calcSCOR(eof_regrid, eof_obs[season])
            cor_glo = calcSCOR(eof_lr_regrid_global, eof_lr_obs[season])
            if debug: print 'cor end'
  
            # Double check for arbitrary sign control --- 
            if cor < 0: 
              eof = MV2.multiply(eof, -1)
              pc = MV2.multiply(pc, -1)
              eof_lr = MV2.multiply(eof_lr, -1)
              eof_lr_regrid_global = MV2.multiply(eof_lr_regrid_global, -1)
              eof_regrid = MV2.multiply(eof_regrid, -1)
              # Calc cor again ---
              cor = calcSCOR(eof_regrid, eof_obs[season])
              cor_glo = calcSCOR(eof_lr_regrid_global, eof_lr_obs[season])
      
            # RMS (uncentered) difference ---
            rms = calcRMS(eof_regrid, eof_obs[season])
            rms_glo = calcRMS(eof_lr_regrid_global, eof_lr_obs[season])
            if debug: print 'rms end'
  
            # RMS (centered) difference ---
            rmsc = calcRMSc(eof_regrid, eof_obs[season])
            rmsc_glo = calcRMSc(eof_lr_regrid_global, eof_lr_obs[season])
            if debug: print 'rmsc end'
  
            # Bias ---
            bias = calcBias(eof_regrid, eof_obs[season])
            bias_glo = calcBias(eof_lr_regrid_global, eof_lr_obs[season])
            if debug: print 'bias end'
      
            # Add to dictionary for json output ---
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_eof'] = float(rms)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_eof_glo'] = float(rms_glo)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_eof'] = float(rmsc)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_eof_glo'] = float(rmsc_glo)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_eof'] = float(cor)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_eof_glo'] = float(cor_glo)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_eof'] = float(bias)
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_eof_glo'] = float(bias_glo)
      
        #-------------------------------------------------
        # pseudo model PC timeseries (CBF-PC) and teleconnection 
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        if pseudo and obs_compare and param.CBF:

          if debug: print 'CBF approach'

          # Regrid (interpolation, model grid to ref grid) ---
          model_timeseries_season_regrid = model_timeseries_season.regrid(ref_grid_global, regridTool='regrid2', mkCyclic=True)
          model_timeseries_season_regrid_subdomain = model_timeseries_season_regrid(regions_specs[mode]['domain'])
    
          # Matching model's missing value location to that of observation ---
          # 1) Replace model's masked grid to 0, so theoritically won't affect to result
          # 2) Give obs's mask to model field, so enable projecField functionality below 
          #
          time = model_timeseries_season_regrid_subdomain.getTime()
          lat = model_timeseries_season_regrid_subdomain.getLatitude()
          lon = model_timeseries_season_regrid_subdomain.getLongitude()
          #
          model_timeseries_season_regrid_subdomain = MV2.array(model_timeseries_season_regrid_subdomain.filled(0.))
          model_timeseries_season_regrid_subdomain.mask = eof_obs[season].mask
          #
          model_timeseries_season_regrid_subdomain.setAxis(0,time)
          model_timeseries_season_regrid_subdomain.setAxis(1,lat)
          model_timeseries_season_regrid_subdomain.setAxis(2,lon)
    
          # CBF PC time series ---
          cbf_pc = gain_pseudo_pcs(solver_obs[season], model_timeseries_season_regrid_subdomain, eofn_obs, reverse_sign_obs[season])
    
          # Calculate stdv of cbf pc time series ---
          stdv_cbf_pc = calcSTD(cbf_pc)
    
          # Linear regression to have extended global map; teleconnection purpose ---
          if RemoveDomainMean:
            slope_cbf, intercept_cbf = linear_regression(cbf_pc, model_timeseries_season_regrid)
            eof_lr_cbf = MV2.add(MV2.multiply(slope_cbf, stdv_cbf_pc), intercept_cbf)
          else: 
            slope_cbf, intercept_cbf = linear_regression(cbf_pc, model_timeseries_season_regrid)
            if not EofScaling:
              eof_lr_cbf = MV2.add(MV2.multiply(slope_cbf, stdv_cbf_pc), intercept_cbf)
            else:
              eof_lr_cbf = MV2.add(slope_cbf, intercept_cbf)

          # Extract subdomain for statistics ---
          eof_lr_cbf_subdomain = eof_lr_cbf(regions_specs[mode]['domain'])

          # Calculate fraction of variance explained by cbf pc ---
          frac_cbf = gain_pcs_fraction(model_timeseries_season_regrid_subdomain, eof_lr_cbf_subdomain, cbf_pc/stdv_cbf_pc)

          #- - - - - - - - - - - - - - - - - - - - - - - - -
          # OBS statistics (over global domain), save as dictionary, alternative approach -- CBF PC analysis
          #. . . . . . . . . . . . . . . . . . . . . . . . .
          # Spatial correlation weighted by area ('generate' option for weights) ---
          cor_cbf = calcSCOR(eof_lr_cbf_subdomain, eof_obs[season])
          cor_cbf_glo = calcSCOR(eof_lr_cbf, eof_lr_obs[season])
          if debug: print 'cbf cor end'

          # RMS (uncentered) difference ---
          rms_cbf = calcRMS(eof_lr_cbf_subdomain, eof_obs[season])
          rms_cbf_glo = calcRMS(eof_lr_cbf, eof_lr_obs[season])
          if debug: print 'cbf rms end'
    
          # RMS (centered) difference ---
          rmsc_cbf = calcRMSc(eof_lr_cbf_subdomain, eof_obs[season])
          rmsc_cbf_glo = calcRMSc(eof_lr_cbf, eof_lr_obs[season])
          if debug: print 'cbf rmsc end'

          # Bias ---
          bias_cbf = calcBias(eof_lr_cbf_subdomain, eof_obs[season])
          bias_cbf_glo = calcBias(eof_lr_cbf, eof_lr_obs[season])
          if debug: print 'cbf bias end'

          # Add to dictionary for json output ---
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_cbf'] = float(rms_cbf)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_cbf_glo'] = float(rms_cbf_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_cbf'] = float(rmsc_cbf)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_cbf_glo'] = float(rmsc_cbf_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_cbf'] = float(cor_cbf)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_cbf_glo'] = float(cor_cbf_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_cbf'] = float(bias_cbf)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_cbf_glo'] = float(bias_cbf_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['stdv_cbf_pc'] = float(stdv_cbf_pc)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['frac_cbf'] = float(frac_cbf)

          # Temporal correlation between pseudo PC timeseries and usual model PC timeseries
          if param.ConvEOF:
            tc = calcTCOR(cbf_pc, pc)
            if debug: print 'cbf tc end'
            var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['tcor_cbf_vs_eof_pc'] = float(tc)

          if debug: print 'cbf pcs end'

        #-------------------------------------------------
        # Record results
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # Set output file name for NetCDF and plot ---
        output_filename = os.path.join(outdir,
                                       mode+'_'+var+'_EOF'+str(eofn_mod)+'_'+season+'_'
                                       +mip+'_'+model+'_'+exp+'_'+run+'_'+fq+'_'+realm+'_'+str(msyear)+'-'+str(meyear))
    
        # Save global map, pc timeseries, and fraction in NetCDF output ---
        if nc_out and param.ConvEOF:
          write_nc_output(output_filename, eof_lr, pc, frac, slope, intercept)
        if nc_out and pseudo and obs_compare and param.CBF: 
          write_nc_output(output_filename+'_cbf', eof_lr_cbf, cbf_pc, frac_cbf, slope_cbf, intercept_cbf)
    
        # Plot map ---
        if plot and param.ConvEOF:
          #plot_map(mode, model+'_'+run, msyear, meyear, season, eof, frac, output_filename+'_org')
          plot_map(mode, model+' ('+run+')', msyear, meyear, season, 
                   eof_lr(regions_specs[mode]['domain']), frac, output_filename)
          plot_map(mode+'_teleconnection', model+' ('+run+')', msyear, meyear, season, 
                   eof_lr(longitude=(lon1g,lon2g)), frac, output_filename+'_teleconnection')
        if plot and pseudo and param.CBF: 
          plot_map(mode, model+' ('+run+')'+' - CBF', msyear, meyear, season, 
                   eof_lr_cbf(regions_specs[mode]['domain']), frac_cbf, output_filename+'_cbf')
          plot_map(mode+'_CBF_teleconnection', model+' ('+run+')', msyear, meyear, season, 
                   eof_lr_cbf(longitude=(lon1g,lon2g)), frac_cbf, output_filename+'_cbf_teleconnection')
    
      #=================================================
      # Write dictionary to json file (let the json keep overwritten in model loop)
      #-------------------------------------------------
      new_json_structure = True

      if new_json_structure:
        JSON = pcmdi_metrics.io.base.Base(outdir,json_filename)
        JSON.write(var_mode_stat_dic,json_structure=["model","realization","reference","mode","season","statistic"],
                   sort_keys=True, indent=4, separators=(',', ': '))
      else:
        json.dump(var_mode_stat_dic, open(json_file,'w'), sort_keys=True, indent=4, separators=(',', ': '))

    except Exception, err:
      print 'faild for ', model, run, err
      pass

if not debug: sys.exit('done')
