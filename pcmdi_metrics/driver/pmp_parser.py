import cdp.cdp_parser
import pcmdi_metrics.driver.pmp_parameter
import pkg_resources
import os
import sys

try:
    basestring  # noqa
except Exception:
    basestring = str
    
def path_to_default_args():
    """Returns path to Default Common Input Arguments in package egg.
    """
    egg_pth = pkg_resources.resource_filename(pkg_resources.Requirement.parse("pcmdi_metrics"), "share/pmp")
    file_path = os.path.join(egg_pth, "DefArgsCIA.json")
    return file_path


class PMPParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPParser, self).__init__(pcmdi_metrics.driver.pmp_parameter.PMPParameter,
                                        path_to_default_args(), *args, **kwargs)
        self.use("parameters")
        self.use("diags")


class PMPMetricsParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPMetricsParser, self).__init__(pcmdi_metrics.driver.pmp_parameter.PMPMetricsParameter,
                                               path_to_default_args(),
                                               *args, **kwargs)
        self.use("parameters")
        self.use("diags")
