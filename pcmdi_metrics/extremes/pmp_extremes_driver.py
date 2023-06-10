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
    create_extremes_parser,
    utilities,
    region_utilities,
    metadata,
    plot_extremes
)

from pcmdi_metrics.io import xcdat_openxml


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
plots = parameter.plots
debug = parameter.debug
cmec = parameter.cmec
msyear = parameter.msyear
meyear = parameter.meyear
osyear = parameter.osyear
oeyear = parameter.oeyear
generate_sftlf = parameter.generate_sftlf
regrid = parameter.regrid
# Block extrema related settings
annual_strict = parameter.annual_strict
exclude_leap = parameter.exclude_leap
dec_mode = parameter.dec_mode
drop_incomplete_djf = parameter.drop_incomplete_djf
# Region masking
shp_path = parameter.shp_path
col = parameter.attribute
region_name = parameter.region_name
coords = parameter.coords

# Check the region masking parameters, if provided
use_region_mask,region_name,coords = region_utilities.check_region_params(
    shp_path,
    coords,
    region_name,
    col,
    "land")

# Verifying output directory
metrics_output_path = utilities.verify_output_path(metrics_output_path,case_id)

# Initialize output.json file
meta = metadata.MetadataFile(metrics_output_path)

# Initialize other directories
if nc_out:
    nc_dir = os.path.join(metrics_output_path,"netcdf")
    os.makedirs(nc_dir,exist_ok=True)
if plots:
    plot_dir_maps = os.path.join(metrics_output_path,"plots","maps")
    os.makedirs(plot_dir_maps,exist_ok=True)
    if reference_data_path is not None:
        plot_dir_taylor = os.path.join(metrics_output_path,"plots","taylor")
        os.makedirs(plot_dir_taylor,exist_ok=True)

# Setting up model realization list
find_all_realizations,realizations = utilities.set_up_realizations(realization)

# Only include reference data in loop if it exists
if reference_data_path is not None:
    model_loop_list = ["Reference"]+model_list
else:
    model_loop_list = model_list

# Initialize output JSON structures
# FYI: if the analysis output JSON is changed, remember to update this function!
metrics_dict = compute_metrics.init_metrics_dict(
    model_loop_list,
    variable_list,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    region_name)

obs = {}

##############
# Run Analysis
##############

