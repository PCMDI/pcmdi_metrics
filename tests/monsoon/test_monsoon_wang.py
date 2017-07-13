import os
import unittest
import pcmdi_metrics
import subprocess
import shlex
import numpy


class MonsoonTest(unittest.TestCase):
    def checkAllClose(self, a, b):
        if numpy.ma.allclose(a.filled(), b.filled()):
            return True
        else:
            axes =a.getAxisList()
            c = numpy.isclose(a.filled(),b.filled())
            w = numpy.argwhere(c==0)
            for d in w:
                print "Error for:",
                for i,indx in enumerate(d):
                    print "%s, " % axes[i][indx],
                print "(",
                for indx in d:
                    print "%i," % indx,
                print "). Test value %.3f vs expected value: %.3f" % (a[tuple(d)],b[tuple(d)])
            return False
        return True

    def testMonsoonWang(self):

        cmd = 'mpindex_compute.py --mp tests/monsoon/data/pr_MODS_Amon_historical_r1i1p1_198001-200512-clim.nc --op tests/monsoon/obs/pr_GPCP_000001-000012_ac.nc --mns "[\'NorESM1-ME\',\'MRI-CGCM3\']" --outpd test_monsoon --outpj test_monsoon'
        p = subprocess.Popen(shlex.split(cmd))
        o, e = p.communicate()

        test_file = "test_monsoon/out.json"
        correct_file = "tests/monsoon/mpi.json"

        self.compareJsons(test_file,correct_file)
        os.remove(test_file)


    def compareJsons(self, test_file, correct_file):

        print "Comparing:",test_file, correct_file
        T = pcmdi_metrics.io.base.JSONs([test_file], oneVariablePerFile=False)
        test = T()

        V = pcmdi_metrics.io.base.JSONs([correct_file], oneVariablePerFile=False)
        valid = V()

        self.assertEqual(test.shape, valid.shape)


        tax = test.getAxisList()
        cax = valid.getAxisList()

        correct = True
        for i in range(len(tax)):
            if not tax[i].id == cax[i].id:
                print "Axes index %i have different names, test is '%s' vs expected: '%s'" % (i,tax[i].id, cax[i].id)
                correct = False
            for j in range(len(tax[i])):
                if not tax[i][j] == cax[i][j]:
                    print "Axes %s, differ at index %i, test value: %s vs expectedi value: %s" % (tax[i].id,j,tax[i][j], cax[i][j])
                    correct = False

        if not self.checkAllClose(test, valid):
            correct = False

        if not correct:
            raise Exception("jsons file %s differ from correct one: %s" % (test_file, correct_file))
