import os
import logging
import cdp.cdp_parameter
from pcmdi_metrics import LOG_LEVEL


class PMPParameter(cdp.cdp_parameter.CDPParameter):
    def __init__(self):
        logging.getLogger("pmp").setLevel(LOG_LEVEL)


class PMPMetricsParameter(cdp.cdp_parameter.CDPParameter):
    def __init__(self):
        logging.getLogger("pcmdi_metrics").setLevel(LOG_LEVEL)

        # Metrics run identification
        self.case_id = ''
        self.period = ''
        self.realization = ''
        self.reference_data_set = []
        self.test_data_set = []

        self.vars = []
        self.target_grid = ''

        self.regrid_tool = ''
        self.regrid_method = ''
        self.regrid_tool_ocn = ''
        self.regrid_method_ocn = ''

        self.regions_specs = {}
        self.regions = {}
        self.regions_values = {}
        self.custom_keys = {}

        self.filename_template = ''
        self.sftlf_filename_template = ''
        self.surface_type_land_fraction_filename_template = ''
        self.generate_surface_type_land_fraction = None

        self.test_data_path = ''
        self.reference_data_path = ''
        self.custom_observations_path = ''
        self.test_clims_interpolated_output = ''

        self.metrics_output_path = ''
        self.filename_output_template = ''
        self.dry_run = False
        self.user_notes = None
        self.output_json_template = "%(variable)%(level)_%(target_grid_name)_%(regrid_tool)_%(regrid_method)_metrics"

    def check_str(self, str_var, str_var_name):
        if type(str_var) is not str:
            raise TypeError(
                "%s is the wrong type. It must be a string." % str_var_name
            )

        if str_var == '':
            logging.getLogger("pcmdi_metrics").warning("%s is blank." % str_var_name)

    def check_str_seq_in_str_list(self, str_sequence,
                                  str_sequence_name, str_vars_list):
        if type(str_sequence) is not list and type(str_sequence) is not tuple:
            raise TypeError(
                ("%s is the wrong type. It must be a list or tuple."
                 % str_sequence_name)
            )

        for str_var in str_sequence:
            if str_var not in str_vars_list:
                logging.getLogger("pcmdi_metrics").warning(
                    ("%s might not be a valid value in %s."
                     % (str_var, str_sequence_name))
                )

    def check_str_var_in_str_list(self, str_var, str_var_name, str_vars_list):
        if type(str_var) is not str:
                raise TypeError(
                    "%s is the wrong type. It must be a string." % str_var_name
                )

        if str_var not in str_vars_list:
                logging.getLogger("pcmdi_metrics").warning(
                    ("%s might not be a valid value in %s."
                     % (str_var, str_var_name))
                )

    def check_case_id(self):
        self.check_str(self.case_id, 'case_id')

    def check_reference_data_set(self):
        if type(self.reference_data_set) is not list \
                and type(self.reference_data_set) is not tuple:
            raise TypeError(
                "reference_data_set is the wrong type." +
                "It must be a list or tuple."
            )

        if self.reference_data_set == [] or self.reference_data_set == ():
            logging.getLogger("pcmdi_metrics").error("reference_data_set is blank.")

    def check_test_data_set(self):
        if type(self.test_data_set) is not list \
                and type(self.test_data_set) is not tuple:
            raise TypeError(
                "test_data_set is the wrong type. It must be a list or tuple."
            )

        if self.test_data_set == [] or self.test_data_set == ():
            logging.getLogger("pcmdi_metrics").error("test_data_set is blank.")

    def check_period(self):
        self.check_str(self.period, 'period')

    def check_realization(self):
        self.check_str(self.realization, 'realization')

    def check_vars(self):
        vars_2d_atmos = ['clt', 'hfss', 'pr', 'prw', 'psl', 'rlut',
                         'rlutcs', 'rsdt', 'rsut', 'rsutcs', 'tas',
                         'tauu', 'tauv', 'ts', 'uas', 'vas']
        vars_3d_atmos = ['hur', 'hus', 'huss', 'ta', 'ua', 'va', 'zg']
        vars_2d_ocean = ['sos', 'tos', 'zos']
        vars_non_std = ['rlwcrf', 'rswcrf']
        vars_values = vars_2d_atmos + vars_3d_atmos \
            + vars_2d_ocean + vars_non_std

        self.check_str_seq_in_str_list(self.vars, 'vars', vars_values)

    def check_ref(self):
        ref_values = ['default', 'all', 'alternate', 'ref3']
        self.check_str_seq_in_str_list(self.reference_data_set, 'reference_data_set', ref_values)

    def check_target_grid(self):
        self.check_str_var_in_str_list(
            self.target_grid, 'target_grid', ['2.5x2.5']
        )

    def check_regrid_tool(self):
        self.check_str_var_in_str_list(
            self.regrid_tool, 'regrid_tool', ['regrid2', 'esmf']
        )

    def check_regrid_method(self):
        self.check_str_var_in_str_list(
            self.regrid_method, 'regrid_method', ['linear', 'conservative']
        )

    def check_regrid_tool_ocn(self):
        self.check_str_var_in_str_list(
            self.regrid_tool_ocn, 'regrid_tool_ocn', ['regrid2', 'esmf']
        )

    def check_regrid_method_ocn(self):
        self.check_str_var_in_str_list(
            self.regrid_method_ocn, 'regrid_method_ocn',
            ['linear', 'conservative']
        )

    def check_save_test_clims(self):
        if self.save_test_clims is None:
            raise ValueError(
                "save_test_clims cannot be None. " +
                "It must be either True or False."
            )

    def check_regions_specs(self):
        if type(self.regions_specs) is not dict:
            raise TypeError(
                "regions_specs is the wrong type. It must be a dictionary."
            )

    def check_regions(self):
        if type(self.regions) is not dict:
            raise TypeError(
                "regions is the wrong type. It must be a dictionary."
            )

    def check_regions_values(self):
        if type(self.regions_values) is not dict:
            raise TypeError(
                "regions_values is the wrong type. It must be a dictionary."
            )

    def check_custom_keys(self):
        if type(self.custom_keys) is not dict:
            raise TypeError(
                "custom_keys is the wrong type. It must be a dictionary."
            )

    def check_filename_template(self):
        self.check_str(self.filename_template, 'filename_template')

    def check_surface_type_land_fraction_filename_template(self):
        self.check_str(self.surface_type_land_fraction_filename_template,
                       'surface_type_land_fraction_filename_template')

    def check_generate_surface_type_land_fraction(self):
        if self.generate_surface_type_land_fraction is None:
            raise ValueError(
                ("generate_surface_type_land_fraction cannot"
                 "be None. It must be either True or False.")
            )

    def check_test_data_path(self):
        self.check_str(self.test_data_path, 'test_data_path')

    def check_reference_data_path(self):
        self.check_str(self.reference_data_path, 'reference_data_path')

    def check_metrics_output_path(self):
        self.check_str(self.metrics_output_path, 'metrics_output_path')

    def check_test_clims_interpolated_output(self):
        self.check_str(self.test_clims_interpolated_output,
                       'test_clims_interpolated_output')

    def check_filename_output_template(self):
        self.check_str(self.filename_output_template,
                       'filename_output_template')

    def check_custom_observations_path(self):
        self.check_str(self.custom_observations_path,
                       'custom_observations_path')

    def check_values(self):
        '''
        # Check that all of the variables in __init__() have a valid value
        self.check_case_id()
        self.check_reference_data_set()
        self.check_test_data_set()
        self.check_period()
        self.check_realization()
        self.check_vars()
        self.check_ref()
        self.check_target_grid()
        self.check_regrid_tool()
        self.check_regrid_method()
        self.check_regrid_tool_ocn()
        self.check_regrid_method_ocn()
        self.check_save_test_clims()
        self.check_regions_specs()
        self.check_regions()
        self.check_custom_keys()
        self.check_filename_template()
        self.check_surface_type_land_fraction_filename_template()
        self.check_generate_surface_type_land_fraction()
        self.check_test_data_path()
        self.check_reference_data_path()
        self.check_metrics_output_path()
        self.check_test_clims_interpolated_output()
        self.check_filename_output_template()
        self.check_custom_observations_path()
        '''
        if getattr(self, "save_test_clims", False):
            if not hasattr(self, "test_clims_interpolated_output"):
                self.test_clims_interpolated_output = os.path.join(
                    self.metrics_output_path,
                    'interpolated_model_clims')
                logging.getLogger("pcmdi_metrics").warning("Your parameter file asks to save interpolated" +
                                                           "test climatologies," +
                                                           " but did not define a path for this\n We set " +
                                                           "'test_clims_interpolated" +
                                                           "_output' to %s for you" %
                                                           self.test_clims_interpolated_output)
            if not hasattr(self, "filename_output_template"):
                template = "%(variable)%(level)_%(model_version)_%(table)_%(realization)" + \
                           "_%(period).interpolated.%(regrid_method).%(target_grid_name)-clim%(ext)"
                self.filename_output_template = template
                logging.getLogger("pcmdi_metrics").warning("Your parameter file asks to save interpolated" +
                                                           "model climatologies," +
                                                           " but did not define a name template for this\n" +
                                                           "We set 'filename_output" +
                                                           "_template' to %s for you" %
                                                           self.filename_output_template)
        if not hasattr(self, 'dry_run'):
            self.dry_run = True
