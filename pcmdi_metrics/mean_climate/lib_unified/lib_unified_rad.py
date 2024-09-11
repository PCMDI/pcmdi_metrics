import xarray as xr


def get_rt(rsdt, rsut, rlut):
    """
    Calculate net radiative flux at the top of the atmosphere (rt).

    Parameters:
    rsdt (xarray.DataArray): Downward shortwave solar radiation at the top of the atmosphere.
    rsut (xarray.DataArray): Upward shortwave solar radiation at the top of the atmosphere.
    rlut (xarray.DataArray): Upward longwave solar radiation at the top of the atmosphere.

    Returns:
    xarray.DataArray: Computed net radiative flux (rt).
    """
    # Calculate rt
    return (rsdt - rsut) - rlut


def get_rst(rsdt, rsut):
    """
    Calculate net shortwave radiative flux at the top of the atmosphere (rst).

    Parameters:
    rsdt (xarray.DataArray): Downward shortwave solar radiation at the top of the atmosphere.
    rsut (xarray.DataArray): Upward shortwave solar radiation at the top of the atmosphere.

    Returns:
    xarray.DataArray: Computed net shortwave radiative flux (rst).
    """
    # Calculate rt
    return rsdt - rsut


def get_rstcre(rsdt, rsut, rsutcs):
    """
    Calculate the shortwave cloud radiative effect (rstcre).

    Parameters:
    rsdt (xarray.DataArray): Downward shortwave solar radiation at the top of the atmosphere.
    rsut (xarray.DataArray): Upward shortwave solar radiation at the top of the atmosphere.
    rsutcs (xarray.DataArray): Upward shortwave solar radiation at the top of the atmosphere assuming clear sky.

    Returns:
    xarray.DataArray: Computed shortwave cloud radiative effect (rstcre).
    """
    # Calculate rstcre
    return (rsdt - rsut) - rsutcs


def get_rltcre(rlut, rlutcs):
    """
    Calculate the longwave cloud radiative effect (rltcre).

    Parameters:
    rlut (xarray.DataArray): Upward longwave solar radiation at the top of the atmosphere.
    rlutcs (xarray.DataArray): Upward longwave solar radiation at the top of the atmosphere assuming clear sky.

    Returns:
    xarray.DataArray: Computed longwave cloud radiative effect (rltcre).
    """
    # Calculate rstcre
    return rlut - rlutcs


def derive_rad_var(
    var,
    encountered_vars,
    data_name,
    ac_dict,
    data_dict,
    out_path,
    in_progress=True,
    data_type="ref",
):
    """
    Derives radiation variables and saves the result to a NetCDF file.

    Parameters
    ----------
    var : str
        The name of the radiation variable to derive (e.g., 'rt', 'rst', 'rstcre', 'rltcre').
    encountered_vars : set
        A set of variables that have been encountered in the data processing.
    data_name : str or tuple
        The name of the reference data if `data_type` is 'ref', or a tuple (model, run) if `data_type` is 'model'.
    ac_dict : dict
        A dictionary containing actual climatology data.
    data_dict : dict
        A dictionary containing data information like variable names.
    out_path : str
        The file path to save the output NetCDF file.
    in_progress : bool, optional
        If True, the function returns None and skips processing (default is True).
    data_type : str, optional
        Type of data, either 'ref' or 'model' (default is 'ref').

    Returns
    -------
    xr.Dataset or None
        The resulting xarray Dataset containing the derived variable, or None if in_progress is True.

    Raises
    ------
    ValueError
        If `data_type` is not 'ref' or 'model'.
    TypeError
        If `data_name` is not a string (for 'ref') or a tuple of strings (for 'model').
    KeyError
        If the specified `var` is not recognized.
    """

    # Sanity checks
    if data_type not in ["ref", "model"]:
        raise ValueError("Invalid data_type. Expected 'ref' or 'model'.")
    if (data_type == "ref" and not isinstance(data_name, str)) or (
        data_type == "model"
        and not (
            isinstance(data_name, tuple)
            and all(isinstance(item, str) for item in data_name)
        )
    ):
        raise TypeError("Invalid data_name for the specified data_type.")

    # Early return if the process is marked as in-progress
    if in_progress:
        return None

    ref, model, run = None, None, None
    if data_type == "ref":
        ref = data_name
        print(f"Processing data for: {ref}")
    else:
        model, run = data_name
        print(f"Processing data for: {model}, {run}")

    # Define required variables and corresponding functions
    variable_info = {
        "rt": ({"rsdt", "rsut", "rlut"}, get_rt),
        "rst": ({"rsdt", "rsut"}, get_rst),
        "rstcre": ({"rsdt", "rsut", "rsutcs"}, get_rstcre),
        "rltcre": ({"rlut", "rlutcs"}, get_rltcre),
    }

    if var not in variable_info:
        raise KeyError(
            f"Variable not defined, should be one of {list(variable_info.keys())}: {var}"
        )

    required_vars, compute_function = variable_info[var]

    # Check if required vars have been encountered
    if not required_vars.issubset(encountered_vars):
        return None

    def extract_data(var_name):
        if data_type == "ref":
            return ac_dict[var_name][ref][data_dict[var_name][ref]["varname"]]
        return ac_dict[var_name][model][run][data_dict[var_name][model][run]["varname"]]

    # Extract the necessary variables
    data = [extract_data(var_name) for var_name in required_vars]

    # Calculate the result using the appropriate function
    result = compute_function(*data)

    # Create a new dataset to store the result, preserving coordinates
    ds = xr.Dataset({var: result})

    # Write the reference variable to the output file
    ds.to_netcdf(out_path)

    return ds


