def AddParserArgument(P):
    # Load pre-defined parsers
    P.use("--mip")
    P.use("--exp")
    P.use("--results_dir")
    P.use("--reference_data_path")
    P.use("--modpath")
    # Add parsers
    P.add_argument("--frequency", default="da")
    P.add_argument("--realm", default="atm")
    P.add_argument("--reference_data_name",
                   type=str,
                   help="Name of reference data set")
    P.add_argument("--modnames",
                   type=list,
                   default=None,
                   help="List of models")
    P.add_argument("-r", "--realization",
                   type=str,
                   default="r1i1p1",
                   help="Consider all accessible realizations as idividual\n"
                        "- r1i1p1: default, consider only 'r1i1p1' member\n"
                        "          Or, specify realization, e.g, r3i1p1'\n"
                        "- *: consider all available realizations")
    # Switches
    P.add_argument("-d", "--debug",
                   type=bool,
                   default=False,
                   help="Option for debug: False (defualt) or True")
    P.add_argument("--nc-out", dest="nc_out", help="record netcdf output", action="store_true", default=False)
    P.add_argument("--plot", dest="plot", help="produce plots", action="store_true", default=False)
    return P


def YearCheck(syear, eyear, P):
    if syear >= eyear:
        P.error('Given starting year, '+str(syear) +
                ', is later than given ending year, '+str(eyear))
    else:
        pass
