import unittest
from pcmdi_metrics.PMP.OutputMetrics import *
from pcmdi_metrics.PMP.PMPParameter import *

class testOutputMetrics(unittest.TestCase):

    def setUp(self):
        var = 'tas'
        parameter = PMPParameter()
        parameter.metrics_output_path = '.'
        parameter.target_grid = '2.5x2.5'
        self.output_metrics = OutputMetrics(parameter, var)

    def test_setup_metrics_dictionary(self):
        try:
            self.output_metrics.setup_metrics_dictionary()
        except:
            self.fail('Cannot run setup_metrics_dictionary. Test failed.')

    def test_open_disclaimer(self):
        try:
            self.output_metrics.open_disclaimer()
        except:
            self.fail('Cannot open the disclaimer file. Test failed.')

    def test_set_target_mask(self):
        tool = 'esmf'
        method = 'linear'
        try:
            self.output_metrics.set_target_grid(tool, method)
        except:
            self.fail('Error when using set_target_mask in OutputMetrics.')

    def test_set_var(self):
        try:
            self.output_metrics.set_var('var')
        except:
            self.fail('Error when using set_var in OutputMetrics.')

    def test_set_realm(self):
        try:
            self.output_metrics.set_realm('ocn')
        except:
            self.fail('Error when using set_realm in OutputMetrics.')

    def test_set_table(self):
        try:
            self.output_metrics.set_table('Omon')
        except:
            self.fail('Error when using set_table in OutputMetrics.')

    def test_set_case_id(self):
        try:
            self.output_metrics.set_case_id('test')
        except:
            self.fail('Error when using set_case_id in OutputMetrics.')

if __name__ == '__main__':
    unittest.main()
