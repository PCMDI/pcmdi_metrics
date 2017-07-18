#!/usr/bin/env python

import logging
LOG_LEVEL = logging.INFO
logging.basicConfig(level=LOG_LEVEL)

import sys, os
import shutil
import cdms2 as cdms
import json

debug = True
#debug = False

def tree(): return defaultdict(tree)

#########################################################

P = PMPParser() # Includes all default options

P.add_argument("--mp", "--modpath",
               type=str,
               dest='modpath',
               required=True,
               help="Explicit path to model monthly PR or TS time series")
P.add_argument("--op", "--obspath",
               type=str,
               dest='obspath',
               default='',
               help="Explicit path to obs monthly PR or TS time series")
P.add_argument('--mns', '--modnames',
               type=str,
               nargs='+',
               dest='modnames',
               required=True,
               help='Models to apply')
P.add_argument("--var", "--variable",
               type=str,
               dest='variable',
               default='ts',
               help="Variable: 'pr', 'tauu',  or 'ts (default)'")
P.add_argument("--varobs", "--variableobs",
               type=str,
               dest='variableobs',
               default='',
               help="Variable name in observation (default: same as var)")
P.add_argument("--outpj", "--outpathjsons",
               type=str,
               dest='outpathjsons',
               default='.',
               help="Output path for jsons")
P.add_argument("--outnj", "--outnamejson",
               type=str,
               dest='jsonname',
               default='atm_feedback_stat.json',
               help="Output path for jsons")
P.add_argument("--outpd", "--outpathdata",
               type=str,
               dest='outpathdata',
               default='.',
               help="Output path for data")
P.add_argument("-e", "--experiment",
               type=str,
               dest='experiment',
               default='historical',
               help="AMIP, historical or picontrol")
P.add_argument("-c", "--MIP",
               type=str,
               dest='mip',
               default='CMIP5',
               help="put options here")
P.add_argument("-p", "--parameters",
               type=str,
               dest='parameters',
               default='',
               help="")
P.add_argument("-s", "--stat",
               type=str,
               dest='stat',
               default='rmse',
               help="rmse or amp")
P.add_argument("--reg", "--region",
               type=str,
               dest='region',
               default='TropPac',
               help="TropPac, Nino3, EqPac, IndoPac, etc. See /share/default_regions.py")

args = P.parse_args(sys.argv[1:])

modpath = args.modpath
obspath = args.obspath
mods = args.modnames
var = args.variable
varobs = args.variableobs
if varobs == '': varobs = var
outpathjsons = args.outpathjsons
outfilejson = args.jsonname
outpathdata = args.outpathdata
exp = args.experiment
stat = args.stat
reg = args.region

##########################################################
libfiles = ['monthly_variability_statistics.py',
            'slice_tstep.py']

libfiles_share = ['default_regions.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

regions_specs = {}
#execfile(sys.prefix + "/share/default_regions.py")
execfile("/export_backup/lee1043/git/pcmdi_metrics/share/default_regions.py")
##########################################################

if debug:
  fdbs = ['AtmBjk'] # Test just one region
else:
  fdbs = ['AtmBjk','SfcFlx','SrtWav','LthFlx']

# SETUP WHERE TO OUTPUT RESULTING  (netcdf)
try:
    jout = outpathjsons
    os.mkdir(jout)
except BaseException:
    pass

models = copy.copy(args.modnames)
if obspath != '':
    models.insert(0,'obs')

# DICTIONARY TO SAVE RESULT
enso_stat_dic = tree() ## Set tree structure dictionary

#=================================================
# Models 
#-------------------------------------------------
for mod in mods:
  print ' ----- ', mod,' ---------------------'

  try:
    # x-axis of slope, common for all type of feedback
    xvar='ts'
    xregion = 'Nino3'
    xvar_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,xvar,run)
    reg_timeseries_x_area_avg_anom = get_axis_base_dataset(xvar, xregion, xvar_path)

    # y-axis of slope for each feedback
    for fdb in fdbs:  ### Too messy... there should be better way... working on it..

      if fdb == 'AtmBjk': # Atmospheric Bjerknes Feedback
        yvar = 'tauu'
        yregion = 'Nino4'
      elif fdb == 'SfcFlx': # Surface Fluxes Feedback
        yvar = 'hfls'
        yvar2 = 'hfss'
        yregion = 'Nino3'
      elif fdb == 'SrtWav': # Shortwave Feedback
        yvar='rsds'
        yregion = 'Nino3'
      elif fdb == 'LthFlx': # Latent Heat Fluexs Feedback
        yvar = 'hfls'
        yregion = 'Nino3'
      else:
        sys.exit(fdb+" is not defined")

      try:
        yvar_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,yvar,run)
        reg_timeseries_y_area_avg_anom = get_axis_base_dataset(yvar, yregion, yvar_path)

        if fdb == 'SfcFlx':
          yvar2_path = get_latest_pcmdi_mip_data_path(mip,exp,mod,fq,realm,yvar2,run)
          reg_timeseries_y2_area_avg_anom = get_axis_base_dataset(yvar2, yregion, yvar2_path)
          reg_timeseries_y_area_avg_anom = sum(reg_timeseries_y_area_avg_anom,reg_timeseries_y2_area_avg_anom)

        # Simple quality control
        if len(reg_timeseries_x_area_avg_anom) == len(reg_timeseries_y_area_avg_anom):
          ntstep = len(reg_timeseries_x_area_avg_anom)
        else:
          print xvar+" and "+yvar+" tstep not match"
          break

        slope = get_slope_linear_regression(reg_timeseries_y_area_avg_anom,reg_timeseries_x_area_avg_anom)
        print mod, fdb, 'slope =', slope

        enso_stat_dic['RESULTS'][mod]['feedback'][fdb] = slope

      except:
        print mod, fdb, "cannot be calculated"

    if debug: print 'reg_time =', ntstep

    enso_stat_dic['RESULTS'][mod]['reg_time'] = ntstep

  except:
    print 'failed for model ', mod
    pass

#=================================================
#  OUTPUT METRICS TO JSON FILE
#-------------------------------------------------
OUT = pcmdi_metrics.io.base.Base(os.path.abspath(jout), outfilejson)

disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pmp",
        "disclaimer.txt")).read()

metrics_dictionary = collections.OrderedDict()
metrics_dictionary["DISCLAIMER"] = disclaimer
metrics_dictionary["REFERENCE"] = "The statistics in this file are based on Bellenger, H et al. Clim Dyn (2014) 42:1999-2018. doi:10.1007/s00382-013-1783-z"
metrics_dictionary["RESULTS"] = enso_stat_dic  # collections.OrderedDict()

OUT.var = var
OUT.write(
    metrics_dictionary,
    json_structure=["model", "index", "statistic", "period_chunk"],
    indent=4,
    separators=(
        ',',
        ': '),
    sort_keys=True)

sys.exit('done')
