#!/usr/bin/env python
import os

import numpy as np
import xarray as xr
import xcdat as xc
from numdifftools.core import Hessian
from scipy.optimize import minimize
from scipy.stats import genextreme

from pcmdi_metrics.extremes.lib import utilities


def compute_rv_from_file(
    filelist, cov_filepath, cov_name, outdir, return_period, meta, maxes=True
):
    # Go through all files and get return value and standard error by file.
    # Write results to netcdf file.
    if cov_filepath is None:
        desc1 = "Return value from stationary GEV fit for single realization"
        desc2 = (
            "Standard error for return value from stationary fit for single realization"
        )
    else:
        desc = "Return value from nonstationary GEV fit for single realization"
        desc2 = "Standard error for return value from nonstationary fit for single realization"

    for ncfile in filelist:
        ds = xc.open_dataset(ncfile)
        print(ncfile)
        rv, se = get_dataset_rv(ds, cov_filepath, cov_name, return_period, maxes)
        if rv is None:
            print("Error in calculating return value for", ncfile)
            print("Skipping file.")
            continue

        fname = os.path.basename(ncfile).replace(".nc", "")
        rv_file = outdir + "/" + fname + "_return_value.nc"
        utilities.write_netcdf_file(rv_file, rv)
        meta.update_data(
            os.path.basename(rv_file),
            rv_file,
            "return_value",
            "return value for single realization",
        )

        se_file = outdir + "/" + fname + "_standard_error.nc"
        utilities.write_netcdf_file(se_file, se)
        meta.update_data(
            os.path.basename(se_file),
            se_file,
            "standard_error",
            "standard error for return value",
        )

    return meta


def compute_rv_for_model(
    filelist, cov_filepath, cov_varname, ncdir, return_period, meta, maxes=True
):
    # Similar to compute_rv_from_dataset, but to work on multiple realizations
    # from the same model
    # Arguments:
    #   ds: xarray dataset
    #   cov_filepath: string
    #   cov_varname: string
    #   return_period: int
    #   maxes: bool

    nreal = len(filelist)

    ds = xc.open_dataset(filelist[0])
    real_list = [os.path.basename(f).split("_")[1] for f in filelist]
    units = ds.ANN.attrs["units"]

    print("Return value for multiple realizations")
    if cov_filepath is not None:
        nonstationary = True
        print("Nonstationary case")
    else:
        nonstationary = False
        print("Stationary case")

    if nonstationary:
        cov_ds = utilities.load_dataset([cov_filepath])

        if len(cov_ds.time) != len(ds.time):
            start_year = int(ds.time.dt.year[0])
            end_year = int(ds.time.dt.year[-1])
            cov_ds = utilities.slice_dataset(cov_ds, start_year, end_year)

        # Even after slicing, it's possible that time ranges didn't overlap
        if len(cov_ds.time) != len(ds.time):
            print(
                "Covariate timeseries must have same number of years as block extremes dataset."
            )
            print("Skipping return value calculation for files:")
            print(filelist)
            return meta

        # To numpy array
        cov_np = cov_ds[cov_varname].data.squeeze()
        cov_ds.close()

    dec_mode = str(ds.attrs["december_mode"])
    drop_incomplete_djf = ds.attrs["drop_incomplete_djf"]
    if drop_incomplete_djf == "False":
        drop_incomplete_djf = False
    else:
        drop_incomplete_djf = True

    time = len(ds.time)  # This will change for DJF cases
    lat = len(ds.lat)
    lon = len(ds.lon)

    if nonstationary:
        return_value = xr.zeros_like(ds)
    else:
        return_value = xr.zeros_like(ds.isel({"time": 0}))
        return_value = return_value.drop(labels=["time"])
    return_value.drop(labels=["lon_bnds", "lat_bnds", "time_bnds"])
    standard_error = xr.zeros_like(return_value)
    ds.close()

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        print("*****\n", season, "\n*****")
        if season == "DJF" and dec_mode == "DJF" and drop_incomplete_djf:
            # Step first time index to skip all-nan block
            i1 = 1
        else:
            i1 = 0
        if nonstationary:
            cov = cov_np[i1:].squeeze()
        else:
            cov = None
        # Flatten input data and create output arrays
        t = time - i1
        arr = np.ones((t * nreal, lat * lon))
        rep_ind = np.zeros((t * nreal))
        count = 0
        for ncfile in filelist:
            ds = xc.open_dataset(ncfile)
            print(ncfile)
            data = np.reshape(ds[season].data, (time, lat * lon))
            ind1 = count * t
            ind2 = ind1 + t
            count += 1
            arr[ind1:ind2, :] = data[i1:, :]
            rep_ind[ind1:ind2] = count
            ds.close()
        scale_factor = np.abs(np.nanmean(arr))
        arr = arr / scale_factor
        if nonstationary:
            rv_array = np.ones((t, lat * lon)) * np.nan
        else:
            rv_array = np.ones((lat * lon)) * np.nan
        se_array = rv_array.copy()
        # Here's where we're doing the return value calculation
        for j in range(0, lat * lon):
            if np.sum(arr[:, j]) == 0:
                continue
            elif np.isnan(np.sum(arr[:, j])):
                continue
            rv, se = calc_rv_py(
                arr[:, j].squeeze(), cov, return_period, nreplicates=nreal, maxes=maxes
            )
            if rv is not None:
                if nonstationary:
                    rv_array[i1:, j] = np.squeeze(rv * scale_factor)
                    se_array[i1:, j] = np.squeeze(se * scale_factor)
                else:
                    rv_array[j] = rv * scale_factor
                    se_array[j] = se * scale_factor

        # reshape array to match desired dimensions and add to Dataset
        # Also reorder dimensions for nonstationary case
        if nonstationary:
            rv_array = np.reshape(rv_array, (time, lat, lon))
            se_array = np.reshape(se_array, (time, lat, lon))
            return_value[season] = (("time", "lat", "lon"), rv_array)
            standard_error[season] = (("time", "lat", "lon"), se_array)
        else:
            rv_array = np.reshape(rv_array, (lat, lon))
            se_array = np.reshape(se_array, (lat, lon))
            return_value[season] = (("lat", "lon"), rv_array)
            standard_error[season] = (("lat", "lon"), se_array)

    return_value.attrs["description"] = "{0}-year return value".format(return_period)
    standard_error.attrs["description"] = "standard error"
    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        return_value[season].attrs["units"] = units
        standard_error[season].attrs["units"] = units

    # Update attributes
    return_value.attrs["description"] = "{0}-year return value".format(return_period)
    standard_error.attrs["description"] = "standard error"
    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        return_value[season].attrs["units"] = units
        standard_error[season].attrs["units"] = units

    return_value = return_value.bounds.add_missing_bounds()
    standard_error = standard_error.bounds.add_missing_bounds()

    # Set descriptions for metadata
    if nonstationary:
        desc1 = "Return value from stationary GEV fit for multiple realizations"
        desc2 = "Standard error for return value from stationary fit for multiple realizations"
    else:
        desc1 = "Return value from nonstationary GEV fit for multiple realizations"
        desc2 = "Standard error for return value from nonstationary fit for multiple realizations"

    fname = os.path.basename(filelist[0])
    real = fname.split("_")[1]
    fname = fname.replace(real + "_", "").replace(".nc", "")
    outfile = os.path.join(ncdir, fname + "_return_value.nc")
    utilities.write_netcdf_file(outfile, return_value)
    meta.update_data(os.path.basename(outfile), outfile, "return_value", desc1)

    outfile = os.path.join(ncdir, fname + "_standard_error.nc")
    utilities.write_netcdf_file(outfile, standard_error)
    meta.update_data(os.path.basename(outfile), outfile, "standard_error", desc2)

    return meta


