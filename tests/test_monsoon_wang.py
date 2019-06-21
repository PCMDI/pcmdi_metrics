from __future__ import print_function
import os
import unittest
import pcmdi_metrics
import numpy
from pcmdi_metrics.monsoon_wang import create_monsoon_wang_parser, monsoon_wang_runner


class MonsoonTest(unittest.TestCase):
    def checkAllClose(self, a, b):
        if numpy.ma.allclose(a.filled(), b.filled()):
            return True
        else:
            axes = a.getAxisList()
            c = numpy.isclose(a.filled(), b.filled())
            w = numpy.argwhere(c == 0)
            for d in w:
                print("Error for:", end=' ')
                for i, indx in enumerate(d):
                    print("%s, " % axes[i][indx], end=' ')
                print("(", end=' ')
                for indx in d:
                    print("%i," % indx, end=' ')
                print("). Test value %.3f vs expected value: %.3f" %
                      (a[tuple(d)], b[tuple(d)]))
            return False
        return True

    def testMonsoonWang(self):

        P = create_monsoon_wang_parser()
        P.add_args_and_values(["--test_data_path",
                               "tests/monsoon/data/%(variable)_1961_1999_MRI-CGCM3_regrid_%(model).nc",
                               "--reference_data_path",
                               "tests/monsoon/obs/pr_gpcp_79_07_mseas.nc",
                               "--mns",
                               "['xa',]",
                               "--results_dir",
                               "test_monsoon",
                               "--threshold=2.5"])
        args = P.get_parameter()
        monsoon_wang_runner(args)

        test_file = "test_monsoon/monsoon_wang.json"
        correct_file = "tests/monsoon/mpi.json"

        self.compareJsons(test_file, correct_file)
        os.remove(test_file)

    def compareJsons(self, test_file, correct_file):

        print("Comparing:", test_file, correct_file)
        T = pcmdi_metrics.io.base.JSONs([test_file], oneVariablePerFile=False)
        test = T()

        V = pcmdi_metrics.io.base.JSONs(
            [correct_file], oneVariablePerFile=False)
        valid = V()

        self.assertEqual(test.shape, valid.shape)

        tax = test.getAxisList()
        cax = valid.getAxisList()

        correct = True
        for i in range(len(tax)):
            if not tax[i].id == cax[i].id:
                print("Axes index %i have different names, test is '%s' vs expected: '%s'" % (
                    i, tax[i].id, cax[i].id))
                correct = False
            for j in range(len(tax[i])):
                if not tax[i][j] == cax[i][j]:
                    print("Axes %s, differ at index %i, test value: %s vs expectedi value: %s" % (
                        tax[i].id, j, tax[i][j], cax[i][j]))
                    correct = False

        if not self.checkAllClose(test, valid):
            correct = False

        if not correct:
            raise Exception("jsons file %s differ from correct one: %s" % (
                test_file, correct_file))
