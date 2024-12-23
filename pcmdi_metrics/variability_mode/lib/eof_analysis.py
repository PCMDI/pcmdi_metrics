from time import gmtime, strftime

import numpy as np
import xarray as xr
from eofs.xarray import Eof

from pcmdi_metrics.io import (
    get_latitude,
    get_latitude_key,
    get_longitude,
    get_longitude_key,
    get_time_key,
)
from pcmdi_metrics.utils import calculate_area_weights, calculate_grid_area


def eof_analysis_get_variance_mode(
    mode: str,
    ds: xr.Dataset,
    data_var: str,
    eofn: int,
    eofn_max: int = None,
    debug: bool = False,
    EofScaling: bool = False,
    save_multiple_eofs: bool = False,
) -> tuple:
    """
    Perform Empirical Orthogonal Function (EOF) analysis.

    Parameters
    ----------
    mode : str
        The mode of variability needed for arbitrary sign control, which is characteristic of EOF analysis.
    ds : xr.Dataset
        An xarray Dataset containing a dataArray: a time-varying 2D array, so a 3D array (time, lat, lon).
    data_var : str
        The name of the dataArray to analyze.
    eofn : int
        The target EOFs to be returned.
    eofn_max : int, optional
        The maximum number of EOFs to diagnose (1 to N). Default is None.
    debug : bool, optional
        If True, enables debugging output. Default is False.
    EofScaling : bool, optional
        If True, applies scaling to the EOFs. Default is False.
    save_multiple_eofs : bool, optional
        If True, saves multiple EOFs. Default is False.

    Returns
    -------
    eof_Nth : np.ndarray or list of np.ndarray
        EOF pattern (map) for the given EOFs if `save_multiple_eofs` is False;
        otherwise, a list of EOF patterns.
    pc_Nth : np.ndarray or list of np.ndarray
        Corresponding principal component time series if `save_multiple_eofs` is False;
        otherwise, a list of principal component time series.
    frac_Nth : float or list of float
        Fraction of explained variance as a single float if `save_multiple_eofs` is False;
        otherwise, a list of floats.
    reverse_sign_Nth : bool or list of bool
        Boolean indicating if the sign is reversed for the EOFs if `save_multiple_eofs` is False;
        otherwise, a list of booleans.
    solver : object
        The solver used for the EOF analysis.

    Notes
    -----
    The function can return either single EOF results or lists of EOF results based on the
    `save_multiple_eofs` parameter.
    """
    debug_print("Lib-EOF: eof_analysis_get_variance_mode function starts", debug)

    if eofn_max is None:
        eofn_max = eofn
        save_multiple_eofs = False

    # EOF (take only first variance mode...) ---
    grid_area = calculate_grid_area(ds)
    area_weights = calculate_area_weights(grid_area)
    da = ds[data_var]
    solver = Eof(da, weights=area_weights)
    debug_print("Lib-EOF: eof", debug)

    # pcscaling=1 by default, return normalized EOFs
    eof = solver.eofsAsCovariance(neofs=eofn_max, pcscaling=1)
    debug_print("Lib-EOF: pc", debug)

    if EofScaling:
        # pcscaling=1: scaled to unit variance
        # (i.e., divided by the square-root of their eigenvalue)
        pc = solver.pcs(npcs=eofn_max, pcscaling=1)
    else:
        pc = solver.pcs(npcs=eofn_max)  # pcscaling=0 by default

    # fraction of explained variance
    frac = solver.varianceFraction(neigs=eofn_max)
    debug_print("Lib-EOF: frac", debug)

    # For each EOFs...
    eof_list = []
    pc_list = []
    frac_list = []
    reverse_sign_list = []

    for n in range(eofn_max):
        eof_Nth = eof[n]
        pc_Nth = pc[:, n]
        frac_Nth = frac[n]

        # Arbitrary sign control, attempt to make all plots have the same sign
        reverse_sign = arbitrary_checking(mode, eof_Nth)

        if reverse_sign:
            eof_Nth *= -1.0
            pc_Nth *= -1.0

        # Supplement NetCDF attributes
        eof_Nth.attrs["variable"] = data_var
        eof_Nth.attrs["eof_mode"] = n + 1
        frac_Nth.attrs["units"] = "ratio"
        pc_Nth.attrs[
            "comment"
        ] = f"Non-scaled time series for principal component of {eofn}th variance mode"
        pc_Nth.attrs["variable"] = data_var
        pc_Nth.attrs["eof_mode"] = n + 1

        # append to lists for returning
        eof_list.append(eof_Nth)
        pc_list.append(pc_Nth)
        frac_list.append(frac_Nth)
        reverse_sign_list.append(reverse_sign)

    # return results
    if save_multiple_eofs:
        return eof_list, pc_list, frac_list, reverse_sign_list, solver
    else:
        # Remove unnecessary dimensions (make sure only taking requested eofs)
        eof_Nth = eof_list[eofn - 1]
        pc_Nth = pc_list[eofn - 1]
        frac_Nth = frac_list[eofn - 1]
        reverse_sign_Nth = reverse_sign_list[eofn - 1]
        return eof_Nth, pc_Nth, frac_Nth, reverse_sign_Nth, solver


