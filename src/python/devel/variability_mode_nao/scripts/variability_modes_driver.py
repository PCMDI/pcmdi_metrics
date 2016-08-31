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
            'calc_stat.py',
            'landmask.py',
            'write_nc_output.py',
            'plot_map.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

##################################################
# User defining options  --- argparse will replace below..
#=================================================

mip = 'cmip5'
#exp = 'piControl'
exp = 'historical'
fq = 'mo'
realm = 'atm'

# Mode of variability --
mode = 'NAM' # Northern Annular Mode
#mode = 'NAO' # Northern Atlantic Oscillation
#mode = 'SAM' # Southern Annular Mode
#mode = 'PNA' # Pacific North American Pattern
#mode = 'PDO' # Pacific Decadal Oscillation

syear = 1900
#syear = 1990 # To match with ERAINT...
eyear = 2005

# Debugging test --
debug = True
#debug = False

# Statistics against observation --
obs_compare = True
#obs_compare = False

# pseudo model PC time series analysis --
pseudo = True
#pseudo = False

# NetCDF output --
nc_out = True
#nc_out = False

# Plot figures --
plot = True
#plot = False

# Conside all ensemble member (multiple realization) --
multi_run = True
#multi_run = False ## Consider only r1i1p1

# Output directory --
out_dir = './results'

##################################################

# Create output directory ---
out_dir = out_dir + '/' + mode
if not os.path.exists(out_dir): os.makedirs(out_dir)

# Multiple realization ---
if multi_run: 
  runs = '*'
else: 
  runs = 'r1i1p1'

if debug: runs = 'r1i1p1'

# Region selector ---
# Below part will be replaced by PMP's region selector ---
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

# Debug option ---
if debug:
  models = ['ACCESS1-0']  # Test just one model
  #models = ['ACCESS1-3']  # Test just one model
  #models = ['ACCESS1-0', 'ACCESS1-3']  # Test just two models
  #models = ['CESM1-CAM5']  # Test just one model
  #models = ['bcc-csm1-1-m']
  #models = ['CNRM-CM5-2', 'GISS-E2-H', 'IPSL-CM5B-LR']
  #models = ['inmcm4']
  #models = ['HadGEM2-AO']
  #models = ['MIROC4h']
  #models = ['CSIRO-Mk3-6-0']
  seasons = ['DJF']
  #seasons = ['MAM']
  #seasons = ['SON']
else:
  models = get_all_mip_mods(mip,exp,fq,realm,var)
  seasons = ['DJF','MAM','JJA','SON']
  if mode == 'PDO':
    models_lf = get_all_mip_mods_lf(mip,'sftlf')
    models = list(set(models).intersection(models_lf)) # Select models when land fraction exists as well
    models = sorted(models, key=lambda s:s.lower()) # Sort list alphabetically, case-insensitive

# lon1g and lon2g is for global map plotting ---
lon1g = -180
lon2g = 180

if mode == 'PDO':
  seasons = ['monthly']
  lon1g = 0
  lon2g = 360

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

  # Load variable ---
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

  # Check available time window and adjust if needed ---
  osyear = obs_timeseries.getTime().asComponentTime()[0].year
  oeyear = obs_timeseries.getTime().asComponentTime()[-1].year

  osyear = max(syear, osyear)
  oeyear = min(eyear, oeyear)

  if debug: print 'osyear:', osyear, 'oeyear:', oeyear

  # Save global grid information for regrid below ---
  ref_grid_global = obs_timeseries.getGrid()

  # Declare dictionary variables to keep information obtained from the observation ---
  eof1_obs={}
  pc1_obs={}
  frac1_obs={}
  solver_obs={}
  reverse_sign_obs={}
  eof1_lr_obs={}
  pc1_obs_stdv={}

  # Dictonary for json archive ---
  var_mode_stat_dic['REF']['obs']={}
  var_mode_stat_dic['REF']['obs']['defaultReference']={}
  var_mode_stat_dic['REF']['obs']['defaultReference']['source'] = {}
  var_mode_stat_dic['REF']['obs']['defaultReference']['source'] = obs_path
  var_mode_stat_dic['REF']['obs']['defaultReference'][mode]={}
  
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
      obs_timeseries, obs_global_mean_timeseries = \
                                 genutil.grower(obs_timeseries, obs_global_mean_timeseries) # Match dimension
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
    eof1_obs[season], pc1_obs[season], frac1_obs[season], solver_obs[season], reverse_sign_obs[season] = \
           eof_analysis_get_first_variance_mode(mode, obs_timeseries_season_subdomain)

    # Calculate stdv of pc time series
    pc1_obs_stdv[season] = calcSTD(pc1_obs[season])

    # Linear regression to have extended global map; teleconnection purpose ---
    eof1_lr_obs[season] = linear_regression(pc1_obs[season], obs_timeseries_season)

    #- - - - - - - - - - - - - - - - - - - - - - - - -
    # Record results 
    #. . . . . . . . . . . . . . . . . . . . . . . . .
    # Set output file name for NetCDF and plot ---
    output_file_name_obs = out_dir + '/' + mode+'_'+var+'_EOF1_'+season+'_obs_'+str(osyear)+'-'+str(oeyear)

    # Save global map, pc timeseries, and fraction in NetCDF output ---
    if nc_out:
      write_nc_output(output_file_name_obs, eof1_lr_obs[season], pc1_obs[season], frac1_obs[season])

    # Plotting ---
    if plot:
      #plot_map(mode, 'obs', osyear, oeyear, season, eof1_obs[season], frac1_obs[season], output_file_name_obs)
      plot_map(mode, 'obs', osyear, oeyear, season, 
               eof1_lr_obs[season](latitude=(lat1,lat2),longitude=(lon1,lon2)), frac1_obs[season], output_file_name_obs)
      plot_map(mode+'_teleconnection', 'obs-lr', osyear, oeyear, season, 
               eof1_lr_obs[season](longitude=(lon1g,lon2g)), frac1_obs[season], output_file_name_obs+'_teleconnection')

    # Save stdv of PC time series in dictionary ---
    var_mode_stat_dic['REF']['obs']['defaultReference'][mode][season]['pc1_stdv'] = float(pc1_obs_stdv[season])

    if debug: print 'obs plotting end'

