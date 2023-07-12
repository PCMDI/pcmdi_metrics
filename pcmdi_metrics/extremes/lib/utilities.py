#!/usr/bin/env python
import cftime
import cdms2
import cdutil
import datetime
import glob
import json
import numpy as np
import os
import sys
import xarray as xr
import xcdat

from pcmdi_metrics.io.base import Base
from pcmdi_metrics.io import xcdat_openxml

from  pcmdi_utils import land_sea_mask

def load_dataset(filepath):
    # Load an xarray dataset from the given filepath.
    # If list of netcdf files, opens mfdataset.
    # If list of xmls, open last file in list.
    if filepath[-1].endswith(".xml"):
        # Final item of sorted list would have most recent version date
        ds = xcdat_openxml.xcdat_openxml(filepath[-1])
    elif len(filepath) > 1:
        ds = xcdat.open_mfdataset(filepath,chunks=None)
    else: ds = xcdat.open_dataset(filepath[0])
    return ds

def slice_dataset(ds,start_year,end_year):
    cal = ds.time.encoding["calendar"]
    start_time = cftime.datetime(start_year,1,1,calendar=cal) - datetime.timedelta(days=0)
    end_time = cftime.datetime(end_year+1,1,1,calendar=cal) - datetime.timedelta(days=1)
    ds = ds.sel(time=slice(start_time,end_time))
    return ds

def replace_multi(string,rdict):
    # Replace multiple keyworks in a string template
    # based on key-value pairs in 'rdict'.
    for k in rdict.keys():
        string = string.replace(k,rdict[k])
    return string

def write_to_nc(data,model,run,region_name,index,years,ncdir,desc,meta):
    # Consolidating some netcdf writing code here to streamline main function
    yrs = "-".join(years)
    filepath = os.path.join(ncdir,"_".join([model,run,region_name,index,yrs])+".nc")
    write_netcdf_file(filepath,data)
    meta.update_data(index,filepath+".png",index,desc)
    return meta

def write_netcdf_file(filepath,ds):
    try:
        ds.to_netcdf(filepath,mode="w")
    except PermissionError as e:
        if os.path.exists(filepath):
            print("  Permission error. Removing existing file",filepath)
            os.remove(filepath)
            print("  Writing new netcdf file",filepath)
            ds.to_netcdf(filepath,mode="w")
        else:
            print("  Permission error. Could not write netcdf file",filepath)
            print("  ",e)
    except Exception as e:
        print("  Error: Could not write netcdf file",filepath)
        print("  ",e)

def write_to_json(outdir,json_filename,json_dict):
    # Open JSON
    JSON = Base(
        outdir, json_filename
    )
    json_structure = json_dict["DIMENSIONS"]["json_structure"]

    JSON.write(
        json_dict,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    return

def verify_years(start_year,end_year,msg="Error: Invalid start or end year"):
    if start_year is None and end_year is None:
        return
    elif start_year is None or end_year is None:
        # If only one of the two is set, exit.
        print(msg)
        print("Exiting")
        sys.exit()

def verify_output_path(metrics_output_path,case_id):
    if metrics_output_path is None:
        metrics_output_path = datetime.datetime.now().strftime("v%Y%m%d")
    if case_id is not None:
        metrics_output_path = metrics_output_path.replace('%(case_id)', case_id)
    if not os.path.exists(metrics_output_path):
        print("\nMetrics output path not found.")
        print("Creating metrics output directory",metrics_output_path)
        try:
            os.makedirs(metrics_output_path)
        except Error as e:
            print("\nError: Could not create metrics output path",metrics_output_path)
            print(e)
            print("Exiting.")
            sys.exit()
    return metrics_output_path

def set_up_realizations(realization):
    find_all_realizations = False
    if realization is None:
        realization = ""
        realizations = [realization]
    elif isinstance(realization, str):
        if realization.lower() in ["all", "*"]:
            find_all_realizations = True
        else:
            realizations = [realization]
    elif isinstance(realization,list):
        realizations = realization
    
    return find_all_realizations,realizations

def generate_land_sea_mask(data,debug=False):
    # generate sftlf if not provided.
    """Commenting out the cdutil version
    latArray = data["lat"]
    lat = cdms2.createAxis(latArray, id="latitude")
    lat.designateLatitude()
    lat.units = "degrees_north"

    lonArray = data["lon"]
    lon = cdms2.createAxis(lonArray, id="longitude")
    lon.designateLongitude()
    lon.units = "degrees_east"

    t_grid_cdms2 = cdms2.grid.TransientRectGrid(lat, lon, 'yx', 'uniform')
    sft = cdutil.generateLandSeaMask(t_grid_cdms2)

    if debug:
        print('sft:', sft)
        print('sft.getAxisList():', sft.getAxisList())

    # add sft to target grid dataset
    t_grid = xr.DataArray(np.array(sft), 
        coords={'lat': latArray,'lon': lonArray}, 
        dims=["lat", "lon"]).to_dataset(name="sftlf")
    t_grid = t_grid * 100
    if debug:
        print('t_grid (after sftlf added):', t_grid)
        t_grid.to_netcdf('target_grid.nc')
    """
    mask = land_sea_mask.generate_land_sea_mask(data, tool="pcmdi", maskname="sftlf")
    mask = mask * 100.
    mask = mask.to_dataset()
    
    return mask