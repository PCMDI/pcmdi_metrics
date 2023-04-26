import xarray as xr
import xcdat
import pandas as pd
import numpy as np
import cftime
import datetime
import sys
import os
import glob

#from pcmdi_metrics.extremes.lib import (
#    compute_metrics,
#    create_extremes_parser
#)
from lib import (
    compute_metrics,
    create_extremes_parser
)


##########
# Set up
##########

# TODO write create_extremes_parser() function
parser = create_extremes_parser.create_extremes_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# parameters
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
variable_list = parameter.vars
#reference_data_set = parameter.reference_data_set
filename_template = parameter.filename_template
sftlf_filename_template = parameter.sftlf_filename_template
generate_sftlf = parameter.generate_sftlf
test_data_path = parameter.test_data_path
#reference_data_path = parameter.reference_data_path
metrics_output_path = parameter.metrics_output_path
debug = parameter.debug
cmec = parameter.cmec
chunk_size = None
strict_annual = True
exclude_leap = False
dec_mode = "DJF"
drop_incomplete_djf = True
# TODO add chunk_size variable
# TODO strict annual
# TODO exclude leap
# TODO DJF mode/drop incomplete djf

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

metrics_dict = compute_metrics.init_metrics_dict()
definitions = {
        "Rx5day": "Maximum consecutive 5-day precipitation, globally averaged"
        "Rx1day": "Maximum daily precipitation, globally averaged"
        "TXx": "Maximum value of daily maximum temperature, globally averaged"
        "TXn": "Minimum value of daily maximum temperature, globally averaged"
        "TNx": "Maximum value of daily minimum temperature, globally averaged"
        "TNn": "Minimum value of daily minimum temperature, globally averaged"
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
    
    for run in realizations:
        sftlf_filename = sftlf_filename_template.replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
        sftlf_filename = glob.glob(sftlf_filename)[0]
        sftlf = xr.open_dataset(sftlf_filename)
        for varname in variable_list:
            test_data_full_path = os.path.join(
                test_data_path,
                filename_template
                ).replace('%(variable)', varname).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
            test_data_full_path = glob.glob(test_data_full_path)[0]
            if os.path.exists(test_data_full_path):
                print('-----------------------')
                print('model, run:', model, run)
                print('test_data (model in this case) full_path:', test_data_full_path)

            # TODO: mfdataset option?
            if chunk_size:
                ds = xr.load_dataset(test_data_full_path,chunks={"latitude":chunk_size,"longitude": chunk_size})
            else:
                ds = xr.load_dataset(test_data_full_path)

            if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                ds = self.ds.convert_calendar('noleap')

            stats_dict = {}

            # TODO convert 3 hourly to daily option
            if varname == "tasmax":
                TXx,TXn = compute_metrics.temperature_metrics(ds,varname)
                #tmp_dict = {"TXx": TXx, "TXn": TXn}
                #result_dict = compute_metrics.temperature_metrics_json(tmp_dict,sftlf)
                #metrics_dict["RESULTS"][model] = {
                #    realization: result_dict
                #}
                stats_dict["TXx"] = TXx
                stats_dict["TXn"] = TXn
                filepath = os.path.join(metrics_output_path,"TXx_{0}.nc".format("_".join([model,realization])))
                TXx.to_netcdf(filepath)
                filepath = os.path.join(metrics_output_path,"TXn_{0}.nc".format("_".join([model,realization])))
                TXn.to_netcdf(filepath)   
   
            if varname == "tasmin":
                TNx,TNn = compute_metrics.temperature_metrics(ds,varname)
                stats_dict["TNx"] = TNx
                stats_dict["TNn"] = TNn
                #tmp_dict = {"TNx": TNx, "TNn": TNn}
                #result_dict = compute_metrics.temperature_metrics_json(tmp_dict,sftlf)
                #metrics_dict["RESULTS"][model] = {
                    realization: result_dict
                #}
                filepath = os.path.join(metrics_output_path,"TNx_{0}.nc".format("_".join([model,realization])))
                TNx.to_netcdf(filepath)
                filepath = os.path.join(metrics_output_path,"TNn_{0}.nc".format("_".join([model,realization])))
                TNn.to_netcdf(filepath)   

            if varname in ["pr","PRECT","precip"]:
                # Rename possible precipitation variable names for consistency
                if varname in ["precip","PRECT"]:
                    ds = ds.rename({variable: "pr"})
                Rx1day,Rx5day = compute_metrics.precipitation_metrics(ds)
                stats_dict["Rx1day"] = Rx1day
                stats_dict["Rx5day"] = Rx5day
                #tmp_dict = {"Rx1day": Rx1day, "Rx5day": Rx5day}
                # Update metrics
                #result_dict = compute_metrics.precipitation_metrics_json(tmp_dict,sftlf)
                #metrics_dict["RESULTS"][model] = {
                #    realization: result_dict
                #}
                P.to_netcdf("Rx5day_{0}.nc".format("_".join([model,realization])))
            
            result_dict = compute_metrics.metrics_json(stats_dict,sftlf)
            metrics_dict["RESULTS"][model] = {
                realization: result_dict
            }
    
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
    metrics_dict["DIMENSIONS"]["metric"][m] = definition[m]

print(metrics_dict)