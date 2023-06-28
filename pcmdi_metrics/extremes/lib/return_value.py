#!/usr/bin/env python
import cftime
import datetime
import numpy as np
import os
import xarray as xr
import xcdat as xc
import climextremes
import glob
import sys

from lib import utilities

def compute_rv_from_file(ncdir,cov_filepath="co2_annual_1950-2000.nc"):
    # Go through all files and get rv
    # Write rv and se to netcdf
    for ncfile in glob.glob(ncdir+"/*"):
        print(ncfile)
        ds = xc.open_dataset(ncfile)
        rv,se = get_dataset_rv(ds,cov_filepath,[1950,1999],"mole_fraction_of_carbon_dioxide_in_air")
        if rv is None:
            continue
        fname = os.path.basename(ncfile).replace(".nc","")
        utilities.write_netcdf_file(ncdir+"/"+fname+"_return_value.nc",rv)
        utilities.write_netcdf_file(ncdir+"/"+fname+"_standard_error.nc",se)

def compute_rv_for_model(filelist,return_period=20,cov_filepath="co2_annual_1950-2000.nc",cov_varname="mole_fraction_of_carbon_dioxide_in_air"):
    # Similar to compute_rv_from_file, but to work on multiple realizations
    # from the same model
    nreal = len(filelist)

    cov_ds = utilities.load_dataset([cov_filepath])
    #cov_ds = utilties.slice_ds(cov_ds,start_year,end_year)

    # To numpy array
    cov_ds = cov_ds[cov_varname].data.squeeze()
    cov_ds = np.log(cov_ds) # TODO - log should probably be optional
    cov_arr = np.zeros(len(cov_ds)*nreal)
    cov_djf = np.zeros((len(cov_ds)-1)*nreal)
    for n in range(1,nreal):
        ind1=n*len(cov_ds)
        ind2=(n+1)*len(cov_ds)
        cov_arr[ind1:ind2] = cov_ds
        
        ind1=n*(len(cov_ds)-1)
        ind2=(n+1)*(len(cov_ds)-1)
        cov_djf[ind1:ind2] = cov_ds[1:]

    ds = xc.open_dataset(filelist[0])
    dec_mode = str(ds.attrs["december_mode"])
    drop_incomplete_djf = bool(ds.attrs["drop_incomplete_djf"])

    time = len(ds.time) # This will change for DJF cases
    lat = len(ds.lat)
    lon = len(ds.lon)
    return_value = xr.zeros_like(ds).expand_dims(dim={"real": nreal}).assign_coords({"real": range(0,nreal)})
    return_value = return_value[["real","time", "lat", "lon"]]
    standard_error = xr.zeros_like(return_value)

    for season in ["DJF"]:
        if season == "DJF" and dec_mode == "DJF" and drop_incomplete_djf:
            # Step first time index to skip all-nan block
            i1 = 1
            cov = cov_djf
        else:
            i1 = 0
            cov = cov_arr
        t = time-i1
        arr = np.ones((t*nreal,lat*lon))
        rep_ind = np.zeros((t*nreal))
        count=0
        for ncfile in filelist:
            ds = xc.open_dataset(ncfile)
            data = np.reshape(ds[season].data,(time,lat*lon))
            ind1 = count*t
            ind2 = ind1+t
            count+=1
            arr[ind1:ind2,:] = data[i1:,:]
            rep_ind[ind1:ind2] = count
        scale_factor = np.abs(np.nanmean(arr))
        arr = arr / scale_factor
        rv_array = np.ones((t*nreal,lat*lon)) * np.nan
        se_array = rv_array.copy()
        for j in range(0,lat*lon):
            rv,se = calc_rv(arr[:,j].squeeze(),cov.squeeze(),return_period,nreplicates=nreal)
            if rv is not None:
                rv_array[:,j] = rv*scale_factor
                se_array[:,j] = se*scale_factor

        rv_array = np.reshape(rv_array,(nreal,t,lat,lon))
        se_array = np.reshape(se_array,(nreal,t,lat,lon))
        if season == "DJF" and dec_mode == "DJF" and drop_incomplete_djf:
            nans = np.ones((nreal,1,lat,lon))*np.nan
            rv_array = np.concatenate((nans,rv_array),axis=1)
            se_array = np.concatenate((nans,se_array),axis=1)
        return_value[season] = (("real","time", "lat", "lon"),rv_array)
        standard_error[season] = (("real","time","lat","lon"),se_array)
    
    return_value = return_value[["time", "real", "lat", "lon"]]
    standard_error = standard_error[["time", "real", "lat", "lon"]]

    fname = "return_value_test.nc"
    utilities.write_netcdf_file(fname,return_value)
    fname = "standard_error_test.nc"
    utilities.write_netcdf_file(fname,standard_error)

    return return_value,standard_error


