import MV2
import numpy as np
import sys
import xarray as xr
from scipy.interpolate import griddata
from typing import Union

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
    #out = MV2.array(out)
    #out.id = data.id
    #out.setAxisList(data.getAxisList()[1:])
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
    #print("mjjas = ", mjjas)
    #print("data  = ", data)
    #print("data.dims = ", data.dims)
    print("data.coords = ", data.coords)

    #data_map = data.drop("time")
    data_map = data.isel(time=0)
    print("data_map =  ", data_map.dims)

    #sys.exit()

    #cc = xr.DataArray(data.values, coords = data.coords, dims = data.dims)
    #print("cc =  ", cc.dims)

    #annrange = MV2.subtract(mjjas, ndjfm)
    annrange = mjjas - ndjfm

    #print('annrange = ', annrange)


    #lat = annrange.getAxis(0)
    #lat = annrange['lat']


#    i, e = lat.mapInterval((-91, 0, "con"))
#    print('i = ', i, '   e = ', e)
#    if i > e:  # reveresedlats
#        tmp = i + 1
#        i = e + 1
#        e = tmp

    #print('annrange = ', annrange)
    print('annrange.shape = ', annrange.shape)
    #print('lat = ', lat)
    #print('i = ', i, '   e = ', e)

    #annrange[slice(i, e)] = -annrange[slice(i, e)]
    annrange = np.absolute(annrange)

    #print('slice = ', slice(i, e))
    #print('annrange = ', annrange)
    #annrange.id = data.id + "_ar"
    #annrange.longname = "annual range"

#    sys.exit()

    mpi = np.divide(annrange, ann, where=ann.astype(bool))
    #mpi = MV2.divide(annrange, ann)
    #mpi.id = data.id + "_int"
    #mpi.longname = "intensity"

    print('mpi.shape = ', mpi.shape)
    print('annrange.shape = ', annrange.shape)

    da_annrange = xr.DataArray(annrange, coords = data_map.coords, dims = data_map.dims)
    da_mpi = xr.DataArray(mpi, coords = data_map.coords, dims = data_map.dims)

    print('da_annrange.dims = ', da_annrange.dims)
    print('da_mpi_dims = ', da_mpi.dims)
    print('da_annrange.coords = ', da_annrange.coords)
    print('da_mpi_coords = ', da_mpi.coords)

    #print("da_mpi = ", da_mpi)

    #sys.exit()

    #return annrange, mpi
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
    #print('annrange_mod_dom = ', annrange_mod_dom)
    print('annrange_mod_dom.shape = ', annrange_mod_dom.shape)
    print('threshold = ', threshold)
    mt = np.ma.greater(annrange_mod_dom, threshold)
    ot = np.ma.greater(annrange_obs_dom, threshold)

    print('mt = ', mt)
    print('type mt = ', type(mt))
    print('mt.shape = ', mt.shape)

    hitmap = mt * ot  # only where both  mt and ot are True
    hit = float(hitmap.sum())

    xor = np.ma.logical_xor(mt, ot)
    missmap = xor * ot
    missed = float(MV2.sum(missmap))

    falarmmap = xor * mt
    falarm = float(MV2.sum(falarmmap))

    if (hit + missed + falarm) > 0.0:
        score = hit / (hit + missed + falarm)
    else:
        score = 1.0e20

    hitmap.id = "hit"
    missmap.id = "miss"
    falarmmap.id = "false_alarm"

    for a in [hitmap, missmap, falarmmap]:
        a.setAxisList(annrange_mod_dom.getAxisList())

    return hit, missed, falarm, score, hitmap, missmap, falarmmap
