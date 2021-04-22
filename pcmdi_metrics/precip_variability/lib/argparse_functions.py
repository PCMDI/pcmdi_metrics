def AddParserArgument(P):
    P.add_argument("--mip",
                   type=str,
                   dest='mip',
                   default=None,
                   help="cmip5, cmip6 or other mip")
    P.add_argument("--mod",
                   type=str,
                   dest='mod',
                   default=None,
                   help="model")
    P.add_argument("--var",
                   type=str,
                   dest='var',
                   default=None,
                   help="pr or other variable")
    P.add_argument("--frq",
                   type=str,
                   dest='frq',
                   default=None,
                   help="day, 3hr or other frequency")
    P.add_argument("--modpath",
                   type=str,
                   dest='modpath',
                   default=None,
                   help="data directory path")
    P.add_argument("--outdir",
                   type=str,
                   dest='outdir',
                   default=None,
                   help="output directory path")
    P.add_argument("--prd",
                   type=str,
                   dest='prd',
                   default=None,
                   help="list of start- and end-year for analysis")
    P.add_argument("--fac",
                   type=str,
                   dest='fac',
                   default=None,
                   help="factor to make unit of [mm/day]")
    P.add_argument("--nperseg",
                   type=str,
                   dest='nperseg',
                   default=None,
                   help="length of segment in power spectra")
    P.add_argument("--noverlap",
                   type=str,
                   dest='noverlap',
                   default=None,
                   help="length of overlap between segments in power spectra")
    return P