# Loop over models
for model in model_loop_list:

    if model=="Reference":
        list_of_runs = [str(reference_data_set)] #TODO: realizations set in multiple places
    elif find_all_realizations:
        tags = {'%(model)': model, '%(model_version)': model, '%(realization)': "*"}
        test_data_full_path = os.path.join(test_data_path,filename_template)
        test_data_full_path = utilities.replace_multi(test_data_full_path,tags)
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

    # Loop over realizations
    for run in list_of_runs:

        # SFTLF
        sftlf_exists = True
        if run == reference_data_set:
            if os.path.exists(reference_sftlf_template):
                sftlf_filename = reference_sftlf_template
            else:
                print("No reference sftlf file template provided.")
                if not generate_sftlf:
                    print("Skipping reference data")
                else:
                    # Set flag to generate sftlf after loading data
                    sftlf_exists = False
        else:
            try:
                tags = {'%(model)': model, '%(model_version)': model, '%(realization)': run}
                sftlf_filename_list = utilities.replace_multi(sftlf_filename_template,tags)
                sftlf_filename = glob.glob(sftlf_filename_list)[0]
            except (AttributeError, IndexError):
                print("No sftlf file found for",model,run)
                if not generate_sftlf:
                    print("Skipping realization",run)
                    continue
                else:
                    # Set flag to generate sftlf after loading data
                    sftlf_exists = False
        if sftlf_exists:
            sftlf = xcdat.open_dataset(sftlf_filename,decode_times=False)
            # Stats calculation is expecting sfltf scaled from 0-100
            if sftlf["sftlf"].max() <= 20:
                sftlf["sftlf"] = sftlf["sftlf"] * 100.
            if use_region_mask:
                print("\nCreating sftlf region mask.")
                sftlf = region_utilities.mask_region(
                    sftlf,
                    region_name,
                    coords=coords,
                    shp_path=shp_path,
                    column=col)
        
        metrics_dict["RESULTS"][model][run] = {}
        
        # Loop over variables - tasmax, tasmin, or pr
        for varname in variable_list:

            # Find model data, determine number of files, check if they exist
            if run==reference_data_set:
                test_data_full_path = reference_data_path
                start_year = osyear
                end_year = oeyear
            else:
                tags = {'%(variable)': varname, '%(model)': model, '%(model_version)': model,'%(realization)': run}
                test_data_full_path = os.path.join(test_data_path,filename_template)
                test_data_full_path = utilities.replace_multi(test_data_full_path,tags)
                start_year = msyear
                end_year = meyear
            yrs = [str(start_year), str(end_year)] # for output file names
            test_data_full_path = glob.glob(test_data_full_path)
            test_data_full_path.sort()
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

            # Load and prep data
            if test_data_full_path[-1].endswith(".xml"):
                # Final item of sorted list would have most recent version date
                ds = xcdat_openxml.xcdat_openxml(test_data_full_path[-1])
            elif len(test_data_full_path) > 1:
                ds = xcdat.open_mfdataset(test_data_full_path,chunks=None)
            else: ds = xcdat.open_dataset(test_data_full_path[0])

            if not sftlf_exists and generate_sftlf:
                print("Generating land sea mask.")
                sftlf = utilities.generate_land_sea_mask(ds,debug=debug)
                if use_region_mask:
                    print("\nCreating sftlf region mask.")
                    sftlf = region_utilities.mask_region(
                        sftlf,
                        region_name,
                        coords=coords,
                        shp_path=shp_path,
                        column=col)
            
            # Mask out Antarctica
            sftlf["sftlf"] = sftlf["sftlf"].where(sftlf.lat>-60)

            if use_region_mask:
                print("Creating dataset mask.")
                ds = region_utilities.mask_region(
                    ds,
                    region_name,
                    coords=coords,
                    shp_path=shp_path,
                    column=col)

            # Get time slice if year parameters exist
            if start_year is not None and end_year is not None:
                cal = ds.time.encoding["calendar"]
                start_time = cftime.datetime(start_year,1,1,calendar=cal) - datetime.timedelta(days=0)
                end_time = cftime.datetime(end_year+1,1,1,calendar=cal) - datetime.timedelta(days=1)
                ds = ds.sel(time=slice(start_time,end_time))

            if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                ds = self.ds.convert_calendar('noleap')

            # This dict is going to hold results for just this run
            stats_dict = {}

            # Here's where the extremes calculations are happening
            if varname == "tasmax":
                TXx,TXn = compute_metrics.temperature_indices(
                    ds,
                    varname,
                    sftlf,
                    dec_mode,
                    drop_incomplete_djf,
                    annual_strict)
                stats_dict["TXx"] = TXx
                stats_dict["TXn"] = TXn

                if run==reference_data_set:
                    obs["TXx"] = TXx
                    obs["TXn"] = TXn

                if nc_out:
                    print("Writing results to netCDF.")
                    desc = "Seasonal maximum of maximum temperature."
                    meta = utilities.write_to_nc(TXx,model,run,region_name,"TXx",yrs,nc_dir,desc,meta)
                    desc = "Seasonal minimum of maximum temperature."
                    meta = utilities.write_to_nc(TXn,model,run,region_name,"TXn",yrs,nc_dir,desc,meta)

                if plots:
                    print("Creating maps")
                    yrs = [start_year, end_year]
                    desc = "Seasonal maximum of maximum temperature."
                    meta = plot_extremes.make_maps(TXx,model,run,region_name,"TXx",yrs,plot_dir_maps,desc,meta)
                    desc = "Seasonal minimum of maximum temperature."
                    meta = plot_extremes.make_maps(TXn,model,run,region_name,"TXn",yrs,plot_dir_maps,desc,meta)

            if varname == "tasmin":
                TNx,TNn = compute_metrics.temperature_indices(
                    ds,
                    varname,
                    sftlf,
                    dec_mode,
                    drop_incomplete_djf,
                    annual_strict)
                stats_dict["TNx"] = TNx
                stats_dict["TNn"] = TNn

                if run==reference_data_set:
                    obs["TNx"] = TNx
                    obs["TNn"] = TNn

                if nc_out:
                    print("Writing results to netCDF.")
                    desc = "Seasonal maximum of minimum temperature."
                    meta = utilities.write_to_nc(TNx,model,run,region_name,"TNx",yrs,nc_dir,desc,meta)
                    desc = "Seasonal minimum of minimum temperature."
                    meta = utilities.write_to_nc(TNn,model,run,region_name,"TNn",yrs,nc_dir,desc,meta)

                if plots:
                    print("Creating maps")
                    yrs = [start_year, end_year]
                    desc = "Seasonal maximum of minimum temperature."
                    meta = plot_extremes.make_maps(TNx,model,run,region_name,"TNx",yrs,plot_dir_maps,desc,meta)
                    desc = "Seasonal minimum of minimum temperature."
                    meta = plot_extremes.make_maps(TNn,model,run,region_name,"TNn",yrs,plot_dir_maps,desc,meta)

            if varname in ["pr","PRECT","precip"]:
                # Rename possible precipitation variable names for consistency
                if varname in ["precip","PRECT"]:
                    ds = ds.rename({variable: "pr"})
                Rx1day,Rx5day = compute_metrics.precipitation_indices(
                    ds,
                    sftlf,
                    dec_mode,
                    drop_incomplete_djf,
                    annual_strict)
                stats_dict["Rx1day"] = Rx1day
                stats_dict["Rx5day"] = Rx5day

                if run==reference_data_set:
                    obs["Rx1day"] = Rx1day
                    obs["Rx5day"] = Rx5day

                if nc_out:
                    print("Writing results to netCDF.")
                    desc = "Seasonal maximum value of daily precipitation."
                    meta = utilities.write_to_nc(Rx1day,model,run,region_name,"Rx1day",yrs,nc_dir,desc,meta)
                    desc = "Seasonal maximum value of 5-day mean precipitation."
                    meta = utilities.write_to_nc(Rx5day,model,run,region_name,"Rx5day",yrs,nc_dir,desc,meta)

                if plots:
                    print("Creating maps")
                    yrs = [start_year, end_year]
                    desc = "Seasonal maximum value of 5-day mean precipitation."
                    meta = plot_extremes.make_maps(Rx5day,model,run,region_name,"Rx5day",yrs,plot_dir_maps,desc,meta)
                    desc = "Seasonal maximum value of daily precipitation."
                    meta = plot_extremes.make_maps(Rx1day,model,run,region_name,"Rx1day",yrs,plot_dir_maps,desc,meta)
            
            # Get stats and update metrics dictionary
            print("Generating metrics.")
            result_dict = compute_metrics.metrics_json(
                stats_dict,
                sftlf,
                obs_dict=obs,
                region=region_name,
                regrid=regrid)
            metrics_dict["RESULTS"][model][run].update(result_dict)
            if run not in metrics_dict["DIMENSIONS"]["realization"]:
                metrics_dict["DIMENSIONS"]["realization"].append(run)

    # Pull out metrics for just this model
    # and write to JSON
    metrics_tmp = metrics_dict.copy()
    metrics_tmp["DIMENSIONS"]["model"] = model
    metrics_tmp["DIMENSIONS"]["realization"] = list_of_runs
    metrics_tmp["RESULTS"] = {model: metrics_dict["RESULTS"][model]}
    metrics_path = "{0}_extremes_metrics.json".format(model)
    utilities.write_to_json(metrics_output_path,metrics_path,metrics_tmp)

    meta.update_metrics(
        model,
        os.path.join(metrics_output_path,metrics_path),
        model+" results",
        "Seasonal metrics for block extrema for single dataset")

