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
    pathDict = xs.findPaths(
        exp, var, frq, mip_era=mip.upper(), model=mod
    )
# Get which area variable needed
print("Reading external variable attribute")
#pathDB =  xs.addAttribute(pathDict, 'external_variables')
areacello = xs.findPaths("historical","areacello","fx",cmipTable="Ofx")
areacella = xs.findPaths("historical","areacella","fx")
path_list = sorted(list(pathDict.keys()))
print("Number of datasets:", len(path_list))

cmd_list = []
log_list = []
model_list = xs.getGroupValues(pathDict,'model')
print(model_list)
for model in model_list[7:11]:
    path = xs.getValuesForFacet(pathDict,'model',model)[0]
    basename = os.path.basename(glob.glob(os.path.join(path,"*"))[0])

    dir_template = "/".join(path.split("/")[0:9]) + "/%(realization)/" + "/".join(path.split("/")[10:13]) +"/*/"
    file_template = "_".join(basename.split("_")[0:4]) + "_%(realization)_" + basename.split("_")[5] + "_*-*.nc"

    single=xs.getValuesForFacet(pathDict,'model',model)
    empty = [{} for item in single]
    d1=zip(single,empty)
    db=dict(d1)
    db = xs.addAttribute(db, 'external_variables')

    #area_var = pathDB[path]["external_variables"]
    try:
        area_var = db[single[0]]['external_variables']
    except:
        print("No external variables")
        print("Guessing areacello")
        area_var = 'areacello'
    if area_var == "areacello": # Same for all realizations
        try:
            apath = xs.getValuesForFacet(areacello,'model',model)
            abase = os.path.basename(glob.glob(os.path.join(apath[0],'*'))[0])
            area_path = os.path.join(apath[0],abase)
        except:
            print("No areacello for model ",model)
            print(apath)
            continue
        ## Make filename template 
        #area_path = "/".join(apath[0].split("/")[0:9]) + "/%(realization)/" + "/".join(apath[0].split("/")[10:])
    elif area_var == "areacella": # Different for each realization
        apath = xs.getValuesForFacet(areacella,'model',model)
        abase = os.path.basename(glob.glob(os.path.join(apath[0],'*'))[0])
        abase = "_".join(abase.split("_")[0:4]) + "_%(realization)_" + "_".join(abase.split("_")[5:])
        # Make filename template 
        area_dir = "/".join(apath[0].split("/")[0:9]) + "/%(realization)/" + "/".join(apath[0].split("/")[10:])
        area_path = os.path.join(area_dir,abase)
    else:
        "Area variable not found."
        continue

    cmd_list.append(
        "python -u ice_driver.py -p parameter_file.py --case_id " + model + \
        " --test_data_set '" + model + "' --test_data_path '" + \
        dir_template + "' --filename_template '" + file_template + \
        "' --area_template '" + area_path + "' --area_var " + area_var
    )
    #log_list.append("log_" + mip + "_" + var + "_" + mymodel)

print(cmd_list)
#parallel_submitter(
#    cmd_list,
#    log_dir="./log",
#    logfilename_list=log_list,
#    num_workers=num_cpus,
#)
