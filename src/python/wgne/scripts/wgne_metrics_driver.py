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
import cdms2
import MV2
import cdutil

regions_values = {"land":100.,"ocean":0.,"lnd":100.,"ocn":0.}

#Load the obs dictionary
obs_dic = json.loads(open(os.path.join(metrics.__path__[0],"..","..","..","..","share","wgne","obs_info_dictionary.json")).read())

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
sys.path.insert(0,os.getcwd())
exec("import %s as parameters" % fnm)
if pth!="":
    sys.path.pop(-1)

#Checking if user has custom_keys
if not hasattr(parameters,"custom_keys"):
  parameters.custom_keys={}

try:
  os.makedirs(os.path.join(parameters.metrics_output_path,parameters.case_id))
except:
  pass

Efile = open(os.path.join(parameters.metrics_output_path,parameters.case_id,"errors_log.txt"),"w")
dup=DUP(Efile)


## First of all attempt to prepare sftlf before/after for all models
sftlf={}
for model_version in parameters.model_versions:   # LOOP THROUGH DIFFERENT MODEL VERSIONS OBTAINED FROM input_model_data.py
  sft = metrics.io.base.Base(parameters.mod_data_path,parameters.filename_template)
  sft.model_version = model_version
  sft.table = "fx"
  sft.realm = "atmos"
  sft.model_period = parameters.model_period
  sft.ext = "nc"
  sft.targetGrid = None
  sft.realization="r0i0p0"
  applyCustomKeys(sft,parameters.custom_keys,"sftlf")
  try:
    sftlf[model_version] = {"raw":sft.get("sftlf")}
  except:
    #Hum no sftlf...
    dup("No mask for ",sft())
    sftlf[model_version] = {"raw":None}
if parameters.targetGrid == "2.5x2.5":
  tGrid = cdms2.createUniformGrid(-88.875,72,2.5,0,144,2.5)
else:
  tGrid = parameters.targetGrid

sftlf["targetGrid"] = cdutil.generateLandSeaMask(tGrid)*100.

#At this point we need to create the tuples var/region to know if a variable needs to be ran over a specific region or global or both
regions = getattr(parameters,"regions",{})
vars = []

#Update/overwrite defsult region_values keys with user ones

regions_values.update(getattr(parameters,"regions_values",{}))


regions_dict = {}
for var in parameters.vars:
  vr = var.split("_")[0]
  rg = regions.get(vr,[None,])
  if not isinstance(rg,(list,tuple)):
    rg = [rg,]
  regions_dict[vr] = rg
print "RGION DICT:",regions_dict

