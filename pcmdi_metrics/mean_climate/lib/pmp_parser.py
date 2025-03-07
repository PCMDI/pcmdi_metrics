import os

import cdp.cdp_parser

from pcmdi_metrics import resources
from pcmdi_metrics.mean_climate.lib.pmp_parameter import (
    PMPMetricsParameter,
    PMPParameter,
)

try:
    basestring  # noqa
except Exception:
    basestring = str


def path_to_default_args():
    """Returns path to Default Common Input Arguments in package egg."""
    egg_pth = resources.resource_path()
    file_path = os.path.join(egg_pth, "DefArgsCIA.json")
    return file_path


class PMPParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPParser, self).__init__(
            PMPParameter,
            path_to_default_args(),
            *args,
            **kwargs,
        )
        self.use("parameters")
        self.use("diags")


class PMPMetricsParser(cdp.cdp_parser.CDPParser):
    def __init__(self, *args, **kwargs):
        super(PMPMetricsParser, self).__init__(
            PMPMetricsParameter,
            path_to_default_args(),
            *args,
            **kwargs,
        )
        self.use("parameters")
        self.use("diags")
