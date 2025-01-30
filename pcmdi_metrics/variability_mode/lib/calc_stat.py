from time import gmtime, strftime

import xarray as xr

from pcmdi_metrics.io import get_grid, region_subset
from pcmdi_metrics.stats import bias_xy, cor_xy, mean_xy, rms_xy, rmsc_xy
from pcmdi_metrics.utils import regrid


def calc_stats_save_dict(
    mode: str,
    dict_head: dict,
    model_ds: xr.Dataset,
    model_data_var: str,
    eof: xr.Dataset,
    eof_lr: xr.Dataset,
    pc,
    stdv_pc,
    frac,
    regions_specs: dict = None,
    obs_ds: xr.Dataset = None,
    eof_obs=None,
    eof_lr_obs=None,
    stdv_pc_obs=None,
    obs_compare=True,
    method="eof",
    debug=False,
):
    """
    Calculate statistics and save results to a dictionary for JSON output.

    This function computes various statistics based on the provided model and observational
    data, and stores the results in a dictionary format suitable for JSON serialization.

    Parameters
    ----------
    mode : str
        The name of the variability mode.
    dict_head : dict
        A subset of the dictionary to which results will be added.
    model_ds : xr.Dataset
        The dataset containing model data.
    model_data_var : str
        The variable name in the model dataset.
    eof : xr.Dataset
        The linear regressed EOF pattern for the EOF domain (2D field).
    eof_lr : xr.Dataset
        The linear regressed EOF pattern for the global domain (2D field).
    pc : array-like
        The principal component time series (1D field).
    stdv_pc : float
        The standard deviation of the principal component time series.
    frac : float
        The fraction of explained variance.
    regions_specs : dict, optional
        Specifications for regions, if applicable. Default is None.
    obs_ds : xr.Dataset, optional
        The dataset containing observational data. Default is None.
    eof_obs : optional
        The EOF pattern over the subdomain from observations (2D field). Default is None.
    eof_lr_obs : optional
        The linear regressed EOF pattern over the globe from observations (2D field). Default is None.
    stdv_pc_obs : float, optional
        The standard deviation of the principal component time series of observations. Default is None.
    obs_compare : bool, optional
        Whether to calculate statistics against the given observations. Default is True.
    method : str, optional
        The method to use, either 'eof' or 'cbf'. Default is 'eof'.
    debug : bool, optional
        A flag to enable debugging output. Default is False.

    Returns
    -------
    None
    """

    # Add to dictionary for json output
    dict_head["frac"] = float(frac)
    dict_head["stdv_pc"] = stdv_pc
    debug_print("frac and stdv_pc end", debug)

    # Mean
    dict_head["mean"] = mean_xy(eof)
    dict_head["mean_glo"] = mean_xy(eof_lr)
    debug_print("mean end", debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # OBS statistics, save as dictionary
    # Note: '_glo' indicates statistics calculated over global domain
    # . . . . . . . . . . . . . . . . . . . . . . . . .
    if obs_compare:
        ref_grid_global = get_grid(obs_ds)
        # Regrid (interpolation, model grid to ref grid)
        debug_print("regrid (global) start", debug)
        eof_model_global = regrid(
            model_ds, data_var=model_data_var, target_grid=ref_grid_global
        )[model_data_var]
        debug_print("regrid end", debug)
        # Extract subdomain
        eof_model = region_subset(eof_model_global, mode, regions_specs=regions_specs)

        # Spatial correlation weighted by area ('generate' option for weights)
        cor = cor_xy(eof_model, eof_obs)
        cor_glo = cor_xy(eof_model_global, eof_lr_obs)
        debug_print(f"cor: {cor}", debug)
        debug_print("cor end", debug)

        if method == "eof":
            # Double check for arbitrary sign control
            if cor < 0:
                debug_print("eof pattern pcor < 0, flip sign!", debug)

                eof.values = eof.values * -1
                pc.values = pc.values * -1
                eof_lr.values = eof_lr.values * -1
                eof_model.values = eof_model.values * -1
                eof_model_global.values = eof_model_global.values * -1

                # Calc cor again
                cor = cor_xy(eof_model, eof_obs)
                cor_glo = cor_xy(eof_model_global, eof_lr_obs)
                debug_print(f"cor (revised): {cor}", debug)

                # Also update mean value
                dict_head["mean"] = mean_xy(eof)
                dict_head["mean_glo"] = mean_xy(eof_lr)

        # RMS (uncentered) difference
        rms = rms_xy(eof_model, eof_obs)
        rms_glo = rms_xy(eof_model_global, eof_lr_obs)
        debug_print("rms end", debug)

        # RMS (centered) difference
        rmsc = rmsc_xy(eof_model, eof_obs, NormalizeByOwnSTDV=True)
        rmsc_glo = rmsc_xy(eof_model_global, eof_lr_obs, NormalizeByOwnSTDV=True)
        debug_print("rmsc end", debug)

        # Bias
        bias = bias_xy(eof_model, eof_obs)
        bias_glo = bias_xy(eof_model_global, eof_lr_obs)
        debug_print("bias end", debug)

        # Add to dictionary for json output
        dict_head["rms"] = rms
        dict_head["rms_glo"] = rms_glo
        dict_head["rmsc"] = rmsc
        dict_head["rmsc_glo"] = rmsc_glo
        dict_head["cor"] = cor
        dict_head["cor_glo"] = cor_glo
        dict_head["bias"] = bias
        dict_head["bias_glo"] = bias_glo
        dict_head["stdv_pc_ratio_to_obs"] = stdv_pc / stdv_pc_obs

        return dict_head, eof_lr


def calcSTD(a):
    # Calculate standard deviation
    # a: xarray DataArray 1d variables
    # biased=0 option enables divided by N-1 instead of N
    result = a.std(ddof=1).values.item()
    return float(result)


def debug_print(string, debug):
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print("debug: " + nowtime + " " + string)
