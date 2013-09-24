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

### CALCULATION OF SEASONAL MEANS 

# print 'djf wts', djf_wts, dm.shape, type(djf_wts)
  do_djf,dm_djf = metrics.wgne.seasonal_mean.compute(do,dm,'djf')  

  bias_djf = metrics.wgne.bias.compute(do_djf,dm_djf)
  print 'djf test', do_djf.shape,' ', dm_djf.shape 

##########################################

  dm_djf = dm

##########################################

  ### CALCUALTE ANNUAL MEANS OF DATA
  do_am, dm_am =  metrics.wgne.annual_mean.compute(dm,do)
  ### ANNUAL MEAN BIAS
  bias_am = metrics.wgne.bias.compute(dm_am,do_am) 
  print 'BIAS IS ' , bias_am, type(bias_am), type(cor_xyt)

  ### ANNUAL MEAN RMS
  rms_xy = metrics.wgne.rms_xy.compute(dm_am,do_am)

  conv = 1.
  if var == 'pr': conv = 1.e5

  for m in ['rms_xyt','rms_xy','bias_am','bias_djf','cor_xyt']:
   if m == 'rms_xyt': metrics_dictionary[m] = format(rms_xyt*conv,'.2f') 
   if m == 'rms_xy': metrics_dictionary[m] =  format(rms_xy*conv,'.2f')
   if m == 'bias_am': metrics_dictionary[m] = format(bias_am*conv,'.2f')
   if m == 'bias_djf': metrics_dictionary[m] = format(bias_djf*conv,'.2f')
   if m == 'cor_xyt': metrics_dictionary[m] = format(cor_xyt,'.2f')
   
 
  return metrics_dictionary 
