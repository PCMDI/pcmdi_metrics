from CDP.base.CDPDriver import *
from CDP.PMP.PMPDriverCheckParameter import *
from CDP.PMP.PMPDriverRunDiags import *


class PMPDriver(CDPDriver):

    def check_parameter(self):
        # Check that all of the variables used from parameter exist.
        PMPDriverCheckParameter.check_parameter(self.parameter)

    def run_diags(self):
        run = PMPDriverRunDiags(self.parameter)
        run.run_diags()

    def export(self):
        pass
