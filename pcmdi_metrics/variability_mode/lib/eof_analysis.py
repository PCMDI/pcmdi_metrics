from time import gmtime, strftime

import numpy as np
import xarray as xr
from eofs.xarray import Eof

from pcmdi_metrics.io import (
    get_latitude,
    get_latitude_bounds,
    get_latitude_bounds_key,
    get_latitude_key,
    get_longitude,
    get_longitude_bounds,
    get_longitude_bounds_key,
    get_longitude_key,
    get_time_key,
    region_subset,
    select_subset,
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
):
    """
    Proceed EOF analysis
    Input
    - mode (string): mode of variability is needed for arbitrary sign
                     control, which is characteristics of EOF analysis
    - ds (xarray Dataset): that containing a dataArray: time varying 2d array, so 3d array (time, lat, lon)
    - data_var (string): name of the dataArray
    - eofn (integer): Target eofs to be return
    - eofn_max (integer): number of eofs to diagnose (1~N)
    Output
      1) When 'save_multiple_eofs = False'
        - eof_Nth: eof pattern (map) for given eofs as eofn
        - pc_Nth: corresponding principle component time series
        - frac_Nth: array but for 1 single number which is float.
                 Preserve array type for netCDF recording.
                 fraction of explained variance
        - reverse_sign_Nth: bool
        - solver
      2) When 'save_multiple_eofs = True'
        - eof_list: list of eof patterns (map) for given eofs as eofn
        - pc_list: list of corresponding principle component time series
        - frac_list: list of array but for 1 single number which is float.
                 Preserve array type for netCDF recording.
                 fraction of explained variance
        - reverse_sign_list: list of bool
        - solver
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
        frac_Nth.attrs["units"] = "ratio"
        pc_Nth.attrs[
            "comment"
        ] = f"Non-scaled time series for principal component of {eofn}th variance mode"

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


def arbitrary_checking(mode, eof_Nth):
    """
    To keep sign of EOF pattern consistent across observations or models,
    this function check whether multiplying -1 to EOF pattern and PC is needed or not
    Input
    - mode: string, modes of variability. e.g., 'PDO', 'PNA', 'NAM', 'SAM'
    - eof_Nth: xarray DataArray, eof pattern
    Ouput
    - reverse_sign: bool, True or False
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
):
    """
    - Reconstruct EOF fist mode including teleconnection purpose as well
    - Have confirmed that "eof_lr" is identical to "eof" over EOF domain (i.e., "subdomain")
    - Note that eof_lr has global field
    """
    if debug:
        print("pc.shape, timeseries.shape:", pc.shape, ds[data_var].shape)

    # Linear regression to have extended global map; teleconnection purpose
    slope, intercept = linear_regression(pc, ds[data_var])

    if not RmDomainMean and EofScaling:
        factor = 1
    else:
        factor = stdv_pc

    eof_lr = (slope * factor) + intercept

    debug_print("linear regression done", debug)

    return eof_lr, slope, intercept


def linear_regression(x, y):
    """
    NOTE: Proceed linear regression
    Input
    - x: 1d timeseries (time)
    - y: time varying 2d field (time, lat, lon)
    Output
    - slope: 2d array, spatial map, linear regression slope on each grid
    - intercept: 2d array, spatial map, linear regression intercept on each grid
    """
    # get original global dimension
    lat = get_latitude(y)
    lon = get_longitude(y)
    # Convert 3d (time, lat, lon) to 2d (time, lat*lon) for polyfit applying
    im = y.shape[2]
    jm = y.shape[1]
    y_2d = y.data.reshape(y.shape[0], jm * im)
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
    return slope, intercept


