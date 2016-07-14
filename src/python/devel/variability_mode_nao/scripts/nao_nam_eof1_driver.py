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

#mode = 'nam' # Northern Hemisphere
mode = 'nao' # Northern Atlantic

plot = True
#plot = False

if test:
  models = ['ACCESS1-0']  # Test just one model
  #models = ['ACCESS1-3']  # Test just one model
  seasons = ['DJF']
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

#=================================================
# Observation
#-------------------------------------------------
obs_path = '/clim_obs/obs/atm/mo/psl/ERAINT/psl_ERAINT_198901-200911.nc'
#fo = cdms.open(obs_path)
#obs_timeseries = fo(var,latitude=(lat1,lat2),longitude=(lon1,lon2),time=(start_time,end_time))/100. # Pa to hPa
#cdutil.setTimeBoundsMonthly(obs_timeseries)

obs_timeseries_season={}

#=================================================
# Model
#-------------------------------------------------
for model in models:
  model_path = get_latest_pcmdi_mip_data_path(mip,exp,model,fq,realm,var,run)
  #model_path = '/work/cmip5/historical/atm/mo/psl/cmip5.'+model+'.historical.r1i1p1.mo.atm.Amon.psl.ver-1.latestX.xml'
  #print model_path
  f = cdms.open(model_path)

  model_timeseries = f(var,latitude=(lat1,lat2),longitude=(lon1,lon2),time=(start_time,end_time))/100. # Pa to hPa
  cdutil.setTimeBoundsMonthly(model_timeseries)

  #-------------------------------------------------
  # Inner loop for season
  #-------------------------------------------------
  for season in seasons:

    if test:
      print model_path, season

    model_timeseries_season = getattr(cdutil,season)(model_timeseries)

    # EOF analysis ---
    eof1, pc1, frac1 = eof_analysis_get_first_variance_mode(model_timeseries_season)

    # Set output file name for NetCDF and plot ---
    output_file_name = mode+'_slp_eof1_'+season+'_'+model+'_'+str(syear)+'-'+str(eyear)

    # Save in NetCDF output ---
    fout = cdms.open(output_file_name+'.nc','w')
    fout.write(eof1,id='eof1')
    fout.write(pc1,id='pc1')
    fout.write(frac1,id='frac1')
    fout.close()

    # OBS statistics (regrid will be needed) output, save as dictionary

    #-------------------------------------------------
    # GRAPHIC (plotting) PART
    #-------------------------------------------------
    if plot:
      plot_map(mode, model, syear, eyear, season, eof1, frac1, output_file_name)


# Dump statistics output to json file....
