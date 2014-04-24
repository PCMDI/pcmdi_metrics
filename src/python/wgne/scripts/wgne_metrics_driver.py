#!/usr/bin/env python
######################################################
#
#  USER INPUT IS SET IN FILE "input_parameters.py"
#  Identified via --parameters key at startup
#
######################################################
import metrics
import sys
import argparse
import os, json
import genutil
import warnings

#Load the obs dictionary
obs_dic = json.loads(open(os.path.join(sys.prefix,"share","wgne","obs_info_dictionary.json")).read())

class DUP(object):
    def __init__(self,outfile):
        self.outfile = outfile
    def __call__(self,*args):
        msg = ""
        for a in args:
            msg+=" "+str(a)
        print msg
        print>>self.outfile, msg

def applyCustomKeys(O,custom_dict,var):
  for k,v in custom_dict.iteritems():
    setattr(O,k,custom_dict.get(var,custom_dict.get("all","")))

P = argparse.ArgumentParser()
P.add_argument("-p","--parameters",dest="param",default="input_parameters.py",help="input parameter file containing local settings",required=True)

args = P.parse_args(sys.argv[1:])

pth,fnm = os.path.split(args.param)
if pth!="":
    sys.path.append(pth)
if fnm.lower()[-3:]==".py":
    fnm = fnm[:-3]
    ext=".py"
else:
    ext=""
## We need to make sure there is no "dot" in filename or import will fail
if fnm.find(".")>-1:
  raise ValueError, "Sorry input parameter file name CANNOT contain 'dots' (.), please rename it (e.g: %s%s)" % (fnm.replace(".","_"),ext)
exec("import %s as parameters" % fnm)
if pth!="":
    sys.path.pop(-1)

#Checking if user has custom_keys
if not hasattr(parameters,"custom_keys"):
  parameters.custom_keys={}

try:
  os.makedirs(parameters.metrics_output_path+parameters.case_id)
except:
  pass

Efile = open(os.path.join(parameters.metrics_output_path,parameters.case_id,"errors_log.txt"),"w")
dup=DUP(Efile)

for var in parameters.vars:   #### CALCULATE METRICS FOR ALL VARIABLES IN vars
    metrics_dictionary = {}
    ## REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID (ATM OR OCN GRID)

    if len(var.split("_"))>1:
        level = float(var.split("_")[-1])*100.
        var=var.split("_")[0]
    else:
        level=None

    if obs_dic[var][obs_dic[var]["default"]]["CMIP_CMOR_TABLE"]=="Omon":
        regridMethod = parameters.regrid_method_ocn
        regridTool = parameters.regrid_tool_ocn
        table_realm = 'Omon'
        realm = "ocn"
    else:
        regridMethod = parameters.regrid_method
        regridTool= parameters.regrid_tool
        table_realm = 'Amon'
        realm = "atm"

    #Ok at that stage we need to loop thru obs
    dup('ref is: ',parameters.ref)
    if isinstance(parameters.ref,list):
        refs=parameters.ref
    elif isinstance(parameters.ref,(unicode,str)):
        #Is it "all"
        if parameters.ref.lower()=="all":
            Refs = obs_dic[var].keys()
            refs=[]
            for r in Refs:
                if isinstance(obs_dic[var][r],(unicode,str)):
                    refs.append(r)
            dup( "refs:",refs)
        else:
            refs=[parameters.ref,]

    OUT = metrics.io.base.Base(parameters.metrics_output_path+parameters.case_id,"%(var)%(level)_%(targetGridName)_%(regridTool)_%(regridMethod)_metrics")
    OUT.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
    OUT.var=var
    OUT.realm = realm
    OUT.table = table_realm
    applyCustomKeys(OUT,parameters.custom_keys,var)

    for ref in refs:
      try:
        if obs_dic[var][obs_dic[var][ref]]["CMIP_CMOR_TABLE"]=="Omon":
            OBS = metrics.wgne.io.OBS(parameters.obs_data_path,var,obs_dic,ref)
        else:
            OBS = metrics.wgne.io.OBS(parameters.obs_data_path,var,obs_dic,ref)
        OBS.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
        OBS.realm = realm
        OBS.table = table_realm
        applyCustomKeys(OBS,parameters.custom_keys,var)
        try:
         if level is not None:
           do = OBS.get(var,level=level)
         else:
           do = OBS.get(var)
        except Exception,err:
           dup('failed with 4D OBS',var,ref,err)
           continue
        dup('OBS SHAPE IS ', do.shape)

        for model_version in parameters.model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
            success = True
            while success:

                MODEL = metrics.io.base.Base(parameters.mod_data_path,parameters.filename_template)
                MODEL.model_version = model_version
                MODEL.table = table_realm
                MODEL.realm = realm
                MODEL.model_period = parameters.model_period  
                MODEL.ext="nc"
                MODEL.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
                MODEL.realization = parameters.realization
                applyCustomKeys(MODEL,parameters.custom_keys,var)
                try:
                   if level is None:
                     OUT.level=""
                     dm = MODEL.get(var,varInFile=var)  #+"_ac")
                   else:
                     OUT.level = "-%i" % (int(level/100.))
                     dm = MODEL.get(var,varInFile=var,level=level)
                except Exception,err:
                    success = False
                    dup('Failed to get variable %s for version: %s, error:\n%s' % ( var, model_version, err))
                    break

                dup(var,' ', model_version,' ', dm.shape,' ', do.shape,'  ', ref)

                ###########################################################################
                #### Basic checks
                ###########################################################################
                if dm.shape!=do.shape:
                  raise RuntimeError, "Obs and Model -%s- have different shapes %s vs %s" % (model_version,do.shape,dm.shape)
                if do.units!=dm.units: # Ok possible issue with units
                    u = genutil.udunits(1,dm.units)
                    try:
                      scaling,offset = u.how(do.units)
                      dm = dm*scaling + offset
                      warnings.warn("Model and observation units differed, converted model (%s) to observation unit (%s)" % (dm.units,do.units))
                    except:
                      raise RuntimeError, "Could not convert model units (%s) to obs units: (%s)" % (dm.units,do.units)

                ###########################################################################
                #### METRICS CALCULATIONS
                onm = obs_dic[var][ref]
                metrics_dictionary[model_version] = metrics_dictionary.get(model_version,{})
                metrics_dictionary[model_version][ref] = {'source':onm}
                metrics_dictionary[model_version][ref][parameters.realization] = metrics.wgne.compute_metrics(var,dm,do)
                ###########################################################################
           
                # OUTPUT INTERPOLATED MODEL CLIMATOLOGIES
                # Only the first time thru an obs set (always the same after)
                if parameters.save_mod_clims and ref==refs[0]: 
                    CLIM= metrics.io.base.Base(parameters.model_clims_interpolated_output+"/"+parameters.case_id,parameters.filename_output_template)
                    CLIM.level=OUT.level
                    CLIM.model_version = model_version
                    CLIM.table_realm = table_realm
                    CLIM.period = parameters.model_period
                    CLIM.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
                    CLIM.variable = var
                    applyCustomKeys(CLIM,parameters.custom_keys,var)
                    CLIM.write(dm,type="nc",id="var")

                break               
      except Exception,err:
        dup("Error while processing observation %s for variable %s:\n\t%s" % (var,ref,err))
    ## Done with obs and models loops , let's dum before next var
    ### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES
    OUT.write(metrics_dictionary, sort_keys=True, indent=4, separators=(',', ': '))    
    # CREATE OUTPUT AS ASCII FILE
    OUT.write(metrics_dictionary,type="txt") 
