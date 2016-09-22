from pcmdi_metrics.base.CDPDriver import *
from pcmdi_metrics.PMP.PMPDriverCheckParameter import *
from pcmdi_metrics.PMP.PMPDriverRunDiags import *


class PMPDriver(CDPDriver):

    def check_parameter(self):
        # Check that all of the variables used from parameter exist.
        PMPDriverCheckParameter.check_parameter(self.parameter)

    def run_diags(self):
        run = PMPDriverRunDiags(self.parameter)
        run()

    def export(self):
        pass
