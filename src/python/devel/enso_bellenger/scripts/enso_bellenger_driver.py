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
            'monthly_variability_statistics.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

#os.system('ln -sf ../lib/durolib.py .') ## This should be a temporary solution...

mip = 'cmip5'
exp = 'piControl'
mod = 'IPSL-CM5B-LR'
fq = 'mo'
realm = 'atm'
var = 'ts'
#var = 'pr'
run = 'r1i1p1'

mods = ['IPSL-CM5B-LR']  # Test just one model
#mods = get_all_mip_mods(mip,exp,fq,realm,var)

enso_stats_dic = {}  # Dictionary to be output to JSON file

for mod in mods:
  print ' ----- ', mod,' ---------------------'
#try:
  enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
  mod_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run)  

  print mod_path 

  f = cdms.open(mod_path)

##  for reg in ['Nino34', 'Nino3', 'Nino4', 'Nino12','TSA','TNA','IO']:
  for reg in ['Nino34']:
    enso_stats_dic[mod][reg] = {}   # create a dictionary within main dictionary
    reg_selector = get_reg_selector(reg)
    print reg, reg_selector
    reg_timeseries = f(var,reg_selector,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
#    reg_timeseries = f(var,reg_selector)  
    std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 

    std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
    std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')

    print mod, ' ', reg,'  ', std
    print 'std_NDJ = ', std_NDJ
    print 'std_MAM = ', std_MAM

    enso_stats_dic[mod][reg]['std'] = std
    enso_stats_dic[mod][reg]['std_NDJ'] = std_NDJ
    enso_stats_dic[mod][reg]['std_MAM'] = std_MAM

  enso_stats_dic[mod]['reg_time'] = len(reg_timeseries)
  f.close()

#except:
#   print 'failed for model ', mod


# Write dictionary to json file

json_filename = 'test_ENSO_' + mip + '_' + exp + '_' + var
json.dump(enso_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

print 'all done'


