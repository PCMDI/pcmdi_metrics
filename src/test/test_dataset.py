import unittest
from pcmdi_metrics.PMP.PMPParameter import *
from pcmdi_metrics.PMP.DataSet import *


class TestDataSet(unittest.TestCase):

    class MyDataSet(DataSet):
        def get(self):
            pass

    def load_obs_dict(self):
        obs_file_name = 'obs_info_dictionary.json'
        obs_json_file = DataSet.load_path_as_file_obj(obs_file_name)
        obs_dic = json.loads(obs_json_file.read())
        obs_json_file.close()
        return obs_dic

    def setUp(self):
        self.parameter = PMPParameter()
        self.parameter.target_grid = '2.5x2.5'
        self.parameter.test_data_set = ['GFDL-ESM2G']
        self.var_name_long = 'tas'
        region_dict = {"tas": ["terre", "ocean", "global"]}
        self.region = region_dict[self.var_name_long][0]
        self.obs_dict = self.load_obs_dict()
        self.data_set = TestDataSet.MyDataSet(self.parameter,
                                              self.var_name_long,
                                              self.region, self.obs_dict)

    def test_calculate_level_with_height(self):
        var = 'hus_850'
        level = self.data_set.calculate_level_from_var(var)
        self.assertEquals(level, 850*100)

    def test_calculate_level_with_no_height(self):
        var = 'hus'
        level = self.data_set.calculate_level_from_var(var)
        self.assertEquals(level, None)

    def test_use_omon_with_false(self):
        result = self.data_set.use_omon(self.obs_dict, self.var_name_long)
        msg = 'use_omon gave the incorrect ans. Check the obs dict .json file.'
        self.assertFalse(result, msg)

    def test_create_sftlf(self):
        # Implicitly done with DataSet.__init__() but whatever.
        try:
            self.data_set.create_sftlf(self.parameter)
        except Exception as e:
            self.fail('Error while running create_sftlf(): %s' % e)

    def test_apply_custom_keys(self):
        custom_keys = {
            "key1": {
                "all": "key1_value_for_all_var",
                "tas": "key1_value_for_tas"
            }
        }
        io_file = PMPIO('', '')
        self.data_set.apply_custom_keys(io_file, custom_keys, 'tas')
        msg = 'apply_custom_keys() failed to put the key in.'
        self.assertTrue('key1' in dir(io_file), msg)

    def test_loading_of_obs_info_dic(self):
        try:
            path = 'obs_info_dictionary.json'
            f = self.data_set.load_path_as_file_obj(path)
        except:
            self.fail('Cannot open obs_info_dictionary.json.')
        finally:
            f.close()

    def test_loading_of_default_regions(self):
        try:
            path = 'default_regions.py'
            f = self.data_set.load_path_as_file_obj(path)
        except:
            self.fail('Cannot open default_regions.py.')
        finally:
            f.close()

    def test_loading_of_default_regions_with_variable_in_it(self):
        try:
            path = 'default_regions.py'
            f = self.data_set.load_path_as_file_obj(path)
            execfile(f.name)
            # This is a variable is from default_regions.py and
            # should be in this namespace now.
            self.regions_specs = locals()['regions_specs']
        except:
            self.fail('Error retrieving regions_specs from default_regions.py')
        finally:
            f.close()

    def test_loading_of_disclaimer_file(self):
        try:
            path = 'disclaimer.txt'
            f = self.data_set.load_path_as_file_obj(path)
        except:
            self.fail('Cannot open disclaimer.txt.')
        finally:
            f.close()

    def test_hash(self):
        # Raises an error because we did not
        # set self.obs_or_model_file in MyDataSet
        with self.assertRaises(TypeError):
            self.data_set.hash()

    def test_file_path(self):
        # Raises an error because we did not
        # set self.obs_or_model_file in MyDataSet
        with self.assertRaises(TypeError):
            self.data_set.file_path()

if __name__ == '__main__':
    unittest.main()
