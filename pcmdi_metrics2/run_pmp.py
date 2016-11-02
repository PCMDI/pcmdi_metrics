import argparse
import os
import json
from pcmdi_metrics2.pmp_driver import *
from pcmdi_metrics2.pmp_parameter import *

parser = argparse.ArgumentParser(
    description='Runs PCMDI Metrics Diagnostics')

parser.add_argument(
    '-p', '--parameters',
    dest='parameter',
    help='Path to the user-defined parameter file',
    required=True)

parser.add_argument(
    '--case_id',
    dest='case_id',
    help='Defines a subdirectory to the metrics output, so multiple cases ' +
         'can be compared',
    required=False)

parser.add_argument(
    '-v', '--vars',
    type=str,
    nargs='+',
    dest='vars',
    help='Variables to use',
    required=False)

parser.add_argument(
    '--regions',
    type=json.loads,
    dest='regions',
    help='Regions on which to run the metrics',
    required=False)

parser.add_argument(
    '--regions_values',
    type=json.loads,
    dest='regions_values',
    help='Users can customize regions values names',
    required=False)

parser.add_argument(
    '-r', '--reference_data_set',
    type=str,
    nargs='+',
    dest='reference_data_set',
    help='List of observations or models that are used as a reference ' +
         'against the test_data_set',
    required=False)

parser.add_argument(
    '--reference_data_path',
    dest='reference_data_path',
    help='Path for the reference climitologies',
    required=False)

parser.add_argument(
    '-t', '--test_data_set',
    type=str,
    nargs='+',
    dest='test_data_set',
    help='List of observations or models to test ' +
         'against the reference_data_set',
    required=False)

parser.add_argument(
    '--test_data_path',
    dest='test_data_path',
    help='Path for the test climitologies',
    required=False)

parser.add_argument(
    '--target_grid',
    dest='target_grid',
    help='Options are "2.5x2.5" or an actual cdms2 grid object',
    required=False)

parser.add_argument(
    '--regrid_tool',
    dest='regrid_tool',
    help='Options are "regrid2" or "esmf"',
    required=False)

parser.add_argument(
    '--regrid_method',
    dest='regrid_method',
    help='Options are "linear" or "conservative", ' +
         'only if regrid_tool is "esmf"',
    required=False)

parser.add_argument(
    '--regrid_tool_ocn',
    dest='regrid_tool_ocn',
    help='Options are "regrid2" or "esmf"',
    required=False)

parser.add_argument(
    '--regrid_method_ocn',
    dest='regrid_method_ocn',
    help='Options are "linear" or "conservative", ' +
         'only if regrid_tool is "esmf"',
    required=False)

parser.add_argument(
    '--period',
    dest='period',
    help='A simulation parameter',
    required=False)

parser.add_argument(
    '--realization',
    dest='realization',
    help='A simulation parameter',
    required=False)

parser.add_argument(
    '--simulation_description_mapping',
    type=json.loads,
    dest='simulation_description_mapping',
    help='List of observations or models to test ' +
         'against the reference_data_set',
    required=False)

parser.add_argument(
    '--model_tweaks',
    type=json.loads,
    dest='model_tweaks',
    help='Model specific tweaks',
    required=False)

parser.add_argument(
    '--ext',
    dest='ext',
    help='Extension for the output files?',
    required=False)

parser.add_argument(
    '--dry_run',
    # If input is 'True' or 'true', return True. Otherwise False.
    type=lambda x: x.lower() == 'true',
    dest='dry_run',
    help='True if output is to be created, False otherwise',
    required=False)

parser.add_argument(
    '--filename_template',
    dest='filename_template',
    help='Template for climatology files',
    required=False)

parser.add_argument(
    '--sftlf_filename_template',
    dest='sftlf_filename_template',
    help='Filename template for landsea masks ("sftlf")',
    required=False)

parser.add_argument(
    '--custom_observations',
    dest='custom_observations',
    help='Path to an alternative, custom observation file',
    required=False)

parser.add_argument(
    '--metrics_output_path',
    dest='metrics_output_path',
    help='Directory of where to put the results',
    required=False)

parser.add_argument(
    '--filename_output_template',
    dest='filename_output_template',
    help='Filename for the interpolated test climatologies',
    required=False)

parser.add_argument(
    '--save_test_clims',
    # If input is 'True' or 'true', return True. Otherwise False.
    type=lambda x: x.lower() == 'true',
    dest='save_test_clims',
    help='True if to save interpolated test climatologies, otherwise False',
    required=False)

parser.add_argument(
    '--test_clims_interpolated_output',
    dest='test_clims_interpolated_output',
    help='Directory of where to put the interpolated test climatologies',
    required=False)

parser.add_argument(
    '--compute_custom_metrics',
    dest='compute_custom_metrics',
    help='Allows for user-defined metrics',
    required=False)

args = parser.parse_args()
parameter = PMPParameter()
# First load the user defined parameter file
parameter.load_parameter_from_py(args.parameter)

# Then overwrite the values of the parameter with the user's args
for arg_name, arg_value in vars(args).iteritems():
    if arg_value is not None:
        # Add it to the parameter
        setattr(parameter, arg_name, arg_value)

driver = PMPDriver(parameter)
driver.run()
