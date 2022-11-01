import cdutil
import genutil
import MV2
import xcdat
import xskillscore as xs
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
    return dm_am, do_am    


def bias_xy(dm, do, var=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['dif'] = dm[var] - do[var]
    stat = dm.spatial.average('dif', axis=['X', 'Y'])['dif'].values
    return float(stat)


def bias_xyt(dm, do, var=None):
    """Computes bias"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Bias",
            "Abstract": "Compute Full Average of Model - Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['dif'] = dm[var] - do[var]
    stat = dm.spatial.average('dif', axis=['X', 'Y']).temporal.average('dif')['dif'].values
    return float(stat)


def cor_xy(dm, do, var=None):
    """Computes correlation"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Correlation",
            "Abstract": "Compute Spatial Correlation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    spatial_weights = dm.spatial.get_weights(axis=['X', 'Y'])
    stat = xs.pearson_r(dm[var], do[var], weights=spatial_weights).values
    return float(stat)


def mean_xy(d, var=None):
    """Computes bias"""
    if d is None:  # just want the doc
        return {
            "Name": "Mean",
            "Abstract": "Area Mean (area weighted)",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    stat = d.spatial.average(var, axis=['X', 'Y'])[var].values
    return float(stat)


def meanabs_xy(dm, do, var=None):
    """Computes Mean Absolute Error"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Absolute Error",
            "Abstract": "Compute Full Average of "
            + "Absolute Difference Between Model And Observation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['absdif'] = abs(dm[var] - do[var])
    stat = dm.spatial.average('absdif', axis=['X', 'Y'])['absdif'].values
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
    dm['absdif'] = abs(dm[var] - do[var])
    stat = dm.spatial.average('absdif', axis=['X', 'Y']).temporal.average('absdif')['absdif'].values
    return float(stat)


def rms_0(dm, do, var=None):
    """Computes rms over first axis"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Root Mean Square over First Axis",
            "Abstract": "Compute Root Mean Square over the first axis",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['diff_square'] = (dm[var] - do[var])**2
    stat = math.sqrt(dm.spatial.average('diff_square', axis=['X', 'Y'])['diff_square'].values)
    return float(stat)


def rms_xy(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Spatial Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['diff_square'] = (dm[var] - do[var])**2
    stat = math.sqrt(dm.spatial.average('diff_square', axis=['X', 'Y'])['diff_square'].values)
    return float(stat)


def rms_xyt(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatio-Temporal Root Mean Square",
            "Abstract": "Compute Spatial and Temporal Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['diff_square'] = (dm[var] - do[var])**2
    dm['diff_square_sqrt'] = np.sqrt(dm.spatial.average('diff_square', axis=['X', 'Y'])['diff_square'])
    stat = dm.temporal.average('diff_square_sqrt')['diff_square_sqrt'].values   
    return float(stat)


def rmsc_xy(dm, do, var=None):
    """Computes centered rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Spatial Root Mean Square",
            "Abstract": "Compute Centered Spatial Root Mean Square",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    dm['anomaly'] = dm[var] - dm.spatial.average(var, axis=['X', 'Y'])[var]
    do['anomaly'] = do[var] - do.spatial.average(var, axis=['X', 'Y'])[var]
    dm['diff_square'] = (dm['anomaly'] - do['anomaly'])**2
    stat = math.sqrt(dm.spatial.average('diff_square', axis=['X', 'Y'])['diff_square'].values)
    return float(stat)


def seasonal_mean(d, sea, var=None):
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

    return d_season


def std_xy(d, var=None):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial Standard Deviation",
            "Abstract": "Compute Spatial Standard Deviation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    average = float(d.spatial.average(var, axis=['X', 'Y'])[var].values)
    d['anomaly'] = (d[var] - average)**2
    variance = float(d.spatial.average('anomaly')['anomaly'].values)
    std = math.sqrt(variance)
    return(std)


def std_xyt(d, var=None):
    """Computes std"""
    if d is None:  # just want the doc
        return {
            "Name": "Spatial-temporal Standard Deviation",
            "Abstract": "Compute Space-Time Standard Deviation",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    average = float(d.spatial.average(var, axis=['X', 'Y']).temporal.average(var)[var].values)
    d['anomaly'] = (d[var] - average)**2
    variance = float(d.spatial.average('anomaly').temporal.average('anomaly')['anomaly'].values)
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
    return cdutil.averager(dm, axis="x"), cdutil.averager(do, axis="x")
