#!/usr/bin/env python
from pcmdi_metrics.monsoon_wang import create_monsoon_wang_parser, monsoon_wang_runner

P = create_monsoon_wang_parser()
args = P.get_parameter(argparse_vals_only=False)
monsoon_wang_runner(args)
