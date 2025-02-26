# This is set up to search for land/sea masks in CMIP5

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
# mip = "cmip6"
mip = "cmip5"
exp = "historical"
var = param.var
mod = None
frq = "mon"

if mod is None:
    pathDict = xs.findPaths(exp, var, frq, mip_era=mip.upper())
else:
    pathDict = xs.findPaths(exp, var, frq, mip_era=mip.upper(), model=mod)
# Get which area variable needed
print("Reading external variable attribute")
# deduplicate because some models, like CESM2, need to grab the gn rather than gr area file
areacello = xs.findPaths(
    "historical", "areacello", "fx", mip_era="CMIP5", deduplicate=False
)
sftof = xs.findPaths("historical", "sftof", "fx", mip_era="CMIP5")
path_list = sorted(list(pathDict.keys()))
print("Number of datasets:", len(path_list))

cmd_list = []
log_list = []
model_list = xs.getGroupValues(pathDict, "model")
area_var = "areacello"
print(model_list)
for model in model_list:
    skip = False
    path = xs.getValuesForFacet(pathDict, "model", model)[0]
    basename = os.path.basename(glob.glob(os.path.join(path, "*"))[0])

    # TODO: Fix how the path gets sliced and indexed
    # because I don't think it's consistent model-to-model
    # for cmip5
    dir_template = (
        "/".join(path.split("/")[:-4])
        + "/%(realization)/"
        + "/".join(path.split("/")[-3:-1])
        + "/"
        #    + "/*/"
    )
    file_template = (
        "_".join(basename.split("_")[0:4])
        + "_%(realization)"
        #        + "_"+basename.split("_")[5]
        + "_*-*.nc"
    )

    single = xs.getValuesForFacet(pathDict, "model", model)
    empty = [{} for item in single]
    d1 = zip(single, empty)
    db = dict(d1)

    try:
        apath = xs.getValuesForFacet(areacello, "model", model)[0]
        print(apath)
        area_path = glob.glob(apath + "/*nc")
        if len(area_path) < 1:
            area_path = glob.glob(apath + "/*/*nc")
            if len(area_path) < 1:
                skip = True
                print("area path not found", model)
                print(area_path)
                print(path)
            else:
                area_path = area_path[0]
        else:
            area_path = area_path[0]
    except Exception:
        print("area path not found", model)
        print(dir_template)
        skip = True

    # get sftof
    gen_sft = True
    try:
        sfpath = xs.getValuesForFacet(sftof, "model", model)
        sf_path = glob.glob(os.path.join(sfpath[0], "*"))
        if len(sf_path) > 0:
            sf_path = sf_path[-1]
            gen_sft = False
        else:
            print("No sftof values for facet", model)
            print(path)
    except Exception:
        pass

    if not skip:
        if gen_sft:
            cmd_list.append(
                "./sea_ice_driver.py -p parameter_file_cmip5.py --case_id "
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
                + " --generate_mask"
            )
        else:
            cmd_list.append(
                "./sea_ice_driver.py -p parameter_file_cmip5.py --case_id "
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
                + " --sft_filename_template "
                + sf_path
            )
        log_list.append("log_" + mip + "_" + var + "_" + model)
print(cmd_list)
for item in cmd_list:
    print(item)


parallel_submitter(
    cmd_list,
    log_dir="./log_cmip5_sft",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
