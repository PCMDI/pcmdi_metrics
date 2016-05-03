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
  #regs = ['Nino34'] # Test just one region
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  #regs = ['Nino34', 'Nino3', 'Nino4', 'Nino12','TSA','TNA','IO']
  #regs = ['Nino34', 'Nino3', 'Nino4']

enso_stats_dic = {}  # Dictionary to be output to JSON file

for mod in mods:
  print ' ----- ', mod,' ---------------------'
#try:
  enso_stats_dic[mod] = {}   # create a dictionary within main dictionary
  mod_ts_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,'ts',run)  
  mod_tauu_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,'tauu',run)  

  print mod_ts_path, mod_tauu_path 

  f1 = cdms.open(mod_ts_path)
  f2 = cdms.open(mod_tauu_path)

  #for reg in regs:
  reg_selector_nino4 = get_reg_selector('Nino4')
  reg_selector_nino3 = get_reg_selector('Nino3')
  #print reg, reg_selector

  if test:
      reg_timeseries_ts = f1('ts',reg_selector_nino3,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
      reg_timeseries_tauu = f2('tauu',reg_selector_nino4,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
  else:
      reg_timeseries_ts = f1('ts',reg_selector_nino3)  
      reg_timeseries_tauu = f2('tauu',reg_selector_nino4)  

  if len(reg_timeseries_ts) == len(reg_timeseries_tauu):
      print 'reg_time =', len(reg_timeseries_ts)
      ntstep = len(reg_timeseries_ts)
  else:
      sys.exit("ts and tauu tstep not match") 

  #slope = get_slope_linear_regression(reg_timeseries_tauu,reg_timeseries_ts)
  slope = get_slope_linear_regression_from_anomaly(reg_timeseries_tauu,reg_timeseries_ts)

  print mod,'slope =', slope

  enso_stats_dic[mod]['slope'] = slope
  enso_stats_dic[mod]['reg_time'] = ntstep
  f1.close()
  f2.close()

#except:
#   print 'failed for model ', mod

# Write dictionary to json file
json_filename = 'AtmFeedback_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var
json.dump(enso_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

print 'all done for', var
