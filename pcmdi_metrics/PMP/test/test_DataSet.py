import unittest
from pcmdi_metrics.PMP.PMPParameter import *
from pcmdi_metrics.PMP.DataSet import *


class testDataSet(unittest.TestCase):

    class TestDataSet(DataSet):
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
        self.var_name_long = 'tas'
        region_dict = {"tas": ["terre", "ocean", "global"]}
        self.region = region_dict[self.var_name_long][0]
        self.obs_dict = self.load_obs_dict()
        self.data_set = testDataSet.TestDataSet(self.parameter,
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

if __name__ == '__main__':
    unittest.main()
