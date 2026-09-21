#!/usr/bin/env python
import os

import numpy as np
import xarray as xr
import xcdat as xc
from joblib import Parallel, delayed
from numdifftools.core import Hessian
from scipy.optimize import minimize
from scipy.stats import genextreme

from pcmdi_metrics.extremes.lib import utilities

SEASONS = ["ANN", "DJF", "MAM", "JJA", "SON"]


def compute_rv_from_file(
    filelist,
    cov_filepath,
    cov_name,
    outdir,
    return_period,
    meta,
    maxes=True,
    norm=0,
):
    # Go through all files and get return value and standard error by file.
    # Write results to netcdf file.
    if cov_filepath is None:
        desc1 = "Return value from stationary GEV fit for single realization"
        desc2 = (
            "Standard error for return value from stationary fit for single realization"
        )
    else:
        desc1 = "Return value from nonstationary GEV fit for single realization"
        desc2 = "Standard error for return value from nonstationary fit for single realization"

    for ncfile in filelist:
        ds = xc.open_dataset(ncfile)
        print(ncfile)
        rv, se = get_dataset_rv(
            ds, cov_filepath, cov_name, return_period, maxes, norm=norm
        )
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
            desc1,
        )

        se_file = outdir + "/" + fname + "_standard_error.nc"
        utilities.write_netcdf_file(se_file, se)
        meta.update_data(
            os.path.basename(se_file),
            se_file,
            "standard_error",
            desc2,
        )

    return meta


def compute_rv_for_model(
    filelist,
    cov_filepath,
    cov_varname,
    ncdir,
    return_period,
    meta,
    maxes=True,
    n_jobs=8,  # Conservative number of cores
    norm=0,
):
    # Similar to compute_rv_from_dataset, but to work on multiple realizations
    # from the same model
    # Arguments:
    #   ds: xarray dataset
    #   cov_filepath: string
    #   cov_varname: string
    #   return_period: int
    #   maxes: bool
    #   norm: int - 0 (subtract mean, divide by std), 1 (divide by mean), 2 (raw)

    slurm_cpus = os.environ.get("SLURM_CPUS_PER_TASK")

    if (
        slurm_cpus is not None
    ):  # If we are in a SLURM environment, default to SLURM setting
        n_jobs = int(slurm_cpus)

    nreal = len(filelist)

    ds = xc.open_dataset(filelist[0])
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
        return_value = return_value.drop_vars(["time"], errors="ignore")
    return_value = return_value.drop_vars(
        ["lon_bnds", "lat_bnds", "time_bnds"], errors="ignore"
    )
    standard_error = xr.zeros_like(return_value)
    ds.close()

    for season in SEASONS:
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
        if nonstationary:
            rv_array = np.ones((t, lat * lon)) * np.nan
        else:
            rv_array = np.ones((lat * lon)) * np.nan
        se_array = rv_array.copy()

        # Pre-compute normalization factors for each grid cell
        centers = np.full(lat * lon, np.nan)
        spreads = np.full(lat * lon, np.nan)
        for j in range(lat * lon):
            data_valid = arr[:, j][np.isfinite(arr[:, j])]
            if data_valid.size > 0 and not np.all(data_valid == data_valid[0]):
                centers[j] = np.mean(data_valid)
                spreads[j] = np.std(data_valid, ddof=1)

        # Here's where we're doing the return value calculation with joblib
        def calc_normalized_rv(j):
            data = arr[:, j].squeeze()
            if np.sum(data) == 0 or np.isnan(np.sum(data)):
                return None, None

            # Apply normalization
            data_valid = data[np.isfinite(data)]
            if data_valid.size == 0 or np.all(data_valid == data_valid[0]):
                return None, None

            center = centers[j]
            spread = spreads[j]

            if norm == 0:
                data_norm = (data - center) / spread
            elif norm == 1:
                data_norm = data / center
            else:  # norm == 2
                data_norm = data

            # Calculate return value with normalized data
            rv, se = calc_rv_py(
                data_norm, cov, return_period, nreplicates=nreal, maxes=maxes
            )

            if rv is None:
                return None, None

            # Denormalize results
            if norm == 0:
                rv = center + spread * np.asarray(rv)
                se = spread * np.asarray(se)
            elif norm == 1:
                rv = center * np.asarray(rv)
                se = abs(center) * np.asarray(se)
            else:  # norm == 2
                rv = np.asarray(rv)
                se = np.asarray(se)

            return rv, se

        results = Parallel(n_jobs=n_jobs, prefer="processes")(
            delayed(calc_normalized_rv)(j) for j in range(lat * lon)
        )
        rv_results, se_results = zip(*results)

        # Unpack results
        for j in range(lat * lon):
            rv, se = rv_results[j], se_results[j]
            if rv is not None:
                if nonstationary:
                    rv_array[i1:, j] = np.squeeze(rv)
                    se_array[i1:, j] = np.squeeze(se)
                else:
                    rv_array[j] = rv
                    se_array[j] = se

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
    for season in SEASONS:
        return_value[season].attrs["units"] = units
        standard_error[season].attrs["units"] = units

    # Update attributes
    return_value.attrs["description"] = "{0}-year return value".format(return_period)
    standard_error.attrs["description"] = "standard error"
    for season in SEASONS:
        return_value[season].attrs["units"] = units
        standard_error[season].attrs["units"] = units

    return_value = return_value.bounds.add_missing_bounds()
    standard_error = standard_error.bounds.add_missing_bounds()

    # Set descriptions for metadata
    if nonstationary:
        desc1 = "Return value from nonstationary GEV fit for multiple realizations"
        desc2 = "Standard error for return value from nonstationary fit for multiple realizations"
    else:
        desc1 = "Return value from stationary GEV fit for multiple realizations"
        desc2 = "Standard error for return value from stationary fit for multiple realizations"

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