def arbitrary_checking(mode: str, eof_Nth: xr.DataArray) -> bool:
    """
    Check if the sign of the EOF pattern needs to be reversed for consistency.

    This function determines whether multiplying the EOF pattern and its corresponding
    principal component by -1 is necessary to maintain a consistent sign across
    observations or models.

    Parameters
    ----------
    mode : str
        The mode of variability, e.g., 'PDO', 'PNA', 'NAM', 'SAM'.
    eof_Nth : xr.DataArray
        The EOF pattern to be checked.

    Returns
    -------
    reverse_sign : bool
        True if the sign of the EOF pattern and principal component should be reversed;
        otherwise, False.
    """
    reverse_sign = False

    # Get latitude and longitude keys
    lat_key = get_latitude_key(eof_Nth)
    lon_key = get_longitude_key(eof_Nth)

    # Explicitly check average of geographical region for each mode
    if mode == "PDO":
        if (
            eof_Nth.sel({lat_key: slice(30, 40), lon_key: slice(150, 180)})
            .mean()
            .item()
            >= 0
        ):
            reverse_sign = True
    elif mode == "PNA":
        if eof_Nth.sel({lat_key: slice(80, 90)}).mean().item() <= 0:
            reverse_sign = True
    elif mode in ["NAM", "NAO"]:
        if eof_Nth.sel({lat_key: slice(60, 80)}).mean().item() >= 0:
            reverse_sign = True
    elif mode == "SAM":
        if eof_Nth.sel({lat_key: slice(-60, -90)}).mean().item() >= 0:
            reverse_sign = True
    elif mode == "PSA1":
        if (
            eof_Nth.sel({lat_key: slice(-59.5, -64.5), lon_key: slice(207.5, 212.5)})
            .mean()
            .item()
            >= 0
        ):
            reverse_sign = True
    elif mode == "PSA2":
        if (
            eof_Nth.sel({lat_key: slice(-57.5, -62.5), lon_key: slice(277.5, 282.5)})
            .mean()
            .item()
            >= 0
        ):
            reverse_sign = True
    else:  # Minimum sign control part was left behind for any future usage..
        if not np.isnan(eof_Nth[-1, -1].item()):
            if eof_Nth[-1, -1].item() >= 0:
                reverse_sign = True
        elif not np.isnan(eof_Nth[-2, -2].item()):  # Double check missing value at pole
            if eof_Nth[-2, -2].item() >= 0:
                reverse_sign = True

    # return result
    return reverse_sign


def linear_regression_on_globe_for_teleconnection(
    pc, ds, data_var, stdv_pc, RmDomainMean=True, EofScaling=False, debug=False
) -> xr.DataArray:
    """
    Reconstruct the first mode of EOF with a focus on teleconnection.

    This function performs linear regression on the global field to reconstruct
    the first mode of EOF, ensuring that the results are consistent with the
    EOF domain (i.e., subdomain). It has been confirmed that the output
    "eof_lr" is identical to "eof" over the specified EOF domain.

    Parameters
    ----------
    pc : np.ndarray
        The principal component time series used for reconstruction.
    ds : xr.Dataset
        An xarray Dataset containing the data for regression.
    data_var : str
        The name of the data variable in the dataset.
    stdv_pc : float
        The standard deviation of the principal component.
    RmDomainMean : bool, optional
        If True, removes the domain mean from the data. Default is True.
    EofScaling : bool, optional
        If True, applies scaling to the EOFs. Default is False.
    debug : bool, optional
        If True, enables debugging output. Default is False.

    Returns
    -------
    eof_lr : xr.DataArray
        The reconstructed EOF pattern with teleconnection considerations.
    """
    if debug:
        print("type(pc), type(ds):", type(pc), type(ds))
        print("pc.shape, timeseries.shape:", pc.shape, ds[data_var].shape)

    # Linear regression to have extended global map; teleconnection purpose
    slope, intercept = linear_regression(pc, ds[data_var], debug=debug)

    if not RmDomainMean and EofScaling:
        factor = 1
    else:
        factor = stdv_pc

    eof_lr = (slope * factor) + intercept

    eof_lr.attrs["variable"] = data_var
    eof_lr.attrs["description"] = "linear regression on global field for teleconnection"
    eof_lr.attrs[
        "comment"
    ] = "Reconstructed EOF pattern with teleconnection considerations"
    if "eof_mode" in pc.attrs:
        eof_lr.attrs["eof_mode"] = pc.attrs["eof_mode"]

    debug_print("linear regression done", debug)

    return eof_lr, slope, intercept


