import regionmask
import xarray as xr
import xcdat as xc


def create_land_sea_mask(ds: xr.Dataset, boolean: bool = False) -> xr.DataArray:
    """A function generates land sea mask (1: land, 0: sea) for given xarray Dataset,
    assuming the given xarray dataset and has latitude and longitude coordinates.

    Parameters
    ----------
    ds : xr.Dataset
        A Dataset object.
    boolen : bool, optional
        Set mask value to True (land) or False (ocean), by default False, thus 1 (land) abd 0 (ocean)

    Returns
    -------
    xr.DataArray
        A DataArray of land sea mask (1|0 or True|False for land|sea)

    Examples
    --------
    Import:

    >>> from pcmdi_metrics.utils import create_land_sea_mask

    Generate land-sea mask (land: 1, ocean: 0):

    >>> mask = create_land_sea_mask(ds)

    Generate land-sea mask (land: True, ocean: False):

    >>> mask = create_land_sea_mask(ds, boolean=True)
    """
    # Create a land-sea mask using regionmask
    land_mask = regionmask.defined_regions.natural_earth_v5_0_0.land_110

    # Get the longitude and latitude from the xarray dataset
    key_lon = xc.axis.get_dim_keys(ds, axis="X")
    key_lat = xc.axis.get_dim_keys(ds, axis="Y")

    lon = ds[key_lon]
    lat = ds[key_lat]

    # Mask the land-sea mask to match the dataset's coordinates
    land_sea_mask = land_mask.mask(lon, lat)

    if not boolean:
        # Convert the land-sea mask to a boolean mask
        land_sea_mask = xr.where(land_sea_mask, 0, 1)

    return land_sea_mask


def find_max(da: xr.DataArray) -> float:
    return float(da.max().values)


def find_min(da: xr.DataArray) -> float:
    return float(da.min().values)


def apply_landmask(
    ds: xr.Dataset,
    data_var: str,
    landfrac: xr.DataArray,
    maskland: bool = True,
    maskocean: bool = False,
    land_criteria=0.8,
    ocean_criteria=0.2,
) -> xr.DataArray:
    """_summary_

    Parameters
    ----------
    ds : xr.Dataset
        Dataset that inlcudes a DataArray to apply land-sea mask
    data_var : str
        name of DataArray in the Dataset
    landfrac : xr.DataArray
        data array for land fraction that consists 0 for ocean and 1 for land (fraction for grid along coastline)
    maskland : bool, optional
        mask out land region (thus value will exist over ocean only), by default True
    maskocean : bool, optional
        mask out ocean region (thus value will exist over land only), by default False
    land_criteria : float, optional
        when fraction is equal to land_criteria or larger, grid will be considered as land, by default 0.8
    ocean_criteria : float, optional
        when fraction is equal to ocean_criteria or smaller, grid will be considered as ocean, by default 0.2

    Returns
    -------
    xr.DataArray
        land-sea mask applied DataArray

    Examples
    --------
    Import:

    >>> from pcmdi_metrics.utils import apply_landmask

    Mask over land (values over ocean only):

    >>> da_masked = apply_landmask(ds, data_var="ts", landmask=mask, maskland=True, maskocean=False)

    Mask over ocean (values over land only):

    >>> da_masked = apply_landmask(ds, data_var="ts", landmask=mask, maskland=False, maskocean=True)
    """
    da = ds[data_var].copy()
    # if land = 100 instead of 1, divides landmask by 100
    if (find_min(landfrac) == 0 and find_max(landfrac) == 100) or (
        "units" in list(landfrac.attrs.keys()) and landfrac.units == "%"
    ):
        landfrac = landfrac / 100.0
    if maskland is True:
        da = da.where(landfrac <= ocean_criteria)
    if maskocean is True:
        da = da.where(landfrac >= land_criteria)

    return da
