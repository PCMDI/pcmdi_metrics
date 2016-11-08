import unittest
from pcmdi_metrics.PMP.Model import *
from pcmdi_metrics.PMP.PMPParameter import *


class TestModel(unittest.TestCase):

    def load_obs_dict(self):
        obs_file_name = 'obs_info_dictionary.json'
        obs_json_file = DataSet.load_path_as_file_obj(obs_file_name)
        obs_dic = json.loads(obs_json_file.read())
        obs_json_file.close()
        return obs_dic

    def setUp(self):
        parameter = PMPParameter()
        parameter.test_data_set = ['GFDL-ESM2G']
        parameter.target_grid = '2.5x2.5'
        parameter.regrid_tool = 'regrid2'
        parameter.regrid_method = 'linear'
        parameter.regrid_tool_ocn = 'esmf'
        parameter.regrid_method_ocn = 'linear'
        parameter.metrics_output_path = '.'
        parameter.test_data_path = os.path.join(
            './',
            'metrics_results', "%(case_id)")
        parameter.filename_template = \
            "%(variable)_%(model_version)_%(table)_historical_%(realization)"+\
            "_%(period)-clim.nc"
        #regions_values = {"terre": 0.0 }
        '''regions_specs = {"Nino34":
                 {"value": 0.,
                  "domain": cdutil.region.domain(latitude=(-5., 5., "ccb"), longitude=(190., 240., "ccb"))},
                 "NAM": {"value": 0.,
                         "domain": {'latitude': (0., 45.), 'longitude': (210., 310.)},
                         }
                 }
        '''
        var = 'tas'
        region_dict = {"tas": ["terre", "ocean", "global"]}
        #region = region_dict[var][0]
        region = {'id': 'global'}
        obs_dict = self.load_obs_dict()
        model = parameter.test_data_set[0]

        self.model = Model(parameter, var, region, model, obs_dict)

    def test_get(self):
        print self.model.get()

if __name__ == '__main__':
    unittest.main()
