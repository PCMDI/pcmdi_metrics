#!/bin/env python

# PJG 10212014 NOW INCLUDES SFTLF FROM /obs AND HARDWIRED TEST CASE WHICH NEEDS FIXIN

import cdms2
import time, string
import json, os, sys
if len(sys.argv)>1:
    data_path = sys.argv[1]
else:
    data_path = '/work/gleckler1/processed_data/metrics_package/obs'


lst = os.popen('ls ' + data_path + '/*/mo/*/*/ac/*.nc').readlines()

## FOR MONTHLY MEAN OBS
obs_dic = {'rlut':{'default':'CERES'},
           'rsut':{'default':'CERES'},
           'rsds':{'default':'CERES',},
           'rlus':{'default':'CERES',},
           'rsus':{'default':'CERES',},
           'rlutcs':{'default':'CERES'},
           'rsutcs':{'default':'CERES'},
           'rsutcre':{'default':'CERES'},
           'rlutcre':{'default':'CERES'},
           'pr':{'default':'GPCP','alternate1':'TRMM'},
           'prw':{'default':'RSS'},
           'tas':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'psl':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'ua':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'va':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'uas':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'hus':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'vas':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'ta':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'zg':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'tauu':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'tauv':{'default':'ERAINT','alternate2':'JRA25','alternate1':'ERA40'},
           'tos':{'default':'UKMETOFFICE-HadISST-v1-1'},
           'zos':{'default':'CNES-AVISO-L4'},
           'sos':{'default':'NODC-WOA09'},
            }

for l in lst:
  subp = l.split('obs')[1]
# print subp

  var = subp.split('/')[3]

### TRAP FILE NAME FOR OBS DATA 

  filename = subp.split('/')[len(subp.split('/'))-1][:-1]

  print 'FILENAME IS ', filename,'  ', subp.split('/')[4]


  if var not in obs_dic.keys(): obs_dic[var] = {}

  product = subp.split('/')[4]

  if product not in obs_dic[var].keys(): obs_dic[var][product] = {}

  partial_filename = subp.split('pcmdi-metrics')[1]

  realm = partial_filename.split('_')[1]
  period = partial_filename.split('_')[3]
  period = period.split('-clim.nc')[0]

  obs_dic[var][product]['filename'] = filename 
  obs_dic[var][product]['CMIP_CMOR_TABLE'] = realm
  obs_dic[var][product]['period'] = period 
  obs_dic[var][product]['RefName'] = product
  obs_dic[var][product]['RefTrackingDate'] = time.ctime(os.path.getmtime(l.strip()))

  md5 = string.split(os.popen('md5sum ' + l[:-1]).readlines()[0],' ')[0]

  obs_dic[var][product]['MD5sum'] = md5 

  print var,' ', product,'  ', realm,' ', period

  f = cdms2.open(l[:-1])
  d = f(var)
  shape = d.shape
  f.close()

  shape = `d.shape`

  obs_dic[var][product]['shape'] = shape

### DONE WITH MONTHLY MEAN OBS
#### NOW TRAP OBS LAND-SEA MASKS IN OBS/FX/SFTLF 

lstm = os.popen('ls ' + data_path + '/fx/sftlf/*.nc').readlines()
sftlf_product_remap={
    "ECMWF-ERAInterim":"ERAINT",
    "ECMWF-ERA40" :"ERA40",
    "NCAR-JRA25" :"JRA25",
    }
for l in lstm:
  subp = l.split('obs')[1]
  var = subp.split('/')[2]

### TRAP FILE NAME FOR SFTLF DATA 

  filename = subp.split('/')[len(subp.split('/'))-1][:-1]
  print 'FILENAME IS ', filename,'  ', subp.split('/')[3]
  if var not in obs_dic.keys(): obs_dic[var] = {}
  partial_filename = subp.split('pcmdi-metrics')[1]
  product = partial_filename.split('/')[0]
  product = string.split(product,'_')[2] 
  # Ok sftlf filenames do not match official OBS product abbreviation
  #need to remap
  product = sftlf_product_remap.get(product,product) 

  if product not in obs_dic[var].keys(): obs_dic[var][product] = {}

  obs_dic[var][product]['CMIP_CMOR_TABLE'] = 'fx' 
  obs_dic[var][product]['filename'] = filename 
  md5 = string.split(os.popen('md5sum ' + l[:-1]).readlines()[0],' ')[0]
  obs_dic[var][product]['MD5sum'] = md5

  f = cdms2.open(l[:-1])
  d = f(var)
  obs_dic[var][product]['shape'] = `d.shape`
  f.close()

#### ADD SPECIAL CASE SFTLF FROM TEST DIR 

product = 'UKMETOFFICE-HadISST-v1-1' 
obs_dic[var][product] = {}
obs_dic[var][product]['CMIP_CMOR_TABLE'] = 'fx'
obs_dic[var][product]['shape'] = '(180, 360)'
obs_dic[var][product]['filename'] = 'sftlf_pcmdi-metrics_fx_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc'


json_name = 'obs_info_dictionary.json'

# SAVE LOCAL AND IN /doc
json.dump(obs_dic, open(json_name, "wb" ),sort_keys=True, indent=4, separators=(',', ': '))

json.dump(obs_dic, open('../../../../doc/' + json_name, "wb" ),sort_keys=True, indent=4, separators=(',', ': '))




