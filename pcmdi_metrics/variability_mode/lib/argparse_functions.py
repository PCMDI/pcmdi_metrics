def AddParserArgument(P):
    # Load pre-defined parsers
    # P.use("--mip")
    # P.use("--exp")
    P.use("--results_dir")
    P.use("--reference_data_path")
    P.use("--modpath")
    # Add parsers
    P.add_argument("--mip",
                   type=str,
                   default="cmip5",
                   help="A WCRP MIP project such as CMIP3 and CMIP5")
    P.add_argument("--exp",
                   type=str,
                   default="historical",
                   help="An experiment such as AMIP, historical or pi-contorl")
    P.add_argument("--frequency", default="mo")
    P.add_argument("--realm", default="atm")
    P.add_argument("--reference_data_name",
                   type=str,
                   help="Name of reference data set")
    P.add_argument("-v", "--variability_mode",
                   type=str,
                   default='NAO',
                   help="Mode of variability: NAM, NAO, SAM, PNA, PDO\n"
                        "- NAM: Northern Annular Mode\n"
                        "- NAO: Northern Atlantic Oscillation\n"
                        "- SAM: Southern Annular Mode\n"
                        "- PNA: Pacific North American Pattern\n"
                        "- PDO: Pacific Decadal Oscillation\n"
                        "(Note: Case insensitive)")
    P.add_argument("--seasons",
                   type=str,
                   nargs='+',
                   default=None,
                   help="List of seasons")
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
    P.add_argument("--modpath_lf",
                   type=str,
                   dest='modpath_lf',
                   help="Directory path to model land fraction field")
    P.add_argument("--varOBS",
                   type=str,
                   help="Name of variable in reference data")
    P.add_argument("--varModel",
                   type=str,
                   help="Name of variable in model(s)")
    P.add_argument("--eofn_obs",
                   type=int,
                   default=1,
                   help="EOF mode from observation as reference")
    P.add_argument("--eofn_mod",
                   type=int,
                   default=1,
                   help="EOF mode from model")
    P.add_argument("--osyear",
                   type=int,
                   default=1900,
                   help="Start year for reference data")
    P.add_argument("--oeyear",
                   type=int,
                   default=2005,
                   help="End year for reference data")
    P.add_argument("--msyear",
                   type=int,
                   default=1900,
                   help="Start year for model(s)")
    P.add_argument("--meyear",
                   type=int,
                   default=2005,
                   help="End year for model(s)")

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

    # Switches
    P.add_argument("-d", "--debug",
                   type=bool,
                   default=False,
                   help="Option for debug: True / False (defualt)")

    P.add_argument("--RemoveDomainMean",
                   type=bool,
                   default=True,
                   help="Option for Remove Domain Mean from each time step: True (defualt)/ False")
    P.add_argument("--EofScaling",
                   type=bool,
                   default=False,
                   help="Option for Consider EOF with unit variance: True / False (default)")
    P.add_argument("--landmask",
                   type=bool,
                   default=False,
                   help="Option for maskout land region: True / False (default)")
    P.add_argument("--ConvEOF",
                   type=bool,
                   default=False,
                   help="Option for Calculate Conventioanl EOF for model: True / False (default)")
    P.add_argument("--CBF",
                   type=bool,
                   default=True,
                   help="Option for Calculate Common Basis Function (CBF) for model: True (default) / False")
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

    return P


def VariabilityModeCheck(mode, P):
    if mode is None:
        P.error('VARIABILITY_MODE is NOT defined')
    else:
        if mode.upper() not in ['NAM', 'NAO', 'SAM', 'PNA', 'PDO', 'NPO', 'NPGO']:
            P.error(
                ''.join(['Given VARIABILITY_MODE, ',
                         mode,
                         ', is NOT correct. ',
                         'Please refer help document by using "-h" option']))
        return mode.upper()


def YearCheck(syear, eyear, P):
    if syear >= eyear:
        P.error('Given starting year, '+str(syear) +
                ', is later than given ending year, '+str(eyear))
    else:
        pass
