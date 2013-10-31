import MV2 as MV
import cdms2 as cdms
from genutil import statistics
import cdutil
import metrics

def compute_metrics(var,dm,do):
  metrics_dictionary = {}


  ### TEMPORARY UNITS CHANGE
  if var == 'tos': do = do + 273.13

  ### ANNUAL CYCLE SPACE-TIME RMS
  rms_xyt = metrics.wgne.rms_xyt.compute(dm,do)
  cor_xyt = metrics.wgne.cor_xyt.compute(dm,do)

  ### CALCUALTE ANNUAL MEANS OF DATA
  do_am, dm_am =  metrics.wgne.annual_mean.compute(dm,do)

  ### ANNUAL MEAN BIAS
  bias_am = metrics.wgne.bias.compute(dm_am,do_am) 
  print 'BIAS IS ' , bias_am, type(bias_am), type(cor_xyt)

  ### ANNUAL MEAN RMS
  rms_xy = metrics.wgne.rms_xy.compute(dm_am,do_am)

  conv = 1.
  if var == 'pr': conv = 1.e5

  for m in ['rms_xyt','rms_xy','bias_am','cor_xyt']:
   if m == 'rms_xyt': metrics_dictionary[m] = format(rms_xyt*conv,'.2f') 
   if m == 'rms_xy': metrics_dictionary[m] =  format(rms_xy*conv,'.2f')
   if m == 'bias_am': metrics_dictionary[m] = format(bias_am*conv,'.2f')
   if m == 'cor_xyt': metrics_dictionary[m] = format(cor_xyt,'.2f')

#### SEASONAL MEANS ######

  djf_ind = [11,0,1]
  mam_ind = [2,3,4]
  jja_ind = [5,6,7]
  son_ind = [8,9,10]
  mo_wts = [31,31,28.25,31,30,31,30,31,31,30,31,30]

  for sea in ['djf','mam','jja','son']:
#  if sea == 'djf': indx = [11,0,1]
#  if sea == 'mam': indx = [2,3,4]
#  if sea == 'jja': indx = [5,6,7]
#  if sea == 'son': indx = [8,9,10]
#  sea_no_days = mo_wts[indx[0]] + mo_wts[indx[1]] + mo_wts[indx[2]]
#  dm_sea = (dm[indx[0]]*mo_wts[indx[0]] + dm[indx[1]]*mo_wts[indx[1]] + dm[indx[2]]*mo_wts[indx[2]])/sea_no_days
#  do_sea = (do[indx[0]]*mo_wts[indx[0]] + do[indx[1]]*mo_wts[indx[1]] + do[indx[2]]*mo_wts[indx[2]])/sea_no_days

   dm_sea = metrics.wgne.seasonal_mean.compute(dm,sea)  
   do_sea = metrics.wgne.seasonal_mean.compute(do,sea)

 ### SEASONAL RMS AND CORRELATION
   rms_sea = metrics.wgne.rms_xy.compute(dm_sea,do_sea)
   cor_sea = metrics.wgne.cor_xy.compute(dm_sea,do_sea) 

   metrics_dictionary['rms_xy_' + sea] = format(rms_sea*conv,'.2f') 
   metrics_dictionary['cor_xy_' + sea] = format(cor_sea,'.2f')
 
  return metrics_dictionary 