# Output single file with all models
metrics_dict["DIMENSIONS"]["model"] = model_loop_list
utilities.write_to_json(metrics_output_path,"extremes_metrics.json",metrics_dict)
fname=os.path.join(metrics_output_path,"extremes_metrics.json")
meta.update_metrics(
    "All",
    fname,
    "All results",
    "Seasonal metrics for block extrema for all datasets")

# Taylor Diagram
if plots and (reference_data_path is not None):
    print("Making Taylor Diagrams")
    years = "-".join(yrs)
    outfile_template = os.path.join(
        plot_dir_taylor,
        "_".join(["taylor","realization","region","index","season",years]))
    plot_extremes.taylor_diag(fname,outfile_template)
    meta.update_plots(
        "Taylor_Diagrams",
        outfile_template,
        "Taylor Diagrams",
        "Taylor Diagrams for block extrema results.")

# Update and write metadata file
try:
    with open(fname,"r") as f:
        tmp = json.load(f)
    meta.update_provenance("environment",tmp["provenance"])
except:
    # Skip provenance if there's an issue
    print("Error: Could not get provenance from extremes json for output.json.")

meta.update_provenance("modeldata", test_data_path)
if reference_data_path is not None:
    meta.update_provenance("obsdata", reference_data_path)
meta.write()
