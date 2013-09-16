#/usr/bin/env python
import metrics
import sys
import argparse
import os

P = argparse.ArgumentParser()
P.add_argument("-p","--parameters",dest="param",default="input_parameters.py",help="input parameter file containing local settings",required=True)
#P.add_argument("-t","--targetGrid",dest="tgrid",choices=["2.5x2.5",],default="2.5x2.5")
#P.add_argument("-r","--regrid",dest="regrid",choices=["regrid2","linear"],default="regrid2")
#P.add_argument("-o","--ocean-regrid",dest="oregrid",choices=["regrid2","linear"],default="linear")

args = P.parse_args(sys.argv[1:])


pth,fnm = os.path.split(args.param)
if pth!="":
    sys.path.append(pth)
if fnm.lower()[-3:]==".py":
    fnm = fnm[:-3]
exec("import %s as parameters" % fnm)
if pth!="":
    sys.path.pop(-1)

######################################################
#
#  USER INPUT IS SET IN FILE "input_parameters.py"
#  Identified via --parameters key at startup
#
######################################################

for var in parameters.vars:   #### CALCULATE METRICS FOR ALL VARIABLES IN vars
 metrics_dictionary = {}
 ## REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID (ATM OR OCN GRID)

 if var in ['pr','tas','rlut']: 
     regridMethod = parameters.regrid_method
     regridTool= parameters.regrid_tool
     table_realm = 'atm.Amon'
     period="000001-000012"
 if var in ['tos','sos','zos']: 
     regridMethod = parameters.regrid_method_ocn
     regridTool = parameters.regrid_tool_ocn
     table_realm = 'ocn.Omon'
     period="198001-200512"
 OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/%(realm)/mo/",var,parameters.ref,period=period)
 OBS.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
 do = OBS.get(var)

 OUT = metrics.io.base.Base(parameters.metrics_output_path+parameters.case_id,"%(var)_%(targetGridName)_%(regridTool)_%(regridMethod)_metrics")
 OUT.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
 OUT.var=var


 for model_version in parameters.model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
  success = True
  while success:
    metrics_dictionary[model_version] = {}

    MODEL = metrics.io.base.Base(parameters.mod_data_path+"/"+parameters.case_id,parameters.filename_template)
    MODEL.model_version = model_version
    MODEL.table_realm = table_realm
    MODEL.period = "1980-1999"
    MODEL.ext="nc"
    MODEL.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
    try:
       dm = MODEL.get(var,varInFile=var+"_ac")
    except Exception,err:
        success = False
        print 'Failed to get variable %s for version: %s, error:\n%s' % ( var, model_version, err)
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

    if parameters.save_mod_clims: 
        CLIM= metrics.io.base.Base(parameters.model_clims_interpolated_output+"/"+parameters.case_id,parameters.filename_output_template)
	CLIM.model_version = model_version
	CLIM.table_realm = table_realm
	CLIM.period = period
        CLIM.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
        CLIM.variable = var
        CLIM.write(dm,type="nc",id="var")
    break


