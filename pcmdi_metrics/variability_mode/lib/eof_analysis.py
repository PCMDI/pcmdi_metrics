from __future__ import print_function
from eofs.cdms import Eof
from time import gmtime, strftime
import cdms2
import cdutil
import genutil
import MV2
import numpy as np
import sys

# from pcmdi_metrics.variability_mode.lib import debug_print


def eof_analysis_get_variance_mode(
        mode, timeseries, eofn, eofn_max=None,
        debug=False, EofScaling=False,
        save_multiple_eofs=False):
    """
    NOTE: Proceed EOF analysis
    Input
    - mode (string): mode of variability is needed for arbitrary sign
                     control, which is characteristics of EOF analysis
    - timeseries (cdms2 variable): time varying 2d array, so 3d array
                                  (time, lat, lon)
    - eofn (integer): Target eofs to be return
    - eofn_max (integer): number of eofs to diagnose (1~N)
    Output
      1) When 'save_multiple_eofs = False'
        - eof_Nth: eof pattern (map) for given eofs as eofn
        - pc_Nth: corresponding principle component time series
        - frac_Nth: cdms2 array but for 1 single number which is float.
                 Preserve cdms2 array type for netCDF recording.
                 fraction of explained variance
        - reverse_sign_Nth: bool
        - solver
      2) When 'save_multiple_eofs = True'
        - eof_list: list of eof patterns (map) for given eofs as eofn
        - pc_list: list of corresponding principle component time series
        - frac_list: list of cdms2 array but for 1 single number which is float.
                 Preserve cdms2 array type for netCDF recording.
                 fraction of explained variance
        - reverse_sign_list: list of bool
        - solver
    """
    if debug:
        print('Lib-EOF: timeseries.shape:', timeseries.shape)
    debug_print('Lib-EOF: solver', debug)

    if eofn_max is None:
        eofn_max = eofn
        save_multiple_eofs = False

    # EOF (take only first variance mode...) ---
    solver = Eof(timeseries, weights='area')
    debug_print('Lib-EOF: eof', debug)

    # pcscaling=1 by default, return normalized EOFs
    eof = solver.eofsAsCovariance(neofs=eofn_max, pcscaling=1)
    debug_print('Lib-EOF: pc', debug)

    if EofScaling:
        # pcscaling=1: scaled to unit variance
        # (i.e., divided by the square-root of their eigenvalue)
        pc = solver.pcs(npcs=eofn_max, pcscaling=1)
    else:
        pc = solver.pcs(npcs=eofn_max)  # pcscaling=0 by default

    # fraction of explained variance
    frac = solver.varianceFraction()
    debug_print('Lib-EOF: frac', debug)

    # For each EOFs...
    eof_list = []
    pc_list = []
    frac_list = []
    reverse_sign_list = []

    for n in range(0, eofn_max):
        eof_Nth = eof[n]
        pc_Nth = pc[:, n]
        frac_Nth = cdms2.createVariable(frac[n])

        # Arbitrary sign control, attempt to make all plots have the same sign
        reverse_sign = arbitrary_checking(mode, eof_Nth)

        if reverse_sign:
            eof_Nth = MV2.multiply(eof_Nth, -1.)
            pc_Nth = MV2.multiply(pc_Nth, -1.)

        # time axis
        pc_Nth.setAxis(0, timeseries.getTime())

        # Supplement NetCDF attributes
        frac_Nth.units = 'ratio'
        pc_Nth.comment = ''.join([
            'Non-scaled time series for principal component of ',
            str(eofn), 'th variance mode'])

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
        eof_Nth = eof_list[eofn-1]
        pc_Nth = pc_list[eofn-1]
        frac_Nth = frac_list[eofn-1]
        reverse_sign_Nth = reverse_sign_list[eofn-1]
        return eof_Nth, pc_Nth, frac_Nth, reverse_sign_Nth, solver


