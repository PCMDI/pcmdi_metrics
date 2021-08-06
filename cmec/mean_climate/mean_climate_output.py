"""
mean_climate_output.py
Create and populate the output.json metadata file that
documents the cmec-driver pipeline outputs for the
Mean Climate metrics.
"""
import json
import os

wkdir = os.getenv("CMEC_WK_DIR")
modeldata = os.getenv("CMEC_MODEL_DATA")
obsdata = os.getenv("CMEC_OBS_DATA")
out_data = os.listdir(wkdir)
json_data = [f for f in out_data if f.endswith(".json")]
log_path = [f for f in out_data if ".log" in f][0]
fname = os.path.join(wkdir,"output.json")

output = {
	"html": {},
	"metrics": {},
	"data": {},
	"plots": {},
	"provenance": {
		"environment": {},
		"modeldata": modeldata,
		"obsdata": obsdata,
		"log": log_path
		}
	}

with open(json_data[0],"r") as tmp_json:
	tmp = json.load(tmp_json)
envir = tmp["provenance"]["packages"]
envir.pop("PMPObs")
output["provenance"]["environment"] = envir

data = {}

# interpolated fields
int_out = os.path.join(wkdir,"interpolated_output")
int_dict = {}
if os.path.exists(int_out):
	int_fields = os.listdir(int_out)
	for item in int_fields:
		int_reg = item.split(".")[0]
		int_dict[int_reg] = {
			"filename": int_out + "/" + item,
			"long_name": int_reg + " interpolated output",
			"description": "Interpolated test clims for region " + int_reg
		}
data.update(int_dict)

# AC files
# TODO: Need to pair files with model name and variable
ac_out = os.path.join(wkdir,"AC")
ac_data = {}
if os.path.exists(ac_out):
	ac_list = sorted([
		f for f in os.listdir(ac_out) if any(s in f for s in [".SON.",".DJf.",".MAM.",".JJA.",".AC."])])
	for item in ac_list:
		print(item)
		season = item.split(".")[-3]
		#model = item_split[2]
		#var = item_split[5]
		#season = item_split[-3]
		season_desc = "Seasonal"
		if season == "AC":
			season_desc = "Annual"
		ac_data[item]={
			"filename": "AC/" + item,
			"long_name":  " climatology",
			"description": season_desc + " climatology for model"
		}
data.update(ac_data)

# JSON results
cmec_list = [f for f in json_data if f.endswith("_cmec.json")]
pmp_list = [f for f in json_data if f not in cmec_list]

metrics = {}
for item in pmp_list:
	var = item.split("_")[0]
	metrics[var]={"filename": item,
		"long_name": var + " metrics",
		"description": "Metrics results for variable " + var}
for item in cmec_list:
	var = item.split("_")[0]
	metrics[var+"_cmec"]={"filename": item,
		"long_name": var + " CMEC metrics",
		"description": "CMEC formatted metrics results for variable " + var}

output["data"].update(data)
output["metrics"].update(metrics)

with open(fname,"w") as output_json:
	json.dump(output,output_json,indent=4)
