import ast
import cdp.cdp_parser
from pcmdi_metrics.driver.pmp_parameter import *


class PMPParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPParser, self).__init__(PMPParameter, *args, **kwargs)

    def load_default_args(self):
        super(PMPParser, self).load_default_args()

        self.add_argument(
            '--case_id',
            dest='case_id',
            help='Defines a subdirectory to the metrics output, so multiple' +
                 'cases can be compared',
            required=False)

        self.add_argument(
            '-v', '--vars',
            type=str,
            nargs='+',
            dest='vars',
            help='Variables to use',
            required=False)

        self.add_argument(
            '--regions',
            type=ast.literal_eval,
            dest='regions',
            help='Regions on which to run the metrics',
            required=False)

        self.add_argument(
            '--regions_values',
            type=ast.literal_eval,
            dest='regions_values',
            help='Users can customize regions values names',
            required=False)

        self.add_argument(
            '-r', '--reference_data_set',
            type=str,
            nargs='+',
            dest='reference_data_set',
            help='List of observations or models that are used as a ' +
                 'reference against the test_data_set',
            required=False)

        self.add_argument(
            '--reference_data_path',
            dest='reference_data_path',
            help='Path for the reference climitologies',
            required=False)

        self.add_argument(
            '-t', '--test_data_set',
            type=str,
            nargs='+',
            dest='test_data_set',
            help='List of observations or models to test ' +
                 'against the reference_data_set',
            required=False)

        self.add_argument(
            '--test_data_path',
            dest='test_data_path',
            help='Path for the test climitologies',
            required=False)

        self.add_argument(
            '--target_grid',
            dest='target_grid',
            help='Options are "2.5x2.5" or an actual cdms2 grid object',
            required=False)

        self.add_argument(
            '--regrid_tool',
            dest='regrid_tool',
            help='Options are "regrid2" or "esmf"',
            required=False)

        self.add_argument(
            '--regrid_method',
            dest='regrid_method',
            help='Options are "linear" or "conservative", ' +
                 'only if regrid_tool is "esmf"',
            required=False)

        self.add_argument(
            '--regrid_tool_ocn',
            dest='regrid_tool_ocn',
            help='Options are "regrid2" or "esmf"',
            required=False)

        self.add_argument(
            '--regrid_method_ocn',
            dest='regrid_method_ocn',
            help='Options are "linear" or "conservative", ' +
                 'only if regrid_tool is "esmf"',
            required=False)

        self.add_argument(
            '--period',
            dest='period',
            help='A simulation parameter',
            required=False)

        self.add_argument(
            '--realization',
            dest='realization',
            help='A simulation parameter',
            required=False)

        self.add_argument(
            '--simulation_description_mapping',
            type=ast.literal_eval,
            dest='simulation_description_mapping',
            help='List of observations or models to test ' +
                 'against the reference_data_set',
            required=False)

        self.add_argument(
            '--model_tweaks',
            type=ast.literal_eval,
            dest='model_tweaks',
            help='Model specific tweaks',
            required=False)

        self.add_argument(
            '--ext',
            dest='ext',
            help='Extension for the output files?',
            required=False)

        self.add_argument(
            '--dry_run',
            # If input is 'True' or 'true', return True. Otherwise False.
            type=lambda x: x.lower() == 'true',
            dest='dry_run',
            help='True if output is to be created, False otherwise',
            required=False)

        self.add_argument(
            '--filename_template',
            dest='filename_template',
            help='Template for climatology files',
            required=False)

        self.add_argument(
            '--sftlf_filename_template',
            dest='sftlf_filename_template',
            help='Filename template for landsea masks ("sftlf")',
            required=False)

        self.add_argument(
            '--custom_observations',
            dest='custom_observations',
            help='Path to an alternative, custom observation file',
            required=False)

        self.add_argument(
            '--metrics_output_path',
            dest='metrics_output_path',
            help='Directory of where to put the results',
            required=False)

        self.add_argument(
            '--filename_output_template',
            dest='filename_output_template',
            help='Filename for the interpolated test climatologies',
            required=False)

        self.add_argument(
            '--save_test_clims',
            # If input is 'True' or 'true', return True. Otherwise False.
            type=lambda x: x.lower() == 'true',
            dest='save_test_clims',
            help='True if to save interpolated test climatologies,' +
                 ' otherwise False',
            required=False)

        self.add_argument(
            '--test_clims_interpolated_output',
            dest='test_clims_interpolated_output',
            help='Directory of where to put the interpolated ' +
                 'test climatologies',
            required=False)

        self.add_argument(
            '--compute_custom_metrics',
            dest='compute_custom_metrics',
            help='Allows for user-defined metrics',
            required=False)
