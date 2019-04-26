import basepmpdriver
import os

class PMPParamTest(basepmpdriver.PMPDriverTest):
    def testParam(self):
        param = os.path.join(self.path_parameter_files,"basic_test_parameters_file.py")
        self.runPMP(param)
