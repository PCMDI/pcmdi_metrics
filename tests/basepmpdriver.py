import basepmp
import subprocess
import os
import shlex
import sys
import pcmdi_metrics
import glob
import shutil

class PMPDriverTest(basepmp.PMPTest):
    def setUp(self):
        self.path_parameter_files = os.path.join(os.path.dirname(__file__),"pcmdi")
        self.traceback = eval(os.environ.get("TRACEBACK","False"))
        self.update = eval(os.environ.get("UPDATE_TESTS","False"))

    def runPMP(self,parameterFile):
        if self.traceback:
            tb="-t"
        else:
            tb = ""
        print
        print
        print
        print
        print "---------------------------------------------------"
        print "RUNNING:", parameterFile
        print "---------------------------------------------------"
        print
        print
        print
        print
        subprocess.call(
            shlex.split(
                #"pcmdi_metrics_driver_legacy.py -p %s %s" %
                "pcmdi_metrics_driver.py -p %s %s" %
                (parameterFile, tb)))

        parameters,files = self.assertFilesOut(parameterFile)

        for fnm in files:
            nm = os.path.basename(fnm)
            # Ok now we are trying to find the same file
            good_files = glob.glob(
                os.path.dirname(__file__) +
                "/pcmdi/%s/*.json" %
                parameters.case_id)
            if len(good_files) == 0:
                raise Exception(" ".join("could not find good files",
                    __file__, os.path.dirname(__file__),
                    "/pcmdi/%s/*.json" % parameters.case_id))
            allCorrect = True
            for gnm in good_files:
                if os.path.basename(gnm) == nm:
                    print "comparing:", fnm, gnm
                    if self.update:
                        shutil.copy(fnm, gnm)
                    else:
                        correct = self.assertSimilarJsons(fnm, gnm, rtol=5.E-3, atol=0., raiseOnError=False)
                        allCorrect = allCorrect and correct
            if not allCorrect:
                raise Exception("Error Encountered on some of the output files, check log")

    def assertFilesOut(self,parameterFile):
        # Ok at that point we we can start testing things
        pth, fnm = os.path.split(parameterFile)
        if pth != "":
            sys.path.append(pth)
        if fnm.lower()[-3:] == ".py":
            fnm = fnm[:-3]
        parameters = ""  # so flake8 doesn't complain
        exec("import %s as parameters" % fnm)
        # Ok now let's figure out where the results have been dumped
        pthout = pcmdi_metrics.io.base.Base(
            os.path.join(
                parameters.metrics_output_path),
            "*.json")
        pthout.case_id = parameters.case_id
        files = glob.glob(pthout())
        if len(files) == 0:
            raise Exception("could not find output files after running pcmdi_metrics_driver on parameter file: %s" % parameterFile)
        return parameters, files

