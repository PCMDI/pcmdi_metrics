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
#var = 'pr'
run = 'r1i1p1'

test = True
#test = False

if test:
  mods = ['IPSL-CM5B-LR']  # Test just one model
  regs = ['Nino34'] # Test just one region
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  #regs = ['Nino34', 'Nino3', 'Nino4', 'Nino12','TSA','TNA','IO']
  regs = ['Nino34', 'Nino3', 'Nino4']

enso_stats_dic = {}  # Dictionary to be output to JSON file

for mod in mods:
  print ' ----- ', mod,' ---------------------'
#try:
  enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
  mod_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run)  

  print mod_path 

  f = cdms.open(mod_path)

  for reg in regs:
    enso_stats_dic[mod][reg] = {}   # create a dictionary within main dictionary
    reg_selector = get_reg_selector(reg)
    print reg, reg_selector

    if test:
      reg_timeseries = f(var,reg_selector,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
    else:
      reg_timeseries = f(var,reg_selector)  

    std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 
    std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
    std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')

    print mod, ' ', reg
    print 'std = ', std
    print 'std_NDJ = ', std_NDJ
    print 'std_MAM = ', std_MAM

    #enso_stats_dic[mod][reg]['std'] = std
    #enso_stats_dic[mod][reg]['std_NDJ'] = std_NDJ
    #enso_stats_dic[mod][reg]['std_MAM'] = std_MAM

    ntstep = len(reg_timeseries)
    if test:
      itstep = 24 # 2-yrs
    else:
      itstep = 1200 # 100-yrs

    enso_stats_dic[mod][reg]['std'] = {}
    enso_stats_dic[mod][reg]['std_NDJ'] = {}
    enso_stats_dic[mod][reg]['std_MAM'] = {}

    for t in tstep_range(0, ntstep, itstep):
      if t == 0: # Record Std. dev. from above calculation
        enso_stats_dic[mod][reg]['std']['entire'] = std
        enso_stats_dic[mod][reg]['std_NDJ']['entire'] = std_NDJ
        enso_stats_dic[mod][reg]['std_MAM']['entire'] = std_MAM
      print t, t+itstep
      reg_timeseries_cut = reg_timeseries[t:t+itstep] 
      std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries_cut)
      std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries_cut,'NDJ')
      std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries_cut,'MAM')
      tkey=`t`+'-'+`t+itstep`+'_months'
      enso_stats_dic[mod][reg]['std'][tkey] = std
      enso_stats_dic[mod][reg]['std_NDJ'][tkey] = std_NDJ
      enso_stats_dic[mod][reg]['std_MAM'][tkey] = std_MAM

  enso_stats_dic[mod]['reg_time'] = ntstep
  f.close()

#except:
#   print 'failed for model ', mod

# Write dictionary to json file
json_filename = 'ENSO_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var
json.dump(enso_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

print 'all done for', var