def get_dataset_rv(ds, cov_filepath, cov_varname, return_period=20, maxes=True):
    # Get the return value for a single model & realization
    # Set cov_filepath and cov_varname to None for stationary GEV.
    # Arguments:
    #   ds: xarray dataset
    #   cov_filepath: string
    #   cov_varname: string
    #   return_period: int
    #   maxes: bool

    dec_mode = str(ds.attrs["december_mode"])
    drop_incomplete_djf = ds.attrs["drop_incomplete_djf"]
    if drop_incomplete_djf == "False":
        drop_incomplete_djf = False
    else:
        drop_incomplete_djf = True
    units = ds.ANN.attrs["units"]

    print(
        "Return value for single realization",
    )
    if cov_filepath is not None:
        nonstationary = True
        print("Nonstationary case")
    else:
        nonstationary = False
        print("Stationary case")

    if nonstationary:
        cov_ds = utilities.load_dataset([cov_filepath])
        if len(cov_ds.time) != len(ds.time):
            start_year = int(ds.time.dt.year[0])
            end_year = int(ds.time.dt.year[-1])
            cov_ds = utilities.slice_dataset(cov_ds, start_year, end_year)

        # Even after slicing, it's possible that time ranges didn't overlap
        if len(cov_ds.time) != len(ds.time):
            print(
                "Covariate timeseries must have same number of years as block extremes dataset."
            )
            print("Skipping return value calculation.")
            return None, None

        # To numpy array
        cov_ds = cov_ds[cov_varname].data.squeeze()

    lat = len(ds["lat"])
    lon = len(ds["lon"])
    time = len(ds["time"])
    dim2 = lat * lon
    rep_ind = np.ones((time))

    if nonstationary:
        return_value = xr.zeros_like(ds)
    else:
        return_value = xr.zeros_like(ds.isel({"time": 0}))
        return_value = return_value.drop(labels=["time"])
    return_value.drop(labels=["lon_bnds", "lat_bnds", "time_bnds"])
    standard_error = return_value.copy()

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        data = ds[season].data
        # Scale x to be around magnitude 1
        scale_factor = np.abs(np.nanmean(data))
        data = data / scale_factor

        if season == "DJF" and dec_mode == "DJF" and drop_incomplete_djf:
            # Step first time index to skip all-nan block
            i1 = 1
        else:
            i1 = 0

        data = np.reshape(data, (time, dim2))
        if nonstationary:
            rv_array = np.ones(np.shape(data)) * np.nan
        else:
            rv_array = np.ones((dim2)) * np.nan
        se_array = rv_array.copy()
        success = np.zeros((dim2))

        # Turn nans to zeros
        data = np.nan_to_num(data)

        if nonstationary:
            cov_slice = cov_ds[i1:]
        else:
            cov_slice = None

        for j in range(0, dim2):
            b = data[i1:, j]
            if np.sum(b) == 0:
                continue
            elif np.isnan(np.sum(b)):
                continue
            rv_tmp, se_tmp = calc_rv_py(
                data[i1:, j].squeeze(), cov_slice, return_period, 1, maxes
            )
            if rv_tmp is not None:
                if nonstationary:
                    rv_array[i1:, j] = rv_tmp * scale_factor
                    se_array[i1:, j] = se_tmp * scale_factor
                else:
                    rv_array[j] = rv_tmp * scale_factor
                    se_array[j] = se_tmp * scale_factor

        if nonstationary:
            rv_array = np.reshape(rv_array, (time, lat, lon))
            se_array = np.reshape(se_array, (time, lat, lon))
            return_value[season] = (("time", "lat", "lon"), rv_array)
            standard_error[season] = (("time", "lat", "lon"), se_array)

        else:
            rv_array = np.reshape(rv_array, (lat, lon))
            se_array = np.reshape(se_array, (lat, lon))
            return_value[season] = (("lat", "lon"), rv_array)
            standard_error[season] = (("lat", "lon"), se_array)

    return_value.attrs["description"] = "{0}-year return value".format(return_period)
    standard_error.attrs["description"] = "standard error"
    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        return_value[season].attrs["units"] = units
        standard_error[season].attrs["units"] = units

    return_value = return_value.bounds.add_missing_bounds()
    standard_error = standard_error.bounds.add_missing_bounds()

    return return_value, standard_error


