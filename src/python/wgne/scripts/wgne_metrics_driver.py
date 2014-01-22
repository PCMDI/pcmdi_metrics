#/usr/bin/env python
import metrics
import sys
import argparse
import os, json
from metrics.wgne.io import obs_dic


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

    if len(var.split("_"))>1:
        level = float(var.split("_")[-1])*100.
        var=var.split("_")[0]
    else:
        level=None

    if var in ['tos','sos','zos']: 
        regridMethod = parameters.regrid_method_ocn
        regridTool = parameters.regrid_tool_ocn
        table_realm = 'ocn.Omon'
        period="198001-200512"
    else:
        regridMethod = parameters.regrid_method
        regridTool= parameters.regrid_tool
        table_realm = 'atm.Amon'
        period="000001-000012"

    #Ok at that stage we need to loop thru obs
    print 'ref is:',parameters.ref
    if isinstance(parameters.ref,list):
        refs=parameters.ref
    elif isinstance(parameters.ref,str):
        #Is it "all"
        if parameters.ref.lower()=="all":
            refs = obs_dic[var].keys()
            print "Refs are:",refs
        else:
            refs=[parameters.ref,]

    OUT = metrics.io.base.Base(parameters.metrics_output_path+parameters.case_id,"%(var)%(level)_%(targetGridName)_%(regridTool)_%(regridMethod)_metrics")
    OUT.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
    OUT.var=var

    for ref in refs:
## PJG ADDED try/except/break  TO DEAL WITH ANY MISSING REF BOMBING
## AND, TRYING TO GET OBS PERIOD from obs_period_dic which is now in /export/gleckler1/git/wgne-wgcm_metrics/src/python/io/obs_period_dictionary.json
#       obs_period_dic = json.load(open('/export/gleckler1/git/wgne-wgcm_metrics/src/python/io/obs_period_dictionary.json','r+'))
#       obsname = obs_dic[var][ref]
#       obs_period = '198901-200911'  #obs_period_dic[var][obsname]
#       try:
        print 'table_realm is ', table_realm
#       OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/%(table_realm)/mo/",var,ref,period=period)
        if var not in ['tos','sos','zos']: OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/atm/mo",var,ref,period=period)
        if var in ['tos','sos','zos']: OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/ocn/mo",var,ref,period=period)
        OBS.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
        do = OBS.get(var)
        print 'OBS SHAPE IS ', do.shape
#       except:
#         break
### PJG ADDING LEVEL CONDITON FOR OBS JAN 21 2014
        try:
         if level is not None:
           do = OBS.get(var,varInFile=var,level=level)
        except:
           print 'failed with 4D OBS'
### END PJG EDIT 

        for model_version in parameters.model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
            success = True
            while success:

                MODEL = metrics.io.base.Base(parameters.mod_data_path+"/"+parameters.case_id,parameters.filename_template)
                MODEL.model_version = model_version
                MODEL.table_realm = table_realm
                MODEL.model_period = parameters.model_period  #"1980-1999"
                MODEL.ext="nc"
                MODEL.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
                MODEL.realization = parameters.realization
                try:
                   if level is None:
                     OUT.level=""
                     dm = MODEL.get(var,varInFile=var)  #+"_ac")
                   else:
                     OUT.level = "-%i" % (int(level/100.))
                     dm = MODEL.get(var,varInFile=var,level=level)
                except Exception,err:
                    success = False
                    print 'Failed to get variable %s for version: %s, error:\n%s' % ( var, model_version, err)
                    break

                print var,' ', model_version,' ', dm.shape,' ', do.shape,'  ', ref
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
                    CLIM.period = period
                    CLIM.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
                    CLIM.variable = var
                    CLIM.write(dm,type="nc",id="var")

                break               

    ## Done with obs and models loops , let's dum before next var
    ### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES
    OUT.write(metrics_dictionary, sort_keys=True, indent=4, separators=(',', ': '))    
    # CREATE OUTPUT AS ASCII FILE
    OUT.write(metrics_dictionary,type="txt") 