def linear_regression(x: xr.DataArray, y: xr.DataArray, debug: bool = False) -> tuple:
    """
    Perform linear regression on a time series against a time-varying 2D field.

    This function computes the linear regression slope and intercept for each grid
    point in the 2D field based on the provided 1D time series.

    Parameters
    ----------
    x : xr.DataArray
        A 1D time series (time) used as the independent variable.
    y : xr.DataArray
        A time-varying 2D field (time, lat, lon) used as the dependent variable.
    debug : bool, optional
        If True, enables debugging output to display shapes of input arrays.
        Default is False.

    Returns
    -------
    slope : xr.DataArray
        A 2D array representing the spatial map of linear regression slopes for each grid point.
    intercept : xr.DataArray
        A 2D array representing the spatial map of linear regression intercepts for each grid point.
    """
    # get original global dimension
    lat = get_latitude(y)
    lon = get_longitude(y)
    # Convert 3d (time, lat, lon) to 2d (time, lat*lon) for polyfit applying
    im = y.shape[2]
    jm = y.shape[1]
    y_2d = y.data.reshape(y.shape[0], jm * im)
    if debug:
        print("x.shape:", x.shape)
        print("y_2d.shape:", y_2d.shape)
    # Linear regression
    slope_1d, intercept_1d = np.polyfit(np.array(x), np.array(y_2d), 1)
    # Retreive to variabile from numpy array
    slope = np.array(slope_1d.reshape(jm, im))
    intercept = np.array(intercept_1d.reshape(jm, im))
    # Set lat/lon coordinates
    slope = xr.DataArray(slope, coords={"lat": lat, "lon": lon}, dims=["lat", "lon"])
    intercept = xr.DataArray(
        intercept, coords={"lat": lat, "lon": lon}, dims=["lat", "lon"]
    )
    # return result
    return slope.where(slope != 1e20), intercept.where(intercept != 1e20)


def gain_pseudo_pcs(
    solver,
    field_to_be_projected: xr.DataArray,
    eofn: int,
    reverse_sign: bool = False,
    EofScaling: bool = False,
) -> xr.DataArray:
    """
    Project a dataset onto the n-th EOF to generate a corresponding set of pseudo-principal components (PCs).

    This function takes a dataset and projects it onto the specified n-th EOF,
    producing a set of pseudo-PCs that represent the data in the EOF space.

    Parameters
    ----------
    solver : object
        An object that contains the necessary methods or attributes for EOF analysis.
    field_to_be_projected : xr.DataArray
        The data field to be projected onto the EOFs.
    eofn : int
        The index of the EOF to project onto (1-based index).
    reverse_sign : bool, optional
        If True, reverses the sign of the resulting pseudo-PCs. Default is False.
    EofScaling : bool, optional
        If True, applies scaling to the EOFs during projection. Default is False.

    Returns
    -------
    pseudo_pcs : xr.DataArray
        The resulting pseudo-principal components after projection onto the n-th EOF.
    """
    if not EofScaling:
        pseudo_pcs = solver.projectField(
            field_to_be_projected, neofs=eofn, eofscaling=0
        )
        pseudo_pcs.attrs["comment"] = "Non-scaled pseudo principal components"
    else:
        pseudo_pcs = solver.projectField(
            field_to_be_projected, neofs=eofn, eofscaling=1
        )
        pseudo_pcs.attrs["comment"] = "Scaled pseudo principal components"
    # Get CBF PC (pseudo pcs in the code) for given eofs
    pseudo_pcs = pseudo_pcs[:, eofn - 1]
    # Arbitrary sign control, attempt to make all plots have the same sign
    if reverse_sign:
        pseudo_pcs *= -1
    # return result
    return pseudo_pcs


