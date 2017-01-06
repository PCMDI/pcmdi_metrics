import unittest
import pcmdi_metrics
import inspect
import os
import numpy

class TestJSONs(unittest.TestCase):

    def __init__(self):
        super(TestJSONs, self).__init__("variability")

    def variability(self):
        pth = os.path.dirname(inspect.getfile(self.__class__))
        J = pcmdi_metrics.io.base.JSONs([os.path.join(pth,"io","var_mode_NAM_EOF1_stat_cmip5_historical_mo_atm_1900-2005_adjust_based_tcor_obs-pc1_vs_obs-pseudo_pcs.json")])
        axes_ids = J.getAxisIds()
        axes = J.getAxisList()
        assert(axes_ids == ['variable', u'model', u'realization', u'reference', u'mode', u'season', u'statistic'])
        data = J()
        assert(data.shape == (1, 47, 33, 1, 1, 4, 24))
        data = J(mode="NAM", season=["DJF","SON"],realization=["r3i1p1"],statistic=["bias","tcor_obs-pc1_vs_obs-pseudo_pcs","cor"])
        assert(data.shape==(1, 47, 1, 1, 1, 2, 3))
        stats = data.getAxis(-1)
        assert(stats[1]=="tcor_obs-pc1_vs_obs-pseudo_pcs")
        data = J(model = "ACCESS1-0", realization=["r1i1p1",], reference = "defaultReference", mode="NAM", season= "DJF", statistic = "bias")
        assert(numpy.allclose(data,-2.54542104e-05))
        data = J(model = "CCSM4", realization=["r1i2p1",], reference = "defaultReference", mode="NAM", season= "JJA", statistic = "rmsc_glo")
        assert(numpy.allclose(data,0.7626659864144966))
