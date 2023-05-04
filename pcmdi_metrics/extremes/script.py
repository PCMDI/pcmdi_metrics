import xarray as xr
import xcdat
import pandas as pd
import numpy as np
import cftime
import datetime
import sys
import os
import glob
import json
#from pcmdi_metrics.extremes.lib import (
#    compute_metrics,
#    create_extremes_parser
#)
from lib import (
    compute_metrics,
    create_extremes_parser
)

from pcmdi_metrics.mean_climate.lib import compute_statistics


##########
# Set up
##########

parser = create_extremes_parser.create_extremes_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# parameters
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
variable_list = parameter.vars
filename_template = parameter.filename_template
sftlf_filename_template = parameter.sftlf_filename_template
test_data_path = parameter.test_data_path
#reference_data_set = parameter.reference_data_set
#reference_data_path = parameter.reference_data_path
metrics_output_path = parameter.metrics_output_path
debug = parameter.debug
cmec = parameter.cmec
chunk_size = None
annual_strict = parameter.annual_strict
exclude_leap = parameter.exclude_leap
dec_mode = parameter.dec_mode
drop_incomplete_djf = parameter.drop_incomplete_djf

if metrics_output_path is not None:
    metrics_output_path = parameter.metrics_output_path.replace('%(case_id)', case_id)

find_all_realizations = False
if realization is None:
    realization = ""
    realizations = [realization]
elif isinstance(realization, str):
    if realization.lower() in ["all", "*"]:
        find_all_realizations = True
    else:
        realizations = [realization]
elif isinstance(realization,list):
    realizations = realization

metrics_dict = compute_metrics.init_metrics_dict(dec_mode,drop_incomplete_djf,annual_strict)
definitions = {
        "Rx5day": "Maximum consecutive 5-day precipitation",
        "Rx1day": "Maximum daily precipitation",
        "TXx": "Maximum value of daily maximum temperature",
        "TXn": "Minimum value of daily maximum temperature",
        "TNx": "Maximum value of daily minimum temperature",
        "TNn": "Minimum value of daily minimum temperature",
    }

# Also loop over all obs. Maybe do obs first?
# Generate stats eg rmse of models vs obs, mean, stddev? (global land only)
# Create JSONs with these stats
# Enable mfdataset capability - how to parse input paths?

# Loop over models
for model in model_list:

    if find_all_realizations:
        test_data_full_path = os.path.join(
            test_data_path,
            filename_template).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', '*')
        ncfiles = glob.glob(test_data_full_path)
        realizations = []
        for ncfile in ncfiles:
            realizations.append(ncfile.split('/')[-1].split('.')[3])
        print('=================================')
        print('model, runs:', model, realizations)
    
    metrics_dict["RESULTS"][model] = {}

    for run in realizations:
        sftlf_filename_list = sftlf_filename_template.replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
        try:
            sftlf_filename = glob.glob(sftlf_filename_list)[0]
        except IndexError:
            print("No sftlf file found:",sftlf_filename_list)
        sftlf = xr.open_dataset(sftlf_filename) # xcdat giving error with no time bounds...but no time dimensions
        
        metrics_dict["RESULTS"][model][run] = {}
        
        for varname in variable_list:
            test_data_full_path = os.path.join(
                test_data_path,
                filename_template
                ).replace('%(variable)', varname).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
            try:
                test_data_full_path = glob.glob(test_data_full_path)[0]
            except:
                print("")
                print("-----------------------")
                print("Not found: model, run, variable:", model, run, varname)
                continue
            if os.path.exists(test_data_full_path):
                print("")
                print('-----------------------')
                print('model, run, variable:', model, run, varname)
                print('test_data (model in this case) full_path:', test_data_full_path)

            if chunk_size:
                ds = xcdat.open_mfdataset(test_data_full_path,chunks={"latitude":chunk_size,"longitude": chunk_size})
            else:
                ds = xcdat.open_dataset(test_data_full_path)

            if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                ds = self.ds.convert_calendar('noleap')

            stats_dict = {}

            if varname == "tasmax":
                TXx,TXn = compute_metrics.temperature_metrics(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict)
                stats_dict["TXx"] = TXx
                stats_dict["TXn"] = TXn

                print("Writing results to netCDF.")
                filepath = os.path.join(metrics_output_path,"TXx_{0}.nc".format("_".join([model,run])))
                TXx.to_netcdf(filepath)
                filepath = os.path.join(metrics_output_path,"TXn_{0}.nc".format("_".join([model,run])))
                TXn.to_netcdf(filepath)   
   
            if varname == "tasmin":
                TNx,TNn = compute_metrics.temperature_metrics(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict)
                stats_dict["TNx"] = TNx
                stats_dict["TNn"] = TNn

                print("Writing results to netCDF.")
                filepath = os.path.join(metrics_output_path,"TNx_{0}.nc".format("_".join([model,run])))
                TNx.to_netcdf(filepath)
                filepath = os.path.join(metrics_output_path,"TNn_{0}.nc".format("_".join([model,run])))
                TNn.to_netcdf(filepath)   

            if varname in ["pr","PRECT","precip"]:
                # Rename possible precipitation variable names for consistency
                if varname in ["precip","PRECT"]:
                    ds = ds.rename({variable: "pr"})
                Rx1day,Rx5day = compute_metrics.precipitation_metrics(ds,sftlf,dec_mode,drop_incomplete_djf,annual_strict)
                stats_dict["Rx1day"] = Rx1day
                stats_dict["Rx5day"] = Rx5day

                print("Writing results to netCDF.")
                filepath = os.path.join(metrics_output_path,"Rx1day_{0}.nc".format("_".join([model,run])))
                Rx1day.to_netcdf(filepath)
                filepath = os.path.join(metrics_output_path,"Rx5day_{0}.nc".format("_".join([model,run])))
                Rx5day.to_netcdf(filepath)
            
            # Get stats and update metrics dictionary
            result_dict = compute_metrics.metrics_json(stats_dict,sftlf)
            metrics_dict["RESULTS"][model][run].update(result_dict)
            if run not in metrics_dict["DIMENSIONS"]["realization"]:
                metrics_dict["DIMENSIONS"]["realization"].append(run)

    # Update metrics definitions
    metrics_dict["DIMENSIONS"]["model"] = model_list

    #JSON = pcmdi_metrics.io.base.Base(
    #    outdir(output_type="metrics_results"), json_filename
    #)
    #JSON.write(met_dict,
    #json_structure = ["model","realization","metric","region","season","year"],
    #sort_keys = True,
    #indent = 4,
    #separators=(",", ": "))

    #if cmec_flag:
    #    JSON.write_cmec(indent=4, separators=(",", ": "))

# Add definitions of the metrics in the file
# TODO: This will be based off the last model/realization in the loop,
# And may not be inclusive
for m in stats_dict:
    metrics_dict["DIMENSIONS"]["metric"][m] = definitions[m]

print("Writing metrics JSON.")
metrics_path = os.path.join(metrics_output_path,"extremes_metrics.json")
with open(metrics_path,"w") as mp:
    json.dump(metrics_dict, mp, indent=2)