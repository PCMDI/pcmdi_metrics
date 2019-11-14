import os
# Must be done before any CDAT library is called.
# https://github.com/CDAT/cdat/issues/2213
if 'UVCDAT_ANONYMOUS_LOG' not in os.environ:
    os.environ['UVCDAT_ANONYMOUS_LOG'] = 'no'

import cdms2
import cdutil
import genutil
import numpy as np
import MV2


def model_land_mask_out(model, model_timeseries, model_lf_path):
    """
    Note: Extract SST (mask out land region)
    """
    try:
        # Read model's land fraction
        f_lf = cdms2.open(model_lf_path)
        lf = f_lf('sftlf', latitude=(-90, 90))
        f_lf.close()
    except Exception:
        # Estimate landmask
        lf = estimate_landmask(model_timeseries)

    # Check land fraction variable to see if it meet criteria
    # (0 for ocean, 100 for land, no missing value)
    lf_axes = lf.getAxisList()
    lf_id = lf.id

    lf = MV2.array(lf.filled(0.))
    lf.setAxisList(lf_axes)
    lf.id = lf_id

    # In case landfraction is in range of 0-1 (ratio), convert it to 0-100 (%)
    if np.max(lf) == 1.:
        lf = lf * 100

    # Matching dimension
    model_timeseries, lf_timeConst = genutil.grower(model_timeseries, lf)

    # full_grid_only = True
    full_grid_only = False

    if full_grid_only:  # Masking out partial land grids as well
        # Mask out land even fractional (leave only pure ocean grid)
        model_timeseries_masked = np.ma.masked_where(
            lf_timeConst > 0, model_timeseries)
    else:  # Mask out only full land grid & use weighting for partial land grid
        model_timeseries_masked = np.ma.masked_where(
            lf_timeConst == 100, model_timeseries)  # mask out pure land grids
        # Special case treatment
        if model == 'EC-EARTH':
            # Mask out over 90% land grids for models those consider river as
            # part of land-sea fraction. So far only 'EC-EARTH' does..
            model_timeseries_masked = np.ma.masked_where(
                lf_timeConst >= 90, model_timeseries)
        lf2 = (100.-lf)/100.
        model_timeseries, lf2_timeConst = genutil.grower(
            model_timeseries, lf2)  # Matching dimension
        model_timeseries_masked = model_timeseries_masked * \
            lf2_timeConst  # consider land fraction like as weighting

    # Retrive dimension coordinate ---
    model_axes = model_timeseries.getAxisList()
    model_timeseries_masked.setAxisList(model_axes)

    return(model_timeseries_masked)


def estimate_landmask(d):
    print('Estimate landmask')
    n = 1
    sft = cdutil.generateLandSeaMask(d(*(slice(0, 1),) * n)) * 100.0
    sft[:] = sft.filled(100.0)
    d2 = sft
    d2.setAxis(0, d.getAxis(1))
    d2.setAxis(1, d.getAxis(2))
    d2.id = 'sftlf'
    return d2
