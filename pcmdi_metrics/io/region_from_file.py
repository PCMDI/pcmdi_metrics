import geopandas as gpd
import regionmask
import xarray as xr
import xcdat

def region_from_file(data,rgn_path,attr,feature):
    # Return data masked from a feature in input file.
    # Arguments:
    #    data: xcdat dataset
    #    feature: str, name of region
    #    rgn_path: str, path to file
    #    attr: str, attribute name

    lon = data["lon"].data
    lat = data["lat"].data

    print("Reading region from file.")
    try:
        regions_df = gpd.read_file(rgn_path)
        if attr is not None:
            regions = regionmask.from_geopandas(regions_df,names=attr)
        else:
            print("Attribute name not provided.")
            regions = regionmask.from_geopandas(regions_df)
        mask = regions.mask(lon, lat)
        # Can't match mask by name, rather index of name
        val = list(regions_file[attr]).index(feature)
    except Exception as e:
        print("Error in creating region subset from file:")
        raise e
    
    try:
        masked_data = data.where(mask == val)
    except Exception as e:
        print("Error: Region selection failed.")
        raise e

    return  masked_data
