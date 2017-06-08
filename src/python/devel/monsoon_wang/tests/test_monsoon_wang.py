import os
import unittest
import pcmdi_metrics
import subprocess
import shlex
import numpy

class MonsoonTest(unittest.TestCase):
    def assertAllClose(self,a,b):
        self.assertTrue(numpy.ma.allclose(a,b))

    def testMonsoonWang(self):
        cmd = 'mpi_compute.py --mp test/monsoon/pr_MODS_Amon_historical_r1i1p1_198001-200512-clim.nc --op test/monsoon/pr_GPCP_000001-000012_ac.nc --mns "[\'NorESM1-ME\',\'MRI-CGCM3\']" --outpd test_monsoon --outpj test_monsoon'
        p = subprocess.Popen(shlex.split(cmd))

        o,e = p.communicate()

        test_file = "test_monsoon/out.json"
        correct_file = "test/monsoon/mpi.json"

        T = pcmdi_metrics.io.base.JSONs([test_file], oneVariablePerFile=False)
        test = T()

        C = pcmdi_metrics.io.base.JSONs([correct_file], oneVariablePerFile=False)
        correct = C()

        self.assertEqual(test.shape,correct.shape)

        self.assertAllClose(correct.filled(),test.filled())

        tax = test.getAxisList()
        cax = correct.getAxisList()

        for i in range(len(tax)):
            self.assertEqual(tax[i].id,cax[i].id)
            for j in range(len(tax[i])):
                self.assertEqual(tax[i][j],cax[i][j])
        os.remove(test_file)
