import cdms2 as cdms
import MV2 as MV
import cdutil
from genutil import statistics
import string, os
import json   # A data-interchange format see http://www.json.org/

from misc import *
import sys
import argparse

P = argparse.ArgumentParser()
P.add_argument("--parameters",dest="param",default="input_parameters.py",help="input parameter file containing local settings")
P.add_argument("-t","--targetGrid",dest="tgrid",choices=["2.5x2.5",],default="2.5x2.5")
P.add_argument("-r","--regrid",dest="regrid",choices=["regrid2","linear"],default="regrid2")
P.add_argument("-o","--ocean-regrid",dest="oregrid",choices=["regrid2","linear"],default="linear")

args = P.parse_args(sys.argv[1:])

exec("import %s as parameters" % args.param)

######################################################
#
#  USER INPUT IS SET IN FILE "input_parameters.py"
#  Identified via --parameters key at startup
#
######################################################

for var in vars:   #### CALCULATE METRICS FOR ALL VARIABLES IN vars
 metrics_dictionary = {}
 ## REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID (ATM OR OCN GRID)

 if var in ['pr','tas','rlut']: 
     regridMethod = parameters.regrid_method
     regridTool= parameters.regridTool
 if var in ['tos','sos','zos']: 
     regridMethod = parameters.regrid_method_ocn
     regridTool = parameters.regrid_tool_ocn
 OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/%(realm)/mo/",var,parameters.ref)
 OBS.setTarget(parameters.targetGrid,regridTool,regridMethod)
 do = OBS.get(var)

 OUT = metric.io.base(parameters.metrics_output_path+parameters.test_case,"%(var)_%(targetGridName)_%(regridTool)_%(regridMethod)_metrics")
 OUT.setTarget(parameters.targetGrid,regridTool,regridMethod)

 for model_version in model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
  success = True
  while success:
    metrics_dictionary[model_version] = {}

    MODEL = metrics.io.base.Base(parameters.mod_data_path,parameters.filename_template)
    MODEL.model_version = model_version
    MODEL.setTarget(parameters.targetGrid,regridTool,regridMethod)
    try:
       dm = MODEL.get(var)
    except:
        success = False
        print 'Failed to get variable %s for version: %s' % ( var, model_version)
        break
    try:
#      dm = get_our_model_clim(data_location + filename,var)  ## INHOUSE
      dm = get_cmip5_model_clim(data_location, model_version,var)   ## CMIP5
    except:
      success = False
      print 'Failed to read model results for ', var, ' ', model_version 
      break

    print var,' ', model_version,' ', dm.shape,' ', do.shape
###########################################################################
#### METRICS CALCULATIONS
    metrics_dictionary[model_version] = metrics.wgne.compute_metrics(var,dm,do)
###########################################################################

### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES

# CREATE OUTPUT AS JSON FILE

    OUT.write(metrics_dictionary, sort_keys=True, indent=4, separators=(',', ': '))    

# CREATE OUTPUT AS ASCII FILE
    OUT.write(metrics_dictionary,type="txt") 


# OUTPUT INTERPOLATED MODEL CLIMATOLOGIES

    if save_mod_clims: 
        CLIM= metrics.io.base.Base(parameters.model_clims_interpolated_output+"/"+parameters.case_id,parameters.filename_template)
        CLIM.write(dm,type="nc",id="var")
    break


