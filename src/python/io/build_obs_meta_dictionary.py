#!/usr/local/uvcdat/latest/bin/python
import cdms2 as cdms
import json, os, sys, string
data_path = '/work/gleckler1/processed_data/metrics_package/obs'


lst = os.popen('ls ' + data_path + '/*/mo/*/*/ac/*.nc').readlines()

obs_dic = {}

for l in lst:
  subp = string.split(l,'obs')[1]
# print subp

  var = string.split(subp,'/')[3]

  if var not in obs_dic.keys(): obs_dic[var] = {}

  product = string.split(subp,'/')[4]

  if product not in obs_dic[var].keys(): obs_dic[var][product] = {}

  partial_filename = string.split(subp,'pcmdi-metrics')[1]

  realm = string.split(partial_filename,'_')[1]
  period = string.split(partial_filename,'_')[3]
  period = string.split(period,'-clim.nc')[0]

  obs_dic[var][product]['CMIP_CMOR_TABLE'] = realm
  obs_dic[var][product]['period'] = period 

  print var,' ', product,'  ', realm,' ', period

  f = cdms.open(l[:-1])
  d = f(var)
  shape = d.shape
  f.close()

  shape = `d.shape`

  obs_dic[var][product]['shape'] = shape

json_name = 'obs_info_dictionary.json'

json.dump(obs_dic, open('../../../doc/' + json_name, "wb" ),sort_keys=True, indent=4, separators=(',', ': '))


 

