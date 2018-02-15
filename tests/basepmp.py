from __future__ import print_function
import unittest
import numpy
import os
import pcmdi_metrics


class PMPTest(unittest.TestCase):
    def checkAllClose(self, a, b, rtol=1e-05, atol=1e-08):
        print("SHAPES: {} {}".format(a.shape,b.shape))
        if numpy.ma.allclose(a.filled(), b.filled(), rtol=rtol, atol=atol):
            return True
        else:
            axes = a.getAxisList()
            a = a.filled()
            b = b.filled()
            c = numpy.isclose(a, b, rtol=rtol, atol=atol)
            w = numpy.argwhere(c==0)
            for d in w:
                print("Error for:", end=' ')
                for i,indx in enumerate(d):
                    print("%s, " % axes[i][indx], end=' ')
                print("(", end=' ')
                for indx in d:
                    print("%i," % indx, end=' ')
                print("). Test value %.3f vs expected value: %.3f realtive: %.3f%%" % (a[tuple(d)],b[tuple(d)],abs((a[tuple(d)]-b[tuple(d)])/b[tuple(d)])*100.))
            return False
        return True

    def assertSimilarJsons(self, test_file, correct_file, rtol=1e-05, atol=1e-08, raiseOnError=True):

        print("Comparing:",test_file, correct_file, "atol:",atol,"rtol:",rtol)
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
                print("Axes index %i have different names, test is '%s' vs expected: '%s'" % (i,tax[i].id, cax[i].id))
                correct = False
            for j in range(len(tax[i])):
                if not tax[i][j] == cax[i][j]:
                    print("Axes %s, differ at index %i, test value: %s vs expectedi value: %s" % (tax[i].id,j,tax[i][j], cax[i][j]))
                    correct = False

        if not self.checkAllClose(test, valid, rtol, atol):
            correct = False

        if not correct and raiseOnError:
            raise Exception("jsons file %s differ from correct one: %s" % (test_file, correct_file))
        return correct
