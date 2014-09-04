import cdms2 as cdms
import pcmdi_metrics
#import cdutil
#import MV2 as MV
#from genutil import statistics

def compute_metrics(var,dm_glb,do_glb):

  cdms.setAutoBounds('on')

  metrics_dictionary = {}

  domains = ['GLB','NHEX','TROPICS','SHEX']

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
    print '---- shapes ', dm.shape,' ', do.shape
    rms_xyt = pcmdi_metrics.pcmdi.rms_xyt.compute(dm,do)
    cor_xyt = pcmdi_metrics.pcmdi.cor_xyt.compute(dm,do)

    ### CALCUALTE ANNUAL MEANS OF DATA
    do_am, dm_am =  pcmdi_metrics.pcmdi.annual_mean.compute(dm,do)

  ### ANNUAL MEAN BIAS
    bias_xy = pcmdi_metrics.pcmdi.bias.compute(dm_am,do_am)
    print var,'  ', 'annual mean bias is ' , bias_xy

   ### MEAN ABSOLOUTE ERROR 
    mae_xy = pcmdi_metrics.pcmdi.meanabs_xy.compute(dm_am,do_am)

    ### ANNUAL MEAN RMS
    rms_xy = pcmdi_metrics.pcmdi.rms_xy.compute(dm_am,do_am)

    conv = 1.
    if var == 'pr': conv = 1.e5

    sig_digits = '.2f'
    if var in ['hus']: sig_digits = '.5f'

    for m in ['rms_xyt','rms_xy','bias_xy','cor_xyt','mae_am']:
     if m == 'rms_xyt': metrics_dictionary[m + '_ann_' + dom] = format(rms_xyt*conv,sig_digits) 
     if m == 'rms_xy': metrics_dictionary[m + '_ann_' + dom] =  format(rms_xy*conv,sig_digits)
     if m == 'bias_xy': metrics_dictionary[m + '_ann_' + dom] = format(bias_xy*conv,sig_digits)
     if m == 'mae_xy': metrics_dictionary[m + '_ann_' + dom] = format(mae_xy*conv,sig_digits)
     if m == 'cor_xyt': metrics_dictionary[m + '_ann_' + dom] = format(cor_xyt,'.2f')

  #### SEASONAL MEANS ######

    for sea in ['djf','mam','jja','son']:

     dm_sea = pcmdi_metrics.pcmdi.seasonal_mean.compute(dm,sea)  
     do_sea = pcmdi_metrics.pcmdi.seasonal_mean.compute(do,sea)

   ### SEASONAL RMS AND CORRELATION
     rms_sea = pcmdi_metrics.pcmdi.rms_xy.compute(dm_sea,do_sea)
     cor_sea = pcmdi_metrics.pcmdi.cor_xy.compute(dm_sea,do_sea) 
     mae_sea = pcmdi_metrics.pcmdi.meanabs_xy.compute(dm_sea,do_sea)
     bias_sea = pcmdi_metrics.pcmdi.bias.compute(dm_sea,do_sea)

     metrics_dictionary['bias_xy_' + sea + '_' + dom] = format(bias_sea*conv,sig_digits)
     metrics_dictionary['rms_xy_' + sea + '_' + dom] = format(rms_sea*conv,sig_digits) 
     metrics_dictionary['cor_xy_' + sea + '_' + dom] = format(cor_sea,'.2f')
     metrics_dictionary['mae_xy_' + sea + '_' + dom] = format(mae_sea*conv,sig_digits)
 
  return metrics_dictionary 
