import unittest
from pcmdi_metrics.PMP.PMPParameter import *
from pcmdi_metrics.PMP.PMPDriverRunDiags import *

class testPMPDriverRunDiags(unittest.TestCase):

    def setUp(self):
        self.pmp_parameter = PMPParameter()
        self.pmp_driver_run_diags = PMPDriverRunDiags(self.pmp_parameter)

    def test_load_obs_dic(self):
        try:
            self.pmp_driver_run_diags.load_obs_dic()
        except:
            self.fail('Cannot run load_obs_dic(). Test failed.')

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


if __name__ == '__main__':
    unittest.main()
