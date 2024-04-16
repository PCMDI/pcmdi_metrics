from time import gmtime, strftime

import xarray as xr

from pcmdi_metrics.io import get_grid, region_subset
from pcmdi_metrics.stats import bias_xy as calcBias
from pcmdi_metrics.stats import cor_xy as calcSCOR
from pcmdi_metrics.stats import mean_xy
from pcmdi_metrics.stats import rms_xy as calcRMS
from pcmdi_metrics.stats import rmsc_xy as calcRMSc
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
    NOTE: Calculate statistics and save numbers to dictionary for JSON.
    Input
    - mode: [str] name of variability mode
    - dict_head: [dict] subset of dictionary
    - eof: [2d field] linear regressed eof pattern (eof domain)
    - eof_lr: [2d field] linear regressed eof pattern (global)
    - slope: [2d field] slope from above linear regression (bring it here to calculate rmsc)
    - pc: [1d field] principle component time series
    - stdv_pc: [float] standard deviation of principle component time series
    - frac: [1 number field] fraction of explained variance
    - eof_obs: [2d field] eof pattern over subdomain from observation
    - eof_lr_obs: [2d field] eof pattern over globe (linear regressed) from observation
    - stdv_pc_obs: [float] standard deviation of principle component time series of observation
    - obs_compare: [bool] calculate statistics against given observation (default=True)
    - method: [string] 'eof' or 'cbf'
    - debug: [bool]
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
        # ref_grid_global = get_grid(eof_lr_obs)
        ref_grid_global = get_grid(obs_ds)
        # Regrid (interpolation, model grid to ref grid)
        debug_print("regrid (global) start", debug)
        # eof_model_global = eof_lr.regrid(eof_lr,
        #    ref_grid_global, regridTool="regrid2", mkCyclic=True
        # )
        # eof_model_global = regrid(eof_lr, ref_grid_global)
        eof_model_global = regrid(
            model_ds, data_var=model_data_var, target_grid=ref_grid_global
        )[model_data_var]
        debug_print("regrid end", debug)
        # Extract subdomain
        # eof_model = eof_model_global(region_subdomain)
        eof_model = region_subset(eof_model_global, mode, regions_specs=regions_specs)

        # Spatial correlation weighted by area ('generate' option for weights)
        cor = calcSCOR(eof_model, eof_obs)
        cor_glo = calcSCOR(eof_model_global, eof_lr_obs)
        debug_print(f"cor: {cor}", debug)
        debug_print("cor end", debug)

        if method == "eof":
            # Double check for arbitrary sign control
            if cor < 0:
                debug_print("eof pattern pcor < 0, flip sign!", debug)
                # variables_to_flip_sign = [eof, pc, eof_lr, eof_model_global, eof_model]
                # for variable in variables_to_flip_sign:
                #    variable *= -1
                eof.values = eof.values * -1
                pc.values = pc.values * -1
                eof_lr.values = eof_lr.values * -1
                eof_model.values = eof_model.values * -1
                eof_model_global.values = eof_model_global.values * -1

                # Calc cor again
                cor = calcSCOR(eof_model, eof_obs)
                cor_glo = calcSCOR(eof_model_global, eof_lr_obs)
                debug_print(f"cor (revised): {cor}", debug)

                # Also update mean value
                dict_head["mean"] = mean_xy(eof)
                dict_head["mean_glo"] = mean_xy(eof_lr)

        # RMS (uncentered) difference
        rms = calcRMS(eof_model, eof_obs)
        rms_glo = calcRMS(eof_model_global, eof_lr_obs)
        debug_print("rms end", debug)

        # RMS (centered) difference
        rmsc = calcRMSc(eof_model, eof_obs)
        rmsc_glo = calcRMSc(eof_model_global, eof_lr_obs)
        debug_print("rmsc end", debug)

        # Bias
        bias = calcBias(eof_model, eof_obs)
        bias_glo = calcBias(eof_model_global, eof_lr_obs)
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
