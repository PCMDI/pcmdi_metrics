
import unittest
import pcmdi_metrics
import inspect
import os

class TestJSONs(unittest.TestCase):

    def __init__(self):
        super(TestJSONs, self).__init__("variability")

    def variability(self):
        pth = os.path.dirname(inspect.getfile(self.__class__))
        J = pcmdi_metrics.io.base.JSONs([os.path.join(pth,"io","var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_1900-2005_adjust_based_tcor_obs-pc1_vs_obs-pseudo_pcs.json")])
        J = pcmdi_metrics.pcmdi.io.JSONs([os.path.join(pth,"io","var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_1900-2005_adjust_based_tcor_obs-pc1_vs_obs-pseudo_pcs.json")])
        axes_ids = J.getAxisIds()
        print axes_ids
        assert(axes_ids == ['variable', u'model', u'realization', u'reference', u'mode', u'season', u'statistic'])
        #data = J()
        #assert(data.shape == (1, 47, 33, 1, 1, 4, 24))
        data = J(mode="NAM")
        print data.shape


