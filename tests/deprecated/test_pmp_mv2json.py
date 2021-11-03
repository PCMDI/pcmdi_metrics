import unittest
from pcmdi_metrics.io import MV2Json
import MV2
import cdms2


class TestMV2Json(unittest.TestCase):
    def test2D(self):
        a = MV2.array(range(6))
        a = MV2.resize(a, (2, 3))
        ax1 = cdms2.createAxis(["A", "B"], id="UPPER")
        ax2 = cdms2.createAxis(["a", "b", "c"], id="lower")
        a.setAxis(0, ax1)
        a.setAxis(1, ax2)
        jsn, struct = MV2Json(a)
        self.assertEqual(
            jsn, {'A': {'a': 0, 'b': 1, 'c': 2}, 'B': {'a': 3, 'b': 4, 'c': 5}})
        self.assertEqual(struct, ['UPPER', 'lower'])

    def test3D(self):
        self.maxDiff = None
        a = MV2.array(range(24))
        a = MV2.resize(a, (2, 4, 3))
        ax1 = cdms2.createAxis(["A", "B"], id="UPPER")
        ax2 = cdms2.createAxis(["1", "2", "3", "4"], id="numbers")
        ax3 = cdms2.createAxis(["a", "b", "c"], id="lower")
        a.setAxis(0, ax1)
        a.setAxis(1, ax2)
        a.setAxis(2, ax3)
        jsn, struct = MV2Json(a)
        self.assertEqual(jsn, {'A': {'1': {'a': 0, 'b': 1, 'c': 2},
                                      '2': {'a': 3, 'b': 4, 'c': 5},
                                      '3': {'a': 6, 'b': 7, 'c': 8},
                                      '4': {'a': 9, 'b': 10, 'c': 11}},
                                'B': {'1': {'a': 12, 'b': 13, 'c': 14},
                                      '2': {'a': 15, 'b': 16, 'c': 17},
                                      '3': {'a': 18, 'b': 19, 'c': 20},
                                      '4': {'a': 21, 'b': 22, 'c': 23}}})

        self.assertEqual(struct, ['UPPER', 'numbers', 'lower'])
