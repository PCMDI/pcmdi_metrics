import basepmpdriver
import os

class PMPParamTest(basepmpdriver.PMPDriverTest):
    def testParam(self):
        param = os.path.join(self.path_parameter_files,"keep_going_on_error_varname_test.py")
        self.runPMP(param)
