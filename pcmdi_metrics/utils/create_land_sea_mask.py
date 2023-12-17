import warnings
from typing import Union

import regionmask
import xarray as xr
import xcdat as xc


def create_land_sea_mask(
    obj: Union[xr.Dataset, xr.DataArray], as_boolean: bool = False
) -> xr.DataArray:
    """Generate a land-sea mask (1 for land, 0 for sea) for a given xarray Dataset or DataArray.

    Parameters
    ----------
    obj : Union[xr.Dataset, xr.DataArray]
        The Dataset or DataArray object.
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
    key_lon = xc.axis.get_dim_keys(obj, axis="X")
    key_lat = xc.axis.get_dim_keys(obj, axis="Y")

    lon = obj[key_lon]
    lat = obj[key_lat]

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
    obj: Union[xr.Dataset, xr.DataArray],
    data_var: str = None,
    landfrac: xr.DataArray = None,
    keep_over: str = None,
    land_criteria: float = 0.8,
    ocean_criteria: float = 0.2,
) -> xr.DataArray:
    """Apply a land-sea mask to a given DataArray in an xarray Dataset.

    Parameters
    ----------
    obj : Union[xr.Dataset, xr.DataArray]
        The Dataset or DataArray object to apply a land-sea mask.
    landfrac : xr.DataArray
        Data array for land fraction that consists of 0 for ocean and 1 for land (fraction for grid along coastline).
    data_var : str
        Name of DataArray in the Dataset, required if obs is an Dataset.
    keep_over : str
        Specify whether to keep values "land" or "ocean".
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

    Keep values over land only (mask over ocean):
    >>> da_land = apply_landmask(da, landfrac=mask, keep_over="land")  # use DataArray
    >>> da_land = apply_landmask(ds, data_var="ts", landfrac=mask, keep_over="land")  # use DataSet

    Keep values over ocean only (mask over land):
    >>> da_ocean = apply_landmask(da, landfrac=mask, keep_over="ocean")  # use DataArray
    >>> da_ocean = apply_landmask(ds, data_var="ts", landfrac=mask, keep_over="ocean")  # use DataSet
    """

    if isinstance(obj, xr.DataArray):
        data_array = obj.copy()
    elif isinstance(obj, xr.Dataset):
        if data_var is None:
            raise ValueError("Invalid value for data_var. Provide name of DataArray.")
        else:
            data_array = obj[data_var].copy()

    # Validate landfrac
    if landfrac is None:
        landfrac = create_land_sea_mask(data_array)
        warnings.warn(
            "landfrac is not provided thus generated using the 'create_land_sea_mask' function"
        )

    # Check units of landfrac
    percentage = False
    if find_min(landfrac) == 0 and find_max(landfrac) == 100:
        percentage = True
    if "units" in list(landfrac.attrs.keys()):
        if landfrac.units == "%":
            percentage = True

    # Convert landfrac to a fraction if it's in percentage form
    if percentage:
        landfrac /= 100.0

    # Validate keep_over parameter
    if keep_over not in ["land", "ocean"]:
        raise ValueError(
            "Invalid value for keep_over. Choose either 'land' or 'ocean'."
        )

    # Apply land and ocean masks
    if keep_over == "land":
        data_array = data_array.where(landfrac >= land_criteria)
    elif keep_over == "ocean":
        data_array = data_array.where(landfrac <= ocean_criteria)

    return data_array
