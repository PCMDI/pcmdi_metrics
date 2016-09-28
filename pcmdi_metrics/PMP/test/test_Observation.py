import unittest
from pcmdi_metrics.PMP.Observation import *
from pcmdi_metrics.PMP.PMPParameter import *
from pcmdi_metrics.PMP.PMPDriverRunDiags import *


class testObservation(unittest.TestCase):

    def setUp(self):
        self.parameter = PMPParameter()
        self.parameter.data_set_a = ['all']
        self.var = 'tos'
        self.obs = 'all'
        self.obs_dict = PMPDriverRunDiags(self.parameter).load_obs_dict()
        self.observation = Observation(self.parameter, self.var, self.obs,
                                       self.obs_dict)

    def test_OBS(self):
        root = '.'
        try:
            obs = OBS(root, self.var, self.obs_dict)
        except:
            self.fail('Error initializing an OBS object.')

    def test_OBS_with_runtime_error(self):
        root = '.'
        var = 'sftlf'
        with self.assertRaises(RuntimeError):
            obs = OBS(root, var, self.obs_dict)

    def test_setup_obs_list_from_parameter_with_all(self):
        obs_list = ['all']
        result = Observation.setup_obs_list_from_parameter(obs_list,
                                                           self.obs_dict,
                                                           self.var)
        self.assertEquals(result, [u'default'])

    def test_setup_obs_list_from_parameter_without_all(self):
        obs_list = ['default', 'alternate']
        result = Observation.setup_obs_list_from_parameter(obs_list,
                                                           self.obs_dict,
                                                           self.var)
        self.assertEquals(result, obs_list)

    def test_create_obs_mask_name(self):
        result = self.observation.create_obs_mask_name()
        self.assertEquals(result, None)

    def test_create_obs_mask_name_2(self):
        obs = Observation(self.parameter, self.var, 'default', self.obs_dict)
        result = obs.create_obs_mask_name()
        actual_result = '//fx/sftlf/UKMETOFFICE-HadISST-v1-1/sftlf_pcmdi' +\
                        '-metrics_fx_UKMETOFFICE-HadISST-v1-1_198002-200501' +\
                        '-clim.nc.json'
        self.assertEquals(result, actual_result)


if __name__ == '__main__':
    unittest.main()
