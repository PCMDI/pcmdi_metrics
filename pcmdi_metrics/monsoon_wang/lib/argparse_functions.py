from pcmdi_metrics.utils.pmp_parser import PMPParser


def create_monsoon_wang_parser():
    P = PMPParser()

    P.use("--modnames")
    P.use("--results_dir")
    P.use("--reference_data_path")
    P.use("--test_data_path")

    P.add_argument(
        "--obs_mask",
        type=str,
        dest="obs_mask",
        default=None,
        help="obs mask pat",
    )
    P.add_argument(
        "--outnj",
        "--outnamejson",
        type=str,
        dest="outnamejson",
        default="monsoon_wang.json",
        help="Output path for jsons",
    )
    P.add_argument(
        "-e",
        "--experiment",
        type=str,
        dest="experiment",
        default="historical",
        help="AMIP, historical or picontrol",
    )
    P.add_argument(
        "-c", "--MIP", type=str, dest="mip", default="CMIP5", help="put options here"
    )
    P.add_argument(
        "--ovar", dest="obsvar", default="pr", help="Name of variable in obs file"
    )
    P.add_argument(
        "-v",
        "--var",
        dest="modvar",
        default="pr",
        help="Name of variable in model files",
    )
    P.add_argument(
        "-t",
        "--threshold",
        default=2.5 / 86400.0,
        type=float,
        help="Threshold for a hit when computing skill score",
    )
    P.add_argument(
        "--cmec",
        dest="cmec",
        default=False,
        action="store_true",
        help="Use to save CMEC format metrics JSON",
    )
    P.add_argument(
        "--no_cmec",
        dest="cmec",
        default=False,
        action="store_false",
        help="Do not save CMEC format metrics JSON",
    )
    P.set_defaults(cmec=False)
    return P
