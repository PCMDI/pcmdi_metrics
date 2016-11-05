
import cdms2,MV2
import sys, string
import os, vcs
from genutil import statistics
import cdutil
import regrid2
import json
from pcmdi_metrics.pcmdi.pmp_parser import *
import pcmdi_metrics
import collections

import argparse
from argparse import RawTextHelpFormatter

P = PMPParser()

P.add_argument("-mp", "--modpath",
                      type = str,
                      dest = 'modpath',
                      default = '',
                      help = "Explicit path to model monthly PR climatology")
P.add_argument("-o", "--obspath",
                      type = str,
                      dest = 'obspath',
                      default = '',
                      help = "Explicit path to obs monthly PR climatology")
P.add_argument("--outpj", "--outpathjsons",
                      type = str,
                      dest = 'outpathjsons',
                      default = '.',
                      help = "Output path for jsons")
P.add_argument("--outpd", "--outpathdata",
                      type = str,
                      dest = 'outpathdata',
                      default = '.',
                      help = "Output path for data")
P.add_argument("--mn", "--modname",
                      type = str,
                      dest = 'modname',
                      default = '',
                      help = "AMIP, historical or picontrol")
P.add_argument("--mns", "--modnames",
                      type = ast.literal_eval,
                      dest = 'modnames',
                      default = '',
                      help = "AMIP, historical or picontrol")
P.add_argument("-e", "--experiment",
                      type = str,
                      dest = 'experiment',
                      default = 'historical',
                      help = "AMIP, historical or picontrol")
P.add_argument("-c", "--MIP",
                      type = str,
                      dest = 'mip',
                      default = 'CMIP5',
                      help = "put options here")
P.add_argument("-d", "--domain",
                      type = str,
                      dest = 'domain',
                      default = 'global',
                      help = "put options here")
P.add_argument("-r", "--reference",
                      type = str,
                      dest = 'reference',
                      default = 'defaultReference',
                      help = "Reference against which the statistics are computed\n"
                             "- Available options: defaultReference (default), alternate1, alternate2")
P.add_argument("-p", "--parameters",
                      type = str,
                      dest = 'parameters',
                      default = '',
                      help = "")

args = P.parse_args(sys.argv[1:])
domain = args.domain
experiment = args.experiment
modpath = args.modpath
obspath = args.obspath 
outpathjsons = args.outpathjsons
outpathdata = args.outpathdata

mods = args.modnames

mip = 'CMIP5'
exp = 'historical'

#mods = ['ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM', 'CanCM4', 'CanESM2', 'CCSM4', 'CESM1-BGC', 'CESM1-CAM5', 'CESM1-FASTCHEM', 'CESM1-WACCM', 'CMCC-CESM', 'CMCC-CM', 'CMCC-CMS', 'CNRM-CM5-2', 'CNRM-CM5', 'CSIRO-Mk3-6-0', 'FGOALS-g2', 'FIO-ESM', 'GFDL-CM2p1', 'GFDL-CM3', 'GFDL-ESM2G', 'GFDL-ESM2M', 'GISS-E2-H', 'GISS-E2-H-CC', 'GISS-E2-R', 'GISS-E2-R-CC', 'HadCM3', 'HadGEM2-AO', 'HadGEM2-CC', 'HadGEM2-ES', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR', 'IPSL-CM5B-LR', 'MIROC4h', 'MIROC5', 'MIROC-ESM', 'MIROC-ESM-CHEM', 'MPI-ESM-LR', 'MPI-ESM-MR', 'MPI-ESM-P', 'MRI-CGCM3', 'MRI-ESM1', 'NorESM1-M', 'NorESM1-ME']

print 'mods is ', mods


# VAR IS FIXED TO BE PRECIP FOR CALCULATING MONSOON PRECIPITATION INDICES
# and threshold is set converted from mm/day to kgs-1m-2
var = 'pr'
thr = 2./86400.
sig_digits = '.3f'

#########################################
## PMP monthly default PR obs 

fcobs = obspath
fobs = cdms2.open(fcobs)
dobs_orig = fobs('pr')

obsgrid = dobs_orig.getGrid()

########################################

#  SEASONAL RANGE
def mpd(d):
 mjjas = (d[4] + d[5] + d[6] + d[7] + d[8])/5.
 ndjfm = (d[10] + d[11] + d[0] + d[1] + d[2])/5.
 ann = MV2.average(d,axis=0)

 annrange = MV2.subtract(mjjas,ndjfm)
 annrange0 = annrange*1.

 lats0 = annrange.getAxis(0)

 for l in range(len(lats0)):
   if lats0[l] <0:
    annrange[l,:] = -1*annrange[l,:]

 mpi = MV2.divide(annrange,ann)

 return annrange, mpi 

annrange_obs, mpi_obs = mpd(dobs_orig)

#print obs,' ', annrange_obs,' ', mpi_obs
#########################################
### SETUP WHERE TO OUTPUT RESULTING DATA (netcdf)
try:
  nout = outpathdata + '/' + exp + '_' + mip + '_wang-monsoon/' 
  os.mkdir(nout)
except:
  pass


modpathall = string.replace(modpath,'MODS','*')


lst = os.popen('ls ' + modpathall).readlines()

### CONFIRM DATA FOR MODS IS AVAIL AND REMOVE THOSE IT IS NOT

