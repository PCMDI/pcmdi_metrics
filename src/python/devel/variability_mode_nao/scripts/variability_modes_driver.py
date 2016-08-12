import sys, os
import string
import subprocess
import cdms2 as cdms
import cdutil
import cdtime
import genutil
import time
import json
from eofs.cdms import Eof
import vcs
import numpy as NP

libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'eof_analysis.py',
            'landmask.py',
            'write_nc_output.py',
            'plot_map.py']

for lib in libfiles:
  #execfile(os.path.join('../lib/',lib))
  execfile(os.path.join('./lib/',lib))

##################################################
# User defining options  --- argparse will replace below..
#=================================================

mip = 'cmip5'
#exp = 'piControl'
exp = 'historical'
fq = 'mo'
realm = 'atm'
run = 'r1i1p1'

# Mode of variability --
#mode = 'NAM' # Northern Annular Mode ## Error
#mode = 'NAO' # Northern Atlantic Oscillation ## Working OK
#mode = 'SAM' # Southern Annular Mode ## Error
#mode = 'PNA' # Pacific North American Pattern ## Working OK, bur arbitrary check needed for model field
mode = 'PDO' # Pacific Decadal Oscillation ## Working OK

syear = 1900
#syear = 1990 # To match with ERAINT...
eyear = 2005

# Debugging test --
debug = True
#debug = False

# Statistics against observation --
obs_compare = True
#obs_compare = False

# Pesudo model PC time series analysis --
pesudo = True
#pesudo = False

# NetCDF output --
nc_out = True
#nc_out = False

# Plot figures --
plot = True
#plot = False

##################################################

# Below part will be replaced by PMP's region selector.. 
if mode == 'NAM':
  lat1 = 20
  lat2 = 90
  lon1 = -180
  lon2 = 180
  var = 'psl'
elif mode == 'NAO':
  lat1 = 20
  lat2 = 80
  lon1 = -90
  lon2 = 40
  var = 'psl'
elif mode == 'SAM':
  lat1 = -20
  lat2 = -90
  lon1 = 0
  lon2 = 360
  var = 'psl'
elif mode == 'PNA':
  lat1 = 20
  lat2 = 85
  lon1 = 120
  lon2 = 240
  var = 'psl'
elif mode == 'PDO':
  lat1 = 20
  lat2 = 70
  lon1 = 110
  lon2 = 260
  var = 'ts'

if debug:
  #models = ['ACCESS1-0']  # Test just one model
  models = ['ACCESS1-3']  # Test just one model
  #models = ['ACCESS1-0', 'ACCESS1-3']  # Test just two models
  #models = ['CESM1-CAM5']  # Test just one model
  seasons = ['DJF']
  #seasons = ['MAM']
else:
  models = get_all_mip_mods(mip,exp,fq,realm,var)
  seasons = ['DJF','MAM','JJA','SON']
  if mode == 'PDO':
    models_lf = get_all_mip_mods_lf(mip,'sftlf')
    models = list(set(models).intersection(models_lf)) # Select models when land fraction is existing
    models = sorted(models, key=lambda s:s.lower()) # Sort list alphabetically, case-insensitive

if mode == 'PDO': seasons = ['monthly']

start_time = cdtime.comptime(syear,1,1)
end_time = cdtime.comptime(eyear,12,31)

#=================================================
# Declare dictionary for .json record 
#-------------------------------------------------
var_mode_stat_dic={}
var_mode_stat_dic['REF']={}
var_mode_stat_dic['RESULTS']={}

