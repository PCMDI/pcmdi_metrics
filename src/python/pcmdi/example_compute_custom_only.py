import cdms2 as cdms
import pcmdi_metrics

def compute_MyCustomMetrics(var,dm_glb,do_glb):
    metrics_dictionary = {}
    
    print 'MyCustomMetric1_' +var+' = MyCustomResult1_'+var
    print 'MyCustomMetric2_' +var+' = MyCustomResult2_'+var
    metrics_dictionary['MyCustomMetric1_' +var] = 'MyCustomResult1_'+var
    metrics_dictionary['MyCustomMetric2_' +var] = 'MyCustomResult2_'+var
            
    return metrics_dictionary
