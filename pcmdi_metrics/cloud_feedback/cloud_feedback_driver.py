#!/usr/bin/env python

import json
import os
from collections import OrderedDict

import pcmdi_metrics.cloud_feedback.lib.cld_fbks_ecs_assessment_v3 as dataviz
from pcmdi_metrics.cloud_feedback.lib import (
    AddParserArgument,
    CloudRadKernel,
    cloud_feedback_metrics_to_json,
    compute_ECS,
    organize_ecs_jsons,
    organize_err_jsons,
    organize_fbk_jsons,
)

# collect user input
param = AddParserArgument()

model = param.model
institution = param.institution
variant = param.variant
grid_label = param.grid_label
version = param.version
input_files_json = param.input_files_json
path = param.path
xml_path = param.xml_path
data_path = param.data_path
figure_path = param.figure_path
output_path = param.output_path
output_json_filename = param.output_json_filename
get_ecs = param.get_ecs
debug = param.debug

cmec = False
if hasattr(param, "cmec"):
    cmec = param.cmec  # Generate CMEC compliant json
print("CMEC:" + str(cmec))

print("model:", model)
print("institution:", institution)
print("variant:", variant)
print("grid_label:", grid_label)
print("version:", version)
print("path:", path)
print("input_files_json:", input_files_json)
print("xml_path:", xml_path)
print("figure_path:", figure_path)
print("output_path:", output_path)
print("output_json_filename:", output_json_filename)
print("get_ecs:", get_ecs)
print("debug:", debug)

if get_ecs:
    exps = ["amip", "amip-p4K", "piControl", "abrupt-4xCO2"]
else:
    exps = ["amip", "amip-p4K"]

# generate xmls pointing to the cmorized netcdf files
os.makedirs(xml_path, exist_ok=True)

filenames = dict()

if input_files_json is not None:
    with open(input_files_json) as f:
        ncfiles = json.load(f)
else:
    print('Warning: input files were not explicitly given. They will be searched from ', path)

for exp in exps:
    filenames[exp] = dict()
    if exp == "amip-p4K":
        activity = "CFMIP"
    else:
        activity = "CMIP"
    if "amip" in exp:
        fields = [
            "tas",
            "rsdscs",
            "rsuscs",
            "wap",
            "clisccp",
        ]  # necessary for cloud feedback calcs
    else:
        fields = ["tas", "rlut", "rsut", "rsdt"]  # needed for ECS calc
    for field in fields:
        if field == "clisccp":
            table = "CFmon"
        else:
            table = "Amon"

        if input_files_json is None:  # PCMDI internal setup
            searchstring = os.path.join(
                path,
                activity,
                institution,
                model,
                exp,
                variant,
                table,
                field,
                grid_label,
                version,
                "*.nc",
            )
        else:
            searchstring = os.path.join(
                ncfiles[exp][field]["path"], ncfiles[exp][field]["file"]
            )
        xmlname = os.path.join(xml_path, ".".join([exp, model, variant, field, "xml"]))
        os.system("cdscan -x " + xmlname + " " + searchstring)
        filenames[exp][field] = xmlname

if debug:
    with open(os.path.join(output_path, "filenames.json"), "w") as f:
        json.dump(filenames, f, sort_keys=True, indent=4)

# calculate all feedback components and Klein et al (2013) error metrics:
fbk_dict, obsc_fbk_dict, err_dict = CloudRadKernel(filenames)

print("calc done")

# add this model's results to the pre-existing json file containing other models' results:
updated_fbk_dict, updated_obsc_fbk_dict = organize_fbk_jsons(
    fbk_dict, obsc_fbk_dict, model, variant, datadir=data_path
)
updated_err_dict = organize_err_jsons(err_dict, model, variant, datadir=data_path)

ecs = None
if get_ecs:
    # calculate ECS and add it to the pre-existing json file containing other models' results:
    ecs = compute_ECS(filenames)
    print("calc ECS done")
    print("ecs: ", ecs)
updated_ecs_dict = organize_ecs_jsons(ecs, model, variant, datadir=data_path)

os.makedirs(output_path, exist_ok=True)
if debug:
    with open(os.path.join(output_path, "fbk_dict.json"), "w") as f:
        json.dump(fbk_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, "err_dict.json"), "w") as f:
        json.dump(err_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, "updated_err_dict.json"), "w") as f:
        json.dump(updated_err_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, "updated_fbk_dict.json"), "w") as f:
        json.dump(updated_fbk_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, "updated_ecs_dict.json"), "w") as f:
        json.dump(updated_ecs_dict, f, sort_keys=True, indent=4)

# generate plots and extract metrics from the plotting routines
os.makedirs(figure_path, exist_ok=True)
climo_cld_rmse, cld_fbk_rmse, assessed_cld_fbk, ecs = dataviz.make_all_figs(
    updated_fbk_dict,
    updated_obsc_fbk_dict,
    updated_err_dict,
    updated_ecs_dict,
    model,
    figdir=figure_path,
    datadir=data_path,
    debug=debug,
)
print("get metrics done")

# save final metrics and accompanying important statistics in JSON format
print("-- Metric result --")
print("model:", model)
print("variant:", variant)
print("clim_cloud_rmse:", climo_cld_rmse)
print("cloud_feedback_rmse:", cld_fbk_rmse)
print("assessed_cloud_feedback:", assessed_cld_fbk)
print("ecs:", ecs)

output_dict = OrderedDict()
output_dict["RESULTS"] = OrderedDict()
output_dict["RESULTS"][model] = OrderedDict()
output_dict["RESULTS"][model][variant] = OrderedDict()
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"] = OrderedDict()
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["high_cloud_altitude"] = assessed_cld_fbk[0]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["tropical_marine_low_cloud"] = assessed_cld_fbk[1]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["tropical_anvil_cloud_area"] = assessed_cld_fbk[2]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["land_cloud_amount"] = assessed_cld_fbk[3]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["middle_latitude_marine_low_cloud_amount"] = assessed_cld_fbk[4]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["high_latitude_low_cloud_optical_depth"] = assessed_cld_fbk[5]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["implied_unassessed"] = assessed_cld_fbk[6]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["sum_of_assessed"] = assessed_cld_fbk[7]
output_dict["RESULTS"][model][variant]["assessed_cloud_feedback"]["total_cloud_feedback"] = assessed_cld_fbk[8]
output_dict["RESULTS"][model][variant]["clim_cloud_rmse"] = climo_cld_rmse
output_dict["RESULTS"][model][variant]["cloud_feedback_rmse"] = cld_fbk_rmse
output_dict["RESULTS"][model][variant]["equilibrium_climate_sensitivity"] = ecs


cloud_feedback_metrics_to_json(
    output_path, output_json_filename, output_dict, cmec_flag=cmec
)

print("Done!")
