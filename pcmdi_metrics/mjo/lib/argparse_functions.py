import datetime


def AddParserArgument(P):
    # Load pre-defined parsers
    # P.use("--mip")
    # P.use("--exp")
    P.use("--results_dir")
    P.use("--reference_data_path")
    P.use("--modpath")
    # Add parsers for options
    P.add_argument("--mip",
                   type=str,
                   default="cmip5",
                   help="A WCRP MIP project such as CMIP3 and CMIP5")
    P.add_argument("--exp",
                   type=str,
                   default="historical",
                   help="An experiment such as amip, historical or piContorl")
    P.add_argument("--frequency", default="da")
    P.add_argument("--realm", default="atm")
    P.add_argument("--reference_data_name",
                   type=str,
                   help="Name of reference data set")
    P.add_argument("--reference_data_lf_path",
                   type=str,
                   help="Path of landsea mask for reference data set")
    P.add_argument("--modpath_lf",
                   type=str,
                   help="Path of landsea mask for model data set")
    P.add_argument("--varOBS",
                   type=str,
                   help="Name of variable in reference data")
    P.add_argument("--varModel",
                   type=str,
                   help="Name of variable in model(s)")
    P.add_argument("--ObsUnitsAdjust",
                   type=tuple,
                   default=(False, 0, 0),
                   help="For unit adjust for OBS dataset. For example:\n"
                        "- (True, 'divide', 100.0)  # Pa to hPa\n"
                        "- (True, 'subtract', 273.15)  # degK to degC\n"
                        "- (False, 0, 0) # No adjustment (default)")
    P.add_argument("--ModUnitsAdjust",
                   type=tuple,
                   default=(False, 0, 0),
                   help="For unit adjust for model dataset. For example:\n"
                        "- (True, 'divide', 100.0)  # Pa to hPa\n"
                        "- (True, 'subtract', 273.15)  # degK to degC\n"
                        "- (False, 0, 0) # No adjustment (default)")
    P.add_argument("--units", dest="units", type=str,
                   help="Final units for the variable")
    P.add_argument("--osyear", dest="osyear", type=int,
                   help="Start year for reference data set")
    P.add_argument("--msyear", dest="msyear", type=int,
                   help="Start year for model data set")
    P.add_argument("--oeyear", dest="oeyear", type=int,
                   help="End year for reference data set")
    P.add_argument("--meyear", dest="meyear", type=int,
                   help="End year for model data set")
    P.add_argument("--modnames",
                   type=str,
                   nargs='+',
                   default=None,
                   help="List of models. 'all' for every available models")
    P.add_argument("-r", "--realization",
                   type=str,
                   default="r1i1p1",
                   help="Consider all accessible realizations as idividual\n"
                        "- r1i1p1: default, consider only 'r1i1p1' member\n"
                        "          Or, specify realization, e.g, r3i1p1'\n"
                        "- *: consider all available realizations")
    P.add_argument("--case_id",
                   type=str,
                   dest="case_id",
                   default="{:v%Y%m%d}".format(datetime.datetime.now()),
                   help="version as date, e.g., v20191116 (yyyy-mm-dd)")

    # Switches
    P.add_argument("-d", "--debug",
                   type=bool,
                   default=False,
                   help="Option for debug: False (defualt) or True")
    P.add_argument("--nc_out",
                   type=bool,
                   default=True,
                   help="Option for generate netCDF file output: True (default) / False")
    P.add_argument("--plot",
                   type=bool,
                   default=True,
                   help="Option for generate individual plots: True (default) / False")
    P.add_argument("--update_json",
                   type=bool,
                   default=True,
                   help="Option for update existing JSON file: True (i.e., update) (default) / False (i.e., overwrite)")
    P.add_argument("--cmec",
                   dest='cmec',
                   default=False,
                   help='Option to save metrics in CMEC format: True / False (default)')
    # Parallel
    P.add_argument("--parallel",
                   action="store_true",
                   dest='parallel',
                   help="Turn on the parallel mode for running code using multiple CPUs")
    P.add_argument("--includeOBS", dest="includeOBS",
                   help="include observation", action="store_true")
    P.add_argument("--no_OBS", dest="includeOBS",
                   help="include observation", action="store_false")
    P.add_argument("--num_workers", dest="num_workers", type=int,
                   default=1,
                   help="Start year for model data set")
    # Defaults
    P.set_defaults(includeOBS=True, parallel=False)
    return P


def YearCheck(syear, eyear, P):
    if syear >= eyear:
        P.error('Given starting year {}  is later than given ending year,\ {}'.format(syear, eyear))
    else:
        pass
