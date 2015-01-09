#!/usr/bin/env python

#################################################################################
#  RELIES UPON CDAT MODULES 
#  PRODUCE SIMPLE PORTRAIT PLOT BASED ON RESULTS FROM PCMDI'S METRICS PACKAGE 
#  WRITTEN BY P. GLECKLER, PCMDI/LLNL
#  LAST UPDATE: 7/23/14 

#  ISSUES TO BE RESOLVED ###
#  PLOT NOT DISPLAYING LABELS 
#  UNABLE TO SAVE PLOT TO VARIOUS FORMATS  
#################################################################################
# STANDARD PYTHON 
try:
  import vcs
except:
  raise RuntimeError("Sorry your python is not build with VCS support and cannot generate portrait plots")

import glob,json,MV2,os,sys
# CDAT MODULES
import pcmdi_metrics.graphics.portraits
from genutil import statistics

## CREATES VCS OBJECT AS A PORTAIT PLOT AND LOADS PLOT SETTINGS FOR EXAMPLE
x=vcs.init()
x.portrait()

## PARAMETERS STUFF
P=pcmdi_metrics.graphics.portraits.Portrait()

## Turn off verbosity
P.verbose = False

#P.PLOT_SETTINGS.levels = [0.,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.]
#P.PLOT_SETTINGS.levels = [-1.e20,-1,-.75,-.5,-.25,0.,.25,.5,.75,1.,1.e20]
P.PLOT_SETTINGS.levels = [-1.e20,-.5,-.4,-.3,-.2,-.1,0.,.1,.2,.3,.4,.5,1.e20]

P.PLOT_SETTINGS.x1 = .1
P.PLOT_SETTINGS.x2 = .85
P.PLOT_SETTINGS.y1 = .22
P.PLOT_SETTINGS.y2 = .95

P.PLOT_SETTINGS.xtic2y1=P.PLOT_SETTINGS.y1
P.PLOT_SETTINGS.xtic2y2=P.PLOT_SETTINGS.y2
P.PLOT_SETTINGS.ytic2x1=P.PLOT_SETTINGS.x1
P.PLOT_SETTINGS.ytic2x2=P.PLOT_SETTINGS.x2

P.PLOT_SETTINGS.missing_color = 240
P.PLOT_SETTINGS.logo = None
P.PLOT_SETTINGS.time_stamp = None
P.PLOT_SETTINGS.draw_mesh='n'
#P.PLOT_SETTINGS.tictable.font = 3

x.scriptrun(os.path.join(sys.prefix,"share","graphics",'vcs','portraits.scr'))
P.PLOT_SETTINGS.colormap = 'bl_rd_12'
#cols=vcs.getcolors(P.PLOT_SETTINGS.levels,range(16,40),split=1)
cols=vcs.getcolors(P.PLOT_SETTINGS.levels,range(144,156),split=1)
P.PLOT_SETTINGS.fillareacolors = cols

P.PLOT_SETTINGS.parametertable.expansion = 100 

# LIST OF VARIABLES TO BE USED IN PORTRAIT PLOT
vars = ['pr','psl','rlut','rsut','rsutcs','ta-850','tas','tos','ua-850','uas','va-850','vas','zg-500']

# LOAD METRICS DICTIONARIES FROM JSON FILES FOR EACH VAR AND STORE AS A SINGLE DICTIONARY
var_cmip5_dics = {}
mods = set()
json_files = glob.glob(os.path.join(sys.prefix,"share","CMIP_metrics_results","CMIP5","historical","*.json")) ; # Use historical files to compare
json_files_gfdl = glob.glob('metrics_output_path/sampletest/*.json')

for f in json_files_gfdl:
    json_files.append(f)

# CMIP5 models to compare
for fnm in json_files:
  f = open(fnm)
  d = json.load(f)
  var = os.path.basename(fnm).split("_")[0]
  vars.append(var)
  for m in d.keys():
    if m not in ['GridInfo']:  mods.add(m)
  if var_cmip5_dics.has_key(var):
      var_cmip5_dics[var].update(d)
  else:
      var_cmip5_dics[var]=d

mods = sorted(list(mods))
for bad in ["References","RegionalMasking","metrics_git_sha1","uvcdat_version"]:
  try:
    mods.remove(bad)
  except:
    pass

