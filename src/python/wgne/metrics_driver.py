import cdms2 as cdms
import MV2 as MV
import cdutil
from genutil import statistics
import string, os
import json   # A data-interchange format see http://www.json.org/

from misc import *
from metrics_calculations import *
execfile('../io/getOurModelData.py')   # CHARLES TO CHANGE THIS

#################################################################################
################################################################################
## OPTIONS SET BY USER
################################################################################
### DATA LOCATION AND MODEL-VERSIONS TO BE TESTED
datapath = '/work/gleckler1/processed_data/metrics_package/'  # PATH FOR OUTPUT OF METRICS RESULTS
model_versions = ['samplerun1','samplerun2']   # DIFFERENT MODEL VERSIONS CAN BE INCLUDED HERE
test_case = 'sampletest'   # DEFINES A SUBDIRECTORY TO OUTPUT RESULTS SO DIFFERENT CASES CAN BE ARCHIVED

### VARIABLES AND OBSERVATIONS
vars = ['pr','rlut','rsut','tas']
ref = 'default'  #  option is 'alternate' obs dataset

### INTERPOLATION
targetGrid = '2.5x2.5'   # OPTIONS: '2.5x2.5'
regrid_method = 'regrid2'   # OPTIONS: 'bilinear'
regrid_method_ocn = 'linear'   # OPTIONS: 'bilinear'
#################################################################################
### END OPTIONS SET BY USER
#################################################################################

for var in vars:
 metrics_dictionary = {}

 for model_version in model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS
  metrics_dictionary[model_version] = {}
###############################
#  TRY CREATING DIRECTORY FOR "test_case" (EXCEPT IF IT ALREADY EXISTS)
  try:
   os.mkdir(datapath + 'metrics_results/' + test_case)
  except:
   pass
###############################
#  GET MODEL DATA
  dm = get_our_model_clim(model_version,var) # CHARLES WORKING ON THIS

################################################ 
## GET OBSERVATIONS
  do = get_obs(var,ref,datapath)

## GET TARGET GRID STRUCTURE
  target_grid = get_target_grid(targetGrid,datapath)

## REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID
# do = do.regrid(target_grid,regridTool=regrid_method)
# dm = dm.regrid(target_grid,regridTool=regrid_method)

  diag = {}
  do= do.regrid(target_grid,regridTool='esmf',regridMethod=regrid_method_ocn, coordSys='deg', diag = diag,periodicity=1)
  dm= dm.regrid(target_grid,regridTool='esmf',regridMethod=regrid_method_ocn, coordSys='deg', diag = diag,periodicity=1)

  print var,' ', dm.shape,' ', do.shape
###########################################################################
#### METRICS CALCULATIONS
  metrics_dictionary[model_version] = compute_metrics(var,dm,do)
###########################################################################

### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES

# CREATE OUTPUT AS JSON FILE
  outfile_json = open(datapath + '/metrics_results/' + test_case + '/' + var + '_metrics.json', 'w')
  json.dump(metrics_dictionary,outfile_json, sort_keys=True, indent=4, separators=(',', ': '))    
  outfile_json.close()

# CREATE OUTPUT AS ASCII FILE
  outfile_ascii = open(datapath + '/metrics_results/' + test_case + '/' + var + '_metrics.txt', 'w')

  for model_version in metrics_dictionary.keys():
    outfile_ascii.writelines(model_version + '   ' + `metrics_dictionary[model_version]` + '\n')
  outfile_ascii.close()



