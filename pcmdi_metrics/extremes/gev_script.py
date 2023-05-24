#!/usr/bin/env python
from scipy.stats import genextreme
from scipy.optimize import minimize
import numpy as np
import xarray as xr


def logliklihood(params,x,covariate):
    # Log liklihood function to minimize for GEV
    beta1 = params[0]
    beta2 = params[1]
    scale = params[2]
    shape = params[3]

    n = len(x)
    location = beta1 + beta2 * covariate

    if scale <= 0:
        return np.inf

    # Use Gumbel distribution if shape is very close to zero
    if shape == 0 or np.isclose(shape,0):
        shape = 0
        y = (x - location) / scale
        result = (n*np.log(scale) + y + np.exp(-1*y))
        return result

    y = 1 + shape * (x - location) / scale
    if y.where(y<=0,False).any():
        # TODO: Double check the inf vs ninf is correct - I think so based on Coles 2001
        return np.inf
    
    if shape > 0:
        shape = np.abs(shape)
    else:
        shape = -1 * np.abs(shape)

    result = (n*np.log(scale) + np.sum(y**(-1 / shape)) + np.sum(np.log(y)*(1/shape + 1)))
    
    return result

def get_standard_error(params, cov, vcov, return_period):
    # V_phi = transpose(grad_phi) x V_theta x grad phi
    # grad_phi = transpose(d_phi/d_theta_d)
    # CI = phi_i +- z_a/2 * sqrt(V_phi)

    var_theta = np.diagonal(vcov)
    chck = [True for item in var_theta if item < 0]
    if len(chck) > 0:
        return "Negative standard error in parameters. Cannot obtain SE for return value."

    shape = params["shape"]
    scale = params["scale"]

    y = -np.log(1-1/return_period)

    if shape == 0:
        grad = [1,-np.log(y)]
    else:
        # TODO: check covariate term
        grad = [1,cov,(-1/shape)*(1-y**(-shape)),scale*(shape**-2)*(1-y**-shape)-(scale/shape*(y**-shape)*np.log(y))]

    # SE is T(grad) X var-cov_theta X grad
    A = np.matmul(np.transpose(grad),vcov)
    B = np.matmul(A,grad)
    se = np.sqrt(np.diagonal(B))

    return se

def get_return_value(x,covariate=None,return_period=20,dim_time="time",maxes=True):
    # Use nonstationary GEV to get the value for a given return period
    # Reference: Coles 2001, climExtremes
    # Arguments:
    #    x: xr.DataArray of test data set time series
    #    covariate: (Optional) xr.DataArray of covariate time series
    #    return_period: (Optional) Return period, numerical, in same
    #                   time units used by x and covariate. Default 20.
    #    dim_time: (Optional) name of time dimension in covariate
    #    maxes: (Optional) True if x contains block maxmima,
    #           False if x contains block minima
    # Returns:
    #    return_value: numpy array of return values for given return period

    n = len(x)

    if maxes is False:
        x = x * -1
        return_period = return_period * -1

    # Scale x to be around magnitude 1
    scale_factor = np.abs(x.max(skipna=True).item())
    x = x / scale_factor

    if covariate is not None:     # nonstationary case
        # Scale covariate from -0.5:0.5
        print("Calculating return value for nonstationary case.")
        cov_max = covariate.max(skipna=True)
        cov_min = covariate.min(skipna=True)
        cov_norm = (covariate - cov_min) / (cov_max - cov_min) - 0.5

        # Use the stationary gev to make initial guess
        shape, loc, scale = genextreme.fit(x)

        ll_min = minimize(logliklihood,(loc,0,scale,shape),args=(x,cov_norm),tol=1e-5,method="BFGS")
        success = bool(ll_min["success"])
        if success:
            params = ll_min["x"]
            vcov = ll_min["hess_inv"]
        else:
            print("Could not minimize logliklihood function. Return Value is NaN.")
            return np.ones(len(x)) * np.nan

        return_value = np.ones((n,1))*np.nan
        for time in range(0,n):
            location = params[0] + params[1] * cov_norm.isel({dim_time:time})
            scale = params[2]
            shape = params[3]
            return_value[time] = genextreme.isf(1/return_period, shape, location, scale)
    
    else: # stationary case
        print("Calculating return value for stationary case.")
        shape, loc, scale = genextreme.fit(x)
        return_value[time] = genextreme.isf(1/return_period, shape, loc, scale)

    return_value = return_value * scale_factor

    # TODO: Standard error

    print("Return value finished")
    return return_value

