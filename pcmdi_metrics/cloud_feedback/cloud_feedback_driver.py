import json
import os

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
figure_path = param.figure_path
output_path = param.output_path
output_json_filename = param.output_json_filename
get_ecs = param.get_ecs
debug = param.debug

cmec = False
if hasattr(param, "cmec"):
    cmec = param.cmec  # Generate CMEC compliant json
print("CMEC:" + str(cmec))


print(
    "model:", model, "\n",
    "institution:", institution, "\n",
    "variant:", variant, "\n",
    "grid_label:", grid_label, "\n",
    "version:", version, "\n",
    "path:", path, "\n",
    "input_files_json:", input_files_json, "\n",
    "xml_path:", xml_path, "\n",
    "figure_path:", figure_path, "\n",
    "output_path:", output_path, "\n",
    "output_json_filename:", output_json_filename, "\n",
    "get_ecs:", get_ecs, "\n",
    "debug:", debug
)

if get_ecs:
    exps = ['amip', 'amip-p4K', 'piControl', 'abrupt-4xCO2']
else:
    exps = ['amip', 'amip-p4K']

# generate xmls pointing to the cmorized netcdf files
os.makedirs(xml_path, exist_ok=True)

filenames = dict()

if input_files_json is not None:
    with open(input_files_json) as f:
        ncfiles = json.load(f)

for exp in exps:
    filenames[exp] = dict()
    if exp == 'amip-p4K':
        activity = 'CFMIP'
    else:
        activity = 'CMIP'
    if 'amip' in exp:
        fields = ['tas', 'rsdscs', 'rsuscs', 'wap', 'clisccp']  # necessary for cloud feedback calcs
    else:
        fields = ['tas', 'rlut', 'rsut', 'rsdt']  # needed for ECS calc
    for field in fields:
        if field == 'clisccp':
            table = 'CFmon'
        else:
            table = 'Amon'

        if input_files_json is None:  # PCMDI internal setup
            searchstring = os.path.join(path, activity, institution, model, exp, variant, table, field, grid_label, version, '*.nc')
        else:
            searchstring = os.path.join(ncfiles[exp][field]['path'], ncfiles[exp][field]['file'])
        xmlname = os.path.join(xml_path, '.'.join([exp, model, variant, field, 'xml']))
        os.system('cdscan -x ' + xmlname + ' ' + searchstring)
        filenames[exp][field] = xmlname

if debug:
    with open(os.path.join(output_path, 'filenames.json'), 'w') as f:
        json.dump(filenames, f, sort_keys=True, indent=4)

# calculate all feedback components and Klein et al (2013) error metrics:
fbk_dict, obsc_fbk_dict, err_dict = CloudRadKernel(filenames)

print('calc done')

# add this model's results to the pre-existing json file containing other models' results:
updated_fbk_dict, updated_obsc_fbk_dict = organize_fbk_jsons(fbk_dict, obsc_fbk_dict, model, variant)
updated_err_dict = organize_err_jsons(err_dict, model, variant)

ecs = None
if get_ecs:
    # calculate ECS and add it to the pre-existing json file containing other models' results:
    ecs = compute_ECS(filenames)
    print('calc ECS done')
    print('ecs: ', ecs)
updated_ecs_dict = organize_ecs_jsons(ecs, model, variant)

os.makedirs(output_path, exist_ok=True)
if debug:
    with open(os.path.join(output_path, 'fbk_dict.json'), 'w') as f:
        json.dump(fbk_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, 'err_dict.json'), 'w') as f:
        json.dump(err_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, 'updated_err_dict.json'), 'w') as f:
        json.dump(updated_err_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, 'updated_fbk_dict.json'), 'w') as f:
        json.dump(updated_fbk_dict, f, sort_keys=True, indent=4)
    with open(os.path.join(output_path, 'updated_ecs_dict.json'), 'w') as f:
        json.dump(updated_ecs_dict, f, sort_keys=True, indent=4)

# generate plots and extract metrics from the plotting routines
os.makedirs(figure_path, exist_ok=True)
rmse, ecs = dataviz.make_all_figs(updated_fbk_dict, updated_obsc_fbk_dict, updated_err_dict, updated_ecs_dict, model, debug)
print('get metrics done')

# save final metrics and accompanying important statistics in JSON format
print('-- Metric result --')
print('model:', model)
print('variant:', variant)
print('rmse:', rmse)
print('ecs:', ecs)

output_dict = dict()
output_dict['RESULTS'] = dict()
output_dict['RESULTS'][model] = dict()
output_dict['RESULTS'][model][variant] = dict()
output_dict['RESULTS'][model][variant]['RMSE'] = rmse
output_dict['RESULTS'][model][variant]['ECS'] = ecs

cloud_feedback_metrics_to_json(output_path, output_json_filename, output_dict, cmec_flag=cmec)

print('Done!')