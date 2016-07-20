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

libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'eof_analysis.py',
            'write_nc_output.py',
            'plot_map.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

mip = 'cmip5'
#exp = 'piControl'
exp = 'historical'
model = 'ACCESS1-0'
fq = 'mo'
realm = 'atm'
var = 'psl'
run = 'r1i1p1'

test = True
#test = False

#mode = 'nam' # Northern Annular Mode
#mode = 'nao' # Northern Atlantic Oscillation
#mode = 'sam' # Southern Annular Mode
mode = 'pna' # Pacific North American Pattern

obs_compare = True
obs_compare = False

nc_out = True
#nc_out = False

plot = True
#plot = False

if test:
  #models = ['ACCESS1-0']  # Test just one model
  models = ['ACCESS1-3']  # Test just one model
  seasons = ['DJF']
  #seasons = ['MAM']
else:
  models = get_all_mip_mods(mip,exp,fq,realm,var)
  seasons = ['DJF','MAM','JJA','SON']

syear = 1900
#syear = 1990 # To match with ERAINT...
eyear = 2005

start_time = cdtime.comptime(syear,1,1)
end_time = cdtime.comptime(eyear,12,31)

if mode == 'nam':
  lat1 = 20
  lat2 = 90
  lon1 = -180
  lon2 = 180
elif mode == 'nao':
  lat1 = 20
  lat2 = 80
  lon1 = -90
  lon2 = 40
elif mode == 'sam':
  lat1 = -20
  lat2 = -90
  lon1 = 0
  lon2 = 360
elif mode == 'pna':
  lat1 = 20
  lat2 = 85
  lon1 = 120
  lon2 = 240

#=================================================
# Observation
#-------------------------------------------------
if obs_compare:
  obs_path = '/clim_obs/obs/atm/mo/psl/ERAINT/psl_ERAINT_198901-200911.nc'
  fo = cdms.open(obs_path)
  obs_timeseries = fo(var,latitude=(lat1,lat2),longitude=(lon1,lon2),time=(start_time,end_time))/100. # Pa to hPa
  cdutil.setTimeBoundsMonthly(obs_timeseries)

  ref_grid = obs_timeseries.getGrid() # Extract grid information for Regrid below

  obs_timeseries_season={}
  eof1_obs={}
  pc1_obs={}
  frac1_obs={}
  
  #-------------------------------------------------
  # Season loop
  #- - - - - - - - - - - - - - - - - - - - - - - - -
  for season in seasons:

    obs_timeseries_season['season'] = getattr(cdutil,season)(obs_timeseries)

    # EOF analysis ---
    eof1_obs['season'], pc1_obs['season'], frac1_obs['season'] = eof_analysis_get_first_variance_mode(obs_timeseries_season['season'])

    # Set output file name for NetCDF and plot ---
    output_file_name_obs = mode+'_psl_eof1_'+season+'_obs_'+str(syear)+'-'+str(eyear)

    # Save in NetCDF output ---
    if nc_out:
      write_nc_output(output_file_name_obs, eof1_obs['season'], pc1_obs['season'], frac1_obs['season'])

    #-------------------------------------------------
    # GRAPHIC (plotting) PART
    #- - - - - - - - - - - - - - - - - - - - - - - - -
    if plot:
      plot_map(mode, 'obs', syear, eyear, season, eof1_obs['season'], frac1_obs['season'], output_file_name_obs)

#=================================================
# Model
#-------------------------------------------------
var_mode_stat_dic={}
var_mode_stat_dic['RESULTS']={}

for model in models:
  var_mode_stat_dic['RESULTS'][model]={}
  var_mode_stat_dic['RESULTS'][model]['defaultReference']={}
  var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode]={}

  model_path = get_latest_pcmdi_mip_data_path(mip,exp,model,fq,realm,var,run)
  #model_path = '/work/cmip5/historical/atm/mo/psl/cmip5.'+model+'.historical.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'
  print model

  f = cdms.open(model_path)
  model_timeseries = f(var,latitude=(lat1,lat2),longitude=(lon1,lon2),time=(start_time,end_time))/100. # Pa to hPa
  cdutil.setTimeBoundsMonthly(model_timeseries)

  #-------------------------------------------------
  # Season loop
  #- - - - - - - - - - - - - - - - - - - - - - - - -
  for season in seasons:
    var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]={}

    model_timeseries_season = getattr(cdutil,season)(model_timeseries)

    # EOF analysis ---
    eof1, pc1, frac1 = eof_analysis_get_first_variance_mode(model_timeseries_season)

    # Set output file name for NetCDF and plot ---
    output_file_name = mode+'_psl_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)

    # Save in NetCDF output ---
    if nc_out:
      write_nc_output(output_file_name,eof1,pc1,frac1)
    
    #-------------------------------------------------
    # OBS statistics (regrid will be needed) output, save as dictionary
    #- - - - - - - - - - - - - - - - - - - - - - - - -
    if obs_compare:

      # Regrid (interpolation, model grid to ref grid) ---
      eof1_regrid = eof1.regrid(ref_grid,regredTool='regrid2') # regrid location test 1

      # RMS difference ---
      rms = genutil.statistics.rms(eof1_regrid, eof1_obs['season'], axis='xy')

      # Spatial correlation weighted by area ('generate' option for weights) ---
      cor = genutil.statistics.correlation(eof1_regrid, eof1_obs['season'], weights='generate', axis='xy')

      # Add to dictionary for json output ---
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['rms'] = float(rms)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['cor'] = float(cor)
      var_mode_stat_dic['RESULTS'][model]['defaultReference'][mode][season]['frac'] = float(frac1)

    #-------------------------------------------------
    # GRAPHIC (plotting) PART
    #- - - - - - - - - - - - - - - - - - - - - - - - -
    if plot:
      plot_map(mode, model, syear, eyear, season, eof1, frac1, output_file_name)

# Write dictionary to json file
if obs_compare:
  json_filename = 'var_mode_'+mode+'_eof1_stat_' + mip + '_' + exp + '_' + run + '_' + fq + '_' + realm + '_' + str(syear) + '-' + str(eyear)
  json.dump(var_mode_stat_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))
