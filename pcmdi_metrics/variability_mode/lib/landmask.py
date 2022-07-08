import cdms2
import cdutil
import genutil
import MV2
import numpy as np


def data_land_mask_out(dataname, data_timeseries, lf_path=None):
    """
    Note: Extract SST (mask out land region)
    """
    if lf_path is not None:
        # Read data's land fraction
        f_lf = cdms2.open(lf_path)
        lf = f_lf("sftlf", latitude=(-90, 90))
        f_lf.close()
    else:
        # Estimate landmask
        lf = estimate_landmask(data_timeseries)

    # Check land fraction variable to see if it meet criteria
    # (0 for ocean, 100 for land, no missing value)
    lf_axes = lf.getAxisList()
    lf_id = lf.id

    lf = MV2.array(lf.filled(0.0))
    lf.setAxisList(lf_axes)
    lf.id = lf_id

    # In case landfraction is in range of 0-1 (ratio), convert it to 0-100 (%)
    if np.max(lf) == 1.0:
        lf = lf * 100

    # Matching dimension
    data_timeseries, lf_timeConst = genutil.grower(data_timeseries, lf)

    # full_grid_only = True
    full_grid_only = False

    if full_grid_only:  # Masking out partial land grids as well
        # Mask out land even fractional (leave only pure ocean grid)
        data_timeseries_masked = np.ma.masked_where(lf_timeConst > 0, data_timeseries)
    else:  # Mask out only full land grid & use weighting for partial land grid
        data_timeseries_masked = np.ma.masked_where(
            lf_timeConst == 100, data_timeseries
        )  # mask out pure land grids
        # Special case treatment
        if dataname == "EC-EARTH":
            # Mask out over 90% land grids for models those consider river as
            # part of land-sea fraction. So far only 'EC-EARTH' does..
            data_timeseries_masked = np.ma.masked_where(
                lf_timeConst >= 90, data_timeseries
            )
        lf2 = (100.0 - lf) / 100.0
        data_timeseries, lf2_timeConst = genutil.grower(
            data_timeseries, lf2
        )  # Matching dimension
        data_timeseries_masked = (
            data_timeseries_masked * lf2_timeConst
        )  # consider land fraction like as weighting

    # Retrive dimension coordinate ---
    data_axes = data_timeseries.getAxisList()
    data_timeseries_masked.setAxisList(data_axes)

    return data_timeseries_masked


def estimate_landmask(d):
    print("Estimate landmask")
    n = 1
    sft = cdutil.generateLandSeaMask(d(*(slice(0, 1),) * n)) * 100.0
    sft[:] = sft.filled(100.0)
    d2 = sft
    d2.setAxis(0, d.getAxis(1))
    d2.setAxis(1, d.getAxis(2))
    d2.id = "sftlf"
    return d2
