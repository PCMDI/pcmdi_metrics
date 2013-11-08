import MV2 as MV
import cdms2 as cdms
from genutil import statistics
import cdutil
import metrics

def compute_metrics(var,dm_glb,do_glb):
  metrics_dictionary = {}

  domains = ['GLB','NHEX','TROPICS','SHEX']

  ### TEMPORARY UNITS CHANGE
  if var == 'tos': do_glb = do_glb + 273.13

  for dom in domains: 

    dm = dm_glb
    do = do_glb

    if dom == 'NHEX':
       dm = dm_glb(latitude = (30.,90))
       do = do_glb(latitude = (30.,90))
    if dom == 'SHEX':
       dm = dm_glb(latitude = (-90.,-30))
       do = do_glb(latitude = (-90.,-30))
    if dom == 'TROPICS':
       dm = dm_glb(latitude = (-30.,30))
       do = do_glb(latitude = (-30.,30))

    ### ANNUAL CYCLE SPACE-TIME RMS AND CORRELATION
    rms_xyt = metrics.wgne.rms_xyt.compute(dm,do)
    cor_xyt = metrics.wgne.cor_xyt.compute(dm,do)

    ### CALCUALTE ANNUAL MEANS OF DATA
    do_am, dm_am =  metrics.wgne.annual_mean.compute(dm,do)

  ### ANNUAL MEAN BIAS
    bias_am = metrics.wgne.bias.compute(dm_am,do_am)
    print var,'  ', 'annual mean bias is ' , bias_am

   ### MEAN ABSOLOUTE ERROR 
    mae_am = metrics.wgne.meanabs_xy.compute(dm_am,do_am)

    ### ANNUAL MEAN RMS
    rms_xy = metrics.wgne.rms_xy.compute(dm_am,do_am)

    conv = 1.
    if var == 'pr': conv = 1.e5

    for m in ['rms_xyt','rms_xy','bias_am','cor_xyt','mae_am']:
     if m == 'rms_xyt': metrics_dictionary[m + '_ann_' + dom] = format(rms_xyt*conv,'.2f') 
     if m == 'rms_xy': metrics_dictionary[m + '_ann_' + dom] =  format(rms_xy*conv,'.2f')
     if m == 'bias_am': metrics_dictionary[m + '_ann_' + dom] = format(bias_am*conv,'.2f')
     if m == 'mae_am': metrics_dictionary[m + '_ann_' + dom] = format(mae_am*conv,'.2f')
     if m == 'cor_xyt': metrics_dictionary[m + '_ann_' + dom] = format(cor_xyt,'.2f')

  #### SEASONAL MEANS ######

    for sea in ['djf','mam','jja','son']:

     dm_sea = metrics.wgne.seasonal_mean.compute(dm,sea)  
     do_sea = metrics.wgne.seasonal_mean.compute(do,sea)

   ### SEASONAL RMS AND CORRELATION
     rms_sea = metrics.wgne.rms_xy.compute(dm_sea,do_sea)
     cor_sea = metrics.wgne.cor_xy.compute(dm_sea,do_sea) 
     mae_sea = metrics.wgne.meanabs_xy.compute(dm_sea,do_sea)

     metrics_dictionary['rms_xy_' + sea + '_' + dom] = format(rms_sea*conv,'.2f') 
     metrics_dictionary['cor_xy_' + sea + '_' + dom] = format(cor_sea,'.2f')
     metrics_dictionary['mae_xy_' + sea + '_' + dom] = format(mae_sea*conv,'.2f')
 
  return metrics_dictionary 
