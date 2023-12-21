def AddParserArgument(P):
    # Load pre-defined parsers
    P.use("--mip")
    P.use("--exp")
    P.use("--results_dir")
    P.use("--reference_data_path")
    P.use("--modpath")
    # Add parsers for options
    P.add_argument("--frequency", default="da")
    P.add_argument("--realm", default="atm")
    P.add_argument("--reference_data_name", type=str, help="Name of reference data set")
    P.add_argument(
        "--reference_data_lf_path",
        type=str,
        help="Path of landsea mask for reference data set",
    )
    P.add_argument(
        "--modpath_lf", type=str, help="Path of landsea mask for model data set"
    )
    P.add_argument("--varOBS", type=str, help="Name of variable in reference data")
    P.add_argument("--varModel", type=str, help="Name of variable in model(s)")
    P.add_argument(
        "--ObsUnitsAdjust",
        type=tuple,
        default=(False, 0, 0),
        help="For unit adjust for OBS dataset. For example:\n"
        "- (True, 'divide', 100.0)  # Pa to hPa\n"
        "- (True, 'subtract', 273.15)  # degK to degC\n"
        "- (False, 0, 0) # No adjustment (default)",
    )
    P.add_argument(
        "--ModUnitsAdjust",
        type=tuple,
        default=(False, 0, 0),
        help="For unit adjust for model dataset. For example:\n"
        "- (True, 'divide', 100.0)  # Pa to hPa\n"
        "- (True, 'subtract', 273.15)  # degK to degC\n"
        "- (False, 0, 0) # No adjustment (default)",
    )

    P.add_argument(
        "--units", dest="units", type=str, help="Final units for the variable"
    )
    P.add_argument(
        "--osyear", dest="osyear", type=int, help="Start year for reference data set"
    )
    P.add_argument(
        "--msyear", dest="msyear", type=int, help="Start year for model data set"
    )
    P.add_argument(
        "--oeyear", dest="oeyear", type=int, help="End year for reference data set"
    )
    P.add_argument(
        "--meyear", dest="meyear", type=int, help="End year for model data set"
    )
    P.add_argument("--modnames", type=list, default=None, help="List of models")
    P.add_argument(
        "-r",
        "--realization",
        type=str,
        default="r1i1p1",
        help="Consider all accessible realizations as idividual\n"
        "- r1i1p1: default, consider only 'r1i1p1' member\n"
        "          Or, specify realization, e.g, r3i1p1'\n"
        "- *: consider all available realizations",
    )
    # Add parsers as switches
    P.add_argument(
        "-d",
        "--debug",
        type=bool,
        default=False,
        help="Option for debug: False (defualt) or True",
    )
    P.add_argument(
        "--nc_out",
        dest="nc_out",
        help="record netcdf output",
        action="store_true",
        default=False,
    )
    P.add_argument(
        "--plot", dest="plot", help="produce plots", action="store_true", default=False
    )
    P.add_argument(
        "--includeOBS",
        dest="includeOBS",
        help="include observation",
        action="store_true",
        default=False,
    )
    P.add_argument(
        "--update_json",
        type=bool,
        default=True,
        help="Option for update existing JSON file: True (i.e., update) (default) / False (i.e., overwrite)",
    )
    return P


def YearCheck(syear, eyear, P):
    if syear >= eyear:
        P.error(
            "Given starting year {} is later than or same as the given ending year {}".format(
                syear, eyear
            )
        )
    else:
        pass
