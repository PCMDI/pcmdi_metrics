import cdp.cdp_parser
import pcmdi_metrics.driver.pmp_parameter
import os
import sys

try:
    basestring  # noqa
except Exception:
    basestring = str


class PMPParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPParser, self).__init__(pcmdi_metrics.driver.pmp_parameter.PMPParameter,
                                        os.path.join(sys.prefix, "share", "cia", "DefArgsCIA.json"), *args, **kwargs)
        self.use("parameters")
        self.use("diags")


class PMPMetricsParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPMetricsParser, self).__init__(pcmdi_metrics.driver.pmp_parameter.PMPMetricsParameter,
                                               os.path.join(sys.prefix, "share", "cia", "DefArgsCIA.json"),
                                               *args, **kwargs)
        self.use("parameters")
        self.use("diags")
