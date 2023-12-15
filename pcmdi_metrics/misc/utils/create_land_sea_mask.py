import regionmask
import xarray as xr
import xcdat as xc


def create_land_sea_mask(ds: xr.Dataset, boolean: bool = False) -> xr.DataArray:
    """
    A function generates land sea mask (1: land, 0: sea) for given xarray Dataset,
    assuming the given xarray dataset and has latitude and longitude coordinates.

    Parameters
    ----------
    ds : xr.Dataset
        A Dataset object.
    boolen : bool, optional
        Set mask value to True (land) or False (sea), by default False

    Returns
    -------
    xr.DataArray
        A DataArray of land sea mask (1: land, 0: sea)
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