#=================================================
# Model
#-------------------------------------------------
for model in models:
  print ' ----- ', model,' ---------------------'
  var_mode_stat_dic['RESULTS'][model]={}
  
  #model_path = get_latest_pcmdi_mip_data_path(mip,exp,model,fq,realm,var,run)
  #model_path = '/work/cmip5/historical/atm/mo/psl/cmip5.'+model+'.historical.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'
  model_path_list = get_latest_pcmdi_mip_data_path_as_list(mip,exp,model,fq,realm,var,runs)
  
  for model_path in model_path_list:

    try:
      run = string.split((string.split(model_path,'/')[-1]),'.')[3]
      print ' --- ', run,' ---'
  
      var_mode_stat_dic['RESULTS'][model][run]={}
      var_mode_stat_dic['RESULTS'][model][run]['defaultReference']={}
      var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode]={}
  
      f = cdms.open(model_path)
    
      if var == 'psl':
        model_timeseries = f(var,time=(start_time,end_time))/100. # Pa to hPa
    
      elif var == 'ts':
        model_timeseries = f(var,time=(start_time,end_time))-273.15 # K to C degree
        model_timeseries.units = 'degC'
    
        # Replace area where temperature below -1.8 C to -1.8 C (sea ice) ---
        model_timeseries[model_timeseries<-1.8] = -1.8
  
      cdutil.setTimeBoundsMonthly(model_timeseries)
  
      #-------------------------------------------------
      # Season loop
      #- - - - - - - - - - - - - - - - - - - - - - - - -
      for season in seasons:
        var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]={}
    
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
          model_timeseries, model_global_mean_timeseries = \
                                    genutil.grower(model_timeseries, model_global_mean_timeseries) # Matching dimension
          model_timeseries = model_timeseries - model_global_mean_timeseries 

          # Assign same variable name as other modes of variability ---
          model_timeseries_season = model_timeseries
    
        else:
          # Get seasonal mean time series ---
          model_timeseries_season = getattr(cdutil,season)(model_timeseries)
    
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # Extract subdomain ---
        #. . . . . . . . . . . . . . . . . . . . . . . . .
        model_timeseries_season_subdomain = model_timeseries_season(latitude=(lat1,lat2),longitude=(lon1,lon2))
    
        #-------------------------------------------------
        # Usual EOF approach
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # EOF analysis ---
        eof1, pc1, frac1, solver, reverse_sign = \
              eof_analysis_get_first_variance_mode(mode, model_timeseries_season_subdomain)
        if debug: print 'eof analysis'
    
        # Linear regression to have extended global map:
        # -- Reconstruct EOF fist mode including teleconnection purpose as well
        # -- Have confirmed that "eof1_lr" is identical to "eof1" over EOF domain (i.e., "subdomain")
        # -- Note that eof1_lr has global field ---
        eof1_lr = linear_regression(pc1, model_timeseries_season)
        if debug: print 'linear regression'
    
        # Calculate stdv of pc time series ---
        model_pcs_stdv = calcSTD(pc1)
    
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # OBS statistics (only over EOF domain), save as dictionary ---
        #. . . . . . . . . . . . . . . . . . . . . . . . .
        if obs_compare:
    
          # Regrid (interpolation, model grid to ref grid) ---
          if debug: print 'regrid (global) start'
          eof1_lr_regrid_global = eof1_lr.regrid(ref_grid_global, regridTool='regrid2', mkCyclic=True)
          if debug: print 'regrid end'
    
          # Extract subdomain ---
          eof1_regrid = eof1_lr_regrid_global(latitude=(lat1,lat2),longitude=(lon1,lon2))

          # Spatial correlation weighted by area ('generate' option for weights) ---
          cor = calcSCOR(eof1_regrid, eof1_obs[season])
          cor_glo = calcSCOR(eof1_lr_regrid_global, eof1_lr_obs[season])
          if debug: print 'cor end'

          # Double check for arbitrary sign control --- 
          if cor < 0: 
            eof1 = eof1 * -1
            pc1 = pc1 * -1
            eof1_lr = eof1_lr * -1
            eof1_lr_regrid_global = eof1_lr_regrid_global * -1
            eof1_regrid = eof1_regrid * -1
            # Calc cor again ---
            cor = calcSCOR(eof1_regrid, eof1_obs[season])
            cor_glo = calcSCOR(eof1_lr_regrid_global, eof1_lr_obs[season])
    
          # RMS (uncentered) difference ---
          rms = calcRMS(eof1_regrid, eof1_obs[season])
          rms_glo = calcRMS(eof1_lr_regrid_global, eof1_lr_obs[season])
          if debug: print 'rms end'

          # RMS (centered) difference ---
          rmsc = calcRMSc(eof1_regrid, eof1_obs[season])
          rmsc_glo = calcRMSc(eof1_lr_regrid_global, eof1_lr_obs[season])
          if debug: print 'rmsc end'

          # Bias ---
          bias = calcBias(eof1_regrid, eof1_obs[season])
          bias_glo = calcBias(eof1_lr_regrid_global, eof1_lr_obs[season])
          if debug: print 'bias end'
    
          # Add to dictionary for json output ---
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms'] = float(rms)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_glo'] = float(rms_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc'] = float(rmsc)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_glo'] = float(rmsc_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor'] = float(cor)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_glo'] = float(cor_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias'] = float(bias)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_glo'] = float(bias_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['frac'] = float(frac1)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['std_model_pcs'] = float(model_pcs_stdv)
    
        #-------------------------------------------------
        # pseudo model PC timeseries and teleconnection 
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        if pseudo and obs_compare:
          # Regrid (interpolation, model grid to ref grid) ---
          model_timeseries_season_regrid = model_timeseries_season.regrid(ref_grid_global, regridTool='regrid2', mkCyclic=True)
          model_timeseries_season_regrid_subdomain = model_timeseries_season_regrid(latitude=(lat1,lat2),longitude=(lon1,lon2))
    
          # Matching model's missing value location to that of observation ---
          # 1) Replace model's masked grid to 0, so theoritically won't affect to result
          # 2) Give obs's mask to model field, so enable projecField functionality below 
          missing_value = model_timeseries_season_regrid_subdomain.missing
          model_timeseries_season_regrid_subdomain[ model_timeseries_season_regrid_subdomain == missing_value ] = 0
          model_timeseries_season_regrid_subdomain.mask = model_timeseries_season_regrid_subdomain.mask + eof1_obs[season].mask
    
          # Pseudo model PC time series ---
          pseudo_pcs = solver_obs[season].projectField(model_timeseries_season_regrid_subdomain,neofs=1,eofscaling=1)
          pseudo_pcs = pseudo_pcs(squeeze=1)
    
          # Arbitrary sign control, attempt to make all plots have the same sign ---
          if reverse_sign_obs[season]: pseudo_pcs = pseudo_pcs * -1.
        
          # Calculate stdv of pc time series
          pseudo_pcs_stdv = calcSTD(pseudo_pcs)
    
          # Linear regression to have extended global map; teleconnection purpose ---
          eof1_lr_pseudo = linear_regression(pseudo_pcs, model_timeseries_season_regrid)
    
          # Extract subdomain for statistics
          eof1_lr_pseudo_subdomain = eof1_lr_pseudo(latitude=(lat1,lat2),longitude=(lon1,lon2))
    
          #- - - - - - - - - - - - - - - - - - - - - - - - -
          # OBS statistics (over global domain), save as dictionary, alternative approach -- pseudo PC analysis
          #. . . . . . . . . . . . . . . . . . . . . . . . .
          # Spatial correlation weighted by area ('generate' option for weights) ---
          cor_alt = calcSCOR(eof1_lr_pseudo_subdomain, eof1_obs[season])
          cor_alt_glo = calcSCOR(eof1_lr_pseudo, eof1_lr_obs[season])
          if debug: print 'pseudo cor end'

          # RMS (uncentered) difference ---
          rms_alt = calcRMS(eof1_lr_pseudo_subdomain, eof1_obs[season])
          rms_alt_glo = calcRMS(eof1_lr_pseudo, eof1_lr_obs[season])
          if debug: print 'pseudo rms end'
    
          # RMS (centered) difference ---
          rmsc_alt = calcRMSc(eof1_lr_pseudo_subdomain, eof1_obs[season])
          rmsc_alt_glo = calcRMSc(eof1_lr_pseudo, eof1_lr_obs[season])
          if debug: print 'pseudo rmsc end'

          # Temporal correlation between pseudo PC timeseries and usual model PC timeseries
          tc = calcTCOR(pseudo_pcs, pc1)
          if debug: print 'pseudo tc end'
    
          # Bias ---
          bias_alt = calcBias(eof1_lr_pseudo_subdomain, eof1_obs[season])
          bias_alt_glo = calcBias(eof1_lr_pseudo, eof1_lr_obs[season])
          if debug: print 'pseudo bias end'

          # Add to dictionary for json output ---
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_alt'] = float(rms_alt)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rms_alt_glo'] = float(rms_alt_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_alt'] = float(rmsc_alt)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['rmsc_alt_glo'] = float(rmsc_alt_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_alt'] = float(cor_alt)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['cor_alt_glo'] = float(cor_alt_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_alt'] = float(bias_alt)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['bias_alt_glo'] = float(bias_alt_glo)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['std_pseudo_pcs'] = float(pseudo_pcs_stdv)
          var_mode_stat_dic['RESULTS'][model][run]['defaultReference'][mode][season]['tcor_pseudo_vs_model_pcs'] = float(tc)
    
          if debug: print 'pseudo pcs end'
    
        #-------------------------------------------------
        # Record results
        #- - - - - - - - - - - - - - - - - - - - - - - - -
        # Set output file name for NetCDF and plot ---
        output_file_name = out_dir + '/' \
                         + mode+'_'+var+'_EOF1_'+season+'_' \
                         + mip+'_'+model+'_'+exp+'_'+run+'_'+fq+'_'+realm+'_'+str(syear)+'-'+str(eyear)
    
        # Save global map, pc timeseries, and fraction in NetCDF output ---
        if nc_out:
          write_nc_output(output_file_name, eof1_lr, pc1, frac1)
          if pseudo and obs_compare: 
            write_nc_output(output_file_name+'_pseudo', eof1_lr_pseudo, pc1, frac1)
    
        # Plot map ---
        if plot:
          #plot_map(mode, model+'_'+run, syear, eyear, season, eof1, frac1, output_file_name)
          plot_map(mode, model+' ('+run+')', syear, eyear, season, 
                   eof1_lr(latitude=(lat1,lat2),longitude=(lon1,lon2)), frac1, output_file_name)
          plot_map(mode+'_teleconnection', model+' ('+run+')', syear, eyear, season, 
                   eof1_lr(longitude=(lon1g,lon2g)), frac1, output_file_name+'_teleconnection')
          if pseudo: 
            plot_map(mode, model+' ('+run+')'+' - pseudo', syear, eyear, season, 
                     eof1_lr_pseudo(latitude=(lat1,lat2),longitude=(lon1,lon2)), -999, output_file_name+'_pseudo')
            plot_map(mode+'_pseudo_teleconnection', model+' ('+run+')', syear, eyear, season, 
                     eof1_lr_pseudo(longitude=(lon1g,lon2g)), -999, output_file_name+'_pseudo_teleconnection')
    
      #=================================================
      # Write dictionary to json file (let the json keep overwritten in model loop)
      #-------------------------------------------------
      if obs_compare:
        json_filename = out_dir + '/' \
                      + 'var_mode_'+mode+'_eof1_stat_'+mip+'_'+exp+'_'+fq+'_'+realm+'_'+str(syear)+'-'+str(eyear)
        json.dump(var_mode_stat_dic, open(json_filename + '.json','w'), sort_keys=True, indent=4, separators=(',', ': '))

    except:
      print 'faild for ', model, run
      pass

if not debug: sys.exit('done')
