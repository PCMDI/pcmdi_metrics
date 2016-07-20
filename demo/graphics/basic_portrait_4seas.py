#!/usr/bin/env python

#################################################################################
#  RELIES ON UV-CDAT MODULES #  PRODUCE SIMPLE PORTRAIT PLOT BASED ON RESULTS FROM PCMDI'S METRICS PACKAGE 
#  WRITTEN BY P. GLECKLER, PCMDI/LLNL
#  LAST UPDATE: 7/19/16 
#  
#  NORMALIZATION WITH RESPECT TO MEDIAN MODEL RESULT (see Gleckler et al., 2008, DOI 10.1029/2007JD008972)

#  ISSUES TO BE RESOLVED ###
#  UNABLE TO SAVE PLOT TO VARIOUS FORMATS, png resolution hardwired in background mode  
#  NUMEROUS OPTIONS ARE LIMITED
#       NEED TO IMPLEMENT OPTION TO COMBINE RESULTS FROM SEPERATE JSONS (E.G., TO COMPARE A NEW MODEL WITH CMIP ENSEMBLE)
#	ONLY ONE PLOT PER PAGE
#  	ONLY TWO SCALE RANGES BY COMMAND LINE
#       MANY OTHER OPTIONS TO GENERALIZE
#################################################################################
# STANDARD PYTHON 
try:
  import vcs
except:
  raise RuntimeError("Sorry your python is not build with VCS support cannot geenrate portrait plots")

import string,sys
import json
import argparse
import os,sys
import glob

# CDAT MODULES
import pcmdi_metrics.graphics.portraits
import MV2
from genutil import statistics
import pcmdi_metrics

#EXAMPLE EXECUTIONS
# >python basic_portrait_4seas.py   # DEFAULT DEMO SPECS AND DATA 
# >python basic_portrait_4seas.py -d n -v 'pr,tas,psl,rlut' -r TROPICS -s rms -m '0.25'

#######################################
# DEMO DEFAULTS
demo_specs = 'y'
demo_data_loc = 'y'
stat = 'rms'
reg = 'GLB'
scale = '0.25'
vars = ['pr', 'tas', 'psl', 'rlut', 'rltcre', 'rstcre', 'ta-850', 'ta-200', ' ua-850', 'ua-200', 'va-850', 'va-200', 'zg-500']

## LOCATION OF DEMO JSON FILES
mm_path =  os.path.join(
        pcmdi_metrics.__path__[0],
        "..",
        "..",
        "..",
        "..",
        "demo/results")
########################################
### COMMAND LINE OPTIONS 

parser = argparse.ArgumentParser(description='Produce a simple portrait plot with the PMP results')
parser.add_argument("-s","--stat",help="Statistics used...options: RMS, MSE,bias,corr")  
parser.add_argument("-r","--region",help="region ... options: GLB, NHEX, TROPICS, SHEX")  
parser.add_argument("-v","--vars",help="variables ... options: ")  
parser.add_argument("-m","--scale",help="Max/min range ... current options: '0.25' or '0.5'") 
parser.add_argument("-c","--cmip_path",help="provide directory where CMIP multi-model json files are located") 
parser.add_argument("-d","--demo_specs",help="produce demo plot y or n") 
parser.add_argument("-dd","--demo_data",help="produce demo plot y or n")

args =parser.parse_args(sys.argv[1:])

if args.demo_specs is not None: demo_specs = args.demo_specs

if demo_specs != 'y':
 stat = args.stat  
 reg = args.region
 scale = args.scale 

if demo_data_loc != 'y':
   mm_path = args.cmip_path

########################################

if args.vars is not None:
 vars = args.vars
 vars = string.split(vars,',')
 for i in range(len(vars)):
     vars[i] = string.replace(vars[i],' ','')

print 'stat reg ar ', stat,' ', reg,'  ', vars 

## CREATES VCS OBJECT AS A PORTAIT PLOT AND LOADS PLOT SETTINGS FOR EXAMPLE
#x=vcs.init(bg=1,geometry=(2400,3200))
x = vcs.init()
x.portrait()

## PARAMETERS STUFF
P=pcmdi_metrics.graphics.portraits.Portrait()

## Turn off verbosity
P.verbose = False

if scale == '0.5': P.PLOT_SETTINGS.levels = [-1.e20,-.5,-.4,-.3,-.2,-.1,0.,.1,.2,.3,.4,.5,1.e20]
if scale == '0.25': P.PLOT_SETTINGS.levels = [-1.e20,-.25,-.2,-.15,-.10,-.05,0.,.05,.1,.15,.2,.25,1.e20]

