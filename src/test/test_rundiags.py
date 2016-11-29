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
        # Though load_obs_dict() is a test itself, we need this for other tests
        self.obs_dict = self.pmp_driver_run_diags.load_obs_dict()


    def test_load_obs_dict(self):
        try:
            self.pmp_driver_run_diags.load_obs_dict()
        except:
            self.fail('Cannot run load_obs_dict(). Test failed.')

    def test_use_omon(self):
        obs_dict = self.pmp_driver_run_diags.load_obs_dict()
        var = 'tos'
        if not self.pmp_driver_run_diags.use_omon(obs_dict, var):
            msg = 'use_omon() returns the wrong answer '\
                  + 'or the obs_dict has changed'
            self.fail(msg)

    def test_setup_obs_or_model_or_output_file(self):
        try:
            om = OutputMetrics(self.pmp_parameter, 'var')
            self.pmp_driver_run_diags.setup_obs_or_model_or_output_file(om)
        except:
            self.fail('Error while running setup_obs_or_metric_or_output_file.')

    def test_is_data_set_obs_with_obs(self):
        obs = ['default']
        obs_true = self.pmp_driver_run_diags.is_data_set_obs(obs, self.obs_dict)
        self.assertEquals(obs_true, True)

    def test_is_data_set_obs_with_model(self):
        models = ['CNRM-CM5', 'CanAM4']
        models_false = self.pmp_driver_run_diags.is_data_set_obs(models, self.obs_dict)
        self.assertEquals(models_false, False)

if __name__ == '__main__':
    unittest.main()


