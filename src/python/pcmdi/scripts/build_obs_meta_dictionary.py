#!python
import cdms2
import json, os, sys
if len(sys.argv)>1:
    data_path = sys.argv[1]
else:
    data_path = '/work/gleckler1/processed_data/metrics_package/obs'


lst = os.popen('ls ' + data_path + '/*/mo/*/*/ac/*.nc').readlines()

obs_dic = {'rlut':{'default':'CERES','alternate':'ERBE'},
           'rsut':{'default':'CERES','alternate':'ERBE'},
           'rsds':{'default':'CERES','alternate':'ERBE'},
           'rlus':{'default':'CERES','alternate':'ERBE'},
           'rsus':{'default':'CERES','alternate':'ERBE'},
           'rlutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcre':{'default':'CERES','alternate':'ERBE'},
           'rlutcre':{'default':'CERES','alternate':'ERBE'},
           'pr':{'default':'GPCP','alternate':'TRMM'},
           'prw':{'default':'RSS'},
           'tas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'psl':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ua':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'va':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'uas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'hus':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'vas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ta':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'zg':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'tauu':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'tauv':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'tos':{'default':'UKMETOFFICE-HadISST-v1-1'},
           'zos':{'default':'CNES-AVISO-L4'},
           'sos':{'default':'NODC-WOA09'},
            }



for l in lst:
  subp = l.split('obs')[1]
# print subp

  var = subp.split('/')[3]

  if var not in obs_dic.keys(): obs_dic[var] = {}

  product = subp.split('/')[4]

  if product not in obs_dic[var].keys(): obs_dic[var][product] = {}

  partial_filename = subp.split('pcmdi-metrics')[1]

  realm = partial_filename.split('_')[1]
  period = partial_filename.split('_')[3]
  period = period.split('-clim.nc')[0]

  obs_dic[var][product]['CMIP_CMOR_TABLE'] = realm
  obs_dic[var][product]['period'] = period 
  obs_dic[var][product]['RefActivity'] = "obs4mips"
  obs_dic[var][product]['RefName'] = product
  obs_dic[var][product]['RefType'] = "???"
  obs_dic[var][product]['RefTrackingDate'] = time.ctime(os.path.getmtime(l.strip())
  obs_dic[var][product]['RefFreeSpace'] = "???"


  print var,' ', product,'  ', realm,' ', period

  f = cdms2.open(l[:-1])
  d = f(var)
  shape = d.shape
  f.close()

  shape = `d.shape`

  obs_dic[var][product]['shape'] = shape

json_name = 'obs_info_dictionary.json'

json.dump(obs_dic, open(json_name, "wb" ),sort_keys=True, indent=4, separators=(',', ': '))


 

