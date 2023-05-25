#!/usr/bin/env python
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
import datetime
import regionmask
import geopandas as gpd

from lib import (
    compute_metrics,
    create_extremes_parser
)
from pcmdi_metrics.io.base import Base

def mask_region(data,name,coords=None,shp_path=None,column=None):
    # Return data masked from coordinate list or shapefile.
    # Masks a single region
    print("Creating region mask.")

    lon = data["lon"].data
    lat = data["lat"].data

    # Option 1: Region is defined by coord pairs
    if coords is not None:
        try:
            names=[name]
            regions = regionmask.Regions([np.array(coords)],names=names)
            mask = regions.mask(lon, lat)
            val=0
        except Exception as e:
            print("Error in creating mask from provided coordinates:")
            print("  ",e)
            return

    # Option 2: region is defined by shapefile
    elif shp_path is not None:
        try:
            regions_file = gpd.read_file(shp_path)
            if column is not None:
                regions = regionmask.from_geopandas(regions_file,names=column)
            else:
                print("Column name not provided.")
                regions = regionmask.from_geopandas(regions_file)
            mask = regions.mask(lon, lat)
            # Can't match mask by name, rather index of name
            val = list(regions_file[col]).index(name)
        except Exception as e:
            print("Error in creating mask from shapefile:")
            print("  ",e)
            return

    else:
        print("Region coordinates or shapefile must be provided.")
        print("Defaulting to global analysis.")
        return
    
    try:
        masked_data = data.where(mask == val)
    except Exception as e:
        print("Error: Masking failed. Defaulting to global analysis.")
        print(e)
        return data

    return  masked_data
    
def write_to_nc(filepath,ds):
    try:
        ds.to_netcdf(filepath,mode="w")
    except PermissionError as e:
        if os.path.exists(filepath):
            print("  Permission error. Removing existing file",filepath)
            os.remove(filepath)
            print("  Writing new netcdf file",filepath)
            ds.to_netcdf(filepath,mode="w")
        else:
            print("  Permission error. Could not write netcdf file",filepath)
            print("  ",e)
    except Error as e:
        print("  Error: Could not write netcdf file",filepath)
        print("  ",e)

