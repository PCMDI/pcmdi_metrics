from pcmdi_metrics.io import get_time_key, get_latitude_key, get_longitude_key
import xarray as xr
from typing import Union


def calculate_temporal_correlation(data_array1: xr.DataArray, data_array2: xr.DataArray, dim:Union [str, tuple] = None) -> float:
    return _calculate_correlation(data_array1, data_array2, method='temporal', dim=None)


def calculate_spatial_correlation(data_array1: xr.DataArray, data_array2: xr.DataArray, wtarray: xr.DataArray = None, dim:Union [str, tuple] = None) -> float:
    return _calculate_correlation(data_array1, data_array2, method='spatial', wtarray=wtarray, dim=None)


def _calculate_correlation(data_array1: xr.DataArray, data_array2: xr.DataArray, wtarray: xr.DataArray = None, method='temporal', dim:Union [str, tuple] = None) -> float:
    """
    Calculate correlation between two xarray DataArrays.

    Parameters:
    - data_array1 (xarray.DataArray): First data array.
    - data_array2 (xarray.DataArray): Second data array.
    - method (str): Method for correlation calculation ('temporal' or 'spatial').
    - dim (tuple or str): Dimensions along which to compute the correlation.
                         For 'temporal' correlation, specify the time dimension.
                         For 'spatial' correlation, specify the spatial dimensions.

    Returns:
    - correlation (float): Correlation coefficient.
    """

    if method not in ['temporal', 'spatial']:
        raise ValueError("Invalid method. Use 'temporal' or 'spatial'.")

    if method == 'temporal':
        # Check if the specified dimension exists in both DataArrays
        if dim is None:
            dim = get_time_key(data_array1)
            if (dim not in data_array1.dims or dim not in data_array2.dims):
                raise ValueError(f"Temporal dimension '{dim}' not found in both input DataArrays.")
        
    elif method == 'spatial':
        # Check if the specified dimensions exist in both DataArrays
        if dim is None:
            lat_key = get_latitude_key(data_array1)
            lon_key = get_longitude_key(data_array1)
            dim = (lat_key, lon_key)
            if (not isinstance(dim, tuple) and dim not in data_array1.dims) or (isinstance(dim, tuple) and any(d not in data_array1.dims or d not in data_array2.dims for d in dim)):
                raise ValueError(f"Spatial dimension '{dim}' not found in both input DataArrays.")

    correlation = xr.corr(data_array1, data_array2, dim=dim).values.item()

    return correlation