gmods = []  #  "Got" these MODS

for mod in mods:
 for l in lst:
   l1 = string.replace(modpath,'MODS',mod)
   if os.path.isfile(l1) is True:
     if mod not in gmods: gmods.append(mod) 
  
print 'gmods is ', gmods



#########################################

#doms = Monsoon_region.keys() 
regions_specs = {}
default_regions = []
execfile(sys.prefix + "/share/pmp/default_regions.py")


doms = ['AllMn','NAMn','SAMn','NAFn','SAFn','ASMn','AUSMn']

#w = sys.stdin.readline()

mpi_stats_dic = {}

for mod in gmods:
 l = string.replace(modpath,'MODS',mod)

 try:
  mpi_stats_dic[mod] = {}

  f = cdms2.open(l) 
  d_orig = f('pr')

  annrange_mod, mpi_mod = mpd(d_orig)
  annrange_mod = annrange_mod.regrid(obsgrid)
  mpi_mod = mpi_mod.regrid(obsgrid)

  for dom in doms:

   mpi_stats_dic[mod][dom] = {}

   reg_sel = regions_specs[dom]['domain']   

   mpi_obs_reg = mpi_obs(reg_sel)
   mpi_obs_reg_sd = float(statistics.std(mpi_obs_reg,axis='xy')) 
   mpi_mod_reg = mpi_mod(reg_sel)

   cor = float(statistics.correlation(mpi_mod_reg,mpi_obs_reg,axis='xy'))
   rms = float(statistics.rms(mpi_mod_reg,mpi_obs_reg,axis='xy'))
   rmsn = rms/mpi_obs_reg_sd 

   print mod,' ', dom, ' ', cor 

## SKILL SCORES
#  HIT/(HIT + MISSED + FALSE ALARMS)
   annrange_mod_dom = annrange_mod(reg_sel)
   annrange_obs_dom = annrange_obs(reg_sel)

   mt = MV2.where(MV2.greater(annrange_mod_dom,thr),1.,0.)
   ot = MV2.where(MV2.greater(annrange_obs_dom,thr),1.,0.)
 
   both = MV2.add(mt,ot) # HIT WILL MEAN 2, OTHERWISE 0 or 1
   hitmap = MV2.where(MV2.equal(both,2.),1.,0.) 
   hit = float(MV2.sum(hitmap))

   mt1 = MV2.where(MV2.greater(annrange_mod_dom,thr),10.,0.)
   both1 = MV2.add(mt1,ot) # 10 for MOD above THRESHOLD, OTHERWISE 0 
   missmap = MV2.where(MV2.equal(both1,1.),1.,0.)
   missed = float(MV2.sum(missmap))

   ot1 = MV2.where(MV2.greater(annrange_obs_dom,thr),10.,0.)
   both2 = MV2.add(mt,ot1) # 10 for OBS above THRESHOLD OTHERWISE 0 
   falarmmap = MV2.where(MV2.equal(both2,1.),1.,0.)
   falarm = float(MV2.sum(falarmmap))

   print mod,' hit missed falarm ', hit,' ', missed,' ', falarm

   score = hit/(hit+missed+falarm)

   mpi_stats_dic[mod][dom] = {}
   mpi_stats_dic[mod][dom]['cor']=  format(cor,sig_digits)  
   mpi_stats_dic[mod][dom]['rmsn']=  format(rmsn,sig_digits) 
   mpi_stats_dic[mod][dom]['threat_score'] = format(score,sig_digits) 

 except:
  print 'FAILED FOR MODEL ', mod 

 fm = nout + '/' + mod + '_' + dom + '_wang-monsoon.nc'
 g = cdms2.open(fm,'w+')
 annrange_mod_dom.id = 'annrange'
 hitmap.id = 'hit'
 missmap.id = 'miss'
 falarmmap.id = 'false_alarm'
 g.write(annrange_mod_dom)
 g.write(hitmap)
 g.write(missmap)
 g.write(falarmmap)
 g.close()

#w = sys.stdin.readline()

json_filename = 'MPI_' + mip + '_' + exp 
json.dump(mpi_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))

#OUT = pcmdi_metrics.io.base.Base(
#           parameters.metrics_output_path,
#           "%(var)%(level)_%(targetGridName)_" +
#           "%(regridTool)_%(regridMethod)_metrics")

OUT = pcmdi_metrics.io.base.Base('.',json_filename)

disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pmp",
        "disclaimer.txt")).read()

#metrics_dictionary = mpi_stats_dic

metrics_dictionary = collections.OrderedDict()
metrics_def_dictionary = collections.OrderedDict()
metrics_dictionary["DISCLAIMER"] = disclaimer
metrics_dictionary["RESULTS"] = mpi_stats_dic  #collections.OrderedDict()

#OUT.setTargetGrid(parameters.targetGrid, regridTool, regridMethod)
OUT.var = var
#OUT.realm = realm 
#OUT.table = table_realm
OUT.case_id = 'crap'  #case_id 

OUT.write(
                metrics_dictionary,
                json_structure=["model","domain"],
#               json_structure=["model", "reference", "rip", "region", "statistic", "season"],
                mode="w",
                indent=4,
                separators=(
                    ',',
                    ': '))





print 'done'
