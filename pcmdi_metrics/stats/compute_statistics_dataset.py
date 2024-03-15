import math
from typing import Union

import numpy as np
import xarray as xr
import xcdat as xc


def da_to_ds(d: Union[xr.Dataset, xr.DataArray], var: str = "variable"):
    if isinstance(d, xr.Dataset):
        return d.copy()
    elif isinstance(d, xr.DataArray):
        return d.to_dataset(name=var).bounds.add_missing_bounds().copy()
    else:
        raise TypeError(
            "Input must be an instance of either xarrary.DataArray or xarrary.Dataset"
        )


def annual_mean(dm, do, var="variable"):
    """Computes ANNUAL MEAN"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Annual Mean",
            "Abstract": "Compute Annual Mean",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "Assumes input are 12 months climatology",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    dm_am = dm.temporal.average(var)
    do_am = do.temporal.average(var)
    return dm_am, do_am  # DataSets


def seasonal_mean(d, season, var="variable"):
    """Computes SEASONAL MEAN"""
    if d is None and season is None:  # just want the doc
        return {
            "Name": "Seasonal Mean",
            "Abstract": "Compute Seasonal Mean",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "Assumes input are 12 months climatology",
        }

    mo_wts = [31, 31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30]

    if season == "djf":
        indx = [11, 0, 1]
    if season == "mam":
        indx = [2, 3, 4]
    if season == "jja":
        indx = [5, 6, 7]
    if season == "son":
        indx = [8, 9, 10]

    season_num_days = mo_wts[indx[0]] + mo_wts[indx[1]] + mo_wts[indx[2]]

    d_season = (
        d.isel(time=indx[0])[var] * mo_wts[indx[0]]
        + d.isel(time=indx[1])[var] * mo_wts[indx[1]]
        + d.isel(time=indx[2])[var] * mo_wts[indx[2]]
    ) / season_num_days

    ds_new = d.isel(time=0).copy(deep=True)
    ds_new[var] = d_season

    return ds_new


# Metrics calculations


def bias_xy(dm, do, var="variable", weights=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    dif = dm[var] - do[var]
    if weights is None:
        weights = dm.spatial.get_weights(axis=["X", "Y"])
    # stat = float(dif.weighted(weights).mean(("lon", "lat")))
    stat = mean_xy(dif, weights=weights)
    return float(stat)


def bias_xyt(dm, do, var="variable"):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    ds = dm.copy(deep=True)
    ds["dif"] = dm[var] - do[var]
    stat = (
        ds.spatial.average("dif", axis=["X", "Y"]).temporal.average("dif")["dif"].values
    )
    return float(stat)


def cor_xy(dm, do, var="variable", weights=None):
    """Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Correlation",
            "Abstract": "Compute Spatial Correlation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    if weights is None:
        weights = dm.spatial.get_weights(axis=["X", "Y"])

    dm_avg = dm.spatial.average(var, axis=["X", "Y"], weights=weights)[var].values
    do_avg = do.spatial.average(var, axis=["X", "Y"], weights=weights)[var].values

    covariance = (
        ((dm[var] - dm_avg) * (do[var] - do_avg))
        .weighted(weights)
        .mean(dim=["lon", "lat"])
        .values
    )
    std_dm = std_xy(dm, var)
    std_do = std_xy(do, var)
    stat = covariance / (std_dm * std_do)

    return float(stat)


