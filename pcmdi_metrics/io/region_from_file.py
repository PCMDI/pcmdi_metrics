import geopandas as gpd
import numpy as np
import os
import pandas as pd
import regionmask
import sys
import xarray as xr
import xcdat

def region_from_file(data,feature,coords=None,rgn_path=None,attr=None):
    # Return data masked from coordinate list or shapefile.
    # Masks a single region
    # Arguments:
    #    data: xcdat dataset
    #    feature: str, name of region
    #    coords: list, coordinates
    #    rgn_path: str, path to file
    #    attr: str, attribute name

    lon = data["lon"].data
    lat = data["lat"].data

    # Option 1: Region is defined by coord pairs
    if coords is not None:
        print("Using coordinates to select region.")
        try:
            names=[feature]
            regions = regionmask.Regions([np.array(coords)],names=names)
            mask = regions.mask(lon, lat)
            val=0
        except Exception as e:
            print("Error in extracting region by provided coordinates:")
            raise e

    # Option 2: region is defined by shapefile
    elif rgn_path is not None:
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

    else:
        raise RuntimeError("Error in region selection: Region coordinates or region file must be provided.")
    
    try:
        masked_data = data.where(mask == val)
    except Exception as e:
        print("Error: Region selection failed.")
        raise e

    return  masked_data
