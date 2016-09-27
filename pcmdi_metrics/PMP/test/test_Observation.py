import unittest
from pcmdi_metrics.PMP.Observation import *
from pcmdi_metrics.PMP.PMPParameter import *
from pcmdi_metrics.PMP.PMPDriverRunDiags import *


class testObservation(unittest.TestCase):

    def setUp(self):
        self.parameter = PMPParameter()
        self.parameter.data_set_a = ['all']
        self.var = 'sftlf'
        self.obs = 'all'
        self.observation = Observation(self.parameter, self.var, self.obs)
        self.obs_dict = PMPDriverRunDiags(self.parameter).load_obs_dict()

    def test_setup_obs_list_from_parameter_with_all(self):
        obs_list = ['all']
        result = Observation.setup_obs_list_from_parameter(obs_list,
                                                           self.obs_dict,
                                                           self.var)
        self.assertEquals(result, [])

    def test_setup_obs_list_from_parameter_without_all(self):
        obs_list = ['default', 'alternate']
        result = Observation.setup_obs_list_from_parameter(obs_list,
                                                           self.obs_dict,
                                                           self.var)
        self.assertEquals(result, obs_list)

if __name__ == '__main__':
    unittest.main()
