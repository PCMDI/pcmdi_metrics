"""
monsoon_wang_output.py
Create and populate the output.json metadata file that
documents the cmec-driver pipeline outputs for the
Monsoon (Wang) metrics.
"""
import glob
import json
import os

# Get cmec-driver environment variables
wkdir = os.getenv("CMEC_WK_DIR")
modeldata = os.getenv("CMEC_MODEL_DATA")
obsdata = os.getenv("CMEC_OBS_DATA")
config = os.getenv("CMEC_CONFIG_DIR")

# Read config file to get some case information
with open(os.path.join(config, "cmec.json"), "r") as config:
    settings = json.load(config)["PMP/monsoon_wang"]

modnames = settings["modnames"]
mip = settings.get("mip", "cmip5")
exp = settings.get("experiment", "historical")
outnamejson = settings.get("outnamejson", "monsoon_wang.json")

# Initialize output.json data structure
output = {
    "html": {},
    "metrics": {},
    "data": {},
    "plots": {},
    "parameter_file": "monsoon_wang_param.py",
    "provenance": {
        "environment": {},
        "modeldata": modeldata,
        "obsdata": obsdata,
        "log": None,
    },
}

# Read an existing metrics json to get environment info
json_list = glob.glob(os.path.join(wkdir, "*.json"))
with open(json_list[0], "r") as tmp_json:
    tmp = json.load(tmp_json)
envir = tmp["provenance"]["packages"]
envir.pop("PMPObs")
output["provenance"]["environment"] = envir

# Find and describe results files
desc = {
    "monsoon metrics": {
        "filename": outnamejson,
        "long_name": "Monsoon (Wang) metrics",
        "description": "Correlation, RMSN, and threat score for monsoon regions",
    },
    "monsoon metrics cmec": {
        "filename": outnamejson.replace(".json", "_cmec.json"),
        "long_name": "Monsoon (Wang) metrics (CMEC format)",
        "description": "Correlation, RMSN, and threat score for monsoon regions in CMEC formatted JSON",
    },
}

datadir = "_".join([exp, mip.upper(), "wang-monsoon"])
# Look through results for single model to get full list of regions
datalist = glob.glob(os.path.join(wkdir, datadir, "*" + modnames[0] + "*"))
regions = []
for item in datalist:
    base = os.path.basename(item)
    region = base.split("_")[1]
    regions.append(region)

data = {}
for mod in modnames:
    for region in regions:
        result_file = "_".join([mod, region, "wang-monsoon.nc"])
        tmp = {
            " ".join([mod, region]): {
                "filename": os.path.join(datadir, result_file),
                "long_name": mod + " spatial results",
                "description": "Hit, miss, and false alarms for "
                + mod
                + " in region "
                + region
                + ".",
            }
        }
        data.update(tmp)

# Populate output dictionary and write to file.
output["metrics"].update(desc)
output["data"].update(data)

fname = os.path.join(wkdir, "output.json")
with open(fname, "w") as output_json:
    json.dump(output, output_json, indent=4)
