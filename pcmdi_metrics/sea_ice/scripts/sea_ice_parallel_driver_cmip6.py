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
mip = "cmip6"
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
    "historical", "areacello", "fx", cmipTable="Ofx", deduplicate=False
)
areacella = xs.findPaths("historical", "areacella", "fx", deduplicate=False)
path_list = sorted(list(pathDict.keys()))
print("Number of datasets:", len(path_list))

cmd_list = []
log_list = []
model_list = xs.getGroupValues(pathDict, "model")
# Drop models with known issues that we're going to do by hand
model_list = [x for x in model_list if "FGOALS" not in x]
model_list = [x for x in model_list if x != "EC-Earth3"]
print(model_list)
for model in model_list:
    skip = False
    path = xs.getValuesForFacet(pathDict, "model", model)[0]
    basename = os.path.basename(glob.glob(os.path.join(path, "*"))[0])

    dir_template = (
        "/".join(path.split("/")[0:9])
        + "/%(realization)/"
        + "/".join(path.split("/")[10:13])
        # + "/"+ path.split("/")[-2] + "/"
        + "/*/"
    )
    file_template = (
        "_".join(basename.split("_")[0:4])
        + "_%(realization)_"
        + basename.split("_")[5]
        + "_*-*.nc"
    )

    grid = path.split("/")[-3]

    single = xs.getValuesForFacet(pathDict, "model", model)
    empty = [{} for item in single]
    d1 = zip(single, empty)
    db = dict(d1)
    db = xs.addAttribute(db, "external_variables")
    try:
        area_var = db[single[0]]["external_variables"]
    except KeyError:
        print("No external variables")
        print("Guessing areacello")
        area_var = "areacello"

    if area_var == "areacello":  # Same for all realizations
        apath = xs.getValuesForFacet(areacello, "model", model)
        if len(apath) > 0:
            apath = [tmp for tmp in apath if tmp.split("/")[-3] == grid]
            if len(apath) > 0:
                abase = os.path.basename(glob.glob(os.path.join(apath[0], "*"))[-1])
                area_path = os.path.join(apath[0], abase)
            else:
                print("wrong grid", model)
                skip = True
        else:
            print("No values for facet", model)
            skip = True
    elif area_var == "areacella":  # Different for each realization
        apath = xs.getValuesForFacet(areacella, "model", model)
        apath = [tmp for tmp in apath if tmp.split("/")[-3] == grid]
        abase = os.path.basename(glob.glob(os.path.join(apath[0], "*"))[-1])
        abase = (
            "_".join(abase.split("_")[0:4])
            + "_%(realization)_"
            + "_".join(abase.split("_")[5:])
        )
        # Make filename template
        area_dir = (
            "/".join(apath[0].split("/")[0:9])
            + "/%(realization)/"
            + "/".join(apath[0].split("/")[10:])
        )
        area_path = os.path.join(area_dir, abase)
    else:
        print("Area variable not found for", model)
        skip = True

    if not skip:
        cmd_list.append(
            "./sea_ice_driver.py -p parameter_file.py --case_id "
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
print(cmd_list)


parallel_submitter(
    cmd_list,
    log_dir="./log_cmip6",
    logfilename_list=log_list,
    num_workers=num_cpus,
)
