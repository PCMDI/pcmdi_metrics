import numpy as np
import scipy.stats
# Note that the calibration and calculation data can be the same but they should both be 1-d monthly mean precipitation array and start from January.


def accumulation(data, temporal_scale):  
    # calculate the accumulated n months (temporal_scale) precipitation data
    data_accumulated = np.convolve(data, np.ones(temporal_scale), 'valid')
    # set the value to NANs for the first n-1 months because there isn't accumulated n months values at the first n-1 months
    data_accumulated = np.concatenate([[np.nan]*(temporal_scale-1), data_accumulated])
    
    # If the last year is incomplete, let's set NAN to the months without values in the last year
    n_year_incomplete = len(data_accumulated)/12 - int(len(data_accumulated)/12)
    n_month_incomplete = int(n_year_incomplete * 12)
    data_accumulated = np.concatenate([data_accumulated,[np.nan]*(n_month_incomplete)])
    # Then reshape the 1-d array to 2-d array with the shape of (the number of years, 12) becasue the SPI's distribution and calculation should be based on each month.
    data_accumulated_reshape = data_accumulated.reshape(int(len(data_accumulated)/12), 12)
    return data_accumulated_reshape


def gamma_transformation(calibration,calculation, temporal_scale):
    # calculate the alphas and betas at each month based on calibration data
    means = np.nanmean(calibration, axis=0)
    a = np.log(means) - np.nanmean(np.log(calibration), axis=0)
    alphas = (1 + np.sqrt(1 + 4 * a / 3)) / (4 * a)
    betas = means / alphas
    # calculate the probability of 0 values
    n_zero = (calculation ==0).sum()
    n_values = np.count_nonzero(~np.isnan(calculation)) + n_zero
    p_zero = n_zero / len(calculation)

    # set the 0 value as NAN
    calculation[calculation == 0] = np.NaN

    # build gamma distribution based on the non-zero values of calibration data
    # calculate the probability and the values of calculation data under gamma distribution built by calibration data
    p_gamma_non_zero = scipy.stats.gamma.cdf(calculation, a=alphas, scale=betas)
    p_gamma = p_zero + ( 1 - p_zero ) * p_gamma_non_zero
    calculation_transformed = scipy.stats.norm.ppf(p_gamma)
    # change the shape to 1-d array
    calculation_transformed = calculation_transformed.flatten()
    return calculation_transformed
    
    
def spi(precipitation_calibration:np.ndarray,
        precipitation_calculation:np.ndarray,
        temporal_scale:int,
        distribution='gamma',
        upper_limit=3.09,
        lower_limit=-3.09):
    
    # precipitation_calibration: It should be the 1-d monthly precipitation array used to calibrate the distribution. It must start from January and can be the same as precipitation_calculate. 
    # precipitation_calculate: It should be the 1-d monthly precipitation array used to calculate the SPI_n. It must start from Januaray too.
    # temporal_scale: It's the temporal scale of SPI_n which indicates the number of n months used to calculate accumulated SPI. For example, to calculate SPI3, it should be 3.
    # distribution: The distribution of SPI and right now it only supports gamma distribution which is the most commonly used one.
    # upper_limit, lower_limit: The maximum and minimum SPI values, according to https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1752-1688.1999.tb03592.x , the default values are 3.09 and -3.09.
    
    """
    # test if there is missing and negative value 
    if np.all(np.isnan(precipitation_calibration)):
        print("calibration data cannot be all NAN!")
    if np.all(np.isnan(precipitation_calculation)):
        print("calculation data cannot be all NAN!")
    """
        
    if precipitation_calibration[~np.isnan(precipitation_calibration)].min()<0:
        print("Calibration data must be positive! All negative values will be assign to be 0")
        precipitation_calibration.clip(min=0)
    
    if precipitation_calculation[~np.isnan(precipitation_calculation)].min()<0:
        print("Calculation data must be positive! All negative values will be assign to be 0")
        precipitation_calculation.clip(min=0)
        
    # calculate the length of input calculation data
    length_input = len(precipitation_calibration)
        
    # calculate the accumulated precipitation of calibration and calculation data, then reshape them to 2-d array.
    precipitation_calibration_accumulated = accumulation(precipitation_calibration, temporal_scale)
    precipitation_calculation_accumulated = accumulation(precipitation_calculation, temporal_scale)
    
    # apply the gamma transformation to accumulated data
    if distribution == 'gamma':
        spi_n = gamma_transformation(precipitation_calibration_accumulated,
                                    precipitation_calculation_accumulated,
                                    temporal_scale)
        
    # clip the spi values 
    spi_n = np.clip(spi_n,a_min=lower_limit , a_max=upper_limit)
    
    # change spi_n to its original length 
    spi_n =  spi_n[0:length_input]
    return spi_n
