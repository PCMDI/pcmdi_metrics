from typing import Union

import numpy as np
import xarray as xr

#  SEASONAL RANGE - USING ANNUAL CYCLE CLIMATOLGIES 0=Jan, 11=Dec


def da_to_ds(d: Union[xr.Dataset, xr.DataArray], var: str = "variable") -> xr.Dataset:
    """Convert xarray DataArray to Dataset

    Parameters
    ----------
    d : Union[xr.Dataset, xr.DataArray]
        Input dataArray. If dataset is given, no process will be done
    var : str, optional
        Name of dataArray, by default "variable"

    Returns
    -------
    xr.Dataset
        xarray Dataset

    Raises
    ------
    TypeError
        Raised when given input is not xarray based variables
    """
    if isinstance(d, xr.Dataset):
        return d.copy()
    elif isinstance(d, xr.DataArray):
        return d.to_dataset(name=var).bounds.add_missing_bounds().copy()
    else:
        raise TypeError(
            "Input must be an instance of either xarrary.DataArray or xarrary.Dataset"
        )


def regrid(da_in, da_grid, data_var="pr"):
    ds_in = da_to_ds(da_in, data_var)
    ds_grid = da_to_ds(da_grid, data_var)

    ds_out = ds_in.regridder.horizontal(data_var, ds_grid, tool="regrid2")
    da_out = ds_out[data_var]

    return da_out


def compute_season(data, season_indices, weights):
    out = np.ma.zeros(data.shape[1:], dtype=data.dtype)
    N = 0
    for i in season_indices:
        out += data[i] * weights[i]
        N += weights[i]
    return out / N


def mpd(data):
    """Monsoon precipitation intensity and annual range calculation
    .. describe:: Input
        *  data
            * Assumes climatology array with 12 times step first one January
    """
    months_length = [
        31.0,
        28.0,
        31.0,
        30.0,
        31.0,
        30.0,
        31.0,
        31.0,
        30.0,
        31.0,
        30.0,
        31.0,
    ]
    mjjas = compute_season(data, [4, 5, 6, 7, 8], months_length)
    ndjfm = compute_season(data, [10, 11, 0, 1, 2], months_length)
    ann = compute_season(data, list(range(12)), months_length)

    data_map = data.isel(time=0)

    annrange = mjjas - ndjfm

    da_annrange = xr.DataArray(annrange, coords=data_map.coords, dims=data_map.dims)
    da_annrange = da_annrange.where(da_annrange.lat >= 0, da_annrange * -1)

    mpi = np.divide(da_annrange.values, ann, where=ann.astype(bool))

    da_mpi = xr.DataArray(mpi, coords=data_map.coords, dims=data_map.dims)

    return da_annrange, da_mpi


def mpi_skill_scores(annrange_mod_dom, annrange_obs_dom, threshold=2.5 / 86400.0):
    """Monsoon precipitation index skill score calculation
    see Wang et al., doi:10.1007/s00382-010-0877-0

      .. describe:: Input

          *  annrange_mod_dom

              * Model Values Range (summer - winter)

          *  annrange_obs_dom

              * Observations Values Range (summer - winter)

          *  threshold [default is 2.5/86400.]

              * threshold in same units as inputs
    """
    mt = np.ma.greater(annrange_mod_dom, threshold)
    ot = np.ma.greater(annrange_obs_dom, threshold)

    hitmap = mt * ot  # only where both  mt and ot are True
    hit = float(hitmap.sum())

    xor = np.ma.logical_xor(mt, ot)
    missmap = xor * ot
    missed = float(missmap.sum())

    falarmmap = xor * mt
    falarm = float(falarmmap.sum())

    if (hit + missed + falarm) > 0.0:
        score = hit / (hit + missed + falarm)
    else:
        score = 1.0e20

    xr_hitmap = xr.DataArray(
        hitmap,
        name="hitmap",
        coords={"lat": annrange_mod_dom.lat, "lon": annrange_mod_dom.lon},
        dims=["lat", "lon"],
    )

    xr_missmap = xr.DataArray(
        missmap,
        name="missmap",
        coords={"lat": annrange_mod_dom.lat, "lon": annrange_mod_dom.lon},
        dims=["lat", "lon"],
    )

    xr_falarmmap = xr.DataArray(
        falarmmap,
        name="falarmmap",
        coords={"lat": annrange_mod_dom.lat, "lon": annrange_mod_dom.lon},
        dims=["lat", "lon"],
    )

    return hit, missed, falarm, score, xr_hitmap, xr_missmap, xr_falarmmap
