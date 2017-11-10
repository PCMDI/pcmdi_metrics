import unittest
import cdat_info
import subprocess
import shlex
import os
import cdms2
import numpy

class DiurnalTest(unittest.TestCase):

    def assertSame(self,a,b):
        return numpy.ma.allclose(a,b)

    def compare_nc(self,test_name):
        self.assertTrue(os.path.exists(os.path.join("test_data",test_name)))
        good_name = test_name.replace("test_data","tests/diurnal")

        test_out = cdms2.open(os.path.join("test_data",test_name))
        good_out = cdms2.open(os.path.join("tests/diurnal",test_name))

        self.assertEqual(test_out.variables.keys(),good_out.variables.keys())

        for v in good_out.variables.keys():
            test = test_out(v)
            good = good_out(v)

            self.assertSame(test,good)
        
    def teestDiurnaliComputeStdDailyMean(self):
        cmd = 'computeStdDailyMeansWrapped.py -i test_data -o test_data/results/nc -t "sample_data_pr_%(model).nc" -m7'
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()

        self.compare_nc("results/nc/pr_CMCC_Jul_1999-2005_std_of_dailymeans.nc")

    def testDiurnalStdDailyVariance(self):
        cmd = 'std_of_dailymeansWrappedInOut.py -i tests/diurnal/results/nc -o test_data/results/jsons -m7'
        p = subprocess.Popen(shlex.split(cmd))
        p.communicate()