def fit_cell(data, covariate, return_period, maxes, norm=0):
    """Fit a stationary or nonstationary GEV at one grid cell."""

    if norm not in [0, 1, 2]:
        raise ValueError("Normalization Option must be 0, 1, or 2")

    data = np.asarray(data, dtype=float)

    nonstationary = covariate is not None

    if nonstationary:
        covariate = np.asarray(covariate, dtype=float)
        valid = np.isfinite(data) & np.isfinite(covariate)
        empty_result = (
            np.full(data.shape, np.nan),
            np.full(data.shape, np.nan),
        )
    else:
        valid = np.isfinite(data)
        empty_result = (np.nan, np.nan)

    data_valid = data[valid]

    if data_valid.size == 0:
        return empty_result

    if np.all(data_valid == data_valid[0]):
        return empty_result

    center = np.mean(data_valid)
    spread = np.std(data_valid, ddof=1)

    # Option 1: Subtract mean divide by STD
    if norm == 0:
        data_norm = (data_valid - center) / spread
    # Option 2: Divide by mean (original)
    elif norm == 1:
        data_norm = data_valid / center
    # Option 3: Raw
    else:
        data_norm = data_valid

    covariate_valid = covariate[valid] if nonstationary else None

    try:
        rv, se = calc_rv_py(
            x=data_norm,
            covariate=covariate_valid,
            return_period=return_period,
            nreplicates=1,
            maxes=maxes,
        )
    except Exception:
        return empty_result

    if rv is None:
        return empty_result

    if norm == 0:
        rv = center + spread * np.asarray(rv)
        se = spread * np.asarray(se)

    elif norm == 1:
        rv = center * np.asarray(rv)
        se = abs(center) * np.asarray(se)

    else:
        rv = np.asarray(rv)
        se = np.asarray(se)

    if not nonstationary:
        return rv, se

    rv_output = np.full(data.shape, np.nan)
    se_output = np.full(data.shape, np.nan)

    rv_output[valid] = rv
    se_output[valid] = se

    return rv_output, se_output


