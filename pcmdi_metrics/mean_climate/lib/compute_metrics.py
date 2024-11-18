import re
from collections import OrderedDict
from typing import Any, Dict, Optional

import xarray as xr

from pcmdi_metrics import stats


def compute_metrics(
    var: str,
    dm: Optional[xr.Dataset] = None,
    do: Optional[xr.Dataset] = None,
    debug: bool = False,
    time_dim_sync: bool = False,
) -> Dict[str, Any]:
    """
    Compute various climate metrics for a given variable.

    This function calculates a wide range of climate metrics, including RMS errors,
    correlations, standard deviations, and means for annual, seasonal, and monthly
    time scales.

    Parameters
    ----------
    var : str
        The variable name to compute metrics for.
    dm : xr.Dataset, optional
        The model dataset.
    do : xr.Dataset, optional
        The observational dataset.
    debug : bool, default False
        If True, print additional debug information.
    time_dim_sync : bool, default False
        If True, synchronize the time dimension between model and observational datasets.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the computed metrics.

    Notes
    -----
    If both `dm` and `do` are None, the function returns a dictionary of metric
    definitions without computing any values.
    """
    # Var is sometimes sent with level associated
    var = re.split(r"[_-]", var)[0]
    print(f"var: {var}")

    # Did we send data? Or do we just want the info?
    if dm is None and do is None:
        metrics_defs = OrderedDict()
        metrics_defs["rms_xyt"] = stats.rms_xyt(None, None)
        metrics_defs["rms_xy"] = stats.rms_xy(None, None)
        metrics_defs["rmsc_xy"] = stats.rmsc_xy(None, None)
        metrics_defs["bias_xy"] = stats.bias_xy(None, None)
        metrics_defs["mae_xy"] = stats.meanabs_xy(None, None)
        metrics_defs["cor_xy"] = stats.cor_xy(None, None)
        metrics_defs["mean_xy"] = stats.mean_xy(None)
        metrics_defs["std_xy"] = stats.std_xy(None)
        metrics_defs["std_xyt"] = stats.std_xyt(None)

        metrics_defs["seasonal_mean"] = stats.seasonal_mean(None, None)
        metrics_defs["annual_mean"] = stats.annual_mean(None, None)
        metrics_defs["zonal_mean"] = stats.zonal_mean(None, None)
        return metrics_defs

    # Copy the dataset to avoid the original being changed
    dm = dm.copy(deep=True)
    do = do.copy(deep=True)

    # unify time and time bounds between observation and model
    if debug:
        print("dm.time: ", dm["time"])
        print("do.time: ", do["time"])

    if time_dim_sync:
        bounds_key = dm.time.attrs["bounds"]
        do["time"] = dm["time"]
        do[bounds_key] = dm[bounds_key]

        if debug:
            print("time and time bounds synced")
            print("dm.time: ", dm["time"])
            print("do.time: ", do["time"])

            dm.to_netcdf("dm.nc")
            do.to_netcdf("do.nc")

    metrics_dictionary = OrderedDict()

    # QC for bounds
    dm = dm.bounds.add_missing_bounds()
    do = do.bounds.add_missing_bounds()

    float_format = "{:.5e}"

    # CALCULATE ANNUAL CYCLE SPACE-TIME RMS, CORRELATIONS and STD
    print("metrics-CALCULATE ANNUAL CYCLE SPACE-TIME RMS, CORRELATIONS and STD")

    print("metrics, rms_xyt")
    rms_xyt = stats.rms_xyt(dm, do, var)
    print("metrics, rms_xyt:", rms_xyt)

    print("metrics, stdObs_xyt")
    stdObs_xyt = stats.std_xyt(do, var)
    print("metrics, stdObs_xyt:", stdObs_xyt)

    print("metrics, std_xyt")
    std_xyt = stats.std_xyt(dm, var)
    print("metrics, std_xyt:", std_xyt)

    # CALCULATE ANNUAL MEANS
    print("metrics-CALCULATE ANNUAL MEANS")
    dm_am, do_am = stats.annual_mean(dm, do, var)

    # CALCULATE ANNUAL MEAN BIAS
    print("metrics-CALCULATE ANNUAL MEAN BIAS")
    bias_xy = stats.bias_xy(dm_am, do_am, var)
    print("metrics-CALCULATE ANNUAL MEAN BIAS, bias_xy:", bias_xy)

    # CALCULATE MEAN ABSOLUTE ERROR
    print("metrics-CALCULATE MSE")
    mae_xy = stats.meanabs_xy(dm_am, do_am, var)
    print("metrics-CALCULATE MSE, mae_xy:", mae_xy)

    # CALCULATE ANNUAL MEAN RMS (centered and uncentered)
    print("metrics-CALCULATE MEAN RMS")
    rms_xy = stats.rms_xy(dm_am, do_am, var)
    rmsc_xy = stats.rmsc_xy(dm_am, do_am, var)
    print("metrics-CALCULATE MEAN RMS: rms_xy, rmsc_xy: ", rms_xy, rmsc_xy)

    # CALCULATE ANNUAL MEAN CORRELATION
    print("metrics-CALCULATE MEAN CORR")
    cor_xy = stats.cor_xy(dm_am, do_am, var)
    print("metrics-CALCULATE MEAN CORR: cor_xy:", cor_xy)

    # CALCULATE ANNUAL OBS and MOD STD
    print("metrics-CALCULATE ANNUAL OBS AND MOD STD")
    stdObs_xy = stats.std_xy(do_am, var)
    std_xy = stats.std_xy(dm_am, var)

    # CALCULATE ANNUAL OBS and MOD MEAN
    print("metrics-CALCULATE ANNUAL OBS AND MOD MEAN")
    meanObs_xy = stats.mean_xy(do_am, var)
    mean_xy = stats.mean_xy(dm_am, var)

    # ZONAL MEANS ######
    # CALCULATE ANNUAL MEANS
    print("metrics-CALCULATE ANNUAL MEANS")
    dm_amzm, do_amzm = stats.zonal_mean(dm_am, do_am, var)

    # CALCULATE ANNUAL AND ZONAL MEAN RMS
    print("metrics-CALCULATE ANNUAL AND ZONAL MEAN RMS")
    rms_y = stats.rms_0(dm_amzm, do_amzm, var)

    # CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN RMS
    print("metrics-CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN RMS")
    dm_am_devzm = dm_am - dm_amzm
    do_am_devzm = do_am - do_amzm
    rms_xy_devzm = stats.rms_xy(
        dm_am_devzm, do_am_devzm, var, weights=dm.spatial.get_weights(axis=["X", "Y"])
    )

    # CALCULATE ANNUAL AND ZONAL MEAN STD

    # CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN STD
    print("metrics-CALCULATE ANNUAL MEAN DEVIATION FROM ZONAL MEAN STD")
    stdObs_xy_devzm = stats.std_xy(
        do_am_devzm, var, weights=do.spatial.get_weights(axis=["X", "Y"])
    )
    std_xy_devzm = stats.std_xy(
        dm_am_devzm, var, weights=dm.spatial.get_weights(axis=["X", "Y"])
    )

    for stat in sorted(
        [
            "std-obs_xy",
            "std_xy",
            "std-obs_xyt",
            "std_xyt",
            "std-obs_xy_devzm",
            "mean_xy",
            "mean-obs_xy",
            "std_xy_devzm",
            "rms_xyt",
            "rms_xy",
            "rmsc_xy",
            "cor_xy",
            "bias_xy",
            "mae_xy",
            "rms_y",
            "rms_devzm",
        ]
    ):
        metrics_dictionary[stat] = OrderedDict()

    metrics_dictionary["mean-obs_xy"]["ann"] = float_format.format(meanObs_xy)
    metrics_dictionary["mean_xy"]["ann"] = float_format.format(mean_xy)
    metrics_dictionary["std-obs_xy"]["ann"] = float_format.format(stdObs_xy)
    metrics_dictionary["std_xy"]["ann"] = float_format.format(std_xy)
    metrics_dictionary["std-obs_xyt"]["ann"] = float_format.format(stdObs_xyt)
    metrics_dictionary["std_xyt"]["ann"] = float_format.format(std_xyt)
    metrics_dictionary["std-obs_xy_devzm"]["ann"] = float_format.format(stdObs_xy_devzm)
    metrics_dictionary["std_xy_devzm"]["ann"] = float_format.format(std_xy_devzm)
    metrics_dictionary["rms_xyt"]["ann"] = float_format.format(rms_xyt)
    metrics_dictionary["rms_xy"]["ann"] = float_format.format(rms_xy)
    metrics_dictionary["rmsc_xy"]["ann"] = float_format.format(rmsc_xy)
    metrics_dictionary["cor_xy"]["ann"] = float_format.format(cor_xy)
    metrics_dictionary["bias_xy"]["ann"] = float_format.format(bias_xy)
    metrics_dictionary["mae_xy"]["ann"] = float_format.format(mae_xy)
    # ZONAL MEAN CONTRIBUTIONS
    metrics_dictionary["rms_y"]["ann"] = float_format.format(rms_y)
    metrics_dictionary["rms_devzm"]["ann"] = float_format.format(rms_xy_devzm)

    # CALCULATE SEASONAL MEANS
    for sea in ["djf", "mam", "jja", "son"]:
        dm_sea = stats.seasonal_mean(dm, sea, var)
        do_sea = stats.seasonal_mean(do, sea, var)

        # CALCULATE SEASONAL RMS AND CORRELATION
        rms_sea = stats.rms_xy(dm_sea, do_sea, var)
        rmsc_sea = stats.rmsc_xy(dm_sea, do_sea, var)
        cor_sea = stats.cor_xy(dm_sea, do_sea, var)
        mae_sea = stats.meanabs_xy(dm_sea, do_sea, var)
        bias_sea = stats.bias_xy(dm_sea, do_sea, var)

        # CALCULATE SEASONAL OBS and MOD STD
        stdObs_xy_sea = stats.std_xy(do_sea, var)
        std_xy_sea = stats.std_xy(dm_sea, var)

        # CALCULATE SEASONAL OBS and MOD MEAN
        meanObs_xy_sea = stats.mean_xy(do_sea, var)
        mean_xy_sea = stats.mean_xy(dm_sea, var)

        metrics_dictionary["bias_xy"][sea] = float_format.format(bias_sea)
        metrics_dictionary["rms_xy"][sea] = float_format.format(rms_sea)
        metrics_dictionary["rmsc_xy"][sea] = float_format.format(rmsc_sea)
        metrics_dictionary["cor_xy"][sea] = float_format.format(cor_sea)
        metrics_dictionary["mae_xy"][sea] = float_format.format(mae_sea)
        metrics_dictionary["std-obs_xy"][sea] = float_format.format(stdObs_xy_sea)
        metrics_dictionary["std_xy"][sea] = float_format.format(std_xy_sea)
        metrics_dictionary["mean-obs_xy"][sea] = float_format.format(meanObs_xy_sea)
        metrics_dictionary["mean_xy"][sea] = float_format.format(mean_xy_sea)

    rms_mo_l = []
    rmsc_mo_l = []
    cor_mo_l = []
    mae_mo_l = []
    bias_mo_l = []
    stdObs_xy_mo_l = []
    std_xy_mo_l = []
    meanObs_xy_mo_l = []
    mean_xy_mo_l = []

    for n, mo in enumerate(
        [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ]
    ):
        dm_mo = dm.isel(time=n)
        do_mo = do.isel(time=n)

        # CALCULATE MONTHLY RMS AND CORRELATION
        rms_mo = stats.rms_xy(dm_mo, do_mo, var)
        rmsc_mo = stats.rmsc_xy(dm_mo, do_mo, var)
        cor_mo = stats.cor_xy(dm_mo, do_mo, var)
        mae_mo = stats.meanabs_xy(dm_mo, do_mo, var)
        bias_mo = stats.bias_xy(dm_mo, do_mo, var)

        # CALCULATE MONTHLY OBS and MOD STD
        stdObs_xy_mo = stats.std_xy(do_mo, var)
        std_xy_mo = stats.std_xy(dm_mo, var)

        # CALCULATE MONTHLY OBS and MOD MEAN
        meanObs_xy_mo = stats.mean_xy(do_mo, var)
        mean_xy_mo = stats.mean_xy(dm_mo, var)

        rms_mo_l.append(float_format.format(rms_mo))
        rmsc_mo_l.append(float_format.format(rmsc_mo))
        cor_mo_l.append(float_format.format(cor_mo))
        mae_mo_l.append(float_format.format(mae_mo))
        bias_mo_l.append(float_format.format(bias_mo))
        stdObs_xy_mo_l.append(float_format.format(stdObs_xy_mo))
        std_xy_mo_l.append(float_format.format(std_xy_mo))
        meanObs_xy_mo_l.append(float_format.format(meanObs_xy_mo))
        mean_xy_mo_l.append(float_format.format(mean_xy_mo))

    metrics_dictionary["bias_xy"]["CalendarMonths"] = bias_mo_l
    metrics_dictionary["rms_xy"]["CalendarMonths"] = rms_mo_l
    metrics_dictionary["rmsc_xy"]["CalendarMonths"] = rmsc_mo_l
    metrics_dictionary["cor_xy"]["CalendarMonths"] = cor_mo_l
    metrics_dictionary["mae_xy"]["CalendarMonths"] = mae_mo_l
    metrics_dictionary["std-obs_xy"]["CalendarMonths"] = stdObs_xy_mo_l
    metrics_dictionary["std_xy"]["CalendarMonths"] = std_xy_mo_l
    metrics_dictionary["mean-obs_xy"]["CalendarMonths"] = meanObs_xy_mo_l
    metrics_dictionary["mean_xy"]["CalendarMonths"] = mean_xy_mo_l

    return metrics_dictionary


# ZONAL AND SEASONAL MEAN CONTRIBUTIONS
#           metrics_dictionary['rms_y'][sea] = format(
#               rms_y,
#               sig_digits)
#           metrics_dictionary['rms_devzm'][sea] = format(
#               rms_xy_devzm,
#               sig_digits)
