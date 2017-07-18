#!/usr/bin/env python

#########################################################
# SAMPLE COMMAND LINE EXECUTION USING ARGUMENTS BELOW
#########################################################
# python enso_mean_stat.py 
# -mp /work/cmip5/piControl/atm/mo/ts/cmip5.MODS.piControl.r1i1p1.mo.atm.Amon.ts.ver-1.latestX.xml
# -op /clim_obs/obs/ocn/mo/tos/UKMETOFFICE-HadISST-v1-1/130122_HadISST_sst.nc
# --mns ACCESS1-0 ACCESS1-3
# --var ts
# --varobs sst (varobs needed only when varname is different to model in obs)
# --outpd /work/lee1043/cdat/pmp/enso/test
# --outpj /work/lee1043/cdat/pmp/enso/test 
# --outnj output_mean_stat.json 
#########################################################

import logging
LOG_LEVEL = logging.INFO
logging.basicConfig(level=LOG_LEVEL)

import cdutil
import genutil
import MV2

import cdms2
import copy
import sys
import os
import string
import json
import pcmdi_metrics
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser
import collections
from collections import defaultdict

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
               default='enso_mean_stat.json',
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
  execfile(os.path.join('./lib/',lib))

regions_specs = {}
execfile(sys.prefix + "/share/default_regions.py")
#execfile("/export_backup/lee1043/git/pcmdi_metrics/share/default_regions.py")
##########################################################

if var != 'ts' and var != 'pr' and var != 'tauu' :
    sys.exit('Variable '+var+' is not correct')

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
# Loop for Observation and Models
#-------------------------------------------------
for mod in models:
    print ' ----- ', mod,' ---------------------'

    if mod == 'obs':
        file_path = obspath
        varname = varobs
        mods_key = 'OBSERVATION'
    else:
        file_path = modpath.replace('MODS', mod)
        varname = var
        mods_key = 'MODELS'

    try:
        f = cdms2.open(file_path)
        reg_selector = regions_specs[reg]['domain']

        if debug:
            reg_timeseries = f(varname, reg_selector, time=slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
        else:
            reg_timeseries = f(varname, reg_selector)

        # Get climatology
        clim = cdutil.averager(reg_timeseries,axis='t')

        if stat == 'rmse': 
            if mod == 'obs':
                obs_clim = clim.clone()
                obs_grid = clim.getGrid()
                result = 0.
            else:
                mod_clim = clim.clone()
                if var == 'ts':
                    mod_clim = MV2.subtract(mod_clim, 273.15) # K to C degree
                    mod_clim.units = 'degC'
                # Regrid (mod to obs)
                mod_clim_regrid = mod_clim.regrid(obs_grid, regridTool='regrid2')
                # Get RMS
                result = float(genutil.statistics.rms(mod_clim_regrid, obs_clim, axis='xy', weights='weighted'))
        elif stat == 'amp':
            ann_cycle = cdutil.ANNUALCYCLE.climatology(reg_timeseries)
            ann_cycle_area_avg = cdutil.averager(obs_ann_cycle,axis='xy')
            # Get amplitude (Is below a right way to get amplitude??)
            result = float(np.amax(ann_cycle_area_avg) - np.mean(ann_cycle_area_avg))

        enso_stat_dic[mods_key][var][stat][reg] = result
        enso_stat_dic[mods_key][var][stat]['source'] = file_path
        f.close()

    except:
        print 'failed for ', mod

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
