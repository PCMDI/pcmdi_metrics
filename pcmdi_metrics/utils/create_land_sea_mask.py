import regionmask
import xarray as xr
import xcdat as xc


def create_land_sea_mask(ds: xr.Dataset, as_boolean: bool = False) -> xr.DataArray:
    """Generate a land-sea mask (1 for land, 0 for sea) for a given xarray Dataset.

    Parameters
    ----------
    ds : xr.Dataset
        A Dataset object.
    as_boolean : bool, optional
        Set mask value to True (land) or False (ocean), by default False, thus 1 (land) and 0 (ocean).

    Returns
    -------
    xr.DataArray
        A DataArray of land-sea mask (1 or 0 for land or sea, or True or False for land or sea).

    Examples
    --------
    Import:

    >>> from pcmdi_metrics.utils import create_land_sea_mask

    Generate land-sea mask (land: 1, sea: 0):

    >>> mask = create_land_sea_mask(ds)

    Generate land-sea mask (land: True, sea: False):

    >>> mask = create_land_sea_mask(ds, as_boolean=True)
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

    if not as_boolean:
        # Convert the land-sea mask to a boolean mask
        land_sea_mask = xr.where(land_sea_mask, 0, 1)

    return land_sea_mask


def find_max(da: xr.DataArray) -> float:
    """Find the maximum value in a given xarray DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Input DataArray.

    Returns
    -------
    float
        Maximum value in the DataArray.
    """
    return float(da.max().values)


def find_min(da: xr.DataArray) -> float:
    """Find the minimum value in a given xarray DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Input DataArray.

    Returns
    -------
    float
        Minimum value in the DataArray.
    """
    return float(da.min().values)


def apply_landmask(
    ds: xr.Dataset,
    data_var: str,
    landfrac: xr.DataArray,
    mask_land: bool = True,
    mask_ocean: bool = False,
    land_criteria: float = 0.8,
    ocean_criteria: float = 0.2,
) -> xr.DataArray:
    """Apply a land-sea mask to a given DataArray in an xarray Dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset that includes a DataArray to apply a land-sea mask.
    data_var : str
        Name of DataArray in the Dataset.
    landfrac : xr.DataArray
        Data array for land fraction that consists of 0 for ocean and 1 for land (fraction for grid along coastline).
    mask_land : bool, optional
        Mask out land region (thus value will exist over ocean only), by default True.
    mask_ocean : bool, optional
        Mask out ocean region (thus value will exist over land only), by default False.
    land_criteria : float, optional
        When the fraction is equal to land_criteria or larger, the grid will be considered as land, by default 0.8.
    ocean_criteria : float, optional
        When the fraction is equal to ocean_criteria or smaller, the grid will be considered as ocean, by default 0.2.

    Returns
    -------
    xr.DataArray
        Land-sea mask applied DataArray.

    Examples
    --------
    Import:

    >>> from pcmdi_metrics.utils import apply_landmask

    Mask over land (keep values over ocean only):

    >>> da_masked = apply_landmask(ds, data_var="ts", landfrac=mask, mask_land=True, mask_ocean=False)

    Mask over ocean (keep values over land only):

    >>> da_masked = apply_landmask(ds, data_var="ts", landfrac=mask, mask_land=False, mask_ocean=True)
    """
    data_array = ds[data_var].copy()

    # Convert landfrac to a fraction if it's in percentage form
    if landfrac.units == "%" or (find_min(landfrac) == 0 and find_max(landfrac) == 100):
        landfrac /= 100.0

    # Apply land and ocean masks
    if mask_land:
        data_array = data_array.where(landfrac <= ocean_criteria)
    if mask_ocean:
        data_array = data_array.where(landfrac >= land_criteria)

    return data_array
