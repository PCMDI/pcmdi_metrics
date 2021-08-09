import json
import os

# Get CMEC environment variables
wkdir = os.getenv("CMEC_WK_DIR")
modeldata = os.getenv("CMEC_MODEL_DATA")
obsdata = os.getenv("CMEC_OBS_DATA")
config = os.getenv("CMEC_CONFIG_DIR")

# Get file lists
out_data = os.listdir(wkdir)
json_list = [f for f in out_data if f.endswith(".json")]
nc_list = [f for f in out_data if f.endswith(".nc")]
png_list = [f for f in out_data if f.endswith(".png")]

print(nc_list)
print(png_list)

# Get user settings for this run
with open(os.path.join(config,"cmec.json"),"r") as config:
	settings = json.load(config)["PMP/mjo"]

modnames = settings["modnames"]
nc_out = settings.get("nc_out",False)
plot = settings.get("plot",False)
mip = settings.get("mip","cmip5")
exp = settings.get("experiment","historical")
modnames.append("obs")

output = {
	"html": {},
	"metrics": {},
	"data": {},
	"plots": {},
	"parameter_file": "mjo_param.py",
	"provenance": {
		"environment": {},
		"modeldata": modeldata,
		"obsdata": obsdata,
		"log": None
		}
	}

# Get environment data from existing PMP JSON
with open(os.path.join(wkdir,json_list[0]),"r") as tmp_json:
	tmp = json.load(tmp_json)
envir = tmp["provenance"]["packages"]
envir.pop("PMPObs")
output["provenance"]["environment"] = envir

# Add general metrics JSON to output.json
name_seg = "_".join(["mjo_stat",mip,exp])
result_file = [f for f in json_list if (name_seg in f) and ("_cmec" not in f)][0]

desc = {
	"MJO statistics": {
		"filename": result_file,
		"long_name": "MJO model statistics",
		"description": "MJJASO and NDJFMA season MJO metrics"
	},
	"MJO statistics cmec": {
		"filename": result_file.split(".")[0]+"_cmec.json",
		"long_name": "MJO model statistics (CMEC format)",
		"description": "MJJASO and NDJFMA season MJO metrics in CMEC formatted JSON"
	}	
}

# Add optional netcdf and plot info
data = {}
plots = {}

for mod in modnames:
	for season in ["MJJASO","NDJFMA"]:
		if nc_out:
			result_file = [f for f in nc_list if ((mod in f) and (season in f))][0]
			tmp={
				"_".join([mod,season]): {
					"filename": result_file,
					"long_name": mod+" "+season+" power spectrum",
					"description": "Wavenumber-frequency power spectrum data for "+mod+" "+season
				}
			}
			data.update(tmp)
		if plot:
			result_file = [f for f in png_list if ((mod in f) and (season in f))][0]
			tmp = {
				"_".join([mod,season]): {
					"filename": result_file,
					"long_name": mod+" "+season+" power spectrum plot",
					"description": "Wavenumber frequency power spectrum figure for "+mod+" "+season
				}
			}
			plots.update(tmp)

output["metrics"].update(desc)
output["data"].update(data)
output["plots"].update(plots)

# Write output.json
fname = os.path.join(wkdir,"output.json")
with open(fname,"w") as output_json:
	json.dump(output,output_json,indent=4)