def write_to_json(outdir,json_filename,json_dict):
    # Open JSON
    JSON = Base(
        outdir, json_filename
    )
    json_structure = json_dict["DIMENSIONS"]["json_structure"]

    JSON.write(
        json_dict,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    return

def check_region_params(shp_path,coords,region_name,col,default):
    use_region_mask = False
    
    if shp_path is not None:
        use_region_mask = True
        if not os.path.exists(shp_path):
            print("Error: Shapefile path does not exist.")
            print("Must provide valid shapefile path.")
            sys.exit()
        if region_name is None:
            print("Error: Region name parameter --region_name must be provided with shapefile.")
            sys.exit()
        if col is None:
            print("Error: Column name parameter --column must be provided with shapefile.")
            sys.exit()
        print("Region settings are:")
        print("  Shapefile:",shp_path)
        print("  Column name:",col)
        print("  Region name:",region_name)
    elif coords is not None:    
        use_region_mask = True
        if isinstance(coords,str):
            # Might be string when ingested from command line, convert to list
            tmp=coords.replace("[","").replace("]","").split(",")
            coords=[[float(tmp[n]),float(tmp[n+1])] for n in range(0,len(tmp)-1,2)]
        if region_name is None:
            print("No region name provided. Using 'custom'.")
            region_name = "custom"
        print("Region settings are:")
        print("  Coordinates:",coords)
        print("  Region name:",region_name)
    else:
        region_name = default
    
    return use_region_mask,region_name

def verify_output_path(metrics_output_path,case_id):
    if metrics_output_path is None:
        metrics_output_path = datetime.datetime.now().strftime("v%Y%m%d")
    if case_id is not None:
        metrics_output_path = metrics_output_path.replace('%(case_id)', case_id)
    if not os.path.exists(metrics_output_path):
        print("\nMetrics output path not found.")
        print("Creating metrics output directory",metrics_output_path)
        try:
            os.makedirs(metrics_output_path)
        except Error as e:
            print("\nError: Could not create metrics output path",metrics_output_path)
            print(e)
            print("Exiting.")
            sys.exit()
    return metrics_output_path

def set_up_realizations(realization):
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
    
    return find_all_realizations,realizations

##########
# Set up
##########

parser = create_extremes_parser.create_extremes_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# Parameters
# I/O settings
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
variable_list = parameter.vars
filename_template = parameter.filename_template
sftlf_filename_template = parameter.sftlf_filename_template
test_data_path = parameter.test_data_path
reference_data_path = parameter.reference_data_path
reference_data_set = parameter.reference_data_set
reference_sftlf_template = parameter.reference_sftlf_template
metrics_output_path = parameter.metrics_output_path
nc_out = parameter.nc_out
debug = parameter.debug
cmec = parameter.cmec
start_year = parameter.year_range[0]
end_year = parameter.year_range[1]
# Block extrema related settings
annual_strict = parameter.annual_strict
exclude_leap = parameter.exclude_leap
dec_mode = parameter.dec_mode
drop_incomplete_djf = parameter.drop_incomplete_djf
# Region masking
shp_path = parameter.shp_path
col = parameter.column
region_name = parameter.region_name
coords = parameter.coords

# Check the region masking parameters, if provided
use_region_mask,region_name = check_region_params(shp_path,coords,region_name,col,"land")

# Verifying output directory
metrics_output_path = verify_output_path(metrics_output_path,case_id)

obs = {}
# TODO: Obs will likely need to be converted to model grid

# Setting up model realization list
find_all_realizations,realizations = set_up_realizations(realization)

# Initialize output JSON structures
# FYI: if new metrics are added to this analysis, 
# the index object in the compute_metrics.init_metrics_dict
# code must be updated manually.
metrics_dict = compute_metrics.init_metrics_dict(dec_mode,drop_incomplete_djf,annual_strict,region_name)

# Only include reference data in loop if it exists
if reference_data_path is not None:
    model_loop_list = ["Reference"]+model_list
else:
    model_loop_list = model_list

##########
# Run Analysis
##########

# Loop over models
for model in model_loop_list:

    if model=="Reference":
        list_of_runs = [str(reference_data_set)] #TODO: realizations set in multiple places
    elif find_all_realizations:
        test_data_full_path = os.path.join(
            test_data_path,
            filename_template).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', '*')
        ncfiles = glob.glob(test_data_full_path)
        realizations = []
        for ncfile in ncfiles:
            realizations.append(ncfile.split('/')[-1].split('.')[3])
        print('=================================')
        print('model, runs:', model, realizations)
        list_of_runs = realizations
    else:
        list_of_runs = realizations
    
    metrics_dict["RESULTS"][model] = {}

    for run in list_of_runs:

        # SFTLF
        if run == reference_data_set:
            sftlf = xcdat.open_dataset(reference_sftlf_template,decode_times=False)
        else:
            sftlf_filename_list = sftlf_filename_template.replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
            try:
                sftlf_filename = glob.glob(sftlf_filename_list)[0]
            except IndexError:
                print("No sftlf file found:",sftlf_filename_list)
                print("Skipping realization",run)
                continue
            sftlf = xcdat.open_dataset(sftlf_filename,decode_times=False)
        # Stats calculation is expecting sfltf scaled from 0-100
        if sftlf["sftlf"].max() <= 20:
            sftlf["sftlf"] = sftlf["sftlf"] * 100.
        if use_region_mask:
            sftlf = mask_region(sftlf,region_name,coords=coords,shp_path=shp_path,column=col)
        
        metrics_dict["RESULTS"][model][run] = {}
        
        for varname in variable_list:
            # Find model data, determine number of files, check if they exist
            if run==reference_data_set:
                test_data_full_path = reference_data_path
            else:
                test_data_full_path = os.path.join(
                    test_data_path,
                    filename_template
                    ).replace('%(variable)', varname).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
            test_data_full_path = glob.glob(test_data_full_path)
            if len(test_data_full_path) == 0:
                print("")
                print("-----------------------")
                print("Not found: model, run, variable:", model, run, varname)
                continue
            else:
                print("")
                print('-----------------------')
                print('model, run, variable:', model, run, varname)
                print('test_data (model in this case) full_path:')
                for t in test_data_full_path:
                    print("  ",t)

            if len(test_data_full_path) > 1 or test_data_full_path[0].endswith(".xml"):
                ds = xcdat.open_mfdataset(test_data_full_path)
            else:
                ds = xcdat.open_dataset(test_data_full_path[0])

            if use_region_mask:
                ds = mask_region(ds,region_name,coords=coords,shp_path=shp_path,column=col)

            if start_year is not None and end_year is not None:
                start_time = cftime.datetime(start_year,1,1) - datetime.timedelta(days=0)
                end_time = cftime.datetime(end_year+1,1,1) - datetime.timedelta(days=1)
                ds = ds.sel(time=slice(start_time,end_time))

            if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                ds = self.ds.convert_calendar('noleap')

            # This dict is going to hold results for just this run
            stats_dict = {}

            if varname == "tasmax":
                TXx,TXn = compute_metrics.temperature_metrics(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict)
                stats_dict["TXx"] = TXx
                stats_dict["TXn"] = TXn

                if run==reference_data_set:
                    obs["TXx"] = TXx
                    obs["TXn"] = TXn

                if nc_out:
                    print("Writing results to netCDF.")
                    filepath = os.path.join(metrics_output_path,"TXx_{0}.nc".format("_".join([model,run,region_name])))
                    write_to_nc(filepath,TXx)
                    filepath = os.path.join(metrics_output_path,"TXn_{0}.nc".format("_".join([model,run,region_name])))
                    write_to_nc(filepath,TXn)
   
            if varname == "tasmin":
                TNx,TNn = compute_metrics.temperature_metrics(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict)
                stats_dict["TNx"] = TNx
                stats_dict["TNn"] = TNn

                if run==reference_data_set:
                    obs["TNx"] = TNx
                    obs["TNn"] = TNn

                if nc_out:
                    print("Writing results to netCDF.")
                    filepath = os.path.join(metrics_output_path,"TNx_{0}.nc".format("_".join([model,run,region_name])))
                    write_to_nc(filepath,TNx)
                    filepath = os.path.join(metrics_output_path,"TNn_{0}.nc".format("_".join([model,run,region_name])))
                    write_to_nc(filepath,TNx)

            if varname in ["pr","PRECT","precip"]:
                # Rename possible precipitation variable names for consistency
                if varname in ["precip","PRECT"]:
                    ds = ds.rename({variable: "pr"})
                Rx1day,Rx5day = compute_metrics.precipitation_metrics(ds,sftlf,dec_mode,drop_incomplete_djf,annual_strict)
                stats_dict["Rx1day"] = Rx1day
                stats_dict["Rx5day"] = Rx5day

                if run==reference_data_set:
                    obs["Rx1day"] = Rx1day
                    obs["Rx5day"] = Rx5day

                if nc_out:
                    print("Writing results to netCDF.")
                    filepath = os.path.join(metrics_output_path,"Rx1day_{0}.nc".format("_".join([model,run,region_name])))
                    write_to_nc(filepath,Rx1day)
                    filepath = os.path.join(metrics_output_path,"Rx5day_{0}.nc".format("_".join([model,run,region_name])))
                    write_to_nc(filepath,Rx5day)
            
            # Get stats and update metrics dictionary
            print("Generating metrics.")
            result_dict = compute_metrics.metrics_json(stats_dict,sftlf,obs_dict=obs,region=region_name)
            metrics_dict["RESULTS"][model][run].update(result_dict)
            if run not in metrics_dict["DIMENSIONS"]["realization"]:
                metrics_dict["DIMENSIONS"]["realization"].append(run)
    
    # Update metrics definitions
    metrics_dict["DIMENSIONS"]["model"] = model_list

    # Pull out metrics for just this model
    # and write to JSON
    metrics_tmp = metrics_dict.copy()
    metrics_tmp["DIMENSIONS"]["model"] = model
    metrics_tmp["DIMENSIONS"]["realization"] = list_of_runs
    metrics_tmp["RESULTS"] = {model: metrics_dict["RESULTS"][model]}
    metrics_path = "{0}_extremes_metrics.json".format(model)
    write_to_json(metrics_output_path,metrics_path,metrics_tmp)

# Output single file with all models
write_to_json(metrics_output_path,"extremes_metrics.json",metrics_dict)
