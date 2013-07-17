import cdms2 as cdms
import MV2 as MV
import cdutil
from genutil import statistics
import string, os
import json   # A data-interchange format see http://www.json.org/

from misc import *
from mean_climate_metrics_calculations import *
from input_parameters import *
#from input_model_data import *   # USE FOR INHOUSE VERSIONS
from input_cmip5_model_data import *  # USED ONLY BY PCMDI, FOR CALCULATING/ARCHIVING ALL CMIP5 RESULTS
import sys

######################################################
#
#  USER INPUT IS SET IN FILE "input_parameters.py"
#
######################################################

for var in vars:   #### CALCULATE METRICS FOR ALL VARIABLES IN vars
 metrics_dictionary = {}

 for model_version in model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
  success = True
  while success == True:
    metrics_dictionary[model_version] = {}

###############################
#  TRY CREATING DIRECTORY FOR "test_case" (EXCEPT IF IT ALREADY EXISTS)
    mkdir_fcn(metrics_output_path + 'metrics_results/' + test_case)

###############################
#  GET MODEL DATA
    try:
      data_location, filename = model_output_structure(model_version,var)
    except:
      success = False
      print 'Failed to consturct model path ', var, ' ', model_version
      break
    try:
#      dm = get_our_model_clim(data_location + filename,var)  ## INHOUSE
      dm = get_cmip5_model_clim(data_location, model_version,var)   ## CMIP5
    except:
      success = False
      print 'Failed to read model results for ', var, ' ', model_version 
      break
################################################ 
## GET OBSERVATIONS
    do = get_obs(var,ref,obs_data_path)

## GET TARGET GRID STRUCTURE
    target_grid = get_target_grid(targetGrid,obs_data_path)

## REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID (ATM OR OCN GRID)

    if var in ['pr','tas','rlut']: regrid_method = regrid_method
    if var in ['tos','sos','zos']: regrid_method = regrid_method_ocn

    do= do.regrid(target_grid,regridTool='esmf',regridMethod=regrid_method_ocn, coordSys='deg', diag = {},periodicity=1)
    dm= dm.regrid(target_grid,regridTool='esmf',regridMethod=regrid_method_ocn, coordSys='deg', diag = {},periodicity=1)

    print var,' ', model_version,' ', dm.shape,' ', do.shape
###########################################################################
#### METRICS CALCULATIONS
    metrics_dictionary[model_version] = compute_metrics(var,dm,do)
###########################################################################

### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES

# CREATE OUTPUT AS JSON FILE

    mkdir_fcn(metrics_output_path +  test_case)

    outfile_json = open(metrics_output_path +  test_case + '/' + var + '_' + targetGrid + '_' + regrid_method + '_metrics.json', 'w')
    json.dump(metrics_dictionary,outfile_json, sort_keys=True, indent=4, separators=(',', ': '))    
    outfile_json.close()

# CREATE OUTPUT AS ASCII FILE
    outfile_ascii = open(metrics_output_path +  test_case + '/' + var + '_' + targetGrid + '_' + regrid_method + '_metrics.txt', 'w')

    for model_version in metrics_dictionary.keys():
      outfile_ascii.writelines(model_version + '   ' + `metrics_dictionary[model_version]` + '\n')
    outfile_ascii.close()

# OUTPUT INTERPOLATED MODEL CLIMATOLOGIES

    if save_mod_clims == 'y': output_interpolated_model_data(dm, var, targetGrid,regrid_method,interpolated_model_output_path+filename) 

    break


