import ast


def AddParserArgument(P):
    P.add_argument(
        "--mip", type=str, dest="mip", default=None, help="cmip5, cmip6 or other mip"
    )
    P.add_argument(
        "--exp", type=str, dest="exp", default=None, help="amip, cmip or others"
    )
    P.add_argument("--mod", type=str, dest="mod", default=None, help="model")
    P.add_argument(
        "--var", type=str, dest="var", default=None, help="pr or other variable"
    )
    P.add_argument(
        "--frq", type=str, dest="frq", default=None, help="day, 3hr or other frequency"
    )
    P.add_argument(
        "--modpath", type=str, dest="modpath", default=None, help="data directory path"
    )
    P.add_argument(
        "--results_dir",
        type=str,
        dest="results_dir",
        default=None,
        help="results directory path",
    )
    P.add_argument(
        "--case_id", type=str, dest="case_id", default=None, help="case_id with date"
    )
    P.add_argument(
        "--prd",
        type=int,
        dest="prd",
        nargs="+",
        default=None,
        help="start- and end-year for analysis (e.g., 1985 2004)",
    )
    P.add_argument(
        "--fac",
        type=str,
        dest="fac",
        default=None,
        help="factor to make unit of [mm/day]",
    )
    P.add_argument(
        "--nperseg",
        type=int,
        dest="nperseg",
        default=None,
        help="length of segment in power spectra",
    )
    P.add_argument(
        "--noverlap",
        type=int,
        dest="noverlap",
        default=None,
        help="length of overlap between segments in power spectra",
    )
    P.add_argument(
        "--ref", type=str, dest="ref", default=None, help="reference data path"
    )
    P.add_argument(
        "--res",
        type=int,
        dest="res",
        default=2,
        help="Horizontal resolution [degree] for interpolation (lon, lat)",
    )
    P.add_argument(
        "--regions_specs",
        type=ast.literal_eval,
        dest="regions_specs",
        help="Provide a single custom region",
        default=None,
        required=False,
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
    P.add_argument(
        "--region_file",
        dest="region_file",
        help="File containing vector region of interest.",
        default=None,
    )
    P.add_argument(
        "--feature", dest="feature", help="Feature in vectorized region.", default=None
    )
    P.add_argument(
        "--attr",
        dest="attr",
        help="Attribute containing feature in vectorized region.",
        default=None,
    )
    P.set_defaults(cmec=False)

    return P