# ORGANIZE METRICS INTO A VARIABLES X MODELS MATRIX 
out1_rel = MV2.zeros((len(vars),len(mods)),MV2.float32) #DEFINE ARRAY
out2_rel = MV2.zeros((len(vars),len(mods)),MV2.float32)
out3_rel = MV2.zeros((len(vars),len(mods)),MV2.float32)
out4_rel = MV2.zeros((len(vars),len(mods)),MV2.float32)

vn = -1 # VARIABLE INDEX
for var in vars:  # LOOP OVER VARIABLE    
   vn = vn + 1

   vals1 = []
   vals2 = []
   vals3 = []
   vals4 = []

   for mod in mods: # LOOP OVER MODEL
    try:
       rms1 = var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_djf_GLB']
       rms2 = var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_mam_GLB']
       rms3 = var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_jja_GLB']
       rms4 = var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_son_GLB']

       if P.verbose:
           print var,' ', mod,'  ', `rms`, ' WITH global'
    except Exception,err:    
       rms1 = 1.e20
       rms2 = 1.e20
       rms3 = 1.e20
       rms4 = 1.e20

       if P.verbose:
           print var,' ', mod,'  ', `rms1`, ' missing'

    rms1 = float(rms1)
    vals1.append(rms1)
    rms2 = float(rms2)
    vals2.append(rms2)
    rms3 = float(rms3)
    vals3.append(rms3)
    rms4 = float(rms4)
    vals4.append(rms4)

   vars_ar1 = MV2.array(vals1)
   med_rms1 = statistics.median(vars_ar1)[0]  # COMPUTE MEDIAN RESULT FOR PORTRAIT NORMALIZATION 
   vars_ar2 = MV2.array(vals2)
   med_rms2 = statistics.median(vars_ar2)[0]  
   vars_ar3 = MV2.array(vals3)
   med_rms3 = statistics.median(vars_ar3)[0]  
   vars_ar4 = MV2.array(vals4)
   med_rms4 = statistics.median(vars_ar4)[0]  


   mn = -1 # MODEL INDEX
   for mod in mods: 
     mn = mn + 1
     try:
       out1_rel[vn,mn] = (float(var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_djf_GLB'])-med_rms1)/med_rms1 # RELATIVE ERROR 
       out2_rel[vn,mn] = (float(var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_mam_GLB'])-med_rms2)/med_rms2 # RELATIVE ERROR 
       out3_rel[vn,mn] = (float(var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_jja_GLB'])-med_rms3)/med_rms3 # RELATIVE ERROR 
       out4_rel[vn,mn] = (float(var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_son_GLB'])-med_rms4)/med_rms4 # RELATIVE ERROR 

     except:
       out1_rel[vn,mn] = 1.e20 
       out2_rel[vn,mn] = 1.e20
       out3_rel[vn,mn] = 1.e20
       out4_rel[vn,mn] = 1.e20

# ADD SPACES FOR LABELS TO ALIGN AXIS LABELS WITH PLOT
modsAxis = mods
varsAxis = vars

# LOOP THROUGH LISTS TO ADD SPACES
for i in range(len(modsAxis)):
  modsAxis[i] =  modsAxis[i] + '  '
for i in range(len(varsAxis)):
  varsAxis[i] = varsAxis[i] + '  ' 
  
yax = [s.encode('utf-8') for s in mods]  # CHANGE FROM UNICODE TO BYTE STRINGS 
xax = vars 

# GENERATE PLOT 
P.decorate(out1_rel,xax,yax)
P.decorate(out2_rel,xax,yax)
P.decorate(out3_rel,xax,yax)
P.decorate(out4_rel,xax,yax)

#P.plot(out1_rel,x=x,multiple=1.1,bg=0)  # FOR PLOTTING TRIANGLES WHEN USING TWO OR MORE REFERENCE DATA SETS
#P.plot(out1_rel,bg=1,x=x)

P.plot(out1_rel,x=x,multiple=1.4,bg=1)
P.plot(out2_rel,x=x,multiple=2.4,bg=1)
P.plot(out3_rel,x=x,multiple=3.4,bg=1)
P.plot(out4_rel,x=x,multiple=4.4,bg=1)

#x.backend.renWin.Render()

### END OF PLOTTING

### SAVE PLOT
x.png('test_portrait-4seas')
#x.postscript('test_portrait-4seas') ; # Existing VTK quirks need fixing for labelling
#x.pdf('test_portrait-4seas') ; # Existing VTK quirks need fixing for labelling
