import datetime
import os
import string

ver = datetime.datetime.now().strftime('v%Y%m%d')

mip = 'cmip6'
exp = 'historical'

#mod_name = 'GFDL-CM4.r1i1p1f1' 
mod_name = 'GPCP-1-3'

realization = 'test'

#modpath = '/export/gleckler1/processing/metrics_package/my_test/mfw_extremes/cmip6.historical.GFDL-CM4.r1i1p1f1.mon.pr_smalldomain.nc'

#modpath = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/FROGS_precip/CMORPH_v1.0_CRT/'

modpath = '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/day/pr/GPCP-1-3/gn/v20200924/pr_day_GPCP-1-3_BE_gn_v20200924_19961002-20170101.nc'

#modpath = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/v20200919/cmip6/historical/atmos/day/pr/cmip6.historical.GFDL-CM4.r1i1p1f1.day.pr.xml'

start_year = '1996'   #'1988'
end_year = '2011'


results_dir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/pr/unevenness/' + mip + '/' + exp + '/'

try:
 os.mkdir(results_dir + '/' + ver) 
except:
 pass

results_dir = results_dir  + '/' + ver 
