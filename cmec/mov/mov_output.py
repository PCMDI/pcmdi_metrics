import json
import os

wkdir = os.getenv("CMEC_WK_DIR")
modeldata = os.getenv("CMEC_MODEL_DATA")
obsdata = os.getenv("CMEC_OBS_DATA")
config = os.getenv("CMEC_CONFIG_DIR")
out_data = os.listdir(wkdir)
json_list = [f for f in out_data if f.endswith(".json")]
nc_list = [f for f in out_data if f.endswith(".nc")]
png_list = [f for f in out_data if f.endswith(".png")]
fname = os.path.join(wkdir,"output.json")

with open(os.path.join(config,"cmec.json"),"r") as config:
	settings = json.load(config)["PMP/variability_modes"]

modnames = settings["modnames"]
nc_out_model = settings.get("nc_out",True)
nc_out_obs = settings.get("nc_out_obs",True)
plot_model = settings.get("plot",True)
plot_obs = settings.get("plot_obs",True)
mip = settings.get("mip","cmip5")
exp = settings.get("experiment","historical")
seasons = settings.get("seasons",None)
varModel = settings.get("varModel",None)
varObs = settings.get("varObs",None)
variability_mode = settings.get("variability_mode","").upper()

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

with open(json_list[0],"r") as tmp_json:
	tmp = json.load(tmp_json)
envir = tmp["provenance"]["packages"]
envir.pop("PMPObs")
output["provenance"]["environment"] = envir

name_seg = "_".join(["var_mode",variability_mode])
result_file = [f for f in json_list if (name_seg in f) and ("_cmec" not in f)][0]

desc = {
	"Modes of Variability metrics": {
		"filename": result_file,
		"long_name": "",
		"description": ""
	},
	"Modes of Variability metrics cmec": {
		"filename": result_file.split(".")[0]+"_cmec.json",
		"long_name": "",
		"description": ""
	}
}

data = {}
plots = {}

for eof in ['1','2','3']:
	for season in seasons:
		season = season.upper()
		for mod in modnames:
			name_seg = "_".join([variability_mode,varModel,"EOF"+eof,season,mip,mod])
			if nc_out_model:
				result_file = [f for f in nc_list if name_seg in f][0]
				tmp={
					"_".join([mod,"EOF"+eof,season]): {
						"filename": result_file,
						"long_name": mod+" ",
						"description": "Global map, PC timeseries, and fraction for "+mod
					}
				}
				data.update(tmp)
			if plot_model:
				result_file = [
					f for f in png_list if \
					((name_seg in f) and ("teleconnection" not in f) \
						and ("_cbf" not in f))][0]
				tmp = {
					"_".join([mod,"EOF"+eof,season]): {
						"filename": result_file,
						"long_name": mod+" map of EOF"+eof,
						"description": ""+mod
					}
				}
				"""tmp = {
					"_".join([mod,"EOF"+eof,season]): {
						"filename": result_file,
						"long_name": mod+" ",
						"description": "Extended global teleconnection map "+mod
					}
				}"""
				# case for CBF (Common basis function approach)
				plots.update(tmp)
		mod = "obs"
		if nc_out_obs:
			result_file = [f for f in nc_list if mod in f][0]
			tmp={
				"_".join([mod,mip]): {
					"filename": result_file,
					"long_name": mod+" ",
					"description": " "+mod
				}
			}
			data.update(tmp)
		if plot_obs:
			result_file = [f for f in png_list if mod in f][0]
			tmp = {
				"_".join([mod,mip]): {
					"filename": result_file,
					"long_name": mod+" ",
					"description": ""+mod
				}
			}
			plots.update(tmp)


output["metrics"].update(desc)
output["data"].update(data)
output["plots"].update(plots)

with open(fname,"w") as output_json:
	json.dump(output,output_json,indent=4)
