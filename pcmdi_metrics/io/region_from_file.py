import geopandas as gpd
import regionmask


def region_from_file(data, rgn_path, attr, feature):
    """
    Return data masked from a feature in the input file.

    This function reads a region from a file, creates a mask based on the specified feature,
    and applies the mask to the input data.

    Parameters
    ----------
    data : xarray.Dataset or xarray.DataArray
        The input data to be masked. Must have 'lon' and 'lat' coordinates.
    rgn_path : str
        Path to the file containing region information.
    attr : str
        Attribute name in the region file to use for feature selection.
    feature : str
        Name of the region to be selected.

    Returns
    -------
    xarray.Dataset or xarray.DataArray
        The input data masked to the specified region.

    Raises
    ------
    Exception
        If there's an error in creating the region subset from the file or in applying the mask.

    Notes
    -----
    This function uses geopandas to read the region file and regionmask to create and apply the mask.
    The input data must have 'lon' and 'lat' coordinates.

    Examples
    --------
    >>> import xarray as xr
    >>> data = xr.open_dataset('path/to/data.nc')
    >>> masked_data = region_from_file(data, 'path/to/regions.shp', 'region_name', 'Europe')
    """
    lon = data["lon"].data
    lat = data["lat"].data

    print("Reading region from file.")
    try:
        regions_df = gpd.read_file(rgn_path)
        regions = regionmask.from_geopandas(regions_df, names=attr)
        mask = regions.mask(lon, lat)
        # Can't match mask by name, rather index of name
        val = list(regions_df[attr]).index(feature)
    except Exception as e:
        print("Error in creating region subset from file:")
        raise e

    try:
        masked_data = data.where(mask == val)
    except Exception as e:
        print("Error: Region selection failed.")
        raise e

    return masked_data