def calc_rv_py(x, covariate, return_period, nreplicates=1, maxes=True):
    # An implementation of the return value and standard error
    # that does not use climextRemes.
    # Arguments:
    #   ds: numpy array
    #   covariate: numpy array
    #   nreplicates: int
    #   return_period: int
    #   maxes: bool

    if maxes:
        mins = False
    else:
        mins = True
        x = -1 * x

    nonstationary = True
    if covariate is None:
        nonstationary = False

    # Need to tile covariate if multiple replicates
    if nonstationary and nreplicates > 1:
        covariate_tiled = np.tile(covariate, nreplicates)
    elif nonstationary:
        covariate_tiled = covariate

    # Use the stationary gev to make initial parameter guess
    fit = genextreme.fit(x)
    shape, loc, scale = fit

    def ll(params):
        # Negative Log liklihood function to minimize for GEV

        n = len(x)
        if nonstationary:
            beta1 = params[0]
            beta2 = params[1]
            scale = params[2]
            shape = params[3]
            location = beta1 + beta2 * covariate_tiled
        else:
            location = params[0]
            scale = params[1]
            shape = params[2]

        if np.allclose(np.array(shape), np.array(0)):
            shape = 0
            y = (x - location) / scale
            result = np.sum(n * np.log(scale) + y + np.exp(-y))
        else:
            # This value must be > 0, Coles 2001
            y = 1 + shape * (x - location) / scale
            check = [True for item in y if item <= 0]
            if len(check) > 0:
                return 1e10
            result = np.sum(
                np.log(scale) + y ** (-1 / shape) + np.log(y) * (1 / shape + 1)
            )

        return result

    # Get GEV parameters
    if nonstationary:
        ll_min = minimize(ll, (loc, 0, scale, shape), tol=1e-7, method="nelder-mead")
    else:
        ll_min = minimize(ll, (loc, scale, shape), tol=1e-7, method="nelder-mead")

    params = ll_min["x"]
    success = ll_min["success"]

    if nonstationary:
        scale = params[2]
        shape = params[3]
    else:
        location = params[0]
        scale = params[1]
        shape = params[2]
        covariate = [1]  # set cov size to 1

    # Calculate return value
    return_value = np.ones((len(covariate), 1)) * np.nan
    for time in range(0, len(covariate)):
        if nonstationary:
            location = params[0] + params[1] * covariate[time]
        rv = genextreme.isf(1 / return_period, shape, location, scale)
        return_value[time] = np.squeeze(np.where(success == 1, rv, np.nan))
    if mins:
        return_value = -1 * return_value

    # Calculate standard error
    try:
        hs = Hessian(ll, step=None, method="central", order=None)
        vcov = np.linalg.inv(hs(ll_min.x))
        var_theta = np.diag(vcov)
        if (var_theta < 0).any():
            # Try again with a different method
            hs = Hessian(ll, step=None, method="complex", order=None)
            vcov = np.linalg.inv(hs(ll_min.x))
            var_theta = np.diag(vcov)
            if (var_theta < 0).any():
                # Negative values on diagonal not good
                raise RuntimeError("Negative value in diagonal of Hessian.")

        if nonstationary:
            cov = covariate
            y = -np.log(1 - 1 / return_period)
            if shape == 0:
                grad = np.array([1, -np.log(y)])
            else:
                db1 = np.ones(len(cov))
                db2 = cov
                dsh = np.ones(len(cov)) * (-1 / shape) * (1 - y ** (-shape))
                dsc = np.ones(len(cov)) * scale * (shape**-2) * (1 - y**-shape) - (
                    scale / shape * (y**-shape) * np.log(y)
                )
                grad = np.array([db1, db2, dsh, dsc])
        else:
            y = -np.log(1 - 1 / return_period)
            if shape == 0:
                grad = np.array([1, -np.log(y)])
            else:
                db1 = 1
                dsh = (-1 / shape) * (1 - y ** (-shape))
                dsc = scale * (shape**-2) * (1 - y**-shape) - (
                    scale / shape * (y**-shape) * np.log(y)
                )
                grad = np.array([db1, dsh, dsc])
                grad = np.expand_dims(grad, axis=1)

        A = np.matmul(np.transpose(grad), vcov)
        B = np.matmul(A, grad)
        se = np.sqrt(np.diag(B))
    except Exception as e:
        se = np.ones(np.shape(return_value)) * np.nan

    return return_value.squeeze(), se.squeeze()


