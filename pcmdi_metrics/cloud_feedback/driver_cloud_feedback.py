import cal_CloudRadKernel as CRK
import compute_ECS as CE
import organize_jsons as OJ
import cld_fbks_ecs_assessment_v3 as dataviz
import os

"""
# User Input: (collect from my_param.py)
#================================================================================================
model = 'GFDL-CM4'	
institution = 'NOAA-GFDL'
variant = 'r1i1p1f1'
grid_label = 'gr1'
version = 'v20180701'
path = '/p/css03/esgf_publish/CMIP6'

# Flag to compute ECS
# True: compute ECS using abrupt-4xCO2 run
# False: do not compute, instead rely on ECS value present in the json file (if it exists)
get_ecs = True
#================================================================================================
"""

from cdp.cdp_parser import CDPParser
import argparse 

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
    '--xml_path',
    type=str,
    dest='xml_path',
    help='path (e.g., ../xmls).',
    required=False)
P.add_argument(
    '--figure_path',
    type=str,
    dest='figure_path',
    help='path (e.g., ../figures/',
    required=False)
P.add_argument(
    '--get_ecs',
    type=bool,
    dest='get_ecs',
    help="Flag to compute ECS.\n"
         "True: compute ECS using abrupt-4xCO2 run.\n"
         "False: do not compute, instead rely on ECS value present in the json file (if it exists).",
    required=False)

param = P.get_parameter()

model = param.model
institution = param.institution
variant = param.variant
grid_label = param.grid_label
version = param.version
path = param.path
xml_path = param.xml_path
figure_path = param.figure_path
get_ecs = param.get_ecs

print(
    "model:", model, "\n",
    "institution:", institution, "\n",
    "variant:", variant, "\n",
    "grid_label:", grid_label, "\n", 
    "version:", version, "\n",
    "path:", path, "\n",
    "xml_path:", xml_path, "\n",
    "figure_path:", figure_path, "\n",
    "get_ecs:", get_ecs
)

if get_ecs:
    exps = ['amip','amip-p4K','piControl','abrupt-4xCO2']
else:
    exps = ['amip','amip-p4K']

# generate xmls pointing to the cmorized netcdf files 
os.makedirs(xml_path, exist_ok=True)
filenames={}
for exp in exps:
    filenames[exp]={}
    if exp=='amip-p4K':
        activity = 'CFMIP'
    else:
        activity = 'CMIP'
    if 'amip' in exp:
        fields = ['tas','rsdscs','rsuscs','wap','clisccp'] # necessary for cloud feedback calcs
    else:
        fields = ['tas', 'rlut', 'rsut', 'rsdt'] # needed for ECS calc
    for field in fields:
        if field=='clisccp':
            table='CFmon'
        else:
            table='Amon'
        searchstring = os.path.join(path, activity, institution, model, exp, variant, table, field, grid_label, version, '*.nc')
        xmlname = os.path.join(xml_path, exp+'.'+model+'.'+variant+'.'+field+'.'+version+'.xml')
        os.system('cdscan -x '+xmlname+' '+searchstring)
        filenames[exp][field] = xmlname

# calculate all feedback components and Klein et al (2013) error metrics:
fbk_dict,obsc_fbk_dict,err_dict = CRK.CloudRadKernel(filenames) 

# add this model's results to the pre-existing json file containing other models' results: 
updated_fbk_dict,updated_obsc_fbk_dict = OJ.organize_fbk_jsons(fbk_dict,obsc_fbk_dict,model,variant)
updated_err_dict = OJ.organize_err_jsons(err_dict,model,variant)

ecs = None
if get_ecs:
    # calculate ECS and add it to the pre-existing json file containing other models' results:
    ecs = CE.compute_ECS(filenames) 
updated_ecs_dict = OJ.organize_ecs_jsons(ecs,model,variant)

# plot this model alongside other models and expert assessment:
os.makedirs(figure_path, exist_ok=True)
result = dataviz.make_all_figs(updated_fbk_dict,updated_obsc_fbk_dict,updated_err_dict,updated_ecs_dict,model)

print('Done!')