def gain_pcs_fraction(
    ds_full_field: xr.Dataset,
    varname_full_field: str,
    ds_eof_pattern: xr.Dataset,
    varname_eof_pattern: str,
    pcs: xr.DataArray,
    debug: bool = False,
) -> xr.DataArray:
    """
    Calculate the fraction of variance explained by pseudo-principal components (PCs).

    This function computes the fraction of variance obtained by projecting the full field
    onto the EOF patterns using the provided pseudo-PCs.

    Parameters
    ----------
    ds_full_field : xr.Dataset
        An xarray dataset that includes the full field data with dimensions (time, y, x).
    varname_full_field : str
        The name of the full field variable in the dataset.
    ds_eof_pattern : xr.Dataset
        An xarray dataset that includes the EOF pattern with dimensions (y, x).
    varname_eof_pattern : str
        The name of the EOF pattern variable in the dataset.
    pcs : xr.DataArray
        A 1D array of pseudo-principal components (time).
    debug : bool, optional
        If True, enables debugging output. Default is False.

    Returns
    -------
    fraction : xr.DataArray
        A single-element array representing the fraction of explained variance,
        preserving array type for netCDF recording.
    """
    full_field = ds_full_field[varname_full_field]
    eof_pattern = ds_eof_pattern[varname_eof_pattern]

    if debug:
        print("ds_full_field:", ds_full_field)
        print("ds_eof_pattern:", ds_eof_pattern)

    # 1) Get total variacne --- using full_field
    # time_key = get_time_key(full_field)
    time_key = get_time_key(ds_full_field)
    variance_total = full_field.var(dim=[time_key])
    # area average
    varname_variance_total = "variance_total"
    ds_full_field[varname_variance_total] = variance_total
    variance_total_area_ave = float(
        ds_full_field.spatial.average(varname_variance_total, weights="generate")[
            varname_variance_total
        ]
    )

    # 2) Get variance for pseudo pattern --- using eof_pattern
    # 2-1) Reconstruct field based on pseudo pattern
    reconstructed_field = eof_pattern * pcs

    # 2-2) Get variance of reconstructed field
    # time_key_2 = get_time_key(reconstructed_field)
    time_key_2 = get_time_key(ds_eof_pattern)
    variance_partial = reconstructed_field.var(dim=[time_key_2])
    # area average
    varname_variance_partial = "variance_partial"
    ds_full_field[varname_variance_partial] = variance_partial
    variance_partial_area_ave = float(
        ds_full_field.spatial.average(varname_variance_partial, weights="generate")[
            varname_variance_partial
        ]
    )

    # 3) Calculate fraction ---
    fraction = float(variance_partial_area_ave / variance_total_area_ave)

    # debugging
    if debug:
        print("from gain_pcs_fraction:")
        print("full_field.shape: ", full_field.shape)
        print("eof_pattern.shape: ", eof_pattern.shape)
        print("full_field.dims:", full_field.dims)
        print("pcs.dims:", pcs.dims)
        print("pcs.shape: ", pcs.shape)
        print("pcs[0:5]:", pcs[0:5].values.tolist())
        print(
            "full_field: max, min:",
            np.max(full_field.to_numpy()),
            np.min(full_field.to_numpy()),
        )
        print("pcs: max, min:", np.max(pcs.to_numpy()), np.min(pcs.to_numpy()))
        print(
            "reconstructed_field: max, min:",
            np.max(reconstructed_field.to_numpy()),
            np.min(reconstructed_field.to_numpy()),
        )
        print(
            "variance_partial: max, min:",
            np.max(variance_partial.to_numpy()),
            np.min(variance_partial.to_numpy()),
        )
        print("reconstructed_field.shape: ", reconstructed_field.shape)
        print("variance_partial_area_ave: ", variance_partial_area_ave)
        print("variance_total_area_ave: ", variance_total_area_ave)
        print("fraction: ", fraction)
        print("from gain_pcs_fraction done")

    # return result
    return fraction


def debug_print(string, debug):
    """
    Print a debug message with a timestamp if debugging is enabled.

    This function prints the provided debug message along with the current timestamp
    if the debug flag is set to True.

    Parameters
    ----------
    string : str
        The debug message to be printed.
    debug : bool
        A flag indicating whether to print the debug message.
        If True, the message will be printed; otherwise, it will be suppressed.

    Returns
    -------
    None
    """
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print("debug: " + nowtime + " " + string)