#=================================================
# Observation
#-------------------------------------------------
if obs_compare:
  var_mode_stat_dic['REF']['obs']={}
  var_mode_stat_dic['REF']['obs']['defaultReference']={}
  var_mode_stat_dic['REF']['obs']['defaultReference'][mode]={}

  if var == 'psl':
    obs_path = '/clim_obs/obs/atm/mo/psl/ERAINT/psl_ERAINT_198901-200911.nc'
    fo = cdms.open(obs_path)
    obs_timeseries = fo(var,time=(start_time,end_time))/100. # Pa to hPa

  elif var == 'ts':
    obs_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
    fo = cdms.open(obs_path)
    obs_timeseries = fo('sst',time=(start_time,end_time))

    # Replace area where temperature below -1.8 C to -1.8 C ---
    obs_mask = obs_timeseries.mask
    obs_timeseries[obs_timeseries<-1.8] = -1.8
    obs_timeseries.mask = obs_mask

  cdutil.setTimeBoundsMonthly(obs_timeseries)

  # Save global grid information for regrid below ---
  ref_grid = obs_timeseries.getGrid()

  # Declare dictionary variables to keep information obtained from the observation ---
  eof1_obs={}
  pc1_obs={}
  frac1_obs={}
  solver_obs={}
  reverse_sign_obs={}
  eof1_lr_obs={}
  pc1_obs_stdv={}
  
  #-------------------------------------------------
  # Season loop
  #- - - - - - - - - - - - - - - - - - - - - - - - -
  for season in seasons:
    var_mode_stat_dic['REF']['obs']['defaultReference'][mode][season]={}

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Time series adjustment
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    if mode == 'PDO' and season == 'monthly':
      # Reomove annual cycle ---
      obs_timeseries = cdutil.ANNUALCYCLE.departures(obs_timeseries)

      # Subtract global mean ---
      obs_global_mean_timeseries = cdutil.averager(obs_timeseries(latitude=(-60,70)), axis='xy', weights='weighted')
      obs_timeseries, obs_global_mean_timeseries = genutil.grower(obs_timeseries, obs_global_mean_timeseries) # Match dimension
      obs_timeseries = obs_timeseries - obs_global_mean_timeseries     

      obs_timeseries_season = obs_timeseries

    else:
      # Get seasonal mean time series ---
      obs_timeseries_season = getattr(cdutil,season)(obs_timeseries)

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Extract subdomain ---
    obs_timeseries_season_subdomain = obs_timeseries_season(latitude=(lat1,lat2),longitude=(lon1,lon2))

    # Save subdomain's grid information for regrid below ---
    ref_grid_subdomain = obs_timeseries_season_subdomain.getGrid()

    # EOF analysis ---
    eof1_obs[season], pc1_obs[season], frac1_obs[season], solver_obs[season], reverse_sign_obs[season] = eof_analysis_get_first_variance_mode(obs_timeseries_season_subdomain)

    # Calculate stdv of pc time series
    pc1_obs_stdv[season] = genutil.statistics.std(pc1_obs[season])

    # Linear regression to have extended global map; teleconnection purpose ---
    eof1_lr_obs[season] = linear_regression(pc1_obs[season], obs_timeseries_season)

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Record results 
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    # Set output file name for NetCDF and plot ---
    output_file_name_obs = mode+'_'+var+'_eof1_'+season+'_obs_'+str(syear)+'-'+str(eyear)

    # Save global map, pc timeseries, and fraction in NetCDF output ---
    if nc_out:
      write_nc_output(output_file_name_obs, eof1_lr_obs[season], pc1_obs[season], frac1_obs[season])

    # Plotting ---
    if plot:
      plot_map(mode, 'obs', syear, eyear, season, eof1_obs[season], frac1_obs[season], output_file_name_obs)
      #plot_map(mode, 'obs-lr', syear, eyear, season, eof1_lr_obs[season](latitude=(lat1,lat2),longitude=(lon1,lon2)), frac1_obs[season], output_file_name_obs+'_lr')
      if mode == 'PDO':
        plot_map(mode+'_teleconnection', 'obs-lr', syear, eyear, season, eof1_lr_obs[season](longitude=(0,360)), frac1_obs[season], output_file_name_obs+'_lr')
      else:
        plot_map(mode+'_teleconnection', 'obs-lr', syear, eyear, season, eof1_lr_obs[season](longitude=(-180,180)), frac1_obs[season], output_file_name_obs+'_lr')

    # Save stdv of PC time series in dictionary ---
    var_mode_stat_dic['REF']['obs']['defaultReference'][mode][season]['pc1_stdv'] = float(pc1_obs_stdv[season])

    print 'obs plotting end'