def mean_xy(d, var="variable", weights=None):
    """Computes bias"""
    if d is None:  # just want the doc
        return {
            "Name": "Mean",
            "Abstract": "Area Mean (area weighted)",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    d = da_to_ds(d, var)

    lat_key = xc.axis.get_dim_keys(d, axis="Y")
    lon_key = xc.axis.get_dim_keys(d, axis="X")

    if weights is None:
        weights = d.spatial.get_weights(axis=["X", "Y"])
    stat = d[var].weighted(weights).mean((lat_key, lon_key))
    return float(stat)


def meanabs_xy(dm, do, var="variable", weights=None):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    if weights is None:
        weights = dm.spatial.get_weights(axis=["X", "Y"])

    dif = abs(dm[var] - do[var])
    stat = dif.weighted(weights).mean(("lon", "lat"))
    return float(stat)


def meanabs_xyt(dm, do, var="variable"):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    ds = dm.copy(deep=True)
    ds["absdif"] = abs(dm[var] - do[var])
    stat = (
        ds.spatial.average("absdif", axis=["X", "Y"])
        .temporal.average("absdif")["absdif"]
        .values
    )
    return float(stat)


def rms_0(dm, do, var="variable", weighted=True):
    """Computes rms over first axis -- compare two zonal mean fields"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Root Mean Square over First Axis",
            "Abstract": "Compute Root Mean Square over the first axis",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    dif_square = (dm[var] - do[var]) ** 2
    if weighted:
        weights = dm.spatial.get_weights(axis=["Y"])
        stat = math.sqrt(dif_square.weighted(weights).mean(("lat")))
    else:
        stat = math.sqrt(dif_square.mean(("lat")))
    return float(stat)


def rms_xy(dm, do, var="variable", weights=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Spatial Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    dif_square = (dm[var] - do[var]) ** 2
    if weights is None:
        weights = dm.spatial.get_weights(axis=["X", "Y"])
    stat = math.sqrt(mean_xy(dif_square, var=var, weights=weights))
    return float(stat)


def rms_xyt(dm, do, var="variable"):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatio-Temporal Root Mean Square",
            "Abstract": "Compute Spatial and Temporal Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    ds = dm.copy(deep=True)
    ds["diff_square"] = (dm[var] - do[var]) ** 2
    ds["diff_square_sqrt"] = np.sqrt(
        ds.spatial.average("diff_square", axis=["X", "Y"])["diff_square"]
    )
    stat = ds.temporal.average("diff_square_sqrt")["diff_square_sqrt"].values
    return float(stat)


def rmsc_xy(dm, do, var="variable", weights=None, NormalizeByOwnSTDV=False):
    """Computes centered rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Centered Spatial Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    if weights is None:
        weights = dm.spatial.get_weights(axis=["X", "Y"])

    if NormalizeByOwnSTDV:
        dm_tmp = dm[var] / std_xy(dm[var], var=var, weights=weights)
        do_tmp = do[var] / std_xy(do[var], var=var, weights=weights)
    else:
        dm_tmp = dm[var].copy()
        do_tmp = do[var].copy()

    # Remove mean
    dm_anomaly = dm_tmp - mean_xy(dm_tmp, var=var, weights=weights)
    do_anomaly = do_tmp - mean_xy(do_tmp, var=var, weights=weights)

    stat = rms_xy(dm_anomaly, do_anomaly, var=var, weights=weights)
    return float(stat)


def std_xy(ds, var="variable", weights=None):
    """Computes std"""
    if ds is None:  # just want the doc
        return {
            "Name": "Spatial Standard Deviation",
            "Abstract": "Compute Spatial Standard Deviation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }

    ds = da_to_ds(ds, var)

    if weights is None:
        weights = ds.spatial.get_weights(axis=["X", "Y"])

    lat_key = xc.axis.get_dim_keys(ds, axis="Y")
    lon_key = xc.axis.get_dim_keys(ds, axis="X")

    average = float(ds[var].weighted(weights).mean((lat_key, lon_key)))
    anomaly = (ds[var] - average) ** 2
    variance = float(anomaly.weighted(weights).mean((lat_key, lon_key)))
    std = math.sqrt(variance)
    return float(std)


def std_xyt(d, var="variable"):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial-temporal Standard Deviation",
            "Abstract": "Compute Space-Time Standard Deviation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = d.copy(deep=True)
    ds = da_to_ds(ds, var)
    average = d.spatial.average(var, axis=["X", "Y"]).temporal.average(var)[var]
    ds["anomaly"] = (d[var] - average) ** 2
    variance = (
        ds.spatial.average("anomaly").temporal.average("anomaly")["anomaly"].values
    )
    std = math.sqrt(variance)
    return std


def zonal_mean(dm, do, var="variable"):
    """Computes ZONAL MEAN assumes rectilinear/regular grid"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Zonal Mean",
            "Abstract": "Compute Zonal Mean",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "",
        }
    dm = da_to_ds(dm, var)
    do = da_to_ds(do, var)

    dm_zm = dm.spatial.average(var, axis=["X"])
    do_zm = do.spatial.average(var, axis=["X"])
    return dm_zm, do_zm  # DataSets