def get_dataset_rv(ds,cov_filepath,years,cov_varname,return_period=20):
    dec_mode = str(ds.attrs["december_mode"])
    drop_incomplete_djf = bool(ds.attrs["drop_incomplete_djf"])

    cov_ds = utilities.load_dataset([cov_filepath])
    #cov_ds = utilties.slice_ds(cov_ds,start_year,end_year)

    if len(cov_ds.time) != len(ds.time):
        print("Covariate timeseries must have same number of years as block extremes dataset.")
        print("Skipping return value calculation.")
        return None,None

    # To numpy array
    cov_ds = cov_ds[cov_varname].data.squeeze()
    cov_ds = np.log(cov_ds) # TODO - log should probably be optional

    lat = len(ds["lat"])
    lon = len(ds["lon"])
    time = len(ds["time"])
    dim2 = lat*lon
    # todo: use all reaizations
    rep_ind = np.ones((time))

    return_value = xr.zeros_like(ds)
    standard_error = xr.zeros_like(ds)

    for season in ["ANN","DJF","MAM","JJA","SON"]:
        print("\n-----",season,"-----\n")
        data = ds[season].data
        # Scale x to be around magnitude 1
        scale_factor = np.abs(np.nanmean(data))
        data = data / scale_factor

        if season == "DJF" and dec_mode == "DJF" and drop_incomplete_djf:
            # Step first time index to skip all-nan block
            i1 = 1
        else:
            i1 = 0

        data = np.reshape(data,(time,dim2))
        rv_array = np.ones(np.shape(data)) * np.nan
        se_array = rv_array.copy()

        # Turn nans to zeros
        data = np.nan_to_num(data)

        # TODO: depending on dec mode, slice off certain years from dec case
        for j in range(0,dim2):
            b=data[i1:,j]
            if np.sum(b) == 0:
                continue
            return_value,std_err = calc_rv(data[i1:,j].squeeze(),cov_ds[i1:],return_period,1)
            if return_value is not None:
                rv_array[i1:,j] = return_value*scale_factor
                se_array[i1:,j] = std_err*scale_factor

        rv_array = np.reshape(rv_array,(time,lat,lon))
        se_array = np.reshape(se_array,(time,lat,lon))
        return_value[season] = (("time", "lat", "lon"),rv_array)
        standard_error[season] = (("time","lat","lon"),se_array)

    return return_value,standard_error

def calc_rv(data,covariate,return_period,nreplicates=1):
    # This function contains the code that does the actual return value calculation.
    # Changes to the return value algorithm can be made here.
    # Returns the return value and standard error.
    return_value = None
    standard_error = None
    tmp = climextremes.fit_gev(
        data.squeeze(),
        covariate,
        returnPeriod=return_period,
        nReplicates=nreplicates,
        locationFun = 1,
        xNew=covariate)
    success = tmp['info']['failure'][0]
    if success == 0:
        return_value = tmp['returnValue']
        standard_error = tmp['se_returnValue']
    return return_value,standard_error