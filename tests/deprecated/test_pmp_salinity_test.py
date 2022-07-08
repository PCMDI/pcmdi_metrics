import basepmpdriver
import os

class PMPParamTest(basepmpdriver.PMPDriverTest):
    def testParam(self):
        param = os.path.join(self.path_parameter_files,"salinity_test.py")
        self.runPMP(param)
