#!/usr/bin/env python

import cdutil
import genutil

import cdms2
import copy
import sys
import os
import string
import json
import pcmdi_metrics
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser
import collections
from collections import defaultdict

libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'monthly_variability_statistics.py',
            'slice_tstep.py']

libfiles_share = ['default_regions.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

for lib in libfiles_share:
  execfile(os.path.join('../../../../../share/',lib))

##################################################
# Pre-defined options
#=================================================
mip = 'cmip5'
exp = 'piControl'
mod = 'IPSL-CM5B-LR'
fq = 'mo'
realm = 'atm'
var = 'ts'
run = 'r1i1p1'

out_dir = './result'
if not os.path.exists(out_dir): os.makedirs(out_dir)

#=================================================
# Additional options
#=================================================
debug = True
#debug = False

if debug:
  mods = ['IPSL-CM5B-LR']  # Test just one model
  stats = ['SST_RMSE','PR_RMSE'] # Test just one reg
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  stats = ['SST_RMSE','SST_AMP','TAUU_RMSE','PR_RMSE']

#=================================================
# Declare dictionary for .json record 
#-------------------------------------------------
# Prepare dictionary frame
def tree(): return defaultdict(tree)
enso_stat_dic = tree()  # Dictionary to be output to JSON file

json_filename = 'out_enso_mean_stat.json'

json_file = out_dir + '/' + json_filename

#=================================================
# Observation
#-------------------------------------------------
mod_var = {}
obs_clim = {}
obs_grid = {}
reg = {}

for stat in stats:
  if stat == 'SST_RMSE':
    mod_var[stat] = 'ts'
    reg[stat] = 'TropPac'
    obs_var = 'sst'
    obs_var_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
  elif stat == 'SST_AMP':
    mod_var[stat] = 'ts'
    reg[stat] = 'Nino3'
    obs_var = 'sst'
    obs_var_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
  elif stat == 'TAUU_RMSE':
    mod_var[stat] = 'tauu'
    reg[stat] = 'EqPac'
    obs_var = 'tauu'
    obs_var_path = '/clim_obs/obs/atm/mo/tauu/ERAINT/tauu_ERAINT_198901-200911.nc'
  elif stat == 'PR_RMSE':
    mod_var[stat] = 'pr'
    reg[stat] = 'IndoPac'
    obs_var = 'pr'
    obs_var_path = '/clim_obs/obs/atm/mo/pr/GPCP/pr_GPCP_197901-200909.nc'
  else:
    sys.exit(stat+" is not defined")

  # Prepare obs dataset
  fo = cdms2.open(obs_var_path)
  if debug:
    reg_timeseries_o = fo(obs_var,regions_specs[reg[stat]]['domain'],time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
  else:
    reg_timeseries_o = fo(obs_var,regions_specs[reg[stat]]['domain'])

  # Get climatology
  obs_clim[stat] = cdutil.averager(reg_timeseries_o,axis='t')

  # Prepare regrid
  obs_grid[stat] = obs_clim[stat].getGrid()

  if stat in ['SST_RMSE','TAUU_RMSE','PR_RMSE']:
    enso_stat_dic['REF'][stat][reg[stat]] = 0
  elif stat == 'SST_AMP':
    obs_ann_cycle = cdutil.ANNUALCYCLE.climatology(reg_timeseries_o)
    obs_ann_cycle_area_avg = cdutil.averager(obs_ann_cycle,axis='xy')
    # Get amplitude (Is below a right way to get amplitude??)
    result = np.amax(obs_ann_cycle_area_avg)-np.mean(obs_ann_cycle_area_avg)
    enso_stat_dic['REF'][stat][reg[stat]] = result

  enso_stat_dic['REF'][stat]['source'] = obs_var_path

  if not debug:
    fo.close()

#=================================================
# Models 
#-------------------------------------------------
for stat in stats:
  print ' ===== ', stat,' ====================='

  for mod in mods:
    try:

      print ' ----- ', mod,' ---------------------'
  
      mod_var_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,mod_var[stat],run)
      fm = cdms2.open(mod_var_path)
  
      if debug:
        reg_timeseries_m = fm(mod_var[stat],regions_specs[reg[stat]]['domain'],time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
      else:
        reg_timeseries_m = fm(mod_var[stat],regions_specs[reg[stat]]['domain'])
  
      if stat in ['SST_RMSE','TAUU_RMSE','PR_RMSE']:
        # Get climatology
        mod_clim = cdutil.averager(reg_timeseries_m,axis='t')
        if stat == 'SST_RMSE':
          mod_clim = mod_clim - 273.15 # K to C degree
        # Regrid (mod to obs)
        mod_clim_regrid = mod_clim.regrid(obs_grid[stat], regridTool='regrid2')
        # Get RMS
        result = float(genutil.statistics.rms(mod_clim_regrid, obs_clim[stat], axis='xy'))
      elif stat == 'SST_AMP':
        # Get annual cycle
        mod_ann_cycle = cdutil.ANNUALCYCLE.climatology(reg_timeseries_m)
        mod_ann_cycle_area_avg = cdutil.averager(mod_ann_cycle,axis='xy')
        # Get amplitude (Is below a right way to get amplitude??)
        result = np.amax(mod_ann_cycle_area_avg)-np.mean(mod_ann_cycle_area_avg)
  
      print mod, stat, 'stat =', result
  
      enso_stat_dic['RESULTS'][mod]['mean_stat'][stat][reg[stat]] = result
  
      if not debug:
        fm.close()
  
    except:
      print 'failed for model ', mod
      pass

#=================================================
#  OUTPUT METRICS TO JSON FILE
#-------------------------------------------------
OUT = pcmdi_metrics.io.base.Base(os.path.abspath(jout), outfilejson)

disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pmp",
        "disclaimer.txt")).read()

metrics_dictionary = collections.OrderedDict()
metrics_dictionary["DISCLAIMER"] = disclaimer
metrics_dictionary["REFERENCE"] = "The statistics in this file are based on Bellenger, H et al. Clim Dyn (2014) 42:1999-2018. doi:10.1007/s00382-013-1783-z"
metrics_dictionary["RESULTS"] = enso_stat_dic  # collections.OrderedDict()

OUT.var = var
OUT.write(
    metrics_dictionary,
    json_structure=["model", "index", "statistic", "period_chunk"],
    indent=4,
    separators=(
        ',',
        ': '),
    sort_keys=True)

sys.exit('done')
