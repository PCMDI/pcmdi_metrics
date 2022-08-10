import argparse
import json
import os

from cdp.cdp_parser import CDPParser

import pcmdi_metrics.cloud_feedback.lib.cld_fbks_ecs_assessment_v3 as dataviz
from pcmdi_metrics.cloud_feedback.lib import (
    CloudRadKernel,
    compute_ECS,
    organize_ecs_jsons,
    organize_err_jsons,
    organize_fbk_jsons,
)

P = CDPParser(
    default_args_file=[],
    description="Cloud feedback metrics",
    formatter_class=argparse.RawTextHelpFormatter
)

P.add_argument(
    '--model',
    type=str,
    dest='model',
    help='model name (e.g., GFDL-CM4).',
    required=False)
P.add_argument(
    '--institution',
    type=str,
    dest='institution',
    help='institution name (e.g., NOAA-GFDL).',
    required=False)
P.add_argument(
    '--variant',
    type=str,
    dest='variant',
    help='variant name (e.g., r1i1p1f1).',
    required=False)
P.add_argument(
    '--grid_label',
    type=str,
    dest='grid_label',
    help='grid_label (e.g., gr1).',
    required=False)
P.add_argument(
    '--version',
    type=str,
    dest='version',
    help='version (e.g., v20180701).',
    required=False)
P.add_argument(
    '--path',
    type=str,
    dest='path',
    help='path (e.g., /p/css03/esgf_publish/CMIP6).',
    required=False)
P.add_argument(
    '--input_files_json',
    type=str,
    dest='input_files_json',
    help='json file for list of input netCDF files (e.g., ./param/input_nc_files.json).',
    default=None,
    required=False)
P.add_argument(
    '--xml_path',
    type=str,
    dest='xml_path',
    help='path (e.g., ./xmls).',
    required=False)
P.add_argument(
    '--figure_path',
    type=str,
    dest='figure_path',
    help='path (e.g., ./figures/).',
    required=False)
P.add_argument(
    '--output_path',
    type=str,
    dest='output_path',
    help='path (e.g., ./output/).',
    default='./output',
    required=False)
P.add_argument(
    '--output_json_filename',
    type=str,
    dest='output_json_filename',
    help='path (e.g., output.json).',
    default='output.json',
    required=False)
P.add_argument(
    '--get_ecs',
    type=bool,
    dest='get_ecs',
    help="Flag to compute ECS.\n"
         "True: compute ECS using abrupt-4xCO2 run.\n"
         "False: do not compute, instead rely on ECS value present in the json file (if it exists).",
    required=False)
P.add_argument(
    '--debug',
    type=bool,
    dest='debug',
    help="Flag to print interim results for debugging.\n"
         "True: print interim results and archive some of them.\n"
         "False: None (default).",
    default=None,
    required=False)

param = P.get_parameter()

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

os.makedirs(output_path, exist_ok=True)

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

        if input_files_json is None:
            searchstring = os.path.join(path, activity, institution, model, exp, variant, table, field, grid_label, version, '*.nc')
        else:
            searchstring = " ".join(ncfiles[exp][field])
        xmlname = os.path.join(xml_path, '.'.join([exp, model, variant, field, version, '.xml']))
        os.system('cdscan -x ' + xmlname + ' ' + searchstring)
        filenames[exp][field] = xmlname

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
updated_ecs_dict = organize_ecs_jsons(ecs, model, variant)

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

# plot this model alongside other models and expert assessment:
os.makedirs(figure_path, exist_ok=True)
rmse, ecs = dataviz.make_all_figs(updated_fbk_dict, updated_obsc_fbk_dict, updated_err_dict, updated_ecs_dict, model)

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

os.makedirs(output_path, exist_ok=True)
output_json = os.path.join(output_path, output_json_filename)
with open(output_json, 'w') as f:
    json.dump(output_dict, f, sort_keys=True, indent=4)

print('Done!')
