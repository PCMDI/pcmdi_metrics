import json, string, os

# PJG: Jan 22, 2014
# THIS CODE IDENTIFIES THE PERIOD FOR EACH OBS DATASET AND SAVES IT INTO A JSON DICTIONARY

obs_base_path = '/work/gleckler1/processed_data/metrics_package/obs/'

lst = os.popen('ls ' + obs_base_path + '*/mo/*/*/ac/*.nc').readlines()

obs_period_dic = {}

vars = []
for l in lst:
  var = string.split(l,'/')[8]
  if var not in vars: vars.append(var)

for var in vars:
 lst1 = os.popen('ls ' + obs_base_path + '*/mo/' + var + '/*/ac/*.nc').readlines() 
 obs_period_dic[var] = {}
 for l in lst1:
  obs = string.split(l,'/')[9]
  tmp = string.split(l,'/')[11]
  period = string.split(tmp,'_')[4]
  period = string.replace(period,'-clim.nc\n','')
  print var,'  ', obs,' ', period 
  obs_period_dic[var][obs] = period

json.dump(obs_period_dic, open('obs_period_dictionary.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

