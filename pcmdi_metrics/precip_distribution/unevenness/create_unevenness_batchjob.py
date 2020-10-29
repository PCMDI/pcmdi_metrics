import os
import glob
import datetime

ver = datetime.datetime.now().strftime('v%Y%m%d')

ver_in = 'v20200815'  # 'v20200526'  #'v20200522'   #'v20200511'  #'v20200428'
mip = 'cmip6'
exp = 'historical'  #'amip'

pin = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + ver_in + '/' + mip + '/' + exp + '/atmos/day/pr/*r1i1p1f1*.xml'

lst = glob.glob(pin) 

#cmd = 'nohup ./unevendays.py -p inparam_CMIP_computeStdOfDailyMeans.py --model '

## TEST ON SMALL DOMAIN DATA
cmd = 'nohup python driver_extrema_longrun_pentad.py -p daily_extremes_input_params.py --modpath /export/gleckler1/processing/metrics_package/my_test/mfw_extremes/cmip6.historical.GFDL-CM4.r1i1p1f1.mon.pr_smalldomain.nc --mod_name '

cmd = 'nohup python ./unevendays.py -p pr_unevenness_param.py --modpath /p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + ver_in + '/' + mip + '/' + exp + '/atmos/day/pr/cmip6.historical.MODEL.day.pr.xml --mod_name '


f= open(mip + '_' + exp + "_unevenness_jobs_" + ver + ".bash","w+")

for l in lst:
  mod = l.split('.' )[4] + '.' + l.split('.' )[5]

  cmd1 = cmd.replace('MODEL',mod) 
  cmd2 = cmd1 + ' ' +   mod + ' ' + ' > ' + mod + '.' + mip + '.' + exp + '.log &'
  print(cmd2)
  f.write(cmd2 + '\n')

f.close()

