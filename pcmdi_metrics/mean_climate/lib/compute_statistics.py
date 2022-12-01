import xcdat
import math
import numpy as np


def annual_mean(dm, do, var=None):
    """Computes ANNUAL MEAN"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Annual Mean",
            "Abstract": "Compute Annual Mean",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "Assumes input are 12 months climatology",
        }
    dm_am = dm.temporal.average(var)
    do_am = do.temporal.average(var)
    return dm_am, do_am  # DataSets


def seasonal_mean(d, season, var=None):
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


def bias_xy(dm, do, var=None, weights=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif = dm[var] - do[var]
    if weights is None:
        weights = dm.spatial.get_weights(axis=['X', 'Y'])
    stat = float(dif.weighted(weights).mean(("lon", "lat")))
    return float(stat)


def bias_xyt(dm, do, var=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    ds['dif'] = dm[var] - do[var]
    stat = ds.spatial.average('dif', axis=['X', 'Y']).temporal.average('dif')['dif'].values
    return float(stat)


def cor_xy(dm, do, var=None, weights=None):
    """Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Correlation",
            "Abstract": "Compute Spatial Correlation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if weights is None:
        weights = dm.spatial.get_weights(axis=['X', 'Y'])
    
    dm_avg = dm.spatial.average(var, axis=['X', 'Y'], weights=weights)[var].values
    do_avg = do.spatial.average(var, axis=['X', 'Y'], weights=weights)[var].values
    
    covariance = ((dm[var] - dm_avg) * (do[var] - do_avg)).weighted(weights).mean(dim=['lon', 'lat']).values
    std_dm = std_xy(dm, var)
    std_do = std_xy(do, var)
    stat = covariance / (std_dm * std_do)
    
    return float(stat)


def mean_xy(d, var=None, weights=None):
    """Computes bias"""
    if d is None:  # just want the doc
        return {
            "Name": "Mean",
            "Abstract": "Area Mean (area weighted)",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    
    if weights is None:
        weights = d.spatial.get_weights(axis=['X', 'Y'])
    stat = float(d[var].weighted(weights).mean(("lon", "lat")))
    return float(stat)


def meanabs_xy(dm, do, var=None, weights=None):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if weights is None:
        weights = dm.spatial.get_weights(axis=['X', 'Y'])
    dif = abs(dm[var] - do[var])
    stat = dif.weighted(weights).mean(("lon", "lat"))
    return float(stat)


def meanabs_xyt(dm, do, var=None):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    ds['absdif'] = abs(dm[var] - do[var])
    stat = ds.spatial.average('absdif', axis=['X', 'Y']).temporal.average('absdif')['absdif'].values
    return float(stat)


def rms_0(dm, do, var=None, weighted=True):
    """Computes rms over first axis -- compare two zonal mean fields"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Root Mean Square over First Axis",
            "Abstract": "Compute Root Mean Square over the first axis",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif_square = (dm[var] - do[var])**2
    if weighted:
        weights = dm.spatial.get_weights(axis=['Y'])
        stat = math.sqrt(dif_square.weighted(weights).mean(("lat")))
    else:
        stat = math.sqrt(dif_square.mean(("lat")))
    return float(stat)


def rms_xy(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Spatial Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dif_square = (dm[var] - do[var])**2
    weights = dm.spatial.get_weights(axis=['X', 'Y'])
    stat = math.sqrt(dif_square.weighted(weights).mean(("lon", "lat")))
    return float(stat)


def rms_xyt(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatio-Temporal Root Mean Square",
            "Abstract": "Compute Spatial and Temporal Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    print('jwlee-test-rms_xyt-1')
    ds['diff_square'] = (dm[var] - do[var])**2
    ds['diff_square_sqrt'] = np.sqrt(ds.spatial.average('diff_square', axis=['X', 'Y'])['diff_square'])
    print('jwlee-test-rms_xyt-2')
    stat = ds.temporal.average('diff_square_sqrt')['diff_square_sqrt'].values   
    print('jwlee-test-rms_xyt-3')
    return float(stat)


def rmsc_xy(dm, do, var=None, weights=None):
    """Computes centered rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Centered Spatial Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if weights is None:
        weights = dm.spatial.get_weights(axis=['X', 'Y'])
        
    dm_anomaly = dm[var] - dm[var].weighted(weights).mean(("lon", "lat"))
    do_anomaly = do[var] - do[var].weighted(weights).mean(("lon", "lat"))
    diff_square = (dm_anomaly - do_anomaly)**2

    stat = math.sqrt(diff_square.weighted(weights).mean(("lon", "lat")))
    return float(stat)


def std_xy(d, var=None, weights=None):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial Standard Deviation",
            "Abstract": "Compute Spatial Standard Deviation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }    
    
    average = float(d.spatial.average(var, axis=['X', 'Y'])[var].values)
    anomaly = (d[var] - average)**2
    if weights is None:
        weights = d.spatial.get_weights(axis=['X', 'Y'])
    variance = float(anomaly.weighted(weights).mean(("lon", "lat")))
    std = math.sqrt(variance)
    return float(std)


def std_xyt(d, var=None):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial-temporal Standard Deviation",
            "Abstract": "Compute Space-Time Standard Deviation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = d.copy(deep=True)
    average = d.spatial.average(var, axis=['X', 'Y']).temporal.average(var)[var]
    ds['anomaly'] = (d[var] - average)**2
    variance = ds.spatial.average('anomaly').temporal.average('anomaly')['anomaly'].values
    std = math.sqrt(variance)
    return(std)


def zonal_mean(dm, do, var=None):
    """Computes ZONAL MEAN assumes rectilinear/regular grid"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Zonal Mean",
            "Abstract": "Compute Zonal Mean",
            "Contact": "pcmdi-metrics@llnl.gov",
            "Comments": "",
        }
    dm_zm = dm.spatial.average(var, axis=['X'])
    do_zm = do.spatial.average(var, axis=['X'])
    return dm_zm, do_zm  # DataSets
