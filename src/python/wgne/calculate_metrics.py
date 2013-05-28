import cdms2 as cdms
import MV2 as MV
import cdutil
from genutil import statistics
import string, os
import json   # A data-interchange format see http://www.json.org/

from misc import *
execfile('../io/getOurModelData.py')

################################
## OPTIONS

experiments = ['samplerun']
outdir = '/work/gleckler1/processed_data/'
targetGrid = '2.5x2.5'
regridMethod = 'bilinear'
vars = ['pr','rlut']
ref = 'ref1'  #  option is 'alternate' obs dataset


for exp in experiments:

###############################
#  TRY CREATING DIRECTORY FOR EXPERIMENT ("EXCEPT" IF IT ALREADY EXISTS)
 try:
  os.mkdir(outdir + experiment)
 except:
  pass

# CREATE OUTPUT AS JSON FILE

#outfile = open('../../data/metrics_results/inhouse/' + experiment + '_metrics.txt', 'w') 

 metrics_dictionary = {}
 metrics_dictionary[exp] = {}

 for var in vars:
################################################
################################################
#  d = get_our_model_clim(experiment,var) # CHARLES WORKING ON THIS
#  TEST DATA 
  pd = '/work/gleckler1/processed_data/cmip5clims/' + var + '/' + 'cmip5.HadCM3.historical.r1i1p1.mo.atm.Amon.' + var + '.ver-1.1980-1999.AC.nc' 
  f = cdms.open(pd)
  d = f(var + '_ac')
################################################
################################################ 
  
  do = get_obs(var,ref,outdir,targetGrid)

  print var,' ', d.shape,' ', do.shape


#### METRICS CALCULATIONS
### ANNUAL CYCLE SPACE-TIME RMS 
  rms = MV.float(statistics.rms(d,do,axis='012',weights='weighted'))
  print var,' ', `rms`

#### END METRICS CALCUATIONS

### ADD METRICS RESULTS TO DICTIONARY
  metrics_dictionary[experiment][var]= rms

### OUTPUT DICTIONARY

# CREATE OUTPUT AS JSON FILE
  outfile = open(outdir + '/' + experiment + '/' + var + '_metrics.txt', 'w')
 
  json.dump(metrics_dictionary,outfile, sort_keys=True, indent=4, separators=(',', ': '))    
  outfile.close()