def derive_rad_var_old(
    var,
    encountered_vars,
    data_name,
    ac_dict,
    data_dict,
    out_path,
    in_progress=True,
    data_type="ref",
):
    # Sanity check for data_type
    if data_type not in ["ref", "model"]:
        raise ValueError("Invalid data_type. Expected 'ref' or 'model'.")

    # Sanity check for data_name
    if isinstance(data_name, str) and data_type == "ref":
        # Process single data name
        print(f"Processing data for: {data_name}")
        ref = data_name
    elif (
        isinstance(data_name, tuple)
        and all(isinstance(item, str) for item in data_name)
        and data_type == "model"
    ):
        # Process multiple data names
        print(f"Processing data for: {', '.join(data_name)}")
        model = data_name[0]
        run = data_name[1]
    else:
        raise TypeError("data_name must be a string or a tuple of strings.")

    # Temporary
    if in_progress:
        return None

    if var == "rt":
        # Check if required vars have been encountered
        required_vars = {"rsdt", "rsut", "rlut"}
        if required_vars.issubset(encountered_vars):
            if data_type == "ref":
                rsdt_varname = data_dict["rsdt"][ref]["varname"]
                rsut_varname = data_dict["rsut"][ref]["varname"]
                rlut_varname = data_dict["rlut"][ref]["varname"]

                rsdt = ac_dict["rsdt"][ref][rsdt_varname]
                rsut = ac_dict["rsut"][ref][rsut_varname]
                rlut = ac_dict["rlut"][ref][rlut_varname]

            elif data_type == "model":
                rsdt_varname = data_dict["rsdt"][model][run]["varname"]
                rsut_varname = data_dict["rsut"][model][run]["varname"]
                rlut_varname = data_dict["rlut"][model][run]["varname"]

                rsdt = ac_dict["rsdt"][model][run][rsdt_varname]
                rsut = ac_dict["rsut"][model][run][rsut_varname]
                rlut = ac_dict["rlut"][model][run][rlut_varname]

            result = get_rt(rsdt, rsut, rlut)

    elif var == "rst":
        # Check if required vars have been encountered
        required_vars = {"rsdt", "rsut"}
        if required_vars.issubset(encountered_vars):
            if data_type == "ref":
                rsdt_varname = data_dict["rsdt"][ref]["varname"]
                rsut_varname = data_dict["rsut"][ref]["varname"]

                rsdt = ac_dict["rsdt"][ref][rsdt_varname]
                rsut = ac_dict["rsut"][ref][rsut_varname]

            elif data_type == "model":
                rsdt_varname = data_dict["rsdt"][model][run]["varname"]
                rsut_varname = data_dict["rsut"][model][run]["varname"]

                rsdt = ac_dict["rsdt"][model][run][rsdt_varname]
                rsut = ac_dict["rsut"][model][run][rsut_varname]

            result = get_rst(rsdt, rsut)

    elif var == "rstcre":
        # Check if required vars have been encountered
        required_vars = {"rsdt", "rsut", "rsutcs"}
        if required_vars.issubset(encountered_vars):
            if data_type == "ref":
                rsdt_varname = data_dict["rsdt"][ref]["varname"]
                rsut_varname = data_dict["rsut"][ref]["varname"]
                rsutcs_varname = data_dict["rsutcs"][ref]["varname"]

                rsdt = ac_dict["rsdt"][ref][rsdt_varname]
                rsut = ac_dict["rsut"][ref][rsut_varname]
                rsutcs = ac_dict["rsutcs"][ref][rsutcs_varname]

            elif data_type == "model":
                rsdt_varname = data_dict["rsdt"][model][run]["varname"]
                rsut_varname = data_dict["rsut"][model][run]["varname"]
                rsutcs_varname = data_dict["rsutcs"][model][run]["varname"]

                rsdt = ac_dict["rsdt"][model][run][rsdt_varname]
                rsut = ac_dict["rsut"][model][run][rsut_varname]
                rsutcs = ac_dict["rsutcs"][model][run][rsutcs_varname]

            result = get_rstcre(rsdt, rsut, rsutcs)

    elif var == "rltcre":
        # Check if required vars have been encountered
        required_vars = {"rlut", "rlutcs"}
        if required_vars.issubset(encountered_vars):
            if data_type == "ref":
                rlut_varname = data_dict["rlut"][ref]["varname"]
                rlutcs_varname = data_dict["rlutcs"][ref]["varname"]

                rlut = ac_dict["rlut"][ref][rsdt_varname]
                rlutcs = ac_dict["rlutcs"][ref][rlutcs_varname]

            elif data_type == "model":
                rlut_varname = data_dict["rlut"][model][run]["varname"]
                rlutcs_varname = data_dict["rlutcs"][model][run]["varname"]

                rlut = ac_dict["rlut"][model][run][rsdt_varname]
                rlutcs = ac_dict["rlutcs"][model][run][rlutcs_varname]

            result = get_rltcre(rlut, rlutcs)

    else:
        raise KeyError(
            f"Variable not defined, should be either of 'rt', 'rstcre', or 'rltcre': {var}"
        )

    # Create a new dataset to store the result, preserving coordinates
    ds = xr.Dataset({var: result})

    # Write the reference variable to the output file
    ds.to_netcdf(out_path)

    return ds
