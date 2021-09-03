"""
mov_output.py
Create and populate the output.json metadata file that
documents the cmec-driver pipeline outputs for the
Modes of Variability metrics.
"""
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
	"parameter_file": "variability_modes_param.py",
	"provenance": {
		"environment": {},
		"modeldata": modeldata,
		"obsdata": obsdata,
		"log": None
		}
	}

with open(os.path.join(wkdir,json_list[0]),"r") as tmp_json:
	tmp = json.load(tmp_json)
envir = tmp["provenance"]["packages"]
envir.pop("PMPObs")
output["provenance"]["environment"] = envir

name_seg = "_".join(["var_mode",variability_mode])
result_file = [f for f in json_list if (name_seg in f) and ("_cmec" not in f)][0]

desc = {
	"Modes of Variability metrics": {
		"filename": result_file,
		"long_name": variability_mode+" statistics",
		"description": variability_mode+" statistics for different EOF modes in CMEC formatted JSON"
	},
	"Modes of Variability metrics cmec": {
		"filename": result_file.split(".")[0]+"_cmec.json",
		"long_name": variability_mode+" statistics CMEC format",
		"description": variability_mode+" statistics for different EOF modes"
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
				result_file = [f for f in nc_list if ((name_seg in f) and ("_cbf" not in f))][0]
				tmp={
					"_".join([mod,"EOF"+eof,season]): {
						"filename": result_file,
						"long_name": " ".join([mod,season,variability_mode,"EOF",eof,"data"]),
						"description": "Global map, PC timeseries, and fraction for "+mod+" EOF "+eof
					}
				}
				data.update(tmp)

				#CBF
				result_file_tmp = result_file.replace(".nc","_cbf.nc")
				if result_file_tmp in nc_list:
					tmp={
						"_".join([mod,"EOF"+eof,season,"cbf"]): {
							"filename": result_file,
							"long_name": " ".join([mod,season,variability_mode,"EOF",eof,"CBF data"]),
							"description": "Common Basis Function approach global map, PC timeseries, and fraction for "+mod+" EOF "+eof
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
						"long_name": " ".join([mod,season,variability_mode,"EOF",eof,"map"]),
						"description": "Map of "+season+" "+variability_mode+" for model "+mod
					}
				}
				plots.update(tmp)

				# Teleconnection plots
				result_file_tmp = result_file.replace(".png","_teleconnection.png")
				if result_file_tmp in png_list:
					tmp = {
						"_".join([mod,"EOF"+eof,season,"teleconnection"]): {
							"filename": result_file_tmp,
							"long_name": " ".join([mod,"EOF",eof,season,"teleconnection map"]),
							"description": "Extended global teleconnection map for model "+mod+" EOF "+eof
						}
					}
					plots.update(tmp)

				# CBF plots
				result_file_tmp = result_file.replace(".png","_cbf.png")
				if result_file_tmp in png_list:
					tmp = {
						"_".join([mod,"EOF"+eof,season,"cbf"]): {
							"filename": result_file_tmp,
							"long_name": " ".join([mod,"EOF",eof,season,"cbf","map"]),
							"description": "Common basis function map for model "+mod+" EOF "+eof
						}
					}
					plots.update(tmp)

				# CBF teleconnection plots
				result_file_tmp = result_file.replace(".png","_cbf_teleconnection.png")
				if result_file_tmp in png_list:
					tmp = {
						"_".join([mod,"EOF"+eof,season,"cbf teleconnection"]): {
							"filename": result_file_tmp,
							"long_name": " ".join([mod,"EOF",eof,season,"cbf teleconnection map"]),
							"description": "Common basis function teleconnection map for model "+mod+" EOF "+eof
						}
					}
					plots.update(tmp)

		mod = "obs"
		if nc_out_obs:
			result_file = [f for f in nc_list if mod in f][0]
			tmp={
				"_".join([mod,mip]): {
					"filename": result_file,
					"long_name": " ".join(["obs",season,variability_mode,"EOF",eof,"data"]),
					"description": "Map of "+season+" "+variability_mode+" for observations"
				}
			}
			data.update(tmp)
		if plot_obs:
			result_file = [f for f in png_list if mod in f and "teleconnection" not in f][0]
			tmp = {
				"_".join([mod,mip]): {
					"filename": result_file,
					"long_name": " ".join(["obs",season,variability_mode,"EOF",eof,"map"]),
					"description": ""+mod
				}
			}
			plots.update(tmp)
			result_file_tmp = result_file.replace(".png","_teleconnection.png")
			if result_file_tmp in png_list:
				tmp = {
					"_".join([mod,mip,"teleconnection"]): {
						"filename": result_file,
						"long_name": " ".join(["obs",season,variability_mode,"EOF",eof,"map"]),
						"description": "Extended global teleconnection map for obs EOF "+eof
					}
				}
				plots.update(tmp)


output["metrics"].update(desc)
output["data"].update(data)
output["plots"].update(plots)

with open(fname,"w") as output_json:
	json.dump(output,output_json,indent=4)
