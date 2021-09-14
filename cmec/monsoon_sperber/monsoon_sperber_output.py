"""
monsoon_sperber_output.py
Create and populate the output.json metadata file that
documents the cmec-driver pipeline outputs for the
Monsoon (Sperber) metrics.
"""
import json
import os

# Get cmec-driver environment variables
wkdir = os.getenv("CMEC_WK_DIR")
modeldata = os.getenv("CMEC_MODEL_DATA")
obsdata = os.getenv("CMEC_OBS_DATA")
config = os.getenv("CMEC_CONFIG_DIR")

# Sort files in output folder
out_data = os.listdir(wkdir)
json_list = [f for f in out_data if f.endswith(".json")]
nc_list = [f for f in out_data if f.endswith(".nc")]
png_list = [f for f in out_data if f.endswith(".png")]
fname = os.path.join(wkdir,"output.json")

# Read config file to get some case information
with open(os.path.join(config,"cmec.json"),"r") as config:
    settings = json.load(config)["PMP/monsoon_sperber"]

modnames = settings["modnames"]
nc_out = settings.get("nc_out",False)
plot = settings.get("plot",False)
mip = settings.get("mip","cmip5")
exp = settings.get("experiment","historical")
ref_data_name = settings.get("reference_data_name","")
includeOBS = settings.get("includeOBS",False)
if includeOBS:
    modnames.append("obs")

# Initialize output.json data structure
output = {
    "html": {},
    "metrics": {},
    "data": {},
    "plots": {},
    "parameter_file": "monsoon_sperber_param.py",
    "provenance": {
        "environment": {},
        "modeldata": modeldata,
        "obsdata": obsdata,
        "log": None
        }
    }

# Read an existing metrics json to get environment info
with open(os.path.join(wkdir,json_list[0]),"r") as tmp_json:
    tmp = json.load(tmp_json)
envir = tmp["provenance"]["packages"]
envir.pop("PMPObs")
output["provenance"]["environment"] = envir

# Find and describe results files
name_seg = "_".join(["monsoon_sperber_stat",mip,exp])
result_file = [f for f in json_list if (name_seg in f) and ("_cmec" not in f)][0]

desc = {
    "monsoon metrics": {
        "filename": result_file,
        "long_name": "Monsoon (Sperber) metrics",
        "description": "Decay index, duration, onset_index, and slope for monsoon regions"
    },
    "monsoon metrics cmec": {
        "filename": result_file.split(".")[0]+"_cmec.json",
        "long_name": "Monsoon (Sperber) metrics (CMEC format)",
        "description": "Decay index, duration, onset_index, and slope for monsoon regions in CMEC formatted JSON"
    }
}

data = {}
plots = {}

for mod in modnames:
    if nc_out:
        result_file = [f for f in nc_list if mod in f][0]
        tmp={
            "_".join([mod,mip]): {
                "filename": result_file,
                "long_name": mod+" time series",
                "description": "Individual year time series for each monsoon domain for "+mod
            }
        }
        data.update(tmp)
    if plot:
        result_file = [f for f in png_list if mod in f][0]
        tmp = {
            "_".join([mod,mip]): {
                "filename": result_file,
                "long_name": mod+" pentad time series",
                "description": "Precipitation pentad time series plot for "+mod
            }
        }
        plots.update(tmp)

# Populate output dictionary and write to file.
output["metrics"].update(desc)
output["data"].update(data)
output["plots"].update(plots)

with open(fname,"w") as output_json:
    json.dump(output,output_json,indent=4)
