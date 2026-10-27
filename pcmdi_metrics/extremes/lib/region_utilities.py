#!/usr/bin/env python
import os
import sys

import geopandas as gpd
import numpy as np
import regionmask


def check_region_params(shp_path, coords, region_name, col, default):
    use_region_mask = False

    # Underscore will mess with file name slicing in extremes driver
    if region_name is not None and "_" in region_name:
        print("Error: Underscore character not permitted in region_name.")
        sys.exit()

    if shp_path is not None:
        use_region_mask = True
        if not os.path.exists(shp_path):
            print("Error: Shapefile path does not exist.")
            print("Must provide valid shapefile path.")
            sys.exit()
        if region_name is None:
            print(
                "Error: Region name parameter --region_name must be provided with shapefile."
            )
            sys.exit()
        if col is None:
            print(
                "Error: Column name parameter --column must be provided with shapefile."
            )
            sys.exit()
        print("Region settings are:")
        print("  Shapefile:", shp_path)
        print("  Column name:", col)
        print("  Region name:", region_name)
    elif coords is not None:
        use_region_mask = True
        # Coords is a list that might be ingested badly
        # from command line, so some cleanup is done here if needed.
        if isinstance(coords, list):
            if coords[0] == "[":
                tmp = ""
                for n in range(0, len(coords)):
                    tmp = tmp + str(coords[n])
                coords = tmp
        if isinstance(coords, str):
            tmp = coords.replace("[", "").replace("]", "").split(",")
            coords = [
                [float(tmp[n]), float(tmp[n + 1])] for n in range(0, len(tmp) - 1, 2)
            ]
        if region_name is None:
            print("No region name provided. Using 'custom'.")
            region_name = "custom"
        print("Region settings are:")
        print("  Coordinates:", coords)
        print("  Region name:", region_name)
    else:
        region_name = default

    return use_region_mask, region_name, coords


def mask_region(data, name, coords=None, shp_path=None, column=None):
    """Mask spatial variables without modifying coordinate bounds."""

    lon = data["lon"]
    lat = data["lat"]

    # Option 1: Region defined by coordinate pairs
    if coords is not None:
        try:
            regions = regionmask.Regions(
                [np.array(coords)],
                names=[name],
            )

            mask = regions.mask_3D(lon, lat)
            mask = mask.isel(region=0, drop=True)

        except Exception as e:
            print("Error creating mask from coordinates:")
            print(e)
            raise

    # Option 2: Region defined by shapefile
    elif shp_path is not None:
        try:
            regions_file = gpd.read_file(shp_path)

            # Select the requested region
            selected = regions_file.loc[regions_file[column] == name].reset_index(
                drop=True
            )

            if selected.empty:
                raise ValueError(f"Region '{name}' not found.")

            regions = regionmask.from_geopandas(
                selected,
                names=column,
                overlap=True,
            )

            mask = regions.mask_3D(lon, lat)
            mask = mask.isel(region=0, drop=True)

        except Exception as e:
            print("Error creating mask from shapefile:")
            print(e)
            raise

    else:
        raise ValueError("Region coordinates or shapefile must be provided.")

    # Only mask variables containing spatial dimensions.
    # Preserve time_bnds, lat_bnds, lon_bnds, etc.
    masked_data = data.copy()

    for var in data.data_vars:
        if "lat" in data[var].dims and "lon" in data[var].dims:
            masked_data[var] = data[var].where(mask)

    return masked_data
