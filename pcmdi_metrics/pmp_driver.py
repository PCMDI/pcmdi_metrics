from cdp.cdp_driver import *
from pcmdi_metrics.checkparameter import *
from pcmdi_metrics.rundiags import *


class PMPDriver(CDPDriver):

    def check_parameter(self):
        # Check that all of the variables used from parameter exist.
        #PMPDriverCheckParameter.check_parameter(self.parameter)
        pass

    def run_diags(self):
        run = RunDiags(self.parameter)
        run()

    def export(self):
        pass
