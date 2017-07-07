#!/usr/bin/env python

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

def tree():
  return defaultdict(tree)

#########################################################
# SAMPLE COMMAND LINE EXECUTION USING ARGUMENTS BELOW
#########################################################
# python -i enso_bellenger_compute.py 
# -mp /work/gleckler1/processed_data/cmip5clims_metrics_package-historical/pr_MODS_Amon_historical_r1i1p1_198001-200512-clim.nc
# -op /work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc
# --mns NorESM1-ME MRI-CGCM3
# --var ts
# --varobs sst ## varobs needed only when varname is different to model in obs
# --outpd /work/gleckler1/processed_data/wang_monsoon 
# --outpj /work/gleckler1/processed_data/metrics_package/metrics_results/wang_monsoon
#########################################################

P = PMPParser() # Includes all default options

P.add_argument("--mp", "--modpath",
               type=str,
               dest='modpath',
               default='',
               help="Explicit path to model monthly PR or TS climatology")
P.add_argument("--op", "--obspath",
               type=str,
               dest='obspath',
               default='',
               help="Explicit path to obs monthly PR or TS climatology")
P.add_argument('--mns', '--modnames',
               type=str,
               nargs='+',
               dest='modnames',
               default=None,
               help='Models to apply')
P.add_argument("--var", "--variable",
               type=str,
               dest='variable',
               default='ts',
               help="Variable: 'pr' or 'ts (default)'")
P.add_argument("--varobs", "--variableobs",
               type=str,
               dest='variableobs',
               default='ts',
               help="Variable name in observation (default: ts)")
P.add_argument("--outpj", "--outpathjsons",
               type=str,
               dest='outpathjsons',
               default='.',
               help="Output path for jsons")
P.add_argument("--outnj", "--outnamejson",
               type=str,
               dest='jsonname',
               default='out.json',
               help="Output path for jsons")
P.add_argument("--outpd", "--outpathdata",
               type=str,
               dest='outpathdata',
               default='.',
               help="Output path for data")
P.add_argument("-e", "--experiment",
               type=str,
               dest='experiment',
               default='historical',
               help="AMIP, historical or picontrol")
P.add_argument("-c", "--MIP",
               type=str,
               dest='mip',
               default='CMIP5',
               help="put options here")
P.add_argument("-p", "--parameters",
               type=str,
               dest='parameters',
               default='',
               help="")

args = P.parse_args(sys.argv[1:])

modpath = args.modpath
obspath = args.obspath
mods = args.modnames
var = args.variable
varobs = args.variableobs
outpathjsons = args.outpathjsons
outfilejson = args.jsonname
outpathdata = args.outpathdata

##########################################################
libfiles = ['durolib.py',
            'get_pcmdi_data.py',
            'PMP_rectangular_domains.py',
            'monthly_variability_statistics.py',
            'slice_tstep.py']

for lib in libfiles:
  execfile(os.path.join('./lib/',lib))
##########################################################

if var == 'ts':
    if obspath == '':
      obspath = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
      varobs = 'sst'
elif var == 'pr':
    if obspath == '':
      obspath = '/clim_obs/obs/atm/mo/pr/GPCP/pr_GPCP_197901-200909.nc'
      varobs = 'pr'
else:
    sys.exit('Variable '+var+' is not correct')

##########################################################

# SETUP WHERE TO OUTPUT RESULTING  (netcdf)
try:
    jout = outpathjsons
    os.mkdir(jout)
except BaseException:
    pass

mip = 'cmip5'
exp = 'piControl'
fq = 'mo'
realm = 'atm'
var = args.variable
run = 'r1i1p1'

debug = True
#debug = False

models = copy.copy(args.modnames)
models.insert(0,'obs')

if debug: 
    regs = ['Nino3.4', 'Nino3']
else: 
    regs = ['Nino3.4', 'Nino3', 'Nino4', 'Nino1.2','TSA','TNA','IO']

enso_stat_dic = tree() ## Set tree structure dictionary

#=================================================
# Loop for Observation and Models 
#-------------------------------------------------
for mod in models:
  print ' ----- ', mod,' ---------------------'

  if mod == 'obs':
    file_path = obspath
    varname = varobs
    mods_key = 'OBSERVATION'
  else:
    if modpath == '':
      modpath = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run)  
    file_path = modpath
    varname = var
    mods_key = 'MODELS'

  try:

    f = cdms2.open(file_path)
    enso_stat_dic[mods_key][mod]['input_data'] = file_path

    if debug: print file_path 
  
    for reg in regs:
      reg_selector = get_reg_selector(reg)
      print reg, reg_selector
  
      if debug:
        reg_timeseries = f(varname,reg_selector,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
      else:
        reg_timeseries = f(varname,reg_selector)  

      if var == 'pr': reg_timeseries *= 86400. # kgs-1m-2 to mm/day
  
      std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 
      std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
      std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')
  
      if debug:
        print mod, ' ', reg
        print 'std = ', std
        print 'std_NDJ = ', std_NDJ
        print 'std_MAM = ', std_MAM
        print 'seasonality = ', std_NDJ/std_MAM

      # Record Std. dev. from above calculation ---
      enso_stat_dic[mods_key][mod][reg]['std']['entire'] = std
      enso_stat_dic[mods_key][mod][reg]['std_NDJ']['entire'] = std_NDJ
      enso_stat_dic[mods_key][mod][reg]['std_MAM']['entire'] = std_MAM
      enso_stat_dic[mods_key][mod][reg]['seasonality']['entire'] = std_NDJ/std_MAM ## Fig. 3b of Bellenger et al. 2014
  
      # Multiple centuries (only for models) ---
      if mod != 'obs':
        ntstep = len(reg_timeseries)
        if debug:
          itstep = 24 # 2-yrs
        else:
          itstep = 1200 # 100-yrs
  
        for t in tstep_range(0, ntstep, itstep):
          print t, t+itstep
          reg_timeseries_cut = reg_timeseries[t:t+itstep] 
          std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries_cut)
          std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries_cut,'NDJ')
          std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries_cut,'MAM')
          tkey=`t`+'-'+`t+itstep`+'_months'
          enso_stat_dic[mods_key][mod][reg]['std'][tkey] = std
          enso_stat_dic[mods_key][mod][reg]['std_NDJ'][tkey] = std_NDJ
          enso_stat_dic[mods_key][mod][reg]['std_MAM'][tkey] = std_MAM
          enso_stat_dic[mods_key][mod][reg]['seasonality'][tkey] = std_NDJ/std_MAM ## Fig. 3b of Bellenger et al. 2014
    
    enso_stat_dic[mods_key][mod]['reg_time'] = ntstep
    f.close()

  except:
    print 'failed for ', mod

#  OUTPUT METRICS TO JSON FILE
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
        ': '))

print 'done'
