import unittest
from CDP.PMP.PMPParameter import *

class testPMPParameter(unittest.TestCase):

    def setUp(self):
        self.pmp_parameter = PMPParameter()


    def test_check_case_id_with_nonstr_value(self):
        self.pmp_parameter.case_id = ['sampletest_140910']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_case_id()

    def test_check_model_versions_with_nonlist_value(self):
        self.pmp_parameter.model_versions = 'GFDL-CM4'
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_model_versions()

    def test_check_period_with_nonstr_value(self):
        self.pmp_parameter.period = ['000101-000112']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_period()

    def test_check_realization_with_nonstr_value(self):
        self.pmp_parameter.realization = ['r1i1p1']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_realization()

    def test_check_vars_with_nonlist_value(self):
        self.pmp_parameter.vars = 'clt, hfss, pr'
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_vars()

    def test_check_ref_with_nonlist_value(self):
        self.pmp_parameter.ref = 'default'
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_ref()

    def test_check_target_grid_with_nonstr_value(self):
        self.pmp_parameter.target_grid = ['default']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_target_grid()

    def test_check_regrid_tool_with_nonstr_value(self):
        self.pmp_parameter.regrid_tool = ['regrid2']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_regrid_tool()

    def test_check_regrid_method_with_nonstr_value(self):
        self.pmp_parameter.regrid_method = ['linear']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_regrid_method()

    def test_check_save_mod_clims_with_none(self):
        self.pmp_parameter.save_mod_clims = None
        with self.assertRaises(ValueError):
            self.pmp_parameter.check_save_mod_clims()

    def test_check_regions_specs_with_non_dict(self):
        self.pmp_parameter.regions_specs = ['Nino34']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_regions_specs()

    def test_check_regions_with_non_dict(self):
        self.pmp_parameter.regions = ['Nino34']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_regions()

    def test_check_regions_values_with_non_dict(self):
        self.pmp_parameter.regions_values = ['Nino34']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_regions_values()

    def test_check_custom_keys_with_non_dict(self):
        self.pmp_parameter.custom_keys = ['Nino34']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_custom_keys()

    def test_check_filename_template_with_nonstr_value(self):
        self.pmp_parameter.filename_template = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_filename_template()

    def test_check_surface_type_land_fraction_filename_template_with_nonstr_value(self):
        self.pmp_parameter.surface_type_land_fraction_filename_template \
            = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_surface_type_land_fraction_filename_template()

    def test_check_generate_surface_type_land_fraction_with_none(self):
        self.pmp_parameter.generate_surface_type_land_fraction = None
        with self.assertRaises(ValueError):
            self.pmp_parameter.check_generate_surface_type_land_fraction()

    def test_check_mod_data_path_with_nonstr_value(self):
        self.pmp_parameter.mod_data_path = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_mod_data_path()

    def test_check_obs_data_path_with_nonstr_value(self):
        self.pmp_parameter.obs_data_path = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_obs_data_path()

    def test_check_metrics_output_path_with_nonstr_value(self):
        self.pmp_parameter.metrics_output_path = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_metrics_output_path()

    def test_check_model_clims_interpolated_output_with_nonstr_value(self):
        self.pmp_parameter.model_clims_interpolated_output \
            = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_model_clims_interpolated_output()

    def test_check_mod_data_path_with_nonstr_value(self):
        self.pmp_parameter.filename_output_template = ['%(variable)_%(period)']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_filename_output_template()

    def test_check_check_custom_observations_path_with_nonstr_value(self):
        self.pmp_parameter.custom_observations_path \
            = ['/path/to/some/file.json']
        with self.assertRaises(TypeError):
            self.pmp_parameter.check_custom_observations_path()

if __name__ == '__main__':
    unittest.main()
