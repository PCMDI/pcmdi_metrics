#/usr/bin/env python
import metrics
import sys
import argparse
import os, json

#Load the obs dictionary
obs_dic = json.loads(open(os.path.join(sys.prefix,"shared","wgne","obs_info_dictionary.json")).read())
print obs_dic
class DUP(object):
    def __init__(self,outfile):
        self.outfile = outfile
    def __call__(self,*args):
        msg = ""
        for a in args:
            msg+=str(a)
        print msg
        print>>self.outfile, msg

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

Efile = open(parameters.metrics_output_path+parameters.case_id+"/errors_log.txt","w")
dup=DUP(Efile)

for var in parameters.vars:   #### CALCULATE METRICS FOR ALL VARIABLES IN vars
    metrics_dictionary = {}
    ## REGRID OBSERVATIONS AND MODEL DATA TO TARGET GRID (ATM OR OCN GRID)

    if len(var.split("_"))>1:
        level = float(var.split("_")[-1])*100.
        var=var.split("_")[0]
    else:
        level=None

    dup("ok table thing",obs_dic[var][obs_dic[var]["default"]]["CMIP_CMOR_TABLE"],"---")
    if obs_dic[var][obs_dic[var]["default"]]["CMIP_CMOR_TABLE"]=="Omon":
        regridMethod = parameters.regrid_method_ocn
        regridTool = parameters.regrid_tool_ocn
        table_realm = 'Omon'
        dup("WE SET TABLE REALM TO",table_realm)
    else:
        dup("we came here!!!!!",obs_dic[var][obs_dic[var]["default"]]["CMIP_CMOR_TABLE"])
        regridMethod = parameters.regrid_method
        regridTool= parameters.regrid_tool
        table_realm = 'Amon'

    #Ok at that stage we need to loop thru obs
    dup('ref is:',parameters.ref)
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

    for ref in refs:
      try:
        if obs_dic[var][obs_dic[var][ref]]["CMIP_CMOR_TABLE"]=="Omon":
            OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/ocn/mo",var,obs_dic,ref)
        else:
            OBS = metrics.wgne.io.OBS(parameters.obs_data_path+"/obs/atm/mo",var,obs_dic,ref)
        OBS.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
### PJG ADDING LEVEL CONDITON FOR OBS JAN 21 2014
        try:
         if level is not None:
           do = OBS.get(var,level=level)
         else:
           do = OBS.get(var)
        except:
           dup('failed with 4D OBS',var,ref)
           continue
        dup('OBS SHAPE IS ', do.shape)
### END PJG EDIT 

        for model_version in parameters.model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
            success = True
            while success:

                MODEL = metrics.io.base.Base(parameters.mod_data_path,parameters.filename_template)
                MODEL.model_version = model_version
                dup("SETTING TABLE REALM TO",table_realm)
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
                    dup('Failed to get variable %s for version: %s, error:\n%s' % ( var, model_version, err))
                    break

                dup(var,' ', model_version,' ', dm.shape,' ', do.shape,'  ', ref)
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
      except Exception,err:
          dup("Error in processing obs:",var,ref,err)
    ## Done with obs and models loops , let's dum before next var
    ### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES
    OUT.write(metrics_dictionary, sort_keys=True, indent=4, separators=(',', ': '))    
    # CREATE OUTPUT AS ASCII FILE
    OUT.write(metrics_dictionary,type="txt") 