#=================================================
# Model
#-------------------------------------------------
for model in models:
  var_mode_stat_dic['RESULTS'][model]={}
  var_mode_stat_dic['RESULTS'][model]['defaultReference']={}
  var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode]={}

  print model
  model_path = get_latest_pcmdi_mip_data_path(mip,exp,model,fq,realm,var,run)
  #model_path = '/work/cmip5/historical/atm/mo/psl/cmip5.'+model+'.historical.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'
  f = cdms.open(model_path)

  if var == 'psl':
    model_timeseries = f(var,time=(start_time,end_time))/100. # Pa to hPa

  elif var == 'ts':
    model_timeseries = f(var,time=(start_time,end_time))-273.15 # K to C degree
    model_timeseries.units = 'degC'

    # Replace area where temperature below -1.8 C to -1.8 C ---
    model_timeseries[model_timeseries<-1.8] = -1.8

  cdutil.setTimeBoundsMonthly(model_timeseries)

  #-------------------------------------------------
  # Season loop
  #- - - - - - - - - - - - - - - - - - - - - - - - -
  for season in seasons:
    var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]={}

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Time series adjustment
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    if mode == 'PDO' and season == 'monthly':
      # Remove annual cycle ---
      model_timeseries = cdutil.ANNUALCYCLE.departures(model_timeseries)

      # Extract SST (land region mask out) ---
      model_timeseries = model_land_mask_out(mip,model,model_timeseries)

      # Take global mean out ---
      model_global_mean_timeseries = cdutil.averager(model_timeseries(latitude=(-60,70)), axis='xy', weights='weighted')
      model_timeseries, model_global_mean_timeseries = genutil.grower(model_timeseries, model_global_mean_timeseries) # Matching dimension
      model_timeseries = model_timeseries - model_global_mean_timeseries 

      model_timeseries_season = model_timeseries

    else:
      # Get seasonal mean time series ---
      model_timeseries_season = getattr(cdutil,season)(model_timeseries)
      if debug: print 'seasonal mean'

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Extract subdomain ---
    model_timeseries_season_subdomain = model_timeseries_season(latitude=(lat1,lat2),longitude=(lon1,lon2))

    #-------------------------------------------------
    # Usual EOF approach
    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # EOF analysis ---
    eof1, pc1, frac1, solver, reverse_sign = eof_analysis_get_first_variance_mode(model_timeseries_season_subdomain)
    if debug: print 'eof analysis'

    # Linear regression to have extended global map; teleconnection purpose ---
    eof1_lr = linear_regression(pc1, model_timeseries_season)
    if debug: print 'linear regression'

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # OBS statistics (only over EOF domain), save as dictionary ---
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    if obs_compare:

      # Regrid (interpolation, model grid to ref grid) ---
      #eof1_regrid = eof1.regrid(ref_grid_subdomain,regridTool='regrid2') 
      eof1_regrid = eof1.regrid(ref_grid_subdomain,regridTool='esmf',regridMethod='linear') 
      if debug: print 'regrid end'

      # RMS difference ---
      rms = genutil.statistics.rms(eof1_regrid, eof1_obs[season], axis='xy')
      if debug: print 'rms end'

      # Spatial correlation weighted by area ('generate' option for weights) ---
      cor = genutil.statistics.correlation(eof1_regrid, eof1_obs[season], weights='generate', axis='xy')
      if debug: print 'cor end'

      # Add to dictionary for json output ---
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['rms'] = float(rms)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['cor'] = float(cor)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['frac'] = float(frac1)

    print 'usual eof end'

    #-------------------------------------------------
    # Pesudo model PC timeseries and teleconnection 
    #- - - - - - - - - - - - - - - - - - - - - - - - -
    if pesudo and obs_compare:
      # Regrid (interpolation, model grid to ref grid) ---
      model_timeseries_season_regrid = model_timeseries_season.regrid(ref_grid,regridTool='regrid2')
      model_timeseries_season_regrid_subdomain = model_timeseries_season_regrid(latitude=(lat1,lat2),longitude=(lon1,lon2))

      # Matching model's missing value location to that of observation ---
      # 1) Replace model's masked grid to 0, so theoritically won't affect to result
      # 2) Give obs's mask to model field, so enable projecField functionality below 
      missing_value = model_timeseries_season_regrid_subdomain.missing
      model_timeseries_season_regrid_subdomain[ model_timeseries_season_regrid_subdomain == missing_value ] = 0
      model_timeseries_season_regrid_subdomain.mask = model_timeseries_season_regrid_subdomain.mask + eof1_obs[season].mask
      # Combine two masks (obs and model)
      #model_timeseries_season_regrid_subdomain.mask = NP.ma.mask_or(model_timeseries_season_regrid_subdomain.mask,eof1_obs[season].mask,shrink=False)

      # Pseudo model PC time series ---
      pesudo_pcs = solver_obs[season].projectField(model_timeseries_season_regrid_subdomain,neofs=1,eofscaling=1)
      pesudo_pcs = pesudo_pcs(squeeze=1)

      # Arbitrary sign control, attempt to make all plots have the same sign ---
      if reverse_sign_obs[season]: pesudo_pcs = pesudo_pcs * -1.
    
      # Calculate stdv of pc time series
      pesudo_pcs_stdv = genutil.statistics.std(pesudo_pcs)

      # Linear regression to have extended global map; teleconnection purpose ---
      eof1_lr_pesudo = linear_regression(pesudo_pcs, model_timeseries_season_regrid)

      #- - - - - - - - - - - - - - - - - - - - - - - - -
      # OBS statistics (over global domain), save as dictionary, alternative approach -- Pesudo PC analysis
      #. . . . . . . . . . . . . . . . . . . . . . . . .
      # RMS difference ---
      rms = genutil.statistics.rms(eof1_lr_pesudo, eof1_lr_obs[season], axis='xy')

      # Spatial correlation weighted by area ('generate' option for weights) ---
      cor = genutil.statistics.correlation(eof1_lr_pesudo, eof1_lr_obs[season], weights='generate', axis='xy')

      # Temporal correlation between pesudo PC timeseries and usual model PC timeseries
      tc = genutil.statistics.correlation(pesudo_pcs, pc1)

      # Add to dictionary for json output ---
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['rms_alt'] = float(rms)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['cor_alt'] = float(cor)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['pesudo_pcs_stdv'] = float(pesudo_pcs_stdv)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['tc_btw_pesudo_and_model_pcs'] = float(tc)

      print 'pesudo pcs end'

    #-------------------------------------------------
    # Record results
    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Set output file name for NetCDF and plot ---
    output_file_name = mode+'_'+var+'_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)

    # Save global map, pc timeseries, and fraction in NetCDF output ---
    if nc_out:
      write_nc_output(output_file_name, eof1_lr, pc1, frac1)

    # Plot map ---
    if plot:
      plot_map(mode, model, syear, eyear, season, eof1, frac1, output_file_name)
      #plot_map(mode, model+'-lr', syear, eyear, season, eof1_lr(latitude=(lat1,lat2),longitude=(lon1,lon2)), frac1, output_file_name+'_lr')
      if mode == 'PDO':
        plot_map(mode+'_teleconnection', model, syear, eyear, season, eof1_lr(longitude=(0,360)), frac1, output_file_name+'_lr')
        if pesudo: 
          plot_map(mode+'_teleconnection_pseudo', model, syear, eyear, season, eof1_lr_pesudo(longitude=(0,360)), frac1, output_file_name+'_lr_pesudo')
      else:
        plot_map(mode+'_teleconnection', model, syear, eyear, season, eof1_lr(longitude=(-180,180)), frac1, output_file_name+'_lr')
        if pesudo:
          plot_map(mode+'_teleconnection_pseudo', model, syear, eyear, season, eof1_lr_pesudo(longitude=(-180,180)), frac1, output_file_name+'_lr_pesudo')
      if pesudo: 
        plot_map(mode, model+'_pseudo', syear, eyear, season, eof1_lr_pesudo(latitude=(lat1,lat2),longitude=(lon1,lon2)), frac1, output_file_name+'_pesudo')

#=================================================
# Write dictionary to json file
#-------------------------------------------------
if obs_compare:
  json_filename = 'var_mode_'+mode+'_eof1_stat_' + mip + '_' + exp + '_' + run + '_' + fq + '_' + realm + '_' + str(syear) + '-' + str(eyear)
  json.dump(var_mode_stat_dic, open(json_filename + '.json','w'), sort_keys=True, indent=4, separators=(',', ': '))
