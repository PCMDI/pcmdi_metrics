#!/usr/bin/env python
import glob
import os

import xcdat

from pcmdi_metrics.drcdm.lib import (
    compute_metrics,
    create_drcdm_parser,
    metadata,
    region_utilities,
    utilities,
)
from pcmdi_metrics.utils import create_land_sea_mask

##########
# Set up
##########

parser = create_drcdm_parser.create_extremes_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# Parameters
# I/O settings
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
# Expected variables - pr, tasmax, tasmin, tas
variable_list = parameter.vars
filename_template = parameter.filename_template
sftlf_filename_template = parameter.sftlf_filename_template
test_data_path = parameter.test_data_path
reference_data_path = parameter.reference_data_path
reference_data_set = parameter.reference_data_set
reference_sftlf_template = parameter.reference_sftlf_template
metrics_output_path = parameter.metrics_output_path
# Do we require variables to use certain units?
ModUnitsAdjust = parameter.ModUnitsAdjust
ObsUnitsAdjust = parameter.ObsUnitsAdjust
plots = parameter.plots
# TODO: Some metrics require a baseline period. Do we use obs for that? Allow two model date ranges?
msyear = parameter.msyear
meyear = parameter.meyear
osyear = parameter.osyear
oeyear = parameter.oeyear
generate_sftlf = parameter.generate_sftlf
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
use_region_mask, region_name, coords = region_utilities.check_region_params(
    shp_path, coords, region_name, col, "land"
)

# Verifying output directory
metrics_output_path = utilities.verify_output_path(metrics_output_path, case_id)

if isinstance(reference_data_set, list):
    # Fix a command line issue
    reference_data_set = reference_data_set[0]

# Verify years
ok_mod = utilities.verify_years(
    msyear,
    meyear,
    msg="Error: Model msyear and meyear must both be set or both be None (unset).",
)
ok_obs = utilities.verify_years(
    osyear,
    oeyear,
    msg="Error: Obs osyear and oeyear must both be set or both be None (unset).",
)

# Initialize output.json file
meta = metadata.MetadataFile(metrics_output_path)

# Initialize other directories
# Not sure if needed so commented for now.
# nc_dir = os.path.join(metrics_output_path, "netcdf")
# os.makedirs(nc_dir, exist_ok=True)
# if plots:
#    plot_dir_maps = os.path.join(metrics_output_path, "plots", "maps")
#    os.makedirs(plot_dir_maps, exist_ok=True)

# Setting up model realization list
find_all_realizations, realizations = utilities.set_up_realizations(realization)

# Only include reference data in loop if it exists
if reference_data_path is not None:
    model_loop_list = ["Reference"] + model_list
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
    region_name,
)

##############
# Run Analysis
##############

