import unittest
import pcmdi_metrics
import inspect
import os
import numpy
import json


class TestJSONs(unittest.TestCase):
    def testMerge(self):
        pth = os.path.dirname(inspect.getfile(self.__class__))
        J = pcmdi_metrics.io.base.JSONs([os.path.join(
            pth, "io", "merge_incomplete_and_missing.json")],
            oneVariablePerFile=False)

        merged = J(merge=["numbers", "lower"])
        axes_ids = merged.getAxisIds()
        axes = merged.getAxisList()
        self.assertEqual(axes_ids, ["upper", "numbers_lower"])
        self.assertEqual(merged.shape, (4, 37))
        self.assertEqual(merged.getAxis(1)[:].tolist(),
                         ['1_a', '1_b', '1_c', '1_d', '1_e', '2_a', '2_b', '2_c', '2_d', '2_e', '3_a', '3_b', '3_d', '3_e', '4_a', '4_b',
                          '4_c', '4_d', '4_e', '5_a', '5_b', '5_d', '5_e', '6_a', '6_b', '6_c', '6_d', '6_e', '7_a', '7_b', '7_c', '7_d', '7_e', '8_a', '8_b', '8_d', '8_e'])
        self.assertTrue(merged.asma()[1, 3] is numpy.ma.masked)
        self.assertEqual(merged[1, 4], 14)