P.PLOT_SETTINGS.x1 = .1
P.PLOT_SETTINGS.x2 = .85
P.PLOT_SETTINGS.y1 = .3
P.PLOT_SETTINGS.y2 = .7 

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

if scale == '.5': P.PLOT_SETTINGS.levels = [-1.e20,-.5,-.4,-.3,-.2,-.1,0.,.1,.2,.3,.4,.5,1.e20]
if scale == '.25':P.PLOT_SETTINGS.levels = [-1.e20,-.25,-.2,-.15,-.10,-.05,0.,.05,.1,.15,.2,.25,1.e20]

vars_avail = []

### LOAD METRICS DICTIONARIES FROM JSON FILES FOR EACH VAR AND STORE AS A SINGLE DICTIONARY
var_cmip5_dics = {}
mods = set()

json_files = glob.glob(mm_path + '/*.json')

## THIS IS FOR COMBINING RESULTS FROM SEPERATE JSON FILES (E.G., MY MODEL AND CMIP) - NOT YET IMPLEMENTED
#json_filesa = glob.glob('/export/gleckler1/processing/metrics_package/my_test/ncar/pmp-test-control/*.json')
#for f in json_filesa: json_files.append(f)


for fnm in json_files:
  f=open(fnm)
  d = json.load(f)
  var = os.path.basename(fnm).split("_")[0]
  var = string.replace(var," ","")
  vars_avail.append(var)
  for m in d['RESULTS'].keys():
    if m not in mods: mods.add(m)
    if var == 'pr' : print m
  if var_cmip5_dics.has_key(var):
      var_cmip5_dics[var]['RESULTS'].update(d['RESULTS'])
      if var == 'pr': print 'a ', fnm
  else:
      var_cmip5_dics[var]={} 
      var_cmip5_dics[var]['RESULTS']=d['RESULTS']
      if var == 'pr': print 'b ', fnm
  if var == 'pr': print 'dic length ', len(var_cmip5_dics['pr']['RESULTS'].keys())


print var_cmip5_dics['pr']['RESULTS'].keys()

## TRAP VARS FROM AVAILABLE JSON FILES
#vars = []
#for j in json_files:
# fn = string.split(j,'/')[8]
# var = string.split(fn,'_')[0] 
# var = string.replace(var," ","")

# if var not in vars: vars.append(var)

#################

mods = sorted(list(mods))

###### ORGANIZE METRICS INTO A VARIABLES X MODELS MATRIX 

print 'mods are... ', mods

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

   realm = 'global'
   if var == 'psl': realm = 'ocean'

   for mod in mods: # LOOP OVER MODEL
    try:
       rms1 = var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_djf_' + reg]
       rms2 = var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_mam_' + reg]
       rms3 = var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_jja_' + reg]
       rms4 = var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_son_' + reg]

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

   realm = 'global'
   if var == 'psl': realm = 'ocean'

   mn = -1 # MODEL INDEX
   for mod in mods: 
     mn = mn + 1
     try:
       out1_rel[vn,mn] = (float(var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_djf_' + reg])-med_rms1)/med_rms1 # RELATIVE ERROR 
       out2_rel[vn,mn] = (float(var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_mam_' + reg])-med_rms2)/med_rms2 # RELATIVE ERROR 
       out3_rel[vn,mn] = (float(var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_jja_' + reg])-med_rms3)/med_rms3 # RELATIVE ERROR 
       out4_rel[vn,mn] = (float(var_cmip5_dics[var]['RESULTS'][mod]["defaultReference"]["r1i1p1"][realm][stat + '_xy_son_' + reg])-med_rms4)/med_rms4 # RELATIVE ERROR 

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

out1_rel = MV2.masked_greater(out1_rel,1000.)
out2_rel = MV2.masked_greater(out2_rel,1000.)
out3_rel = MV2.masked_greater(out3_rel,1000.)
out4_rel = MV2.masked_greater(out4_rel,1000.)


#P.plot(out1_rel,bg=1,x=x)
P.plot(out1_rel,x=x,multiple=1.4,bg=0)
P.plot(out2_rel,x=x,multiple=2.4,bg=0)
P.plot(out3_rel,x=x,multiple=3.4,bg=0)
P.plot(out4_rel,x=x,multiple=4.4,bg=0)

header = x.createtext()
header.To.height = 24
header.To.halign = "center"
header.To.valign = "top"
header.x = .5
header.y = .8

tit = reg + ' ' + stat
header.string = [tit]

x.plot(header, bg=1)

### END OF PLOTTING, SAVE TO FILE 
### SAVE PLOT
#x.postscript('test')

x.png('test_' + stat + '_' + reg) 

w = sys.stdin.readline()

