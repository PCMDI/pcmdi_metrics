import pcmdi_metrics
import json
import unittest
import numpy


class JSONTest(unittest.TestCase):
    def testMerge(self):
        data = {}
        for i in range(8):
            data[i] = {}
            for j in range(7):
                data[i][j] = {}
                for k in range(6):
                    data[i][j][k] = {}
                    for l in range(5):
                        data[i][j][k][l] = {}
                        for m in range(4):
                            data[i][j][k][l][m] = i + j/10. + k/100. + l/1000. + m/10000.

        out = {"RESULTS": data,
            "json_structure": ["i", "j", "k", "l", "m"],
            "json_version": 3.0
            }

        with open("data.json", "w") as f:
            json.dump(out, f)


        J = pcmdi_metrics.io.base.JSONs(["data.json"], oneVariablePerFile=False)


        regular = J()
        self.assertEqual(regular.shape, (8,7,6,5,4))
        merged_one = J(merge=[["k", "l"]])
        self.assertEqual(merged_one.shape, (8,7,30,4))

        merged_two = J(merge=[["j", "m"], ["k", "l"]])
        self.assertEqual(merged_two.shape, (8,28,30))
        merged_three = J(merge=[["k", "l"], ["j","m"]])
        self.assertEqual(merged_three.shape, (8,28,30))
        merged_four = J(merge=[["j","m"],["k","i"]])
        self.assertEqual(merged_four.shape, (48, 28, 5))

        merged_five = J(merge=[["i","k","l"], ["j", "m"]])
        self.assertEqual(merged_five.shape, (240, 28))
        regular = regular.filled()
        merged_six = J(merge=["l","m"]).filled()
        self.assertEqual(merged_six.shape, (8,7,6,20))
        self.assertTrue(numpy.allclose(regular[0,0,0].flat, merged_six[0,0,0].flat))

        merged_seven = J(merge=["m","l"]).filled()
        self.assertTrue(numpy.allclose(numpy.transpose(regular[0,0,0]).flat, merged_seven[0,0,0].flat))
