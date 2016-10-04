import sys, os
import string
import cdms2 as cdms
import time
import json
import shutil

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
fq = 'mo'
realm = 'atm'
run = 'r1i1p1'

#var = 'ts'
var = 'pr'

out_dir = './result'
if not os.path.exists(out_dir): os.makedirs(out_dir)

#=================================================
# Additional options
#=================================================
debug = True
#debug = False

if debug:
  #mods = ['IPSL-CM5B-LR']  # Test just one model
  #mods = ['ACCESS1-0']  # Test just one model
  mods = ['ACCESS1-3']  # Test just one model
  regs = ['Nino1.2'] # Test just one region
else:
  mods = get_all_mip_mods(mip,exp,fq,realm,var)
  #regs = ['Nino3.4', 'Nino3', 'Nino4', 'Nino1.2','TSA','TNA','IO']
  regs = ['Nino3', 'Nino4']

#=================================================
# Declare dictionary for .json record 
#-------------------------------------------------
enso_stat_dic = {}  # Dictionary for JSON output file

json_filename = 'ENSO_' + mip + '_' + exp + '_' + run + '_' + fq + '_' +realm + '_' + var

json_file = out_dir + '/' + json_filename + '.json'
json_file_org = out_dir + '/' + json_filename + '_org.json'

# Keep previous version of json file against overwrite ---
if os.path.isfile(json_file):
  shutil.copyfile(json_file, json_file_org)

update_json = True

if update_json == True and os.path.isfile(json_file): 
  fj = open(json_file)
  enso_stat_dic = json.loads(fj.read())
  fj.close()

if 'REF' not in enso_stat_dic.keys():
  enso_stat_dic['REF']={}
if 'RESULTS' not in enso_stat_dic.keys():
  enso_stat_dic['RESULTS']={}

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

    if reg not in enso_stat_dic['REF'].keys():
      enso_stat_dic['REF'][reg] = {}

    if debug:
      reg_timeseries = fo(var_o, regions_specs[reg]['domain'], time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
    else:
      reg_timeseries = fo(var_o, regions_specs[reg]['domain']) 

    std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 
    std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
    std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')

    # Dictionary ---
    enso_stat_dic['REF']['source'] = obs_path

    if 'std' not in enso_stat_dic['REF'][reg].keys():
      enso_stat_dic['REF'][reg]['std'] = {}
    if 'std_NDJ' not in enso_stat_dic['REF'][reg].keys():
      enso_stat_dic['REF'][reg]['std_NDJ'] = {}
    if 'std_MAM' not in enso_stat_dic['REF'][reg].keys():
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

    if mod not in enso_stat_dic['RESULTS'].keys():
      enso_stat_dic['RESULTS'][mod] = {}

    mod_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,var,run)  
    f = cdms.open(mod_path)
    if debug: print mod_path 
  
    for reg in regs:
      if reg not in enso_stat_dic['RESULTS'][mod].keys():
        enso_stat_dic['RESULTS'][mod][reg] = {}
  
      if debug:
        reg_timeseries = f(var, regions_specs[reg]['domain'], time = slice(0,60))   # RUN CODE FAST ON 5 YEARS OF DATA
      else:
        reg_timeseries = f(var, regions_specs[reg]['domain'])  
  
      std = interannual_variabilty_std_annual_cycle_removed(reg_timeseries) 
      std_NDJ = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'NDJ')
      std_MAM = interannual_variability_seasonal_std_mean_removed(reg_timeseries,'MAM')
  
      if debug:
        print mod, ' ', reg
        print 'std = ', std
        print 'std_NDJ = ', std_NDJ
        print 'std_MAM = ', std_MAM
  
      # Dictionary ---
      if 'std' not in enso_stat_dic['RESULTS'][mod][reg].keys():
        enso_stat_dic['RESULTS'][mod][reg]['std'] = {}
      if 'std_NDJ' not in enso_stat_dic['RESULTS'][mod][reg].keys():
        enso_stat_dic['RESULTS'][mod][reg]['std_NDJ'] = {}
      if 'std_MAM' not in enso_stat_dic['RESULTS'][mod][reg].keys():
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
    json.dump(enso_stat_dic, open(json_file,'w'), sort_keys=True, indent=4, separators=(',', ': '))
  
  except:
    print 'failed for model ', mod

print 'all done for', var
