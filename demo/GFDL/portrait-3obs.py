#!/usr/bin/env python

#################################################################################
#  RELIES UPON CDAT MODULES 
#  PRODUCE SIMPLE PORTRAIT PLOT BASED ON RESULTS FROM PCMDI'S METRICS PACKAGE 
#  WRITTEN BY P. GLECKLER, PCMDI/LLNL
#  FURTHER TWEAKED BY C. DOUTRIAUX
#  ISSUE TO BE RESOLVED WITH UV-CDAT PLANNED IMPROVEMENTS: ABILITY TO SAVE PLOTS IN MULTIPLE FORMATS  
#################################################################################

# CHECK TO VERIFY VCS MODULE IS INSTALLED
try:
  import vcs
except:
  raise RuntimeError("Sorry your python is not build with VCS support and cannot generate portrait plots")

# PATH WHERE METRICS RESULTS FOR GFDL SIT
gfdl_pth="/work/durack1/Shared/140808_metrics-gfdl/metrics_output_path/sampletest"

# STANDARD PYTHON MODULES
import glob,json,os,sys
import numpy as np
# CDAT MODULES
import pcmdi_metrics.graphics.portraits
import MV2
from genutil import statistics

# CREATE VCS OBJECT AS A PORTAIT PLOT AND LOAD PLOT SETTINGS FOR TEST CASE 
x=vcs.init()
x.portrait()

#######################
# PORTRAIT PLOT PARAMETER SETTINGS
P=pcmdi_metrics.graphics.portraits.Portrait()
# Turn off verbosity
P.verbose = False

P.PLOT_SETTINGS.levels = [-1.e20,-.5,-.4,-.3,-.2,-.1,0.,.1,.2,.3,.4,.5,1.e20]
P.PLOT_SETTINGS.x1 = .1
P.PLOT_SETTINGS.x2 = .85
P.PLOT_SETTINGS.y1 = .22
P.PLOT_SETTINGS.y2 = .95
P.PLOT_SETTINGS.xtic2y1=P.PLOT_SETTINGS.y1
P.PLOT_SETTINGS.xtic2y2=P.PLOT_SETTINGS.y2
P.PLOT_SETTINGS.ytic2x1=P.PLOT_SETTINGS.x1
P.PLOT_SETTINGS.ytic2x2=P.PLOT_SETTINGS.x2
#P.PLOT_SETTINGS.missing_color = 240
# Logo is simply a vcs text object, set to None for off
P.PLOT_SETTINGS.logo = None
# timestamp is simply a vcs text object, set to None for off
P.PLOT_SETTINGS.time_stamp = None
P.PLOT_SETTINGS.draw_mesh='y'
#P.PLOT_SETTINGS.tictable.font = 3
x.scriptrun(os.path.join(sys.prefix,"share","graphics",'vcs','portraits.scr'))
P.PLOT_SETTINGS.colormap = 'bl_rd_12'
cols=vcs.getcolors(P.PLOT_SETTINGS.levels,range(144,156),split=1)
P.PLOT_SETTINGS.fillareacolors = cols
P.PLOT_SETTINGS.parametertable.expansion = 100 
#######################


# LIST OF VARIABLES TO BE USED IN PORTRAIT PLOT
# REDUCED LIST FOR TEST CASE
vars = ['pr','tas','psl','rlut','rsut','ua-850','ua-200','va-850','va-200','zg-500']

# LOAD METRICS DICTIONARIES FROM JSON FILES FOR EACH VAR AND STORE AS A SINGLE DICTIONARY
var_cmip5_dics = {}
mods = set()

# CMIP5 METRICS RESULTS - CURRENTLY USING FOR CONTROL SIMULATIONS
json_files = glob.glob(os.path.join(sys.prefix,"share","CMIP_metrics_results","CMIP5","piControl","*.json")) 
# ADD GFDL JSON FILES... 
# This is pretty hard coded might want to consider more magic
json_files += glob.glob(os.path.join(gfdl_pth,'*.json'))

# CONSTRUCT PYTHON DICTIONARY WITH RESULTS METRICS USED IN PORTRAIT  
non_mods = ["GridInfo","References","RegionalMasking","metrics_git_sha1","uvcdat_version"]
for fnm in json_files:
  f=open(fnm)
  d = json.load(f)
  var = os.path.basename(fnm).split("_")[0]
  for m in d.keys():
    # Skip non model bits`
    if m not in non_mods: 
        mods.add(m)
    else:
        # Let's clean it up
        del(d[m])
  if var_cmip5_dics.has_key(var):
      var_cmip5_dics[var].update(d)
  else:
      var_cmip5_dics[var]=d

mods = sorted(list(mods))

# ORGANIZE METRICS INTO A VARIABLES X MODELS MATRIX 
out1_rel,out2_rel,out3_rel = [np.ma.masked_all((len(vars),len(mods)),np.float32) for _ in range(3)] ; # Define arrays to fill

for vn, var in enumerate(vars):
    # LOOP OVER VARIABLE
    # LOOP OVER MODEL
    for mn,mod in enumerate(mods):
        try:
            out1_rel[vn,mn] = float(var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xy_djf_GLB'])
            out2_rel[vn,mn] = float(var_cmip5_dics[var][mod]["alternate1"]["r1i1p1"]["global"]['rms_xy_djf_GLB'])
            out3_rel[vn,mn] = float(var_cmip5_dics[var][mod]["alternate2"]["r1i1p1"]["global"]['rms_xy_djf_GLB'])
        except Exception,err:
           pass
    
    med_rms1 = np.ma.median(out1_rel[vn,:])
    med_rms2 = np.ma.median(out2_rel[vn,:])
    med_rms3 = np.ma.median(out3_rel[vn,:])
   
    out1_rel[vn,:]=(out1_rel[vn,:]-med_rms1)/med_rms1
    out2_rel[vn,:]=(out2_rel[vn,:]-med_rms2)/med_rms2
    out3_rel[vn,:]=(out3_rel[vn,:]-med_rms3)/med_rms3

# ADD SPACES FOR LABELS TO ALIGN AXIS LABELS WITH PLOT
yax = [ m.encode('utf-8')+" " for m in mods ]
xax = [ v+" " for v in vars ]
  
# Convert to MV so we can decorate
out1_rel = MV2.array(out1_rel)
out2_rel = MV2.array(out2_rel)
out3_rel = MV2.array(out3_rel)

# GENERATE PLOT 
P.decorate(out1_rel,xax,yax)
P.decorate(out2_rel,xax,yax)
P.decorate(out3_rel,xax,yax)

# PLOT
P.plot(out1_rel,x=x,multiple=1.3,bg=1)
P.plot(out2_rel,x=x,multiple=2.3,bg=1)
P.plot(out3_rel,x=x,multiple=3.3,bg=1)
# END OF PLOTTING

# SAVE PLOT
fileName = 'test_3obsRMS'
x.png(fileName)
#x.postscript(fileName) ; # Labelling requires VCS updates expected with UV-CDAT 2.1.1 release
#x.pdf(fileName) ; # Labelling requires VCS updates expected with UV-CDAT 2.1.1 release
