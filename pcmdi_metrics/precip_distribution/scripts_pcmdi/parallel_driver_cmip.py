import glob
import os

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.misc.scripts import parallel_submitter
from pcmdi_metrics.precip_distribution.lib import AddParserArgument

num_cpus = 20

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
mip = param.mip
modpath = param.modpath
res = param.res
mod = param.mod
if mod is None:
    mod = "*"

file_list = sorted(glob.glob(os.path.join(modpath, "*" + mod + "*")))

cmd_list = []
log_list = []
for ifl, fl in enumerate(file_list):
    file = fl.split("/")[-1]
    cmd_list.append(
        "python -u ../precip_distribution_driver.py -p ../param/precip_distribution_params_"
        + mip
        + ".py --mod "
        + file
    )
    log_list.append(
        "log_" + file + "_" + str(round(360 / res[0])) + "x" + str(round(180 / res[1]))
    )
    print(cmd_list[ifl])
print("Number of data: " + str(len(cmd_list)))

parallel_submitter(
    cmd_list,
    log_dir="./log",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
