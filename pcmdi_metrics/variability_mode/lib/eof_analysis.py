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
        print("type(pc), type(ds):", type(pc), type(ds))
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
    ds_full_field: xr.Dataset,
    varname_full_field: str,
    ds_eof_pattern: xr.Dataset,
    varname_eof_pattern: str,
    pcs: xr.DataArray,
    debug: bool = False,
):
    """
    NOTE: This function is designed for getting fraction of variace obtained by
          pseudo pcs
    Input: (dimension x, y, t should be identical for above inputs)
    - ds_full_field: xarray dataset that includes full_field (t, y, x)
    - varname_full_field: name of full_field in the dataset
    - ds_eof_pattern: xarray dataset that includes eof pattern (y, x)
    - varname_eof_pattern: name of the eof_pattern in the dataset
    - pcs (t)
    Output:
    - fraction: array but for 1 single number which is float.
                Preserve array type for netCDF recording.
                fraction of explained variance
    """

    full_field = ds_full_field[varname_full_field]
    eof_pattern = ds_eof_pattern[varname_eof_pattern]

    # 1) Get total variacne --- using full_field
    time_key = get_time_key(full_field)
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
    time_key_2 = get_time_key(reconstructed_field)
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
        # remove seasonal cycle
        ds_anomaly = ds.temporal.departures(data_var, freq="month", weighted=True)
        # yearly time series
        ds_anomaly = ds_anomaly.temporal.group_average(
            data_var, freq="year", weighted=True
        )
        # restore bounds (especially time bounds)
        ds_anomaly = ds_anomaly.bounds.add_missing_bounds()
        # get overall average
        ds_ave = ds_anomaly.temporal.average(data_var)
        # anomaly
        ds_anomaly[data_var] = ds_anomaly[data_var] - ds_ave[data_var]
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
