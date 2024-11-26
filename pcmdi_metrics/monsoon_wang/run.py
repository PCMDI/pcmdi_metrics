from monsoon_wang_driver import create_monsoon_wang_parser, monsoon_wang_runner

P = create_monsoon_wang_parser()
args = P.get_parameter(argparse_vals_only=False)
monsoon_wang_runner(args)