def gain_pseudo_pcs(
    solver,
    field_to_be_projected: xr.DataArray,
    eofn,
    reverse_sign=False,
    EofScaling=False,
):
    """
    Given a data set, projects it onto the n-th EOF to generate a corresponding set of pseudo-PCs
    """
    if not EofScaling:
        pseudo_pcs = solver.projectField(
            field_to_be_projected, neofs=eofn, eofscaling=0
        )
    else:
        pseudo_pcs = solver.projectField(
            field_to_be_projected, neofs=eofn, eofscaling=1
        )
    # Get CBF PC (pseudo pcs in the code) for given eofs
    pseudo_pcs = pseudo_pcs[:, eofn - 1]
    # Arbitrary sign control, attempt to make all plots have the same sign
    if reverse_sign:
        # pseudo_pcs = MV2.multiply(pseudo_pcs, -1.0)
        pseudo_pcs *= -1
    # return result
    return pseudo_pcs


def gain_pcs_fraction(
    full_field: xr.DataArray,
    eof_pattern: xr.DataArray,
    pcs: xr.DataArray,
    weights: xr.DataArray = None,
    debug: bool = False,
):
    """
    NOTE: This function is designed for getting fraction of variace obtained by
          pseudo pcs
    Input: (dimension x, y, t should be identical for above inputs)
    - full_field (t,y,x)
    - eof_pattern (y,x)
    - pcs (t)
    Output:
    - fraction: array but for 1 single number which is float.
                Preserve array type for netCDF recording.
                fraction of explained variance
    """
    # 1) Get total variacne ---
    """
    variance_total = genutil.statistics.variance(full_field, axis="t")
    variance_total_area_ave = cdutil.averager(
        variance_total, axis="xy", weights="weighted"
    )
    """
    variance_total = np.var(full_field, axis=0)
    variance_total_area_ave = np.average(variance_total, weights=weights)
    # 2) Get variance for pseudo pattern ---
    # 2-1) Reconstruct field based on pseudo pattern
    if debug:
        print("from gain_pcs_fraction:")
        print("full_field.shape (before grower): ", full_field.shape)
        print("eof_pattern.shape (before grower): ", eof_pattern.shape)
    # Extend eof_pattern (add 3rd dimension as time then copy same 2d value for all time step)
    """
    reconstructed_field = genutil.grower(full_field, eof_pattern)[
        1
    ]  # Matching dimension (add time axis)
    for t in range(0, len(pcs)):
        reconstructed_field[t] = MV2.multiply(reconstructed_field[t], pcs[t])
    """
    reconstructed_field = full_field * pcs
    # 2-2) Get variance of reconstructed field
    """
    variance_partial = genutil.statistics.variance(reconstructed_field, axis="t")
    variance_partial_area_ave = cdutil.averager(
        variance_partial, axis="xy", weights="weighted"
    )
    """
    variance_partial = np.var(reconstructed_field, axis=0)
    variance_partial_area_ave = np.average(variance_partial, weights=weights)
    # 3) Calculate fraction ---
    """
    fraction = MV2.divide(variance_partial_area_ave, variance_total_area_ave)
    """
    fraction = variance_partial_area_ave / variance_total_area_ave
    # debugging
    if debug:
        print("full_field.shape (after grower): ", full_field.shape)
        print("reconstructed_field.shape: ", reconstructed_field.shape)
        print("variance_partial_area_ave: ", variance_partial_area_ave)
        print("variance_total_area_ave: ", variance_total_area_ave)
        print("fraction: ", fraction)
        print("from gain_pcs_fraction done")
    # return result
    return fraction


