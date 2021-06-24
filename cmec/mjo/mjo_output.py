import json
import os

wkdir = os.getenv("CMEC_WK_DIR")
modeldata = os.getenv("CMEC_MODEL_DATA")
obsdata = os.getenv("CMEC_OBS_DATA")
out_data = os.listdir(wkdir)
json_data = [f for f in out_data where ".json" in f]
log_path = [f for f in out_data where ".log" in f][0]
fname = os.path.join(wkdir,"output.json")

output = {
	"html": {}
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

desc = {
	"model statistics": {
		"filename": "mjo_stat_*.json",
		"long_name": "MJO model statistics",
		"description": "MJJASO and NDJFMA season MJO metrics for single model"
	},
	"obs statistics": {
		"filename": "mjo_stat_cmip6_historical_da_atm_obs_GPCP-1-3_1985-2004.json",
		"long_name": "OBS statistics",
		"description": "MJJASO and NDJFMA season MJO metrics for observational data"
	},
	"all models": {
		"filename": "mjo_stat_cmip6_historical_da_atm_allModels_allRuns_1985-2004.json",
		"long_name": "",
		"description": "MJJASO and NDJFMA season MJO metrics for all models and observations"
	}
}

output["metrics"].update(desc)

with open(os.path.join(wkdir,"output.json"),"w") as output_json:
	json.dumps(output_json,output,indent=4)
