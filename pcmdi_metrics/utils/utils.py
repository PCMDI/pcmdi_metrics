import xarray as xr
import xcdat as xc


def get_axis_list(ds: xr.Dataset) -> list[str]:
    axes = list(ds.coords.keys())
    return axes


def get_longitude(ds: xr.Dataset) -> xr.DataArray:
    key_lon = xc.axis.get_dim_keys(ds, axis="X")
    lon = ds[key_lon]
    return lon


def get_latitude(ds: xr.Dataset) -> xr.DataArray:
    key_lat = xc.axis.get_dim_keys(ds, axis="Y")
    lat = ds[key_lat]
    return lat


def select_subset(
    ds: xr.Dataset, lat: tuple = None, lon: tuple = None, time: tuple = None
) -> xr.Dataset:
    """_summary_

    Parameters
    ----------
    ds : xr.Dataset
        _description_
    lat : tuple, optional
        _description_, by default None
    lon : tuple, optional
        _description_, by default None
    time : tuple, optional
        _description_, by default None

    Returns
    -------
    xr.Dataset
        _description_

    Examples
    ---------
    Import:

    >>> from pcmdi_metrics.utils import select_subset

    Spatial subsetting:

    >>> (lat1, lat2) = (30, 50)
    >>> (lon1, lon2) = (110, 130)
    >>> ds_subset = select_subset(ds, lat=(lat1, lat2), lon=(lon1, lon2))

    Temporal subsetting:

    >>> import cftime
    >>> time1 = cftime.DatetimeProlepticGregorian(1850, 1, 16, 12, 0, 0, 0)
    >>> time2 = cftime.DatetimeProlepticGregorian(1851, 1, 16, 12, 0, 0, 0)
    >>> ds_subset = select_subset(ds, time=(time1, time2))
    """

    sel_keys = {}
    if lat is not None:
        lat_key = xc.axis.get_dim_keys(ds, axis="Y")
        sel_keys[lat_key] = slice(*lat)
    if lon is not None:
        lon_key = xc.axis.get_dim_keys(ds, axis="X")
        sel_keys[lon_key] = slice(*lon)
    if time is not None:
        time_key = xc.axis.get_dim_keys(ds, axis="T")
        sel_keys[time_key] = slice(*time)

    ds = ds.sel(**sel_keys)
    return ds
