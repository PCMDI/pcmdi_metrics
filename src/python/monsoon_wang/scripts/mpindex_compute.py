#!/usr/bin/env python
import cdms2
import numpy
import sys
import os
from genutil import statistics
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser
from pcmdi_metrics.monsoon_wang import mpd, mpi_skill_scores
import pcmdi_metrics
import collections
import glob

from __future__ import print_function

P = PMPParser()

P.use("--modpath")
P.use("--modnames")
P.use("--reference_data_path")

P.add_argument("--outpj", "--outpathjsons",
               type=str,
               dest='outpathjsons',
               default='.',
               help="Output path for jsons")

P.add_argument("--outpd", "--outpathdiags",
               type=str,
               dest='outpathdiags',
               default='.',
               help="Output path for diagnostics, usually netCDF")

P.add_argument("--outnj", "--outnamejson",
               type=str,
               dest='jsonname',
               default='out.json',
               help="Output path for jsons")
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
P.add_argument("--ovar",
               dest='obsvar',
               default='pr',
               help="Name of variable in obs file")
P.add_argument("-v", "--var",
               dest='modvar',
               default='pr',
               help="Name of variable in model files")
P.add_argument("-t", "--threshold",
               default=2.5 / 86400.,
               type=float,
               help="Threshold for a hit when computing skill score")

args = P.get_parameter()
modpath = args.modpath
outpathjsons = args.outpathjsons
outpathdata = args.outpathdiags
obspath = args.reference_data_path

mods = args.modnames   # LIST OF MODELS COMING FROM INPUT PARAMETER FILE
experiment = args.experiment
modpath.experiment = experiment

json_filename = args.jsonname

if json_filename == 'CMIP_MME':
    json_filename = '/MPI_' + args.mip + '_' + args.experiment

# VAR IS FIXED TO BE PRECIP FOR CALCULATING MONSOON PRECIPITATION INDICES
var = args.modvar
thr = args.threshold
sig_digits = '.3f'

#########################################
# PMP monthly default PR obs
cdms2.axis.longitude_aliases.append("longitude_prclim_mpd")
cdms2.axis.latitude_aliases.append("latitude_prclim_mpd")
fobs = cdms2.open(args.reference_data_path)
dobs_orig = fobs(args.obsvar)
fobs.close()

obsgrid = dobs_orig.getGrid()

########################################

# FCN TO COMPUTE GLOBAL ANNUAL RANGE AND MONSOON PRECIP INDEX

annrange_obs, mpi_obs = mpd(dobs_orig)
#########################################
# SETUP WHERE TO OUTPUT RESULTING DATA (netcdf)

nout = outpathdata 

try:
    os.makedirs(nout)
except BaseException:
    pass

# SETUP WHERE TO OUTPUT RESULTS (json)
jout = outpathjsons
try:
    os.makedirs(nout)
except BaseException:
    pass

gmods = [] # TRAP LIST OF MODELS AVAILABLE WHICH MAY BE LESS THAN REQUESTED FROM PARAM FILE.
for m in mods:
  modpath.model = m
  if os.path.isfile(modpath()) is True and m not in gmods:  
    gmods.append(m)

mods_notfound=[]
for m in mods:
  if m not in gmods: mods_notfound.append(m)

print('FOUND THESE MODELS ', gmods)
if mods_notfound == []: print('ALL MODELS FOUND')
if mods_notfound != []: print('MODELS NOT FOUND INCLUDE ', mods_notfound)

#########################################

regions_specs = {}
default_regions = []
exec(compile(open(sys.prefix + "/share/pmp/default_regions.py").read(),
             sys.prefix + "/share/pmp/default_regions.py", 'exec'))

doms = ['AllMW', 'AllM', 'NAMM', 'SAMM', 'NAFM', 'SAFM', 'ASM', 'AUSM']

mpi_stats_dic = {}

for mod in gmods:
    modpath.model = mod
    modelFile = modpath() 
    mpi_stats_dic[mod] = {}

    print("******************************************************************************************")
    print(modelFile)
    f = cdms2.open(modelFile)
    d_orig = f(var)

    annrange_mod, mpi_mod = mpd(d_orig)
    annrange_mod = annrange_mod.regrid(obsgrid)
    mpi_mod = mpi_mod.regrid(obsgrid)

    for dom in doms:

        mpi_stats_dic[mod][dom] = {}

        reg_sel = regions_specs[dom]['domain']

        mpi_obs_reg = mpi_obs(reg_sel)
        mpi_obs_reg_sd = float(statistics.std(mpi_obs_reg, axis='xy'))
        mpi_mod_reg = mpi_mod(reg_sel)

        cor = float(
            statistics.correlation(
                mpi_mod_reg,
                mpi_obs_reg,
                axis='xy'))
        rms = float(statistics.rms(mpi_mod_reg, mpi_obs_reg, axis='xy'))
        rmsn = rms / mpi_obs_reg_sd

#  DOMAIN SELECTED FROM GLOBAL ANNUAL RANGE FOR MODS AND OBS
        annrange_mod_dom = annrange_mod(reg_sel)
        annrange_obs_dom = annrange_obs(reg_sel)

# SKILL SCORES
#  HIT/(HIT + MISSED + FALSE ALARMS)
        hit, missed, falarm, score, hitmap, missmap, falarmmap = mpi_skill_scores(
            annrange_mod_dom, annrange_obs_dom, thr)

#  POPULATE DICTIONARY FOR JSON FILES
        mpi_stats_dic[mod][dom] = {}
        mpi_stats_dic[mod][dom]['cor'] = format(cor, sig_digits)
        mpi_stats_dic[mod][dom]['rmsn'] = format(rmsn, sig_digits)
        mpi_stats_dic[mod][dom]['threat_score'] = format(score, sig_digits)

# SAVE ANNRANGE AND HIT MISS AND FALSE ALARM FOR EACH MOD DOM
        fm = os.path.join(nout, '_'.join([mod, dom, 'monsoon-wang.nc']))
        g = cdms2.open(fm, 'w')
        g.write(annrange_mod_dom)
        g.write(hitmap, dtype=numpy.int32)
        g.write(missmap, dtype=numpy.int32)
        g.write(falarmmap, dtype=numpy.int32)
        g.close()
    f.close()

    print('DONE WITH ', mod)

#  OUTPUT METRICS TO JSON FILE
OUT = pcmdi_metrics.io.base.Base(os.path.abspath(jout), json_filename)

disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pmp",
        "disclaimer.txt")).read()

metrics_dictionary = collections.OrderedDict()
metrics_def_dictionary = collections.OrderedDict()
metrics_dictionary["DISCLAIMER"] = disclaimer
metrics_dictionary["REFERENCE"] = "The statistics in this file are based on Wang, B., Kim, HJ., Kikuchi, K. et al. " +\
                                   "Clim Dyn (2011) 37: 941. doi:10.1007/s00382-010-0877-0"
metrics_dictionary["Reference Data"] = obspath 
metrics_dictionary["RESULTS"] = mpi_stats_dic  # collections.OrderedDict()

OUT.var = var
OUT.write(
    metrics_dictionary,
    json_structure=["model", "domain", "statistic"],
    indent=4,
    separators=(
        ',',
        ': '))
