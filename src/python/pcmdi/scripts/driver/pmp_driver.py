import logging
import os
import cdp.cdp_driver
import pcmdi_metrics.driver.rundiags
import pcmdi_metrics.driver.pmp_parser


class PMPDriver(cdp.cdp_driver.CDPDriver):
    def __init__(self):
        parser = pcmdi_metrics.driver.pmp_parser.PMPParser()
        super(PMPDriver, self).__init__(parser.get_parameter())
        self.run()

    def check_parameter(self):
        # Check that all of the variables used from parameter exist.
        # Just check that the parameters use exist in the parameter object.
        # The validity for each option was already
        #  checked by the parameter itself.
        '''
        vars_to_check = ['case_id', 'test_data_set', 'period', 'realization',
                         'vars', 'reference_data_set', 'target_grid', 'regrid_tool',
                         'regrid_method', 'regrid_tool_ocn',
                         'regrid_method_ocn', 'save_test_clims',
                         'regions_specs', 'regions', 'custom_keys',
                         'filename_template',
                         'generate_surface_type_land_fraction',
                         'surface_type_land_fraction_filename_template',
                         'test_data_path', 'reference_data_path',
                         'metrics_output_path',
                         'test_clims_interpolated_output',
                         'filename_output_template',
                         'custom_observations_path']

        for var in vars_to_check:
            if not hasattr(self.parameter, var):
                logging.error("%s is not in the parameter file!" % var)
                raise AttributeError("%s is not in the parameter file!" % var)
        '''
        # TODO Add this all to PMPParameter class soon
        if getattr(self.parameter, "save_test_clims", False):
            if not hasattr(self.parameter, "test_clims_interpolated_output"):
                self.parameter.test_clims_interpolated_output = os.path.join(
                    self.parameter.metrics_output_path,
                    'interpolated_model_clims')
                logging.warning("Your parameter file asks to save interpolated test climatologies," +
                                " but did not define a path for this\n We set 'test_clims_interpolated" +
                                "_output' to %s for you" % self.parameter.test_clims_interpolated_output)
            if not hasattr(self.parameter, "filename_output_template"):
                template = "%(variable)%(level)_%(model_version)_%(table)_%(realization)" + \
                           "_%(period).interpolated.%(regrid_method).%(target_grid_name)-clim%(ext)"
                self.parameter.filename_output_template = template
                logging.warning("Your parameter file asks to save interpolated model climatologies," +
                                " but did not define a name template for this\nWe set 'filename_output" +
                                "_template' to %s for you" % self.parameter.filename_output_template)
        if not hasattr(self.parameter, 'dry_run'):
            self.parameter.dry_run = True

    def run_diags(self):
        run = pcmdi_metrics.driver.rundiags.RunDiags(self.parameter)
        run()

    def export(self):
        pass