def get_dataset_rv(
    ds,
    cov_filepath,
    cov_varname,
    return_period=20,
    maxes=True,
    n_jobs=8,  # Conservative number of cores
    norm=0,
):
    # Get the return value for a single model & realization
    # Set cov_filepath and cov_varname to None for stationary GEV.
    # Arguments:
    #   ds: xarray dataset
    #   cov_filepath: string
    #   cov_varname: string
    #   return_period: int
    #   maxes: bool

    slurm_cpus = os.environ.get("SLURM_CPUS_PER_TASK")

    if (
        slurm_cpus is not None
    ):  # If we are in a SLURM environment, default to SLURM setting
        n_jobs = int(slurm_cpus)

    dec_mode = str(ds.attrs["december_mode"])
    drop_incomplete_djf = ds.attrs["drop_incomplete_djf"] != "False"
    units = ds.ANN.attrs["units"]

    print(
        "Return value for single realization",
    )

    nonstationary = cov_filepath is not None

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

    n_lat = len(ds["lat"])
    n_lon = len(ds["lon"])
    n_time = len(ds["time"])
    n_cells = n_lat * n_lon

    if nonstationary:
        return_value = xr.zeros_like(ds)
    else:
        return_value = xr.zeros_like(ds.isel({"time": 0}))
        return_value = return_value.drop_vars(["time"], errors="ignore")
    return_value = return_value.drop_vars(
        ["lon_bnds", "lat_bnds", "time_bnds"], errors="ignore"
    )
    standard_error = return_value.copy()
    # type_code = return_value.copy()

    for season in SEASONS:
        data = ds[season].data

        # Scale factor being the mean caused instability in the initial GEV fit, looking to normalize on a per grid-cell basis next.

        if season == "DJF" and dec_mode == "DJF" and drop_incomplete_djf:
            # Step first time index to skip all-nan block
            t_ind = 1
        else:
            t_ind = 0

        data = np.reshape(data, (n_time, n_cells))
        if nonstationary:
            rv_array = np.ones(np.shape(data)) * np.nan
        else:
            rv_array = np.ones((n_cells)) * np.nan
        se_array = rv_array.copy()

        if nonstationary:
            cov_slice = cov_ds[t_ind:]
        else:
            cov_slice = None

        results = Parallel(n_jobs=n_jobs, prefer="processes")(
            delayed(fit_cell)(
                data[t_ind:, j], cov_slice, return_period, maxes, norm=norm
            )
            for j in range(n_cells)
        )
        rv_results, se_results = zip(*results)

        if nonstationary:
            # Each result has shape (time - t_ind,)
            rv_fit = np.stack(rv_results, axis=1)
            se_fit = np.stack(se_results, axis=1)

            # Keep the skipped first DJF index as NaN
            rv_array = np.full((n_time, n_cells), np.nan)
            se_array = np.full((n_time, n_cells), np.nan)

            rv_array[t_ind:, :] = rv_fit
            se_array[t_ind:, :] = se_fit

            rv_array = rv_array.reshape(n_time, n_lat, n_lon)
            se_array = se_array.reshape(n_time, n_lat, n_lon)

            return_value[season] = (
                ("time", "lat", "lon"),
                rv_array,
            )
            standard_error[season] = (
                ("time", "lat", "lon"),
                se_array,
            )

        else:
            # Each result is a scalar
            rv_array = np.asarray(rv_results).reshape(n_lat, n_lon)
            se_array = np.asarray(se_results).reshape(n_lat, n_lon)

            return_value[season] = (
                ("lat", "lon"),
                rv_array,
            )
            standard_error[season] = (
                ("lat", "lon"),
                se_array,
            )

    return_value.attrs["description"] = "{0}-year return value".format(return_period)
    standard_error.attrs["description"] = "standard error"
    for season in SEASONS:
        return_value[season].attrs["units"] = units
        standard_error[season].attrs["units"] = units

    return_value = return_value.bounds.add_missing_bounds(axes=["X", "Y"])
    standard_error = standard_error.bounds.add_missing_bounds(axes=["X", "Y"])

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
    x = np.asarray(x, dtype=float).squeeze()  # Ensure numpy array
    x = x[np.isfinite(x)]

    # if len(x) < 5:  # Minimum periods = 5
    #     return np.nan, np.nan

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
    scipy_shape, loc, scale = genextreme.fit(x)
    shape = -scipy_shape  # Convention

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

        if not np.isfinite(scale) or scale <= 0:
            return 1e10

        if abs(shape) < 1e-6:
            shape = 0
            y = (x - location) / scale
            # result = np.sum(n * np.log(scale) + y + np.exp(-y)) # Incorrect (scales with n^2 instead of n)
            result = n * np.log(scale) + np.sum(
                y + np.exp(-y)
            )  # Corrected summation implementation
        else:
            # This value must be > 0, Coles 2001
            y = 1 + shape * (x - location) / scale
            if np.any(y <= 0):
                return 1e10

            result = np.sum(
                np.log(scale) + y ** (-1 / shape) + np.log(y) * (1 / shape + 1)
            )

        return result

    # Get GEV parameters

    optimizer_options = {
        "xatol": 1e-4,  # parameter absolute tolerance
        "fatol": 1e-4,  # function absolute tolerance
        "maxiter": 5000,  # max NM calls
        "maxfev": 10000,  # max LL func calls
    }

    if nonstationary:
        params = (loc, 0, scale, shape)  # Guess 0 for the covariate location slope
    else:
        params = (loc, scale, shape)

    ll_min = minimize(
        ll,
        params,
        method="nelder-mead",
        options=optimizer_options,
    )

    params = ll_min["x"]
    success = ll_min["success"]

    if nonstationary:
        beta0 = params[0]
        beta1 = params[1]
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
            location = beta0 + beta1 * covariate[time]
        rv = genextreme.isf(1 / return_period, -shape, location, scale)

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
            log_y = np.log(y)

            if abs(shape) < 1e-6:
                grad = np.array(
                    [
                        np.ones(len(covariate)),
                        covariate,
                        np.full(len(covariate), -log_y),
                        np.full(len(covariate), 0.5 * scale * log_y**2),
                    ]
                )
            else:
                db1 = np.ones(len(cov))
                db2 = cov
                dsh = np.ones(len(cov)) * (-1 / shape) * (1 - y ** (-shape))
                dsc = np.ones(len(cov)) * scale * (shape**-2) * (1 - y**-shape) - (
                    scale / shape * (y**-shape) * log_y
                )
                grad = np.array([db1, db2, dsh, dsc])
        else:  # stationary
            y = -np.log(1 - 1 / return_period)
            log_y = np.log(y)

            if abs(shape) < 1e-6:
                # grad = np.array([1, -np.log(y)])
                grad = np.array([1.0, -log_y, 0.5 * scale * log_y**2])[
                    :, None
                ]  # Gumbel limit gradients, Coles (2001)
            else:
                db1 = 1
                dsh = (-1 / shape) * (1 - y ** (-shape))
                dsc = scale * (shape**-2) * (1 - y**-shape) - (
                    scale / shape * (y**-shape) * log_y
                )
                grad = np.array([db1, dsh, dsc])
                grad = np.expand_dims(grad, axis=1)

        A = np.matmul(np.transpose(grad), vcov)
        B = np.matmul(A, grad)
        se = np.sqrt(np.diag(B))
    except Exception:
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
        except Exception:  # any issues, set to NaN
            rv = np.nan
            break
        count += 1
    return rv, np.nan


"""
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
"""