def arbitrary_checking(mode, eof_Nth):
    """
    NOTE: To keep sign of EOF pattern consistent across observations or models,
          this function check whether multiplying -1 to EOF pattern and PC
          is needed or not
    Input
    - mode: string, modes of variability. e.g., 'PDO', 'PNA', 'NAM', 'SAM'
    - eof_Nth: cdms2 array from eofs, eof pattern
    Ouput
    - reverse_sign: bool, True or False
    """
    reverse_sign = False
    # Explicitly check average of geographical region for each mode
    if mode == 'PDO':
        if float(cdutil.averager(
                 eof_Nth(latitude=(30, 40), longitude=(150, 180)),
                 axis='xy', weights='weighted')) >= 0:
            reverse_sign = True
    elif mode == 'PNA':
        if float(cdutil.averager(eof_Nth(latitude=(80, 90)),
                                 axis='xy', weights='weighted')) <= 0:
            reverse_sign = True
    elif mode == 'NAM' or mode == 'NAO':
        if float(cdutil.averager(eof_Nth(latitude=(60, 80)),
                                 axis='xy', weights='weighted')) >= 0:
            reverse_sign = True
    elif mode == 'SAM':
        if float(cdutil.averager(eof_Nth(latitude=(-60, -90)),
                                 axis='xy', weights='weighted')) >= 0:
            reverse_sign = True
    else:  # Minimum sign control part was left behind for any future usage..
        if float(eof_Nth[-1][-1]) is not eof_Nth.missing:
            if float(eof_Nth[-1][-1]) >= 0:
                reverse_sign = True
        elif float(eof_Nth[-2][-2]) is not eof_Nth.missing:
            if float(eof_Nth[-2][-2]) >= 0:  # Double check missing value at pole
                reverse_sign = True
    # return result
    return reverse_sign


def linear_regression_on_globe_for_teleconnection(
        pc, model_timeseries, stdv_pc,
        RmDomainMean, EofScaling, debug=False):
    """
    - Reconstruct EOF fist mode including teleconnection purpose as well
    - Have confirmed that "eof_lr" is identical to "eof" over EOF domain (i.e., "subdomain")
    - Note that eof_lr has global field
    """
    if debug:
        print('pc.shape, timeseries.shape:', pc.shape, model_timeseries.shape)

    # Linear regression to have extended global map; teleconnection purpose
    slope, intercept = linear_regression(
        pc, model_timeseries)
    if RmDomainMean:
        eof_lr = MV2.add(MV2.multiply(
            slope, stdv_pc), intercept)
    else:
        if not EofScaling:
            eof_lr = MV2.add(MV2.multiply(
                slope, stdv_pc), intercept)
        else:
            eof_lr = MV2.add(slope, intercept)

    debug_print('linear regression done', debug)

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
    lat = y.getLatitude()
    lon = y.getLongitude()
    # Convert 3d (time, lat, lon) to 2d (time, lat*lon) for polyfit applying
    im = y.shape[2]
    jm = y.shape[1]
    y_2d = y.reshape(y.shape[0], jm * im)
    # Linear regression
    slope_1d, intercept_1d = np.polyfit(x, y_2d, 1)
    # Retreive to cdms2 variabile from numpy array
    slope = MV2.array(slope_1d.reshape(jm, im))
    intercept = MV2.array(intercept_1d.reshape(jm, im))
    # Set lat/lon coordinates
    slope.setAxis(0, lat)
    slope.setAxis(1, lon)
    slope.mask = y.mask
    intercept.setAxis(0, lat)
    intercept.setAxis(1, lon)
    intercept.mask = y.mask
    # return result
    return slope, intercept


def gain_pseudo_pcs(solver, field_to_be_projected, eofn, reverse_sign,
                    EofScaling=False):
    """
    NOTE: Given a data set, projects it onto the n-th EOF to generate a
          corresponding set of pseudo-PCs
    """
    if not EofScaling:
        pseudo_pcs = solver.projectField(
            field_to_be_projected, neofs=eofn, eofscaling=0)
    else:
        pseudo_pcs = solver.projectField(
            field_to_be_projected, neofs=eofn, eofscaling=1)
    # Get CBF PC (pseudo pcs in the code) for given eofs
    pseudo_pcs = pseudo_pcs[:, eofn - 1]
    # Arbitrary sign control, attempt to make all plots have the same sign
    if reverse_sign:
        pseudo_pcs = MV2.multiply(pseudo_pcs, -1.)
    # return result
    return pseudo_pcs


