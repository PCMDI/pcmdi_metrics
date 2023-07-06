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

from pcmdi_metrics.extremes.lib import utilities

def compute_rv_from_file(filelist,cov_filepath,cov_name,outdir,return_period,maxes=True):
    # Go through all files and get return value and standard error by file.
    # Write results to netcdf file.
    for ncfile in filelist:
        print(ncfile)
        ds = xc.open_dataset(ncfile)
        rv,se = get_dataset_rv(ds,cov_filepath,cov_name,return_period,maxes)
        if rv is None:
            print("Error in calculating return value for",ncfile)
            sys.exit()
        fname = os.path.basename(ncfile).replace(".nc","")
        utilities.write_netcdf_file(outdir+"/"+fname+"_return_value.nc",rv)
        utilities.write_netcdf_file(outdir+"/"+fname+"_standard_error.nc",se)


def compute_rv_for_model(filelist,cov_filepath,cov_varname,return_period,maxes=True):
    # Similar to compute_rv_from_file, but to work on multiple realizations
    # from the same model
    nreal = len(filelist)

    ds = xc.open_dataset(filelist[0])
    cov_ds = utilities.load_dataset([cov_filepath])

    if len(cov_ds.time) != len(ds.time):
        start_year = int(ds.time.dt.year[0])
        end_year = int(ds.time.dt.year[-1])
        cov_ds = utilities.slice_dataset(cov_ds,start_year,end_year)

    # Even after slicing, it's possible that time ranges didn't overlap
    if len(cov_ds.time) != len(ds.time):
        print("Covariate timeseries must have same number of years as block extremes dataset.")
        print("Skipping return value calculation.")
        return None,None

    # To numpy array
    cov_np = cov_ds[cov_varname].data.squeeze()
    cov_ds.close()
    cov_np = np.log(cov_np) # TODO - log should probably be optional

    #cov_arr = np.zeros(len(cov_np)*nreal)
    #cov_djf = np.zeros((len(cov_np)-1)*nreal)
    #for n in range(1,nreal):
    #    ind1=n*len(cov_np)
    #    ind2=(n+1)*len(cov_np)
    #    cov_arr[ind1:ind2] = cov_np
        
    #    ind1=n*(len(cov_np)-1)
    #    ind2=(n+1)*(len(cov_np)-1)
    #    cov_djf[ind1:ind2] = cov_np[1:]


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
            cov = cov_np[1:]
        else:
            i1 = 0
            cov = cov_np
        cov_tile = np.tile(cov,nreal)
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
            print(arr[:,j].squeeze())
            print(cov.squeeze())
            print(nreal)
            rv,se = calc_rv(arr[:,j].squeeze(),cov_tile.squeeze(),return_period,nreplicates=nreal,maxes=maxes)
            if rv is not None:
                rv_array[:,j] = rv*scale_factor
                se_array[:,j] = se*scale_factor
        ds.close()

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


def get_dataset_rv(ds,cov_filepath,cov_varname,return_period=20,maxes=True):
    dec_mode = str(ds.attrs["december_mode"])
    drop_incomplete_djf = bool(ds.attrs["drop_incomplete_djf"])

    cov_ds = utilities.load_dataset([cov_filepath])
    if len(cov_ds.time) != len(ds.time):
        start_year = int(ds.time.dt.year[0])
        end_year = int(ds.time.dt.year[-1])
        cov_ds = utilities.slice_dataset(cov_ds,start_year,end_year)

    # Even after slicing, it's possible that time ranges didn't overlap
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
    return_value.drop(labels=["lon_bnds","lat_bnds","time_bnds"])
    standard_error = return_value.copy()

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
        success = np.zeros((dim2))

        # Turn nans to zeros
        data = np.nan_to_num(data)

        for j in range(0,dim2):
            b=data[i1:,j]
            if np.sum(b) == 0:
                continue
            rv_tmp,se_tmp = calc_rv(data[i1:,j].squeeze(),cov_ds[i1:],return_period,1,maxes)
            if rv_tmp is not None:
                rv_array[i1:,j] = rv_tmp*scale_factor
                se_array[i1:,j] = se_tmp*scale_factor
                success[j] = 1

        rv_array = np.reshape(rv_array,(time,lat,lon))
        se_array = np.reshape(se_array,(time,lat,lon))
        success = np.reshape(success,(lat,lon))
        return_value[season] = (("time","lat","lon"),rv_array)
        return_value[season+"_success"] = (("lat","lon"),success)
        standard_error[season] = (("time","lat","lon"),se_array)
        standard_error[season+"_success"] = (("lat","lon"),success)

    return_value = return_value.bounds.add_missing_bounds() 
    standard_error = standard_error.bounds.add_missing_bounds()

    return return_value,standard_error

def calc_rv(data,covariate,return_period,nreplicates=1,maxes=True):
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
        maxes=maxes,
        xNew=covariate)
    success = tmp['info']['failure'][0]
    if success == 0:
        return_value = tmp['returnValue']
        standard_error = tmp['se_returnValue']
    return return_value,standard_error