import unittest
import shlex
import subprocess
import os
import sys
import glob
import difflib
import numpy
import pcmdi_metrics
import shutil


class TestFromParam(unittest.TestCase):

    def __init__(self, parameter_file=None, good_files=[], traceback=False, update_files=False):
        super(TestFromParam, self).__init__("test_from_parameter_file")
        self.param = parameter_file
        self.good_files = good_files
        self.tb = traceback
        self.update = update_files

    def setUp(self):
        if self.tb:
            tb = "-t"
        else:
            tb = ""
        print
        print
        print
        print
        print "---------------------------------------------------"
        print "RUNNING:", self.param
        print "---------------------------------------------------"
        print
        print
        print
        print
        subprocess.call(
            shlex.split(
                #"pcmdi_metrics_driver_legacy.py -p %s %s" %
                "pcmdi_metrics_driver.py -p %s %s" %
                (self.param, tb)))
        pass

    def test_from_parameter_file(self):
        # Ok at that point we we can start testing things
        pth, fnm = os.path.split(self.param)
        if pth != "":
            sys.path.append(pth)
        if fnm.lower()[-3:] == ".py":
            fnm = fnm[:-3]
        parameters = ""  # so flake8 doesn't complain
        exec("import %s as parameters" % fnm)
        # Ok now let's figure out where the results have been dumped
        pthout = pcmdi_metrics.io.pmp_io.PMPIO(
            os.path.join(
                parameters.metrics_output_path),
            "*.json")
        pthout.case_id = parameters.case_id
        files = glob.glob(pthout())
        print "FILES:", pthout, files
        if len(files) == 0:
            raise Exception("could not find out files!")
        for fnm in files:
            nm = os.path.basename(fnm)
            # Ok now we are trying to find the same file
            if self.good_files == []:
                self.good_files = glob.glob(
                    os.path.dirname(__file__) +
                    "/pcmdi/%s/*.json" %
                    parameters.case_id)
            ok = True
            if len(self.good_files) == 0:
                ok = False
                print "could not find good files",\
                    __file__, os.path.dirname(__file__) +\
                    "/pcmdi/%s/*.json" % parameters.case_id
            for gnm in self.good_files:
                if os.path.basename(gnm) == nm:
                    print "comparing:", fnm, gnm
                    if self.update:
                        shutil.copy(fnm, gnm)
                    u = difflib.unified_diff(
                        open(gnm).readlines(),
                        open(fnm).readlines())
                    lines = []
                    for l in u:
                        lines.append(l)
                    for i, l in enumerate(lines):
                        if l[:2] == "+ ":
                            if l.find("{") > -1:
                                continue
                            elif l.find("}") > -1:
                                continue
                        if l[:2] == "- ":
                            if l.find("metrics_git_sha1") > -1:
                                continue
                            elif l.find("uvcdat_version") > -1:
                                continue
                            elif l.find("DISCLAIMER") > -1:
                                continue
                            else:
                                for j in range(100):
                                    ll = lines[i + j]
                                    sp = ll.split()
                                    # print "lines[%i+%i=%i]: %s" % (i,j,i+j,sp)
                                    if sp[0] == "+" and sp[1] == l.split()[1]:
                                        if ll.find("{") > -1 or ll.find("}") > -1:
                                            break
                                        good = float(l.split()[-1][1:-2])
                                        bad = float(sp[-1][1:-2])
                                        if not numpy.allclose(
                                                good, bad, atol=1.E-2):
                                            print "Failing line:", l.strip(), "(we read:", bad, ")"
                                            ok = False
                                        break
            self.assertTrue(ok)
        # shutil.rmtree(os.path.join(parameters.metrics_output_path,parameters.case_id))
