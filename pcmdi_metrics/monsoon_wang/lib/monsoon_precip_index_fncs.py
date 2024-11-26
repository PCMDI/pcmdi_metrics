import numpy as np
import xarray as xr

from pcmdi_metrics.io import da_to_ds

#  SEASONAL RANGE - USING ANNUAL CYCLE CLIMATOLGIES 0=Jan, 11=Dec


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


def mpd(data: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Monsoon precipitation intensity and annual range calculation.

    Parameters
    ----------
    data : xarray.DataArray
        Assumes climatology array with 12 time steps, the first one being January.

    Returns
    -------
    da_annrange : xarray.DataArray
        The annual range of monsoon precipitation.
    da_mpi : xarray.DataArray
        The monsoon precipitation intensity.

    Notes
    -----
    This function calculates the monsoon precipitation intensity and annual range
    by computing the difference between the monsoon season (May to September) and
    the non-monsoon season (November to March) precipitation, and then normalizing
    it by the annual precipitation.

    Examples
    --------
    >>> import xarray as xr
    >>> data = xr.DataArray([...], dims=["time", "lat", "lon"])
    >>> da_annrange, da_mpi = mpd(data)
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


def mpi_skill_scores(
    annrange_mod_dom: xr.DataArray,
    annrange_obs_dom: xr.DataArray,
    threshold: float = 2.5 / 86400.0,
) -> tuple[float, float, float, float, xr.DataArray, xr.DataArray, xr.DataArray]:
    """
    Monsoon precipitation index skill score calculation.

    Parameters
    ----------
    annrange_mod_dom : xarray.DataArray
        Model values range (summer - winter).
    annrange_obs_dom : xarray.DataArray
        Observations values range (summer - winter).
    threshold : float, optional
        Threshold in the same units as inputs, by default 2.5/86400.

    Returns
    -------
    hit : float
        Number of hits where both model and observation exceed the threshold.
    missed : float
        Number of misses where observation exceeds the threshold but model does not.
    falarm : float
        Number of false alarms where model exceeds the threshold but observation does not.
    score : float
        Skill score calculated as hit / (hit + missed + falarm).
    xr_hitmap : xarray.DataArray
        DataArray of hits.
    xr_missmap : xarray.DataArray
        DataArray of misses.
    xr_falarmmap : xarray.DataArray
        DataArray of false alarms.

    Notes
    -----
    This function calculates the monsoon precipitation index skill score as described
    in Wang et al., doi:10.1007/s00382-010-0877-0.

    Examples
    --------
    >>> import xarray as xr
    >>> annrange_mod_dom = xr.DataArray([...], dims=["lat", "lon"])
    >>> annrange_obs_dom = xr.DataArray([...], dims=["lat", "lon"])
    >>> hit, missed, falarm, score, xr_hitmap, xr_missmap, xr_falarmmap = mpi_skill_scores(annrange_mod_dom, annrange_obs_dom)
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
