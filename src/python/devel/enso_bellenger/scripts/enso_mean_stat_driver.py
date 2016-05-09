import sys, os
import string
#import durolib    ## P. Durack functions for determing 'latest' xml files
import subprocess
import cdms2 as cdms
import cdutil
import genutil
import time
import json

libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'PMP_rectangular_domains.py',
            'monthly_variability_statistics.py',
            'slice_tstep.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

mip = 'cmip5'
exp = 'piControl'
mod = 'IPSL-CM5B-LR'
fq = 'mo'
realm = 'atm'
var = 'ts'
run = 'r1i1p1'

#test = True
test = False

if test:
  mods = ['IPSL-CM5B-LR']  # Test just one model
  #stats = ['SST_RMSE'] # Test just one reg
  #stats = ['SST_AMP'] # Test just one reg
  #stats = ['TAUU_RMSE'] # Test just one reg
  stats = ['PR_RMSE'] # Test just one reg
  stats = ['SST_RMSE','PR_RMSE'] # Test just one reg
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  stats = ['SST_RMSE','SST_AMP','TAUU_RMSE','PR_RMSE']

# Prepare dictionary frame
enso_stats_dic = {}  # Dictionary to be output to JSON file
for mod in mods:
  enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
  enso_stats_dic[mod]['mean_stat'] = {}   # create an additional level of dictionary

# Start loop
for stat in stats:
  print ' ----- ', stat,' ---------------------'
  # Too messy below.. should be a better way....
  if stat == 'SST_RMSE':
    mod_var = 'ts'
    reg = 'TropPac'
    obs_var = 'sst'
    obs_var_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
  elif stat == 'SST_AMP':
    mod_var = 'ts'
    reg = 'Nino3'
    obs_var = 'sst'
    obs_var_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
  elif stat == 'TAUU_RMSE':
    mod_var='tauu'
    reg = 'EqPac'
    obs_var = 'tauu'
    obs_var_path = '/clim_obs/obs/atm/mo/tauu/ERAINT/tauu_ERAINT_198901-200911.nc'
  elif stat == 'PR_RMSE':
    mod_var = 'pr'
    reg = 'IndoPac'
    obs_var = 'pr'
    obs_var_path = '/clim_obs/obs/atm/mo/pr/GPCP/pr_GPCP_197901-200909.nc'
  else:
    sys.exit(stat+" is not defined")

  # Get region information
  reg_selector = get_reg_selector(reg)

  # Prepare obs dataset
  fo = cdms.open(obs_var_path)
  if test:
    reg_timeseries_o = fo(obs_var,reg_selector,time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
  else:
    reg_timeseries_o = fo(obs_var,reg_selector)
  # Get climatology
  obs_clim = cdutil.averager(reg_timeseries_o,axis='t')
  # Prepare regrid
  obs_grid = obs_clim.getGrid()

  for mod in mods:
    #print ' ----- ', mod,' ---------------------'
    #enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
    #enso_stats_dic[mod]['mean_stat'] = {}   # create an additional level of dictionary

    mod_var_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,mod_var,run)
    fm = cdms.open(mod_var_path)
    if test:
      reg_timeseries_m = fm(mod_var,reg_selector,time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
    else:
      reg_timeseries_m = fm(mod_var,reg_selector)
    if stat != 'SST_AMP':
      # Get climatology
      mod_clim = cdutil.averager(reg_timeseries_m,axis='t')
      if stat == 'SST_RMSE':
        mod_clim = mod_clim - 273.15 # K to C degree
      # regrid needed here (mod to obs)
      mod_clim_regrid = mod_clim.regrid(obs_grid,regridTool='regrid2')
      # get RMS
      result = float(genutil.statistics.rms(mod_clim_regrid,obs_clim,axis='xy'))
    else:
      # Get annual cycle
      mod_ann_cycle = cdutil.ANNUALCYCLE.climatology(reg_timeseries_m)
      #obs_ann_cycle = cdutil.ANNUALCYCLE.climatology(reg_timeseries_o)
      mod_ann_cycle_area_avg = cdutil.averager(mod_ann_cycle,axis='xy')
      # Is below a right way to get amplitude??
      #result = (np.amax(mod_ann_cycle_area_avg)-np.amin(mod_ann_cycle_area_avg))/2.
      result = np.amax(mod_ann_cycle_area_avg)-np.mean(mod_ann_cycle_area_avg)

    print mod, stat, 'stat =', result
    enso_stats_dic[mod]['mean_stat'][stat] = result

    if not test:
      fm.close()
      fo.close()

# Write dictionary to json file
json_filename = 'ENSO_mean_stat_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm
json.dump(enso_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

print 'all done'
