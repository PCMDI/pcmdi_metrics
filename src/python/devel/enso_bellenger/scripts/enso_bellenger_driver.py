import sys, os
import string
#import durolib    ## P. Durack functions for determing 'latest' xml files
import subprocess
import cdms2 as cdms
import cdutil
import genutil
import time
import json

execfile('/export/durack1/git/pylib/durolib.py')
execfile('get_pcmdi_data.py')
execfile('PMP_rectangular_domains.py')
execfile('monthly_variability_statistics.py')

mip = 'cmip5'
exp = 'piControl'
mod = 'IPSL-CM5B-LR'
fq = 'mo'
realm = 'atm'
var = 'ts'
run = 'r1i1p1'

#mods = ['IPSL-CM5B-LR']  # Test just one model
mods = get_all_mip_mods(mip,exp,fq,realm,var)


enso_stats_dic = {}  # Dictionary to be output to JSON file

for mod in mods:
  print ' ----- ', mod,' ---------------------'
#try:
  enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
  mod_ts_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,'ts',run)  
# mod_pr_path = get_pcmdi_mip_data_path(mip,exp,mod,fq,realm,'pr',run)  # for precipiation

  print mod_ts_path 

  f = cdms.open(mod_ts_path)

  for reg in ['Nino3','Nino4']:
    enso_stats_dic[mod][reg] = {}   # create a dictionary within main dictionary
    if reg == 'Nino3': reg_selector = regionNino3 
    if reg == 'Nino4': reg_selector = regionNino4 
    reg_timeseries = f('ts',reg_selector,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
#   reg_timeseries = f('ts',reg_selector)  
    std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 

    print mod, ' ', reg,'  ', std

    enso_stats_dic[mod][reg]['std'] = std

  f.close()

#except:
#   print 'failed for model ', mod


# Write dictionary to json file

json_filename = 'test_ENSO_' + mip + '_' + exp
json.dump(enso_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

print 'all done'


