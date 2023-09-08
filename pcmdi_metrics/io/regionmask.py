import geopandas as gpd
import numpy as np
import os
import pandas as pd
import regionmask
import sys
import xarray as xr
import xcdat

def mask_region(data,name,coords=None,shp_path=None,column=None):
    # Return data masked from coordinate list or shapefile.
    # Masks a single region

    lon = data["lon"].data
    lat = data["lat"].data

    # Option 1: Region is defined by coord pairs
    if coords is not None:
        try:
            names=[name]
            regions = regionmask.Regions([np.array(coords)],names=names)
            mask = regions.mask(lon, lat)
            val=0
        except Exception as e:
            print("Error in creating mask from provided coordinates:")
            raise e

    # Option 2: region is defined by shapefile
    elif shp_path is not None:
        try:
            regions_file = gpd.read_file(shp_path)
            if column is not None:
                regions = regionmask.from_geopandas(regions_file,names=column)
            else:
                print("Column name not provided.")
                regions = regionmask.from_geopandas(regions_file)
            mask = regions.mask(lon, lat)
            # Can't match mask by name, rather index of name
            val = list(regions_file[column]).index(name)
        except Exception as e:
            print("Error in creating mask from shapefile:")
            raise e

    else:
        raise RuntimeError("Error in masking: Region coordinates or shapefile must be provided.")
    
    try:
        masked_data = data.where(mask == val)
    except Exception as e:
        print("Error: Masking failed.")
        raise e

    return  masked_data
