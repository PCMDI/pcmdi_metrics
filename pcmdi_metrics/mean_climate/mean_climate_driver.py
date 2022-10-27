#!/usr/bin/env python
from pcmdi_metrics.mean_climate.lib import PMPDriver, create_mean_climate_parser

parser = create_mean_climate_parser()
parameter = parser.get_parameter(cmd_default_vars=False, argparse_vals_only=False)
driver = PMPDriver(parameter)
driver.run_diags()
