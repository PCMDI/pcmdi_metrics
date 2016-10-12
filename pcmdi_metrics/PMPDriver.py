from CDP.base.CDPDriver import *
from pcmdi_metrics.PMPDriverCheckParameter import *
from pcmdi_metrics.PMPDriverRunDiags import *


class PMPDriver(CDPDriver):

    def check_parameter(self):
        # Check that all of the variables used from parameter exist.
        #PMPDriverCheckParameter.check_parameter(self.parameter)
        pass

    def run_diags(self):
        run = PMPDriverRunDiags(self.parameter)
        run()

    def export(self):
        pass