def adjust_timeseries(
    ds: xr.Dataset,
    data_var: str,
    mode: str,
    season: str,
    regions_specs: dict = None,
    RmDomainMean: bool = True,
) -> xr.Dataset:
    """
    Remove annual cycle (for all modes) and get its seasonal mean time series if
    needed. Then calculate residual by subtraction domain (or global) average.
    Input
    - ds: array (t, y, x)
    Output
    - timeseries_season: array (t, y, x)
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError(
            "The first parameter of adjust_timeseries must be an xarray Dataset"
        )
    # Reomove annual cycle (for all modes) and get its seasonal mean time series if needed
    ds_anomaly = get_anomaly_timeseries(ds, data_var, season)
    # Calculate residual by subtracting domain (or global) average
    ds_residual = get_residual_timeseries(
        ds_anomaly, data_var, mode, regions_specs, RmDomainMean=RmDomainMean
    )
    # return result
    return ds_residual


def get_anomaly_timeseries(ds: xr.Dataset, data_var: str, season: str) -> xr.Dataset:
    """
    Get anomaly time series by removing annual cycle
    Input
    - timeseries: variable
    - season: string
    Output
    - timeseries_ano: variable
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError(
            "The first parameter of get_anomaly_timeseries must be an xarray Dataset"
        )
    # Get anomaly field
    if season == "yearly":
        ds_anomaly = ds.temporal.departures(data_var, freq="year", weighted=True)
    else:
        # Remove annual cycle
        ds_anomaly = ds.temporal.departures(data_var, freq="month", weighted=True)
        if season != "monthly":
            ds_anomaly_all_seasons = ds_anomaly.temporal.departures(
                data_var,
                freq="season",
                weighted=True,
                season_config={"dec_mode": "DJF", "drop_incomplete_djf": True},
            )
            ds_anomaly = select_by_season(ds_anomaly_all_seasons, season)
    # return result
    return ds_anomaly


def select_by_season(ds: xr.Dataset, season: str) -> xr.Dataset:
    time_key = get_time_key(ds)
    lat_bnds_key = get_latitude_bounds_key(ds)
    lon_bnds_key = get_longitude_bounds_key(ds)
    ds_subset = ds.where(ds[time_key].dt.season == season, drop=True)
    # Preserve original spatial bounds info
    ds_subset[lat_bnds_key] = get_latitude_bounds(ds)
    ds_subset[lon_bnds_key] = get_longitude_bounds(ds)
    return ds_subset


def get_residual_timeseries(
    ds_anomaly: xr.Dataset,
    data_var: str,
    mode: str,
    regions_specs: dict = None,
    RmDomainMean: bool = True,
) -> xr.Dataset:
    """
    Calculate residual by subtracting domain average (or global mean)
    Input
    - ds_anomaly: anomaly time series, array, 3d (t, y, x)
    - mode: string, mode name, must be defined in regions_specs
    - RmDomainMean: bool (True or False).
          If True, remove domain mean of each time step.
          Ref:
              Bonfils and Santer (2011)
                  https://doi.org/10.1007/s00382-010-0920-1
              Bonfils et al. (2015)
                  https://doi.org/10.1175/JCLI-D-15-0341.1
          If False, remove global mean of each time step for PDO, or
              do nothing for other modes
          Default is True for this function.
    - region_subdomain: lat lon range of sub domain for given mode, which was
          extracted from regions_specs -- that is a dict contains domain
          lat lon ragne for given mode
    Output
    - ds_residual: array, 3d (t, y, x)
    """
    if not isinstance(ds_anomaly, xr.Dataset):
        raise TypeError(
            "The first parameter of get_residual_timeseries must be an xarray Dataset"
        )
    ds_residual = ds_anomaly.copy()
    if RmDomainMean:
        # Get domain mean
        ds_anomaly_region = region_subset(
            ds_anomaly, mode, data_var=data_var, regions_specs=regions_specs
        )
        ds_anomaly_mean = ds_anomaly_region.spatial.average(data_var)
        # Subtract domain mean
        ds_residual[data_var] = ds_anomaly[data_var] - ds_anomaly_mean[data_var]
    else:
        if mode in ["PDO", "NPGO", "AMO"]:
            # Get global mean (latitude -60 to 70)
            ds_anomaly_subset = select_subset(ds_anomaly, lat=(-60, 70))
            ds_anomaly_subset_mean = ds_anomaly_subset.spatial.average(data_var)
            # Subtract global mean
            ds_residual[data_var] = (
                ds_anomaly[data_var] - ds_anomaly_subset_mean[data_var]
            )
    # return result
    return ds_residual


def debug_print(string, debug):
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print("debug: " + nowtime + " " + string)