# Loop over models
for model in model_loop_list:
    if model == "Reference":
        list_of_runs = [str(reference_data_set)]
    elif find_all_realizations:
        tags = {"%(model)": model, "%(model_version)": model, "%(realization)": "*"}
        test_data_full_path = os.path.join(test_data_path, filename_template)
        test_data_full_path = utilities.replace_multi(test_data_full_path, tags)
        ncfiles = glob.glob(test_data_full_path)
        realizations = []
        for ncfile in ncfiles:
            realizations.append(ncfile.split("/")[-1].split(".")[3])
        print("=================================")
        print("model, runs:", model, realizations)
        list_of_runs = realizations
    else:
        list_of_runs = realizations

    metrics_dict["RESULTS"][model] = {}

    # Loop over realizations
    for run in list_of_runs:
        # Finding land/sea mask
        sftlf_exists = True
        if run == reference_data_set:
            if reference_sftlf_template is not None and os.path.exists(
                reference_sftlf_template
            ):
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
                tags = {
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
                }
                sftlf_filename_list = utilities.replace_multi(
                    sftlf_filename_template, tags
                )
                sftlf_filename = glob.glob(sftlf_filename_list)[0]
            except (AttributeError, IndexError):
                print("No sftlf file found for", model, run)
                if not generate_sftlf:
                    print("Skipping realization", run)
                    continue
                else:
                    # Set flag to generate sftlf after loading data
                    sftlf_exists = False
        if sftlf_exists:
            sftlf = xcdat.open_dataset(sftlf_filename, decode_times=False)
            if use_region_mask:
                print("\nCreating region mask for land/sea mask.")
                sftlf = region_utilities.mask_region(
                    sftlf, region_name, coords=coords, shp_path=shp_path, column=col
                )

        if run == reference_data_set:
            units_adjust = ObsUnitsAdjust
        else:
            units_adjust = ModUnitsAdjust

        # Initialize results dictionary for this mode/run
        # Presumably we will be populating this will metrics as we go
        metrics_dict["RESULTS"][model][run] = {}

        # In extremes we are looping over different variables. I am really
        # not sure what will be the best way to approach this, if we should loop
        # over variables, take in multiple variables at once, etc.
        for varname in variable_list:
            # Populate the filename templates to get actual data path
            if run == reference_data_set:
                test_data_full_path = reference_data_path
                start_year = osyear
                end_year = oeyear
            else:
                tags = {
                    "%(variable)": varname,
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
                }
                test_data_full_path = os.path.join(test_data_path, filename_template)
                test_data_full_path = utilities.replace_multi(test_data_full_path, tags)
                start_year = msyear
                end_year = meyear
            yrs = [str(start_year), str(end_year)]  # for output file names
            test_data_full_path = glob.glob(test_data_full_path)
            test_data_full_path.sort()
            if len(test_data_full_path) == 0:
                print("")
                print("-----------------------")
                print("Not found: model, run, variable:", model, run, varname)
                continue
            else:
                print("")
                print("-----------------------")
                print("model, run, variable:", model, run, varname)
                print("test_data (model in this case) full_path:")
                for t in test_data_full_path:
                    print("  ", t)

            # Load and prep data
            # TODO: substitute PMP version of loading
            ds = utilities.load_dataset(test_data_full_path)

            if not sftlf_exists and generate_sftlf:
                print("Generating land sea mask.")
                sft = create_land_sea_mask(ds)
                sftlf = ds.copy(data=None)
                sftlf["sftlf"] = sft
                if use_region_mask:
                    print("\nCreating region mask for land/sea mask.")
                    sftlf = region_utilities.mask_region(
                        sftlf, region_name, coords=coords, shp_path=shp_path, column=col
                    )

            # Mask out Antarctica
            sftlf["sftlf"] = sftlf["sftlf"].where(sftlf.lat > -60)

            if use_region_mask:
                print("Creating dataset mask.")
                ds = region_utilities.mask_region(
                    ds, region_name, coords=coords, shp_path=shp_path, column=col
                )

            # Get time slice if year parameters exist
            if start_year is not None:
                ds = utilities.slice_dataset(ds, start_year, end_year)
            else:
                # Get labels for start/end years from dataset
                yrs = [str(int(ds.time.dt.year[0])), str(int(ds.time.dt.year[-1]))]

            # If any of the metrics use daily data we'll want to keep
            # something like this calendar handling
            if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                ds = ds.convert_calendar("noleap")

            # -------------------------------
            # Metrics go here
            # -------------------------------
            # Maybe start with the metrics from this paper: https://climatemodeling.science.energy.gov/sites/default/files/2023-11/Validation%20of%20LOCA2%20and%20STAR-ESDM%20Statistically%20Downscaled%20Products%20v2.pdf
            #
            # pr: annualmean_pr, seasonalmean_pr, pr_q50, pr_q99p9, annual pxx
            # tasmax: annualmean_tasmax, seasonalmean_tasmax, annual txx, annual_tasmax_ge_95F,
            #         annual_tasmax_ge_100F, annual_tasmax_ge_105F, tasmax_q50, tasmax_q99p9
            # tasmin: annualmean_tasmin, annual_tasmin_le_32F, annual_tnn
            # ETTCDI has some metrics for tas as well

            # In the extremes metrics, I go by variable and call compute_metrics.temperature_indices() or
            # compute_metrics.precipitation_indices() and those functions handle all the data wrangling
            # for getting all the indices for that variable. Not sure if that's the best way to do it here.
            # For example:
            Rx1day, Rx5day = compute_metrics.precipitation_indices(
                ds,
                sftlf,
                units_adjust,
                dec_mode,
                drop_incomplete_djf,
                annual_strict,
            )


# -------------------------------
# Output JSON with metrics here
# -------------------------------

# Update and write metadata file
# Will want something similar to below code I've left commented
# try:
#    with open(fname, "r") as f:
#        tmp = json.load(f)
#   meta.update_provenance("environment", tmp["provenance"])
# except Exception:
#    # Skip provenance if there's an issue
#    print("Error: Could not get provenance from extremes json for output.json.")

meta.update_provenance("modeldata", test_data_path)
if reference_data_path is not None:
    meta.update_provenance("obsdata", reference_data_path)
meta.write()
