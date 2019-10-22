import cdutil
import genutil
import MV2

# from pcmdi_metrics.variability_mode.lib import debug_print


def calc_stats_save_dict(
        dict_head, eof, eof_lr, slope, pc, stdv_pc, frac,
        region_subdomain,
        eof_obs=None, eof_lr_obs=None, stdv_pc_obs=None,
        obs_compare=True, method='eof', debug=False):
    """
    NOTE: Calculate statistics and save numbers to dictionary for JSON.
    Input
    - dict_head: [dict] subset of dictionary
    - eof: [2d cdms2 field] linear regressed eof pattern (eof domain)
    - eof_lr: [2d cdms2 field] linear regressed eof pattern (global)
    - slope: [2d cdms2 field] slope from above linear regression (bring it here to calculate rmsc)
    - pc: [1d cdms2 field] principle component time series
    - stdv_pc: [float] standard deviation of principle component time series
    - frac: [1 number cdms2 field] fraction of explained variance
    - eof_obs: [2d cdms2 field] eof pattern over subdomain from observation
    - eof_lr_obs: [2d cdms2 field] eof pattern over globe (linear regressed) from observation
    - stdv_pc_obs: [float] standard deviation of principle component time series of observation
    - obs_compare: [bool] calculate statistics against given observation (default=True)
    - method: [string] 'eof' or 'cbf'
    - debug: [bool]
    """

    # Add to dictionary for json output
    dict_head['frac'] = float(frac)
    dict_head['stdv_pc'] = stdv_pc

    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # OBS statistics, save as dictionary
    # Note: '_glo' indicates statistics calculated over global domain
    # . . . . . . . . . . . . . . . . . . . . . . . . .
    if obs_compare:

        if method in ['eof', 'cbf']:
            ref_grid_global = eof_lr_obs.getGrid()
            # Regrid (interpolation, model grid to ref grid)
            debug_print('regrid (global) start', debug)
            eof_model_global = eof_lr.regrid(
                ref_grid_global, regridTool='regrid2', mkCyclic=True)
            debug_print('regrid end', debug)
            # Extract subdomain
            eof_model = eof_model_global(region_subdomain)

        # Spatial correlation weighted by area ('generate' option for weights)
        cor = calcSCOR(eof_model, eof_obs)
        cor_glo = calcSCOR(eof_model_global, eof_lr_obs)
        debug_print('cor end', debug)

        if method == 'eof':
            # Double check for arbitrary sign control
            if cor < 0:
                eof = MV2.multiply(eof, -1)
                pc = MV2.multiply(pc, -1)
                eof_lr = MV2.multiply(eof_lr, -1)
                eof_model_global = MV2.multiply(
                    eof_model_global, -1)
                eof_model = MV2.multiply(eof_model, -1)
                # Calc cor again
                cor = calcSCOR(eof_model, eof_obs)
                cor_glo = calcSCOR(eof_model_global, eof_lr_obs)

        # RMS (uncentered) difference
        rms = calcRMS(eof_model, eof_obs)
        rms_glo = calcRMS(
            eof_model_global, eof_lr_obs)
        debug_print('rms end', debug)

        # RMS (centered) difference
        rmsc = calcRMSc(eof_model, eof_obs)
        rmsc_glo = calcRMSc(eof_model_global, eof_lr_obs)
        debug_print('rmsc end', debug)

        # Bias
        bias = calcBias(eof_model, eof_obs)
        bias_glo = calcBias(eof_model_global, eof_lr_obs)
        debug_print('bias end', debug)

        # Add to dictionary for json output
        dict_head['rms'] = rms
        dict_head['rms_glo'] = rms_glo
        dict_head['rmsc'] = rmsc
        dict_head['rmsc_glo'] = rmsc_glo
        dict_head['cor'] = cor
        dict_head['cor_glo'] = cor_glo
        dict_head['bias'] = bias
        dict_head['bias_glo'] = bias_glo
        dict_head['stdv_pc_ratio_to_obs'] = stdv_pc / stdv_pc_obs

        return dict_head, eof_lr


def calcBias(a, b):
    # Calculate bias
    # a, b: cdms 2d variables (lat, lon)
    result = cdutil.averager(a, axis='xy', weights='weighted') - \
        cdutil.averager(b, axis='xy', weights='weighted')
    return float(result)


def calcRMS(a, b):
    # Calculate root mean square (RMS) difference
    # a, b: cdms 2d variables on the same grid (lat, lon)
    result = genutil.statistics.rms(a, b, axis='xy', weights='weighted')
    return float(result)


def calcRMSc(a, b):
    # Calculate centered root mean square (RMS) difference
    # Reference: Taylor 2001 Journal of Geophysical Research, 106:7183-7192
    # a, b: cdms 2d variables on the same grid (lat, lon)
    result = genutil.statistics.rms(
        a, b, axis='xy', centered=1, weights='weighted')
    return float(result)


def calcSCOR(a, b):
    # Calculate spatial correlation
    # a, b: cdms 2d variables on the same grid (lat, lon)
    result = genutil.statistics.correlation(
        a, b, weights='generate', axis='xy')
    return float(result)


def calcTCOR(a, b):
    # Calculate temporal correlation
    # a, b: cdms 1d variables
    result = genutil.statistics.correlation(a, b)
    return float(result)


def calcSTD(a):
    # Calculate standard deviation
    # a: cdms 1d variables
    # biased=0 option enables divided by N-1 instead of N
    result = genutil.statistics.std(a, biased=0)
    return float(result)


def calcSTDmap(a):
    # Calculate spatial standard deviation from 2D map field
    # a: cdms 2d (xy) variables
    wts = cdutil.area_weights(a)
    std = genutil.statistics.std(a, axis='xy', weights=wts)
    return float(std)


def debug_print(string, debug):
    if debug:
        print('debug: '+nowtime()+' '+string)
