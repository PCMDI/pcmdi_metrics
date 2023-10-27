import glob
import os

import xsearch as xs

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.misc.scripts import parallel_submitter
from pcmdi_metrics.precip_variability.lib import AddParserArgument

num_cpus = 20

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
exp = param.exp
var = param.var
frq = param.frq
mod = param.mod

if mod is None:
    pathDict = xs.findPaths(exp, var, frq, cmipTable=frq, mip_era=mip.upper())
else:
    pathDict = xs.findPaths(
        exp, var, frq, cmipTable=frq, mip_era=mip.upper(), model=mod
    )
path_list = sorted(list(pathDict.keys()))
print("Number of datasets:", len(path_list))
print(path_list)

cmd_list = []
log_list = []
for path in path_list:
    fl = sorted(glob.glob(os.path.join(path, "*")))
    model = fl[0].split("/")[-1].split("_")[2]
    ens = fl[0].split("/")[-1].split("_")[4]
    dat = model + "." + ens
    cmd_list.append(
        "python -u ../variability_across_timescales_PS_driver.py -p ../param/variability_across_timescales_PS_3hr_params_"
        + mip
        + ".py --modpath "
        + path
        + " --mod *"
    )
    log_list.append("log_" + mip + "_" + var + "_" + dat)

parallel_submitter(
    cmd_list,
    log_dir="./log",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
