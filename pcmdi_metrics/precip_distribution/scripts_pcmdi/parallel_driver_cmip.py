import glob
import os

import xsearch as xs

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.misc.scripts import parallel_submitter
from pcmdi_metrics.precip_distribution.lib import AddParserArgument

num_cpus = 20

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
exp = param.exp
var = param.var
frq = param.frq
res = param.res
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
        "python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_"
        + mip
        + ".py --modpath "
        + path
        + " --mod *"
    )
    log_list.append(
        "log_"
        + mip
        + "_"
        + var
        + "_"
        + dat
        + "_"
        + str(round(360 / res[0]))
        + "x"
        + str(round(180 / res[1]))
    )

parallel_submitter(
    cmd_list,
    log_dir="./log",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
