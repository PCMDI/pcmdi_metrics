#!/usr/bin/env python
import geopandas as gpd
import numpy as np
import os
import regionmask
import sys
import xarray as xr
import xcdat


def check_region_params(shp_path,coords,region_name,col,default):
    use_region_mask = False
    
    if shp_path is not None:
        use_region_mask = True
        if not os.path.exists(shp_path):
            print("Error: Shapefile path does not exist.")
            print("Must provide valid shapefile path.")
            sys.exit()
        if region_name is None:
            print("Error: Region name parameter --region_name must be provided with shapefile.")
            sys.exit()
        if col is None:
            print("Error: Column name parameter --column must be provided with shapefile.")
            sys.exit()
        print("Region settings are:")
        print("  Shapefile:",shp_path)
        print("  Column name:",col)
        print("  Region name:",region_name)
    elif coords is not None:    
        use_region_mask = True
        # Coords is a list that might be ingested badly
        # from command line, so some cleanup is done here if needed.
        if isinstance(coords,list):
            if coords[0] == '[':
                tmp=""
                for n in range(0,len(coords)):
                    tmp=tmp+str(coords[n])
                coords = tmp
        if isinstance(coords,str):
            tmp=coords.replace("[","").replace("]","").split(",")
            coords=[[float(tmp[n]),float(tmp[n+1])] for n in range(0,len(tmp)-1,2)]
        if region_name is None:
            print("No region name provided. Using 'custom'.")
            region_name = "custom"
        print("Region settings are:")
        print("  Coordinates:",coords)
        print("  Region name:",region_name)
    else:
        region_name = default
    
    return use_region_mask,region_name,coords

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
            print("  ",e)
            sys.exit()

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
            print("  ",e)
            sys.exit()

    else:
        print("Error in masking: Region coordinates or shapefile must be provided.")
        sys.exit()
    
    try:
        masked_data = data.where(mask == val)
    except Exception as e:
        print("Error: Masking failed.")
        print("  ",e)
        sys.exit()

    return  masked_data