def gain_pcs_fraction(full_field, eof_pattern, pcs, debug=False):
    """
    NOTE: This function is designed for getting fraction of variace obtained by
          pseudo pcs
    Input: (dimension x, y, t should be identical for above inputs)
    - full_field (t,y,x)
    - eof_pattern (y,x)
    - pcs (t)
    Output:
    - fraction: cdms2 array but for 1 single number which is float.
                Preserve cdms2 array type for netCDF recording.
                fraction of explained variance
    """
    # 1) Get total variacne ---
    variance_total = genutil.statistics.variance(full_field, axis='t')
    variance_total_area_ave = cdutil.averager(
        variance_total, axis='xy', weights='weighted')
    # 2) Get variance for pseudo pattern ---
    # 2-1) Reconstruct field based on pseudo pattern
    if debug:
        print('from gain_pcs_fraction:')
        print('full_field.shape (before grower): ', full_field.shape)
        print('eof_pattern.shape (before grower): ', eof_pattern.shape)
    # Extend eof_pattern (add 3rd dimension as time then copy same 2d value for all time step)
    reconstructed_field = genutil.grower(full_field, eof_pattern)[1]  # Matching dimension (add time axis)
    for t in range(0, len(pcs)):
        reconstructed_field[t] = MV2.multiply(reconstructed_field[t], pcs[t])
    # 2-2) Get variance of reconstructed field
    variance_partial = genutil.statistics.variance(
        reconstructed_field, axis='t')
    variance_partial_area_ave = cdutil.averager(
        variance_partial, axis='xy', weights='weighted')
    # 3) Calculate fraction ---
    fraction = MV2.divide(variance_partial_area_ave, variance_total_area_ave)
    # debugging
    if debug:
        print('full_field.shape (after grower): ', full_field.shape)
        print('reconstructed_field.shape: ', reconstructed_field.shape)
        print('variance_partial_area_ave: ', variance_partial_area_ave)
        print('variance_total_area_ave: ', variance_total_area_ave)
        print('fraction: ', fraction)
        print('from gain_pcs_fraction done')
    # return result
    return fraction


def adjust_timeseries(timeseries, mode, season, region_subdomain, RmDomainMean):
    """
    NOTE
    Remove annual cycle (for all modes) and get its seasonal mean time series if
    needed. Then calculate residual by subtraction domain (or global) average.
    Input
    - timeseries: cdms2 array (t, y, x)
    Output
    - timeseries_season: cdms2 array (t, y, x)
    """
    # Reomove annual cycle (for all modes) and get its seasonal mean time series if needed
    timeseries_ano = get_anomaly_timeseries(timeseries, season)
    # Calculate residual by subtracting domain (or global) average
    timeseries_season = get_residual_timeseries(
        timeseries_ano, mode, region_subdomain, RmDomainMean=RmDomainMean)
    # return result
    return timeseries_season


def get_anomaly_timeseries(timeseries, season):
    """
    NOTE: Get anomaly time series by removing annual cycle
    Input
    - timeseries: cdms variable
    - season: string
    Output
    - timeseries_ano: cdms variable
    """
    # Get anomaly field
    if season == 'yearly':
        timeseries_ano = cdutil.YEAR.departures(timeseries)
    else:
        # Special treat for DJF
        if season == 'DJF':
            # Input field must be monthly, starting at Jan and ending at Dec
            smon = timeseries.getTime().asComponentTime()[0].month
            emon = timeseries.getTime().asComponentTime()[-1].month
            if (smon == 1 and emon == 12):
                # Truncate first Jan Feb and last Dec
                timeseries = timeseries[2:-1, :, :]
            else:
                sys.exit(' '.join([
                    'ERROR: Starting month', str(smon),
                    'and ending month', str(emon),
                    'must be 1 and 12, respectively']))
        # Reomove annual cycle
        timeseries_ano = cdutil.ANNUALCYCLE.departures(timeseries)
        if season != 'monthly':
            # Get seasonal mean time series
            # each season chunk should have 100% of data
            timeseries_ano = getattr(cdutil, season)(
                timeseries_ano, criteriaarg=[1.0, None])
    # return result
    return timeseries_ano


def get_residual_timeseries(timeseries_ano, mode, region_subdomain, RmDomainMean=True):
    """
    NOTE: Calculate residual by subtracting domain average (or global mean)
    Input
    - timeseries_ano: anomaly time series, cdms2 array, 3d (t, y, x)
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
    - timeseries_residual: cdms2 array, 3d (t, y, x)
    """
    if RmDomainMean:
        # Get domain mean
        regional_ano_mean_timeseries = cdutil.averager(
            timeseries_ano(region_subdomain),
            axis='xy',
            weights='weighted')
        # Match dimension
        timeseries_ano, regional_ano_mean_timeseries = \
            genutil.grower(
                timeseries_ano, regional_ano_mean_timeseries)
        # Subtract domain mean
        timeseries_residual = MV2.subtract(
            timeseries_ano, regional_ano_mean_timeseries)
    else:
        if mode in ['PDO', 'NPGO']:
            # Get global mean
            global_ano_mean_timeseries = cdutil.averager(
                timeseries_ano(latitude=(-60, 70)),
                axis='xy',
                weights='weighted')
            # Match dimension
            timeseries_ano, global_ano_mean_timeseries = \
                genutil.grower(
                    timeseries_ano, global_ano_mean_timeseries)
            # Subtract global mean
            timeseries_residual = MV2.subtract(
                timeseries_ano, global_ano_mean_timeseries)
        else:
            timeseries_residual = timeseries_ano
    # return result
    return timeseries_residual


def debug_print(string, debug):
    if debug:
        nowtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print('debug: '+nowtime+' '+string)