def calc_rv_interpolated(tseries, return_period, average=False):
    # A function to get a stationary return period
    # interpolated from the block maximum data
    # The "average" parameter works best for the 100
    # year timeseries.
    if return_period < 1:
        return None
    nyrs = len(tseries)
    tsorted = np.sort(tseries)[::-1]
    if return_period > nyrs:
        print("Return period cannot be greater than length of timeseries.")
        return None
    rplist = [nyrs / n for n in range(1, nyrs + 1)]
    count = 0
    for item in rplist:
        try:
            if item > return_period:
                continue
            if item < return_period:
                # linearly interpolate between measurements
                # to estimate return value
                rp_upper = rplist[count - 1]
                rp_lower = rplist[count]

                def f(x):
                    m = (tsorted[count - 1] - tsorted[count]) / (rp_upper - rp_lower)
                    b = tsorted[count] - (m * rp_lower)
                    return m * x + b

                rv = f(return_period)
                break
            elif item == return_period:
                if average:
                    rv = (tsorted[count] + tsorted[count - 1]) / 2.0
                else:
                    rv = tsorted[count]
                break
        except:  # any issues, set to NaN
            rv = np.nan
            break
        count += 1
    return rv, np.nan


def calc_rv_climex(data, covariate, return_period, nreplicates=1, maxes=True):
    # Use climextRemes to get the return value and standard error
    # This function exists for easy comparison with the pure Python
    # implementation in calc_rv_py. However, generating the return
    # value this way is not supported as part of the PMP.
    # Returns the return value and standard error.
    # Arguments:
    #   ds: numpy array
    #   covariate: numpy array
    #   nreplicates: int
    #   return_period: int
    #   maxes: bool
    return_value = None
    standard_error = None
    if covariate is None:  # Stationary
        tmp = climextremes.fit_gev(
            data.squeeze(),
            returnPeriod=return_period,
            nReplicates=nreplicates,
            maxes=maxes,
        )
    else:  # Nonstationary
        if len(covariate) < len(data):
            covariate_tiled = np.tile(covariate, nreplicates)
            xnew = covariate
        else:
            covariate_tiled = covariate
            xlen = len(covariate) / nreplicates
            xnew = covariate[0:xlen]
        tmp = climextremes.fit_gev(
            data.squeeze(),
            covariate_tiled,
            returnPeriod=return_period,
            nReplicates=nreplicates,
            locationFun=1,
            maxes=maxes,
            xNew=xnew,
        )
    success = tmp["info"]["failure"][0]
    if success == 0:
        return_value = tmp["returnValue"]
        standard_error = tmp["se_returnValue"]
    return return_value, standard_error
