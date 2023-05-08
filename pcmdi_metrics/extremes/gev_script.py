#!/usr/bin/env python
from scipy.stats import genextreme
from scipy.optimize import minimize
import xarray as xr


def logliklihood(params,x,covariate,maxes):
    # Log liklihood function to minimize for GEV
    beta1 = params[0]
    beta2 = params[1]
    scale = params[2]
    shape = params[3]

    n = len(x)
    location = beta1 + beta2 * covariate
    y = 1 + shape * (x - location) / scale
    if y.where(y<0,False).any():
        # TODO: Double check the inf vs ninf is correct
        if maxes:
            return np.inf
        else:
            return np.ninf
    if shape > 0:
        shape = np.abs(shape)
    else:
        shape = -1 * np.abs(shape)
    result = (n * np.log(scale) + np.sum(y**(-1 / shape)) + np.sum(np.log(y)*(1/shape + 1)))
    
    return result

def get_return_value(x,covariate,return_period,dim_time="time",maxes=True):
    # Use nonstationary GEV to get the value for a given return period
    # Arguments:
    #    x: xr.DataArray of test data set time series
    #    covariate: xr.DataArray of covariate time series
    #    return_period: Return period, numerical, in same time units
    #                   used by x and covariate
    #    dim_time: (Optional) name of time dimension in covariate
    #    maxes: (Optional) True if x contains block maxmima,
    #           False if x contains block minima
    # Returns:
    #    return_value: numpy array of return values for given return period

    n = len(x)

    if maxes is False:
        x = x * -1

    # Scale covariate from -0.5:0.5
    print("Scaling covariate")
    cov_max = covariate.max(skipna=True)
    cov_min = covariate.min(skipna=True)
    cov_norm = (covariate - cov_min) / (cov_max - cov_min) - 0.5

    # Use the stationary gev to make initial guess
    print("Generating initial guess")
    shape, loc, scale = genextreme.fit(x)

    print("Minimizing log liklihood")
    ll_min = minimize(logliklihood,(loc,0,scale,shape),args=(x,cov_norm,maxes),method="Nelder-Mead")
    params = ll_min["x"]

    print("Calculating return value")
    return_value = np.ones((n,1))*np.nan
    for time in range(0,n):
        location = params[0] + params[1] * cov_norm.isel({dim_time:time})
        scale = params[2]
        shape = params[3]
        return_value[time] = genextreme.isf(1/return_period, shape, location, scale)

    print("Return value finished")
    return return_value


