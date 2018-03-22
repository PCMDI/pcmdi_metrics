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
import ast
import glob

###########
# SAMPLE COMMAND LINE EXECUTION USING ARGUMENTS BELOW
# python -i mpi_compute.py -mp
# /work/gleckler1/processed_data/cmip5clims_metrics_package-historical/pr_MODS_Amon_historical_r1i1p1_198001-200512-clim.nc
# -op
# /work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc
# --mns "['NorESM1-ME','MRI-CGCM3']" --outpd
# /work/gleckler1/processed_data/wang_monsoon --outpj
# /work/gleckler1/processed_data/metrics_package/metrics_results/wang_monsoon

##########


P = PMPParser()

P.use("--modpath")
P.use("--modnames")
P.use("--results_dir")
P.use("--reference_data_path")

P.add_argument("--outpj", "--outpathjsons",
               type=str,
               dest='outpathjsons',
               default='.',
               help="Output path for jsons")
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


# args = P.parse_args(sys.argv[1:])
args = P.get_parameter()
modpath = args.modpath
outpathjsons = args.outpathjsons
outpathdata = args.results_dir
mods = args.modnames

json_filename = args.jsonname

if json_filename == 'CMIP_MME':
    json_filename = '/MPI_' + args.mip + '_' + args.experiment

if args.mip == 'CMIP5' and args.experiment == 'historical' and mods is None:
    mods = [
        'ACCESS1-0',
        'ACCESS1-3',
        'bcc-csm1-1',
        'bcc-csm1-1-m',
        'BNU-ESM',
        'CanCM4',
        'CanESM2',
        'CCSM4',
        'CESM1-BGC',
        'CESM1-CAM5',
        'CESM1-FASTCHEM',
        'CESM1-WACCM',
        'CMCC-CESM',
        'CMCC-CM',
        'CMCC-CMS',
        'CNRM-CM5-2',
        'CNRM-CM5',
        'CSIRO-Mk3-6-0',
        'FGOALS-g2',
        'FIO-ESM',
        'GFDL-CM2p1',
        'GFDL-CM3',
        'GFDL-ESM2G',
        'GFDL-ESM2M',
        'GISS-E2-H',
        'GISS-E2-H-CC',
        'GISS-E2-R',
        'GISS-E2-R-CC',
        'HadCM3',
        'HadGEM2-AO',
        'HadGEM2-CC',
        'HadGEM2-ES',
        'inmcm4',
        'IPSL-CM5A-LR',
        'IPSL-CM5A-MR',
        'IPSL-CM5B-LR',
        'MIROC4h',
        'MIROC5',
        'MIROC-ESM',
        'MIROC-ESM-CHEM',
        'MPI-ESM-LR',
        'MPI-ESM-MR',
        'MPI-ESM-P',
        'MRI-CGCM3',
        'MRI-ESM1',
        'NorESM1-M',
        'NorESM1-ME']


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
nout = os.path.join(outpathdata, "_".join(
    [args.experiment, args.mip, 'wang-monsoon']))
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

modpathall = modpath.replace('MODS', '*')
lst = glob.glob(modpathall)
# CONFIRM DATA FOR MODS IS AVAIL AND REMOVE THOSE IT IS NOT

gmods = []  # "Got" these MODS
print("MODS:", mods)
print("LST:", lst)
for mod in mods:
    for l in lst:
        l1 = modpath.replace('MODS', mod)
        print("L!:", l1)
        if os.path.isfile(l1) is True:
            if mod not in gmods:
                gmods.append(mod)

if args.experiment == 'historical' and mods is None:
    gmods = [
        'ACCESS1-0',
        'ACCESS1-3',
        'bcc-csm1-1',
        'bcc-csm1-1-m',
        'BNU-ESM',
        'CanCM4',
        'CanESM2',
        'CCSM4',
        'CESM1-BGC',
        'CESM1-CAM5',
        'CESM1-FASTCHEM',
        'CESM1-WACCM',
        'CMCC-CESM',
        'CMCC-CM',
        'CMCC-CMS',
        'CNRM-CM5-2',
        'CNRM-CM5',
        'CSIRO-Mk3-6-0',
        'FGOALS-g2',
        'FIO-ESM',
        'GFDL-CM2p1',
        'GFDL-CM3',
        'GFDL-ESM2G',
        'GFDL-ESM2M',
        'GISS-E2-H',
        'GISS-E2-H-CC',
        'GISS-E2-R',
        'GISS-E2-R-CC',
        'HadCM3',
        'HadGEM2-AO',
        'HadGEM2-CC',
        'HadGEM2-ES',
        'inmcm4',
        'IPSL-CM5A-LR',
        'IPSL-CM5A-MR',
        'IPSL-CM5B-LR',
        'MIROC4h',
        'MIROC5',
        'MIROC-ESM',
        'MIROC-ESM-CHEM',
        'MPI-ESM-LR',
        'MPI-ESM-MR',
        'MPI-ESM-P',
        'MRI-CGCM3',
        'MRI-ESM1',
        'NorESM1-M',
        'NorESM1-ME']


#########################################

regions_specs = {}
default_regions = []
exec(compile(open(sys.prefix + "/share/pmp/default_regions.py").read(),
             sys.prefix + "/share/pmp/default_regions.py", 'exec'))

doms = ['AllMW', 'AllM', 'NAMM', 'SAMM', 'NAFM', 'SAFM', 'ASM', 'AUSM']

mpi_stats_dic = {}
print("GMODS:", gmods)
for mod in gmods:
    modelFile = modpath.replace('MODS', mod)

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
        fm = os.path.join(nout, '_'.join([mod, dom, 'wang-monsoon.nc']))
        g = cdms2.open(fm, 'w')
        g.write(annrange_mod_dom)
        g.write(hitmap, dtype=numpy.int32)
        g.write(missmap, dtype=numpy.int32)
        g.write(falarmmap, dtype=numpy.int32)
        g.close()
    f.close()


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
metrics_dictionary["RESULTS"] = mpi_stats_dic  # collections.OrderedDict()

OUT.var = var
OUT.write(
    metrics_dictionary,
    json_structure=["model", "domain", "statistic"],
    indent=4,
    separators=(
        ',',
        ': '))
