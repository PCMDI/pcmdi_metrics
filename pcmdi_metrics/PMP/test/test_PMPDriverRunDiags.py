import unittest
from pcmdi_metrics.PMP.PMPDriverRunDiags import *
from pcmdi_metrics.PMP.OutputMetrics import *

class testPMPDriverRunDiags(unittest.TestCase):

    def setUp(self):
        self.pmp_parameter = PMPParameter()
        self.pmp_parameter.metrics_output_path = '.'
        self.pmp_parameter.target_grid = '2.5x2.5'
        self.pmp_driver_run_diags = PMPDriverRunDiags(self.pmp_parameter)
        # Usually var is loaded from the parameter.
        self.pmp_driver_run_diags.var = 'tos'


    def test_load_obs_dict(self):
        try:
            self.pmp_driver_run_diags.load_obs_dict()
        except:
            self.fail('Cannot run load_obs_dict(). Test failed.')

    def test_loading_of_obs_info_dic(self):
        try:
            path = 'obs_info_dictionary.json'
            f = self.pmp_driver_run_diags.load_path_as_file_obj(path)
        except:
            self.fail('Cannot open obs_info_dictionary.json. Test failed.')
        finally:
            f.close()

    def test_loading_of_default_regions(self):
        try:
            path = 'default_regions.py'
            f = self.pmp_driver_run_diags.load_path_as_file_obj(path)
        except:
            self.fail('Cannot open default_regions.py. Test failed.')
        finally:
            f.close()

    def test_loading_of_default_regions_with_variable_in_it(self):
        try:
            path = 'default_regions.py'
            f = self.pmp_driver_run_diags.load_path_as_file_obj(path)
            execfile(f.name)
            # This is variable is from default_regions.py and should be in this
            # namespace now.
            self.regions_specs
        except:
            self.fail('Cannot access self.regions_specs, error regarding default_regions.py. Test failed.')
        finally:
            f.close()

    def test_loading_of_disclaimer_file(self):
        try:
            path = 'disclaimer.txt'
            f = self.pmp_driver_run_diags.load_path_as_file_obj(path)
        except:
            self.fail('Cannot open disclaimer.txt. Test failed.')
        finally:
            f.close()

    def test_use_omon(self):
        obs_dict = self.pmp_driver_run_diags.load_obs_dict()
        var = 'tos'
        if not self.pmp_driver_run_diags.use_omon(obs_dict, var):
            msg = 'use_omon() returns the wrong answer '\
                  + 'or the obs_dict has changed'
            self.fail(msg)

    def test_calculate_level_with_height(self):
        var = 'hus_850'
        level = self.pmp_driver_run_diags.calculate_level_from_var(var)
        self.assertEquals(level, 850*100)

    def test_calculate_level_with_no_height(self):
        var = 'hus'
        level = self.pmp_driver_run_diags.calculate_level_from_var(var)
        self.assertEquals(level, None)

    def test_setup_obs_or_metric_or_output_file(self):
        #try:
        om = OutputMetrics(self.pmp_parameter, 'var')
        self.pmp_driver_run_diags.setup_obs_or_metric_or_output_file(om)
        #except:
            #self.fail('Error while running setup_obs_or_metric_or_output_file.')

if __name__ == '__main__':
    unittest.main()
