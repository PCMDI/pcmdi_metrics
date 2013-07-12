import MV2 as MV
import cdms2 as cdms
from genutil import statistics
import cdutil

def compute_metrics(var,dm,do):
  metrics_dictionary = {}


### TEMPORARY UNITS CHANGE
  if var == 'tos': do = do + 273.13

### ANNUAL CYCLE SPACE-TIME RMS
  rms_xyt = MV.float(statistics.rms(dm,do,axis='012',weights='weighted'))
  cor_xyt = MV.float(statistics.correlation(dm,do,axis='012',weights='weighted'))

### CALCUALTE ANNUAL MEANS OF DATA
  cdms.setAutoBounds('on')  ####  NEED TO HARDWIRE TIME WEIGHTS 
  do_am = cdutil.averager(do,axis='t')
  dm_am = cdutil.averager(dm,axis='t')

### ANNUAL MEAN BIAS
  bias_am = dm_am - do_am

### ANNUAL MEAN RMS
  rms_xy = MV.float(statistics.rms(dm_am,do_am,axis='01',weights='weighted'))

  conv = 1.
  if var == 'pr': conv = 1.e5

  metrics_list = ['rms_xyt','rms_xy','bias_am','cor_xyt']
  for m in metrics_list:
   if m == 'rms_xyt': metrics_dictionary[m] = format(rms_xyt*conv,'.2f') 
   if m == 'rms_xy': metrics_dictionary[m] =  format(rms_xy*conv,'.2f')
   if m == 'bias_am': metrics_dictionary[m] = format(bias_am*conv,'.2f')
   if m == 'cor_xyt': metrics_dictionary[m] = format(cor_xyt*conv,'.2f')
 
  return metrics_dictionary 
