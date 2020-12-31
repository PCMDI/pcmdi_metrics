import glob, os
import datetime

var = 'tas'
verin = 'v20201226' 
pin = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + verin + '/cmip6/historical/atmos/mon/' + var + '/'

verout = datetime.datetime.now().strftime('v%Y%m%d')

lst = glob.glob(pin + '*r1i1p1f1*.xml')

pathout = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/' + verout + '/' + var + '/' 

try:
 os.mkdir('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/' + verout)
except:
 pass
try:
 os.mkdir('/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/cmip6/historical/' + verout + '/' + var)
except:
 pass

cmd0 = "python ./clim_calc_driver.py -p clim_calc_cmip_inparam.py --start 1981-01 --end 2005-12 --infile " 

for l in lst:
  print('nohup ' + cmd0 + l + " --outpath " + pathout + ' --var ' + var + ' &')
  