for var in parameters.vars:   #### CALCULATE METRICS FOR ALL VARIABLES IN vars
  try:
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
    grd = {}
    grd["RegridMethod"] = regridMethod
    grd["RegridTool"] = regridTool
    grd["GridName"] = parameters.targetGrid


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

    OUT = metrics.io.base.Base(os.path.join(parameters.metrics_output_path,parameters.case_id),"%(var)%(level)_%(targetGridName)_%(regridTool)_%(regridMethod)_metrics")
    OUT.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
    OUT.var=var
    OUT.realm = realm
    OUT.table = table_realm
    applyCustomKeys(OUT,parameters.custom_keys,var)
    metrics_dictionary["RegionalMasking"] = {}
    for region in regions_dict[var]:
      if isinstance(region,str):
        region_name = region
        region = regions_values.get(region_name,regions_values.get(region_name.lower()))
      elif region is None:
        region_name = "global"
      else:
        region_name = "%i" % region
      metrics_dictionary["RegionalMasking"][region_name]=region
      metrics_dictionary["References"]={}
      for ref in refs:
        if ref in ["default","alternate"]:
          refabbv = ref+"Reference"
        else:
          refabbv = ref
        metrics_dictionary["References"][ref] = obs_dic[var][obs_dic[var][ref]]
        try:
          if obs_dic[var][obs_dic[var][ref]]["CMIP_CMOR_TABLE"]=="Omon":
              OBS = metrics.wgne.io.OBS(parameters.obs_data_path,var,obs_dic,ref)
          else:
              OBS = metrics.wgne.io.OBS(parameters.obs_data_path,var,obs_dic,ref)
          OBS.setTargetGrid(parameters.targetGrid,regridTool,regridMethod)
          OBS.realm = realm
          OBS.table = table_realm
          applyCustomKeys(OBS,parameters.custom_keys,var)
          if region is not None:
            ## Ok we need to apply a mask
            oMask = metrics.wgne.io.OBS(parameters.obs_data_path,"sftlf",obs_dic,ref)
            oMask = oMask.get("sftlf")
            OBS.mask = MV2.logical_not(MV2.equal(oMask,region))
            OBS.targetMask = MV2.logical_not(MV2.equal(sftlf["targetGrid"],region))
          try:
           if level is not None:
             do = OBS.get(var,level=level)
           else:
             do = OBS.get(var)
          except Exception,err:
             dup('failed with 4D OBS',var,ref,err)
             continue
          grd["GridResolution"] = do.shape[1:]
          metrics_dictionary["GridInfo"] = grd

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
                  if region is not None:
                    MODEL.mask = MV2.logical_not(MV2.equal(sftlf[model_version]["raw"],region))
                    MODEL.targetMask = MV2.logical_not(MV2.equal(sftlf["targetGrid"],region))
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
                  ## Stores model's simul descrition
                  if not metrics_dictionary[model_version].has_key("SimulationDescription"):
                      descr = {"MIPTable":obs_dic[var][obs_dic[var][ref]]["CMIP_CMOR_TABLE"],
                              "Model":model_version,
                              }

                      sim_descr_mapping = {
                              "ModelActivity":"project_id",
                              "ModellingGroup":"institute_id",
                              "Experiment":"experiment",
                              "ModelFreeSpace":"ModelFreeSpace",
                              "SimName":"realization",
                              }

                      sim_descr_mapping.update(getattr(parameters,"simulation_description_mapping",{}))
                      for att in sim_descr_mapping.keys():
                            nm = sim_descr_mapping[att]
                            if not isinstance(nm,(list,tuple)):
                                nm = ["%s",nm]
                            fmt = nm[0]
                            vals = []
                            for a in nm[1:]:
                                #First trying from parameter file
                                if hasattr(parameters,a):
                                    vals.append(getattr(parameters,a))
                                # Now fall back on file...
                                else:
                                    f = cdms2.open(MODEL())
                                    if hasattr(f,a):
                                        try:
                                            vals.append(float(getattr(f,a)))
                                        except:
                                            vals.append(getattr(f,a))
                                    # Ok couldn't find it anywhere setting to N/A
                                    else:
                                        vals.append("N/A")
                            descr[att] = fmt % tuple(vals)
                      metrics_dictionary[model_version]["SimulationDescription"] = descr 
                    
                  if not metrics_dictionary[model_version].has_key(refabbv):
                    metrics_dictionary[model_version][refabbv] = {'source':onm}
                  pr = metrics_dictionary[model_version][refabbv].get(parameters.realization,{})
                  pr[region_name] = metrics.wgne.compute_metrics(var,dm,do)
                  metrics_dictionary[model_version][refabbv][parameters.realization] = pr
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
                      CLIM.region = region_name
                      applyCustomKeys(CLIM,parameters.custom_keys,var)
                      CLIM.write(dm,type="nc",id="var")

                  break               
        except Exception,err:
          dup("Error while processing observation %s for variable %s:\n\t%s" % (var,ref,err))
      ## Done with obs and models loops , let's dum before next var
    ### OUTPUT RESULTS IN PYTHON DICTIONARY TO BOTH JSON AND ASCII FILES
    OUT.write(metrics_dictionary, mode="w", sort_keys=True, indent=4, separators=(',', ': '))    
    # CREATE OUTPUT AS ASCII FILE
    OUT.write(metrics_dictionary, mode="w", type="txt") 
  except Exception,err:
    dup("Error while processing variable %s:\n\t%s" % (var,err))

