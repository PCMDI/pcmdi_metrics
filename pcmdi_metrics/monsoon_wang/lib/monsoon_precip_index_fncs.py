import datetime

import numpy as np
import xarray as xr
import xcdat as xc  # noqa: F401

import pcmdi_metrics
from pcmdi_metrics.io import da_to_ds

#  SEASONAL RANGE - USING ANNUAL CYCLE CLIMATOLGIES 0=Jan, 11=Dec


def mpd(
    ds: xr.Dataset,
    data_var: str,
    reference_period: tuple = ("1981-01-01", "2004-12-31"),
) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Monsoon precipitation intensity and annual range calculation.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset containing the monsoon precipitation data.
        Assumes climatology array with 12 time steps, the first one being January.
        Otherwise, the annual climatology is computed from the input data.
    data_var : str
        The name of the variable in the dataset that contains precipitation data.
    reference_period : tuple, optional
        A tuple specifying the reference period for climatology as (start_date, end_date).
        If None, the full dataset period is used. The dates should be in 'YYYY-MM-DD' format.
        Only applies when input data is not already calculated annual climatology thus does not have 12 months.
        Default is ('1981-01-01', '2004-12-31').

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
    >>> from pcmdi_metrics.monsoon_wang.lib import mpd
    >>> ds = xr.open_dataset("path_to_your_dataset.nc")  # Load your dataset here
    >>> da_annrange, da_mpi = mpd(ds, data_var="pr")
    """
    data = ds[data_var]  # Extract the specified variable from the dataset

    # Check if the given file has the correct number of time steps (i.e., 12 months), otherwise, calculate annual climatology
    if data.shape[0] != 12:
        print(
            f"Input data, shaped {data.shape}, must have 12 time steps (months) for annual climatology."
        )
        ds_clim = ds.temporal.climatology(
            data_var, "month", reference_period=reference_period
        )
        data = ds_clim[data_var]  # Reassign data to the climatology if not 12 months
        print(
            f"Annual cycle calculated for the input data for period {reference_period}, data shaped , shaped {data.shape}."
        )

    # Ensure the input data is a DataArray
    if not isinstance(data, xr.DataArray):
        raise TypeError("Input data must be an xarray.DataArray.")

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


def save_to_netcdf_with_attributes(ds_new, ds_org, org_path, nout_mpi_obs):
    """
    Save the new dataset to a NetCDF file with attributes from the original dataset.

    Parameters
    ----------
    ds_new : xarray.Dataset
        The new dataset to be saved.
    ds_org : xarray.Dataset
        The original dataset from which attributes are copied.

    Returns
    -------
    None
    """
    # Copy global attributes from the original dataset
    for attr in ds_org.attrs:
        if attr not in ["history", "source"]:
            ds_new.attrs[attr] = ds_org.attrs[attr]
    # Add new global attributes
    ds_new.attrs[
        "history"
    ] = f"Created by PMP {pcmdi_metrics.__version__} on {datetime.datetime.now()}"
    ds_new.attrs["source"] = f"Created from {org_path} by PMP"
    # Save to netcdf
    ds_new.to_netcdf(nout_mpi_obs)
