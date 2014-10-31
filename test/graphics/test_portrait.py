#!/usr/bin/env python

#################################################################################
#  RELIES UPON CDAT MODULES 
#  PRODUCE SIMPLE PORTRAIT PLOT BASED ON RESULTS FROM PCMDI'S METRICS PACKAGE 
#  WRITTEN BY P. GLECKLER, PCMDI/LLNL
#  LAST UPDATE: 7/23/14 
#  Cleaned up by C. Doutriaux
# Adapted to unitest format by C. Doutriaux
# See git for change logs
#################################################################################
import unittest
import checkimage
class TestGraphics(unittest.TestCase):
  def __init__(self,name):
    super(TestGraphics,self).__init__(name)

  def test_portrait(self):
    try:
      import vcs
    except:
      raise RuntimeError("Sorry your python is not build with VCS support cannot geenrate portrait plots")

    import string,sys
    import json
    # CDAT MODULES
    import pcmdi_metrics.graphics.portraits
    import MV2
    from genutil import statistics
    import os,sys
    import glob

    #import portrait_test_functions

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
    P.PLOT_SETTINGS.y1 = .12
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

    ## LIST OF VARIABLES TO BE USED IN PORTRAIT PLOT
    vars = ['pr', 'rsut','rsutcs','rlutcs','tas','tos','sos','zos','ua-850','ua-200','zg-500']
    vars = []

    ### LOAD METRICS DICTIONARIES FROM JSON FILES FOR EACH VAR AND STORE AS A SINGLE DICTIONARY
    var_cmip5_dics = {}
    mods = set()
    json_files = glob.glob(os.path.join(sys.prefix,"share","CMIP_results","CMIP5","amip","*.json"))

    for fnm in json_files:
      f=open(fnm)
      d = json.load(f)
      var = os.path.basename(fnm).split("_")[0]
      vars.append(var)
      for m in d.keys():
          mods.add(m)
      if var_cmip5_dics.has_key(var):
          var_cmip5_dics[var].update(d)
      else:
          var_cmip5_dics[var]=d

    mods = sorted(list(mods))
    for bad in ["References","RegionalMasking","metrics_git_sha1","uvcdat_version"]:
        mods.remove(bad)

    ###### ORGANIZE METRICS INTO A VARIABLES X MODELS MATRIX 

    out1_rel = MV2.zeros((len(vars),len(mods)),MV2.float32) #DEFINE ARRAY

    vn = -1 # VARIABLE INDEX
    for var in vars:  # LOOP OVER VARIABLE    
       vn = vn + 1

       vals = []
       for mod in mods: # LOOP OVER MODEL
        try:
           rms = var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xyt_ann_GLB']
           if P.verbose:
               print var,' ', mod,'  ', `rms`, ' WITH global'
        except Exception,err:    
           rms = 1.e20
           if P.verbose:
               print var,' ', mod,'  ', `rms`, ' missing'

        rms = float(rms)
        vals.append(rms)

       vars_ar = MV2.array(vals)
       med_rms = statistics.median(vars_ar)[0]  # COMPUTE MEDIAN RESULT FOR PORTRAIT NORMALIZATION 

       mn = -1 # MODEL INDEX
       for mod in mods: 
         mn = mn + 1
         try:
           out1_rel[vn,mn] = (float(var_cmip5_dics[var][mod]["defaultReference"]["r1i1p1"]["global"]['rms_xyt_ann_GLB'])-med_rms)/med_rms # RELATIVE ERROR 
         except:
           out1_rel[vn,mn] = 1.e20 

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
    #P.plot(out1_rel,x=x,multiple=1.1,bg=0)  # FOR PLOTTING TRIANGLES WHEN USING TWO OR MORE REFERENCE DATA SETS
    P.plot(out1_rel,bg=1,x=x)
    #x.backend.renWin.Render()

    ### END OF PLOTTING

    ### SAVE PLOT
    src = os.path.join(os.path.dirname(__file__),"testPortrait.png")
    print src
    fnm = os.path.join(os.getcwd(),"testPortrait.png")
    x.png(fnm)
    ret = checkimage.check_result_image(fnm,src,checkimage.defaultThreshold)
    print ret
