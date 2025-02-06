import os
import re
import glob
import json
import time
import datetime
import xcdat as xc
import numpy as np
import shutil

import pcmdi_metrics
from pcmdi_metrics.io import (
        xcdat_open
)

from pcmdi_zppy_util import(
    derive_var,
)

model_name = 'obs.historical.%(model).00.Amon'
variables = 'pr,prw,psl,rlds,rldscs,rltcre,rstcre,rsus,rsuscs,rlus,rlut,rlutcs,rsds,rsdscs,rsdt,rsut,rsutcs,rtmt,sfcWind,tas,tauu,tauv,ts,ta-200,ta-850,ua-200,ua-850,va-200,va-850,zg-500'.split(",")
obs_sets = 'default'.split(",")
ts_dir_ref_source = '/lcrc/soft/climate/e3sm_diags_data/obs_for_e3sm_diags/time-series'

# variable map from observation to cmip
altobs_dic = { "pr"      : "PRECT",
               "sst"     : "ts",
               "sfcWind" : "si10",
               "taux"    : "tauu",
               "tauy"    : "tauv",
               "rltcre"  : "toa_cre_lw_mon",
               "rstcre"  : "toa_cre_sw_mon",
               "rtmt"    : "toa_net_all_mon"}

obs_dic = json.load(open('reference_alias.json'))

########################################
#first loop: link data to work directory
########################################
for i,vv in enumerate(variables):
  if "_" in vv or "-" in vv:
    varin = re.split("_|-", vv)[0]
  else:
    varin = vv
  if len(obs_sets) > 1 and len(obs_sets) == len(variables):
    obsid = obs_sets[i]
  else:
    obsid = obs_sets[0]

  obsname = obs_dic[varin][obsid]
  if "ceres_ebaf" in obsname:
    obsstr = obsname.replace("_","*").replace("-","*")
  else:
    obsstr = obsname

  fpaths = sorted(glob.glob(os.path.join(ts_dir_ref_source,obsstr,varin+"_*.nc")))
  if (len(fpaths) > 0) and (os.path.exists(fpaths[0])):
     template = fpaths[0].split("/")[-1]
     yms = template.split("_")[-2][0:6]
     yme = template.split("_")[-1][0:6]
     obs = obsname.replace(".","_")
     out = os.path.join(
          'obs_link',
          '{}.{}.{}-{}.nc'.format(
           model_name.replace('%(model)',obs),
           varin,yms,yme)
     )
     if not os.path.exists(out):
        os.symlink(fpaths[0],out)
  elif varin in altobs_dic.keys():
    varin1 = altobs_dic[varin]
    fpaths = sorted(glob.glob(
        os.path.join(ts_dir_ref_source,obsstr,varin1+"_*.nc"))
    )
    if (len(fpaths) > 0) and (os.path.exists(fpaths[0])):
       template = fpaths[0].split("/")[-1]
       yms = template.split("_")[-2][0:6]
       yme = template.split("_")[-1][0:6]
       obs = obsname.replace(".","_")
       out = os.path.join(
          'obs_link',
          '{}.{}.{}-{}.nc'.format(
           model_name.replace('%(model)',obs),
           varin,yms,yme)
       )
       ds = xcdat_open(fpaths[0])
       ds = ds.rename(name_dict={varin1:varin})
       ds.to_netcdf(out)

#####################################################################
#second loop: check and process derived quantities
#note: these quantities are possibly not included as default in cmip
#####################################################################
for vv in enumerate(variables):
    if vv in ['rltcre','rstcre']:
       fpaths = sorted(glob.glob(
          os.path.join('obs_link',"*"+vv+"_*.nc"))
       )
       if (len(fpaths) < 1) and (vv == 'rstcre'):
          derive_var('obs_link',vv,{'rsutcs':1,'rsut':-1},model_name)
       elif (len(fpaths) < 1) and (vv == 'rltcre'):
          derive_var('obs_link',vv,{'rlutcs':1,'rlut':-1},model_name)

