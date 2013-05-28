import cdms2 as cdms
import MV2 as MV
import cdutil
from genutil import statistics
import string, os
import pickle   ## WORKING TOWARD REPLACING PICKLE WITH JSON
import json

from misc import *

################################
## OPTIONS

experiment = 'samplerun'
targetGrid = '2.5x2.5'
vars = ['pr','rlut']
ref = 'ref1'  #  option is 'alternate' obs dataset

###############################

# CREATE OUTPUT AS JSON FILE
outfile = open('../../data/metrics_results/inhouse/' + experiment + '_metrics.txt', 'w') 

metrics_dictionary = {}
metrics_dictionary[experiment] = {}

for var in vars:

  d = get_our_model_clim(experiment,var,targetGrid)  
  
  do = get_obs(var,ref,targetGrid)

  print var,' ', d.shape,' ', do.shape

### ANNUAL CYCLE SPACE-TIME RMS 
  rms = MV.float(statistics.rms(d,do,axis='012',weights='weighted'))
  print var,' ', `rms`

### ADD METRICS RESULTS TO DICTIONARY
  metrics_dictionary[experiment][var]= rms

### OUTPUT DICTIONARY
 
json.dump(metrics_dictionary,outfile, sort_keys=True, indent=4, separators=(',', ': '))    
outfile.close()

