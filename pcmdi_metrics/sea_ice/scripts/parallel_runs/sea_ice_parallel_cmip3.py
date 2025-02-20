# This runs over CMIP3. I generated the grid area files
# manually with cdo.

import glob

from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPParser
from pcmdi_metrics.misc.scripts import parallel_submitter
from pcmdi_metrics.precip_variability.lib import AddParserArgument

num_cpus = 18

# Read parameters
P = PMPParser()
P = AddParserArgument(P)
param = P.get_parameter()
# mip = "cmip6"
mip = "cmip3"
exp = "historical"
var = param.var
mod = None
frq = "mon"


cmd_list = []
log_list = []
area_var = "cell_area"

flist = glob.glob("/home/ordonez4/pmp_param/sea_ice/cmip_parallel/symlinks/*")

mod_list = []
for item in flist:
    model = item.split(".")[1]
    if model not in mod_list:
        mod_list.append(model)

for model in mod_list:
    # dir_template="/p/cscratch/durack1/xmls/20c3m/seaIce/mon/sic/"
    dir_template = "/home/ordonez4/pmp_param/sea_ice/cmip_parallel/symlinks"
    file_template = "cmip3.%(model).20c3m.%(realization).mo.sic.ver-2.xml"
    area_path = "/work/ordonez4/sea_ice/area/%(model)/area_%(model).nc"

    if model in ["ingv-echam4", "ipsl-cm4"]:
        # No sea ice units adjust
        paramfile = "parameter_file_cmip3.py"
    else:
        # Need modunitsadjust
        paramfile = "parameter_file_cmip3_adjust.py"

    cmd_list.append(
        "./sea_ice_driver.py -p "
        + paramfile
        + " --case_id "
        + model
        + " --test_data_set "
        + model
        + " --test_data_path "
        + dir_template
        + " --filename_template "
        + file_template
        + " --area_template "
        + area_path
        + " --area_var "
        + area_var
    )
    log_list.append("log_" + mip + "_" + var + "_" + model)
for item in cmd_list:
    print(item)


parallel_submitter(
    cmd_list,
    log_dir="./log_cmip3",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
