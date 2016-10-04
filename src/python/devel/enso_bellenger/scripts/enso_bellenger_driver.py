import sys, os
import string
import cdms2 as cdms
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
fq = 'mo'
realm = 'atm'
#var = 'ts'
var = 'pr'
run = 'r1i1p1'

#debug = True
debug = False

if debug:
  mods = ['IPSL-CM5B-LR']  # Test just one model
  regs = ['Nino3.4'] # Test just one region
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  #regs = ['Nino3.4', 'Nino3', 'Nino4', 'Nino1.2','TSA','TNA','IO']
  regs = ['Nino3', 'Nino4']

enso_stat_dic = {}  # Dictionary for JSON output file
enso_stat_dic['REF'] = {}
enso_stat_dic['RESULTS'] = {}

#=================================================
# Observation
#-------------------------------------------------
print ' ----- obs ---------------------'

if var == 'ts':
  obs_path = '/clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc'
  var_o = 'sst'
elif var == 'pr':
  obs_path = '/clim_obs/obs/atm/mo/pr/GPCP/pr_GPCP_197901-200909.nc'
  var_o = 'pr'

fo = cdms.open(obs_path)

try:
  for reg in regs:
    enso_stat_dic['REF'][reg] = {}
    reg_selector = get_reg_selector(reg)
    print reg, reg_selector
  
    if debug:
      reg_timeseries = fo(var_o, reg_selector, time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
    else:
      reg_timeseries = fo(var_o ,reg_selector) 

    std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 
    std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
    std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')

    # Dictionary ---
    enso_stat_dic['REF']['source'] = obs_path
    enso_stat_dic['REF'][reg]['std'] = {}
    enso_stat_dic['REF'][reg]['std_NDJ'] = {}
    enso_stat_dic['REF'][reg]['std_MAM'] = {}

    # Record Std. dev. from above calculation ---
    enso_stat_dic['REF'][reg]['std']['entire'] = std
    enso_stat_dic['REF'][reg]['std_NDJ']['entire'] = std_NDJ
    enso_stat_dic['REF'][reg]['std_MAM']['entire'] = std_MAM

except:
  print 'failed for obs'
  pass

#=================================================
# Models 
#-------------------------------------------------
for mod in mods:
  print ' ----- ', mod,' ---------------------'

  try:
    enso_stat_dic['RESULTS'][mod] = {}

    mod_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run)  
    f = cdms.open(mod_path)
    if debug: print mod_path 
  
    for reg in regs:
      enso_stat_dic['RESULTS'][mod][reg] = {}
      reg_selector = get_reg_selector(reg)
      print reg, reg_selector
  
      if debug:
        reg_timeseries = f(var,reg_selector,time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
      else:
        reg_timeseries = f(var,reg_selector)  
  
      std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 
      std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
      std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')
  
      if debug:
        print mod, ' ', reg
        print 'std = ', std
        print 'std_NDJ = ', std_NDJ
        print 'std_MAM = ', std_MAM
  
      # Dictionary ---
      enso_stat_dic['RESULTS'][mod][reg]['std'] = {}
      enso_stat_dic['RESULTS'][mod][reg]['std_NDJ'] = {}
      enso_stat_dic['RESULTS'][mod][reg]['std_MAM'] = {}
  
      # Record Std. dev. from above calculation ---
      enso_stat_dic['RESULTS'][mod][reg]['std']['entire'] = std
      enso_stat_dic['RESULTS'][mod][reg]['std_NDJ']['entire'] = std_NDJ
      enso_stat_dic['RESULTS'][mod][reg]['std_MAM']['entire'] = std_MAM
  
      # Multiple centuries ---
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
        enso_stat_dic['RESULTS'][mod][reg]['std'][tkey] = std
        enso_stat_dic['RESULTS'][mod][reg]['std_NDJ'][tkey] = std_NDJ
        enso_stat_dic['RESULTS'][mod][reg]['std_MAM'][tkey] = std_MAM
  
    enso_stat_dic['RESULTS'][mod]['reg_time'] = ntstep
    f.close()

    # Write dictionary to json file ---
    json_filename = 'ENSO_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var
    json.dump(enso_stat_dic, open(json_filename + '.json','w'), sort_keys=True, indent=4, separators=(',', ': '))
  
  except:
    print 'failed for model ', mod

print 'all done for', var
