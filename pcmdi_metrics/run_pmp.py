import argparse
import os
import json
from pcmdi_metrics.PMPDriver import *
from pcmdi_metrics.PMPParameter import *

parser = argparse.ArgumentParser(
    description='Runs PCMDI Metrics Diagnostics')

parser.add_argument(
    '-p', '--parameters',
    dest='parameter',
    default='',
    help='Path to the user-defined parameter file',
    required=True)
'''
parser.add_argument(
    '--case_id',
    dest='case_id',
    default='',
    help='Defines a subdirectory to the metrics output, so multiple cases ' +
         'can be compared',
    required=False)

parser.add_argument(
    '-t', '--test_data_set',
    dest='test_data_set',
    default=[],
    help='List of observations or models to test ' +
         'against the reference_data_set',
    required=False)

parser.add_argument(
    '--simulation_description_mapping',
    dest='simulation_description_mapping',
    default={},
    help='List of observations or models to test ' +
         'against the reference_data_set',
    required=False,
    type=json.loads)

parser.add_argument(
    '-v', '--vars',
    dest='vars',
    default=[],
    help='Variables to use',
    required=False)

parser.add_argument(
    '--model_tweaks',
    dest='model_tweaks',
    default={},
    help='Model specific tweaks',
    required=False,
    type=json.loads)

parser.add_argument(
    '--regions',
    dest='regions',
    default={},
    help='Regions on which to run the metrics',
    required=False,
    type=json.loads)

parser.add_argument(
    '--regions_values',
    dest='regions_values',
    default={},
    help='Users can customize regions values names',
    required=False,
    type=json.loads)

parser.add_argument(
    '-r', '--reference_data_set',
    dest='reference_data_set',
    default=[],
    help='List of observations or modules that are used as a reference ' +
         'against the test_data_set',
    required=False)

parser.add_argument(
    '--ext',
    dest='ext',
    default='',
    help='Extension for the output files?',
    required=False)

parser.add_argument(
    '--target_grid',
    dest='target_grid',
    default='',
    help='Options are "2.5x2.5" or an actual cdms2 grid object',
    required=False)

parser.add_argument(
    '--regrid_tool',
    dest='regrid_tool',
    default='',
    help='Options are "regrid2" or "esmf"',
    required=False)

parser.add_argument(
    '--regrid_method',
    dest='regrid_method',
    default='',
    help='Options are "linear" or "conservative", ' +
         'only if regrid_tool is "esmf"',
    required=False)

parser.add_argument(
    '--regrid_tool_ocn',
    dest='regrid_tool_ocn',
    default='',
    help='Options are "regrid2" or "esmf"',
    required=False)

parser.add_argument(
    '--regrid_method_ocn',
    dest='regrid_method_ocn',
    default='',
    help='Options are "linear" or "conservative", ' +
         'only if regrid_tool is "esmf"',
    required=False)

parser.add_argument(
    '--period',
    dest='period',
    default='',
    help='A simulation parameter',
    required=False)

parser.add_argument(
    '--realization',
    dest='realization',
    default='',
    help='A simulation parameter',
    required=False)

parser.add_argument(
    '--save_test_clims',
    dest='save_test_clims',
    default='',
    help='True if to save interpolated test climatologies, otherwise False',
    required=False)



parser.add_argument(
    '--filename_template',
    dest='filename_template',
    default='',
    help='Template for climatology files',
    required=False)

parser.add_argument(
    '--sftlf_filename_template',
    dest='sftlf_filename_template',
    default='',
    help='Filename template for landsea masks ("sftlf")',
    required=False)

parser.add_argument(
    '--test_data_path',
    dest='test_data_path',
    default='',
    help='Path for the test climitologies',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)

parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)





parser.add_argument(
    '--xxxx',
    dest='xxxx',
    default='',
    help='descr',
    required=False)
'''


args = parser.parse_args()
parameter = PMPParameter()
# First load the user defined parameter file
parameter.load_parameter_from_py(args.parameter)
'''
# Then overwrite the values of the parameter with the user's args
parameter.case_id = args.case_id
parameter.test_data_set = args.test_data_set
parameter.simulation_description_mapping = args.simulation_description_mapping
parameter.vars = args.vars
parameter.model_tweaks = args.model_tweaks
parameter.regions = args.regions
parameter.regions_values = args.regions_values
parameter.reference_data_set = args.reference_data_set
parameter.ext = args.ext
parameter.target_grid = args.target_grid
parameter.regrid_tool = args.regrid_tool
parameter.regrid_method = args.regrid_method
parameter.regrid_tool_ocn = args.regrid_tool_ocn
parameter.regrid_method_ocn = args.regrid_method_ocn
parameter.period = args.period
parameter.realization = args.realization
parameter.save_test_clims = args.save_test_clims
parameter.filename_template = args.filename_template
parameter.sftlf_filename_template = args.sftlf_filename_template
parameter.test_data_path = args.test_data_path
parameter.reference_data_path = args.reference_data_path
parameter.custom_observations = args.custom_observations
parameter.dry_run = args.dry_run
parameter.metrics_output_path = args.metrics_output_path
parameter.test_clims_interpolated_output = args.test_clims_interpolated_output
parameter.filename_output_template = args.filename_output_template
parameter.compute_custom_metrics = args.compute_custom_metrics
'''
driver = PMPDriver(parameter)
driver.run()
