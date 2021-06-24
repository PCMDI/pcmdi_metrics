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

