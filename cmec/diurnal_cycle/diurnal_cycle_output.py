import json
import os

wkdir = os.getenv("CMEC_WK_DIR")

fname = os.path.join(wkdir,"output.json")

output = {
	"index": "",
	"html": "",
	"metrics": {},
	"data": {},
	"plots": {},
	"provenance": {
		"environment": {},
		"modeldata": "",
		"obsdata": "",
		"log": ""
		}
}

ascii_data = os.listdir(os.path.join(wkdir,"ascii"))
json_data = os.listdir(os.path.join(wkdir,"json"))
nc_data = os.listdir(os.path.join(wkdir,"nc"))

for item in ascii_data:
	fullpath = os.path.join(wkdir,"ascii",item)
	desc = {"fourierDiurnalGridPoints": {
		"filename": os.path.relpath(fullpath,wkdir),
		"long_name": "Composite diurnal cycle",
		"description": "Composite diurnal cycle at select grid points from fourierDiurnalGridpoints"
		}
	}
	output["data"].update(desc)

for item in json_data:
	fullpath = os.path.join(wkdir,"json",item)
	if "_savg_DiurnalFourier" in item:
		desc = {"savg_DiurnalFourier": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Fourier values",
			"description": "Amplitude and phase for diurnal cycle of precipitation from savg_fourier analysis"
			}
		}
	if "_std_of_hourlymeans" in item:
		desc = {"std_of_hourlymeans": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Standard deviation of hourly means",
			"description": "Results from std_of_hourlyvalues"
			}
		}
	if "_std_of_meandiurnalcyc" in item:
		desc = {"std_of_meandiurnalcyc": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Average variance of hourly values",
			"description": "Results from std_of_meandiurnalcycle"
			}
		}
	if "_std_of_dailymeans" in item:
		desc = {"std_of_dailymeans": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Standard deviation of daily means",
			"description": "Standard deviation at each cell from computeStdOfDailyMeans"
			}
		}
	if "cmec" in item:
		key = [*desc][0]
		new_key = key + "_cmec"
		desc[new_key] = desc[key].copy()
		desc[new_key]["description"] = desc[key]["description"] + " (CMEC format)"
		desc.pop(key)
	output["metrics"].update(desc)

for item in nc_data:
	fullpath = os.path.join(wkdir,"nc",item)
	if "_S.nc" in item:
		desc = {"S": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Amplitude",
			"description": "Amplitude for each gridpoint/harmonic from fourierDiurnalAllGrid"
			}
		}
	elif "_diurnal_avg.nc" in item:
		desc = {"diurnal_avg": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "mean diurnal cycle",
			"description": "Results from compositeDiurnalStatistics analysis"
			}
		}
	elif "_diurnal_std.nc" in item:
		desc = {"diurnal_std": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Standard deviation of mean diurnal cycle",
			"description": "Results from compositeDiurnalStatistics analysis"
			}
		}
	elif "_std_of_dailymeans.nc" in item:
		desc = {"std_of_dailymeans": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Standard deviation of daily means",
			"description": "Results from std_of_dailymeans"
			}
		}
	elif "_tS.nc" in item:
		desc = {"tS": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Time of maximum value",
			"description": "Time of max value for each gridpoint/harmonic from fourierDiurnalAllGrid"
			}
		}
	elif "_tmean.nc" in item:
		desc = {"tmean": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Mean value at each gridpoint",
			"description": "'Zeroth' term in Fourier result from fourierDiurnalAllGrid"
			}
		}
	elif "_LocalSolarTimes.nc" in item:
		desc = {"LocalSolarTimes": {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "Local solar time",
			"description": "Results from compositeDiurnalStatistics analysis"
			}
		}
	else:
		desc = {os.path.relpath(fullpath,wkdir): {
			"filename": os.path.relpath(fullpath,wkdir),
			"long_name": "",
			"description": ""
			}
		}
	output["data"].update(desc)

with open(fname,"w") as output_json:
	json.dump(output,output_json,indent=4)
