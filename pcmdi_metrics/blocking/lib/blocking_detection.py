#!/usr/bin/env python

"""
Atmospheric Blocking Detection using Deep Learning.

The model utilizes ResNet152 architecture with added input size flexibility, decoder
part and skipped connections (U-Net). Uses 500 hPa geopotential height to detect
atmospheric blocking patterns.

Created by: Elina Valkonen (November 2022)
Updates by: Jiwoo Lee (October 2023, December 2022)
Adapted for PMP by: Claude (November 2026)

History:
- Nov 10, 2022: Initial version (Elina Valkonen)
- Oct 4, 2022: Changed time period to 1950-2100
- Nov 7, 2022: Added MPI, MIROC, CESM training data
- Dec 9, 2022: Jiwoo Lee - enabled usage with PCMDI database
- Oct 17, 2023: Elina Valkonen - added cyclic point handling, per-model normalization
- Oct 21, 2023: Jiwoo Lee - added time subsetting, layer extraction, API docstring
- Nov 19, 2026: Adapted for PCMDI Metrics Package structure

References
----------
Valkonen, E., Lee, J., et al. (2023). U-Net based atmospheric blocking detection
for climate model evaluation. In preparation.
"""

import time
import warnings
from typing import Optional

import numpy as np
import xarray as xr
import xcdat as xc

from .blocking_utils import (
    check_input_grid,
    find_nearest,
    get_model_path,
    validate_blocking_input,
)

# TensorFlow imported on-demand to avoid forcing dependency
_TENSORFLOW_AVAILABLE = None


def _check_tensorflow():
    """Check if TensorFlow is available."""
    global _TENSORFLOW_AVAILABLE
    if _TENSORFLOW_AVAILABLE is None:
        try:
            import tensorflow  # noqa: F401

            _TENSORFLOW_AVAILABLE = True
        except ImportError:
            _TENSORFLOW_AVAILABLE = False
    return _TENSORFLOW_AVAILABLE


def detect_blocking(
    ds: xr.Dataset,
    var: str = "zg",
    level: float = 50000,
    model_path: Optional[str] = None,
    threshold: float = 0.34,
    start: Optional[str] = None,
    end: Optional[str] = None,
    output_file: Optional[str] = None,
    verbose: bool = True,
) -> xr.Dataset:
    """
    Detect atmospheric blocking using deep learning.

    Applies U-Net neural network with ResNet152 backbone to identify blocking
    patterns from 500 hPa geopotential height fields. Automatically handles:
    - Layer extraction (if 4D data)
    - Regridding to 2°×2°
    - Per-model normalization
    - 5-day temporal window
    - Binary classification

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset with geopotential height. Can be 3D (time, lat, lon) or
        4D (time, plev, lat, lon). Daily frequency required.
    var : str, optional
        Variable name for geopotential height. Default 'zg'.
    level : float, optional
        Pressure level in Pa to extract if 4D. Default 50000 (500 hPa).
    model_path : str, optional
        Path to pre-trained model file. If None, searches in:
        1. $CONDA_PREFIX/share/pmp/blocking_models/
        2. <site-packages>/share/pmp/blocking_models/
        If not found, raises error with download instructions.
    threshold : float, optional
        Probability threshold for binary mask [0-1]. Default 0.34
        (optimized value from training).
    start : str, optional
        Start date in format 'yyyy-mm' to subset data. Default None (all data).
    end : str, optional
        End date in format 'yyyy-mm'. Default None (all data).
    output_file : str, optional
        If provided, save results to this NetCDF file. Default None (no save).
    verbose : bool, optional
        Print progress messages. Default True.

    Returns
    -------
    xr.Dataset
        Output dataset with variables:
        - 'pval': Blocking probability [0-1]
        - 'pval_binary': Binary blocking mask (0=no block, 1=block)

        Coordinates match input except:
        - Time: 4 days shorter (2 removed from each end due to 5-day window)
        - Spatial: 2°×2° global grid (90 lat × 180 lon)

    Raises
    ------
    ImportError
        If TensorFlow is not installed.
    FileNotFoundError
        If model file cannot be found.
    ValueError
        If input data is invalid.

    Notes
    -----
    - Input must be daily frequency on pressure levels
    - Model trained on 1950-2100 CMIP6 data (CESM2, MPI, MIROC)
    - Processing time: ~30 seconds per year on CPU, ~5 seconds on GPU
    - First and last 2 days are removed due to 5-day window requirement

    Examples
    --------
    Basic usage:

    >>> import xarray as xr
    >>> from pcmdi_metrics.blocking import detect_blocking
    >>>
    >>> ds = xr.open_mfdataset('zg_day_*.nc')
    >>> blocking = detect_blocking(ds, var='zg')
    >>> blocking['pval_binary'].mean(dim='time').plot()

    Detect blocking for specific period:

    >>> blocking = detect_blocking(
    ...     ds,
    ...     var='zg',
    ...     start='2000-01',
    ...     end='2010-12'
    ... )

    Save diagnostics to file:

    >>> blocking = detect_blocking(
    ...     ds,
    ...     var='zg',
    ...     output_file='blocking_diagnostics.nc'
    ... )

    Use custom model and threshold:

    >>> blocking = detect_blocking(
    ...     ds,
    ...     model_path='/path/to/custom_model.h5',
    ...     threshold=0.5
    ... )

    See Also
    --------
    compute_blocking_metrics : Calculate regional/seasonal statistics
    """
    # Check TensorFlow availability
    if not _check_tensorflow():
        raise ImportError(
            "TensorFlow is required for blocking detection.\n"
            "Install with:\n"
            "  conda install -c conda-forge 'tensorflow>=2'\n"
            "Or:\n"
            "  pip install 'pcmdi_metrics[blocking]'"
        )

    from tensorflow import keras

    # Validate input
    validate_blocking_input(ds, var, level)

    if verbose:
        print(f"Input variable: {var}")
        print(f"Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
        if start or end:
            print(f"Subsetting to: {start} - {end}")

    # Time subset if requested
    if (start is not None) or (end is not None):
        ds = select_time_range(ds, start=start, end=end)
        if verbose:
            print(f"After subsetting: {len(ds.time)} time steps")

    # Extract layer if 4D
    if ds[var].ndim == 4:
        if verbose:
            print(f"Extracting {level} Pa level...")
        ds[var] = extract_layer(ds, var, level)

    # Regrid if needed
    if check_input_grid(ds, expected_shape=(90, 180)):
        if verbose:
            print("Data already on 2°×2° grid")
        SLP_train_full = ds[var].values
        ds_regridded = ds
    else:
        if verbose:
            print("Regridding to 2°×2° uniform grid...")
        target_grid = xc.create_uniform_grid(-89, 89, 2.0, 0, 358, 2.0)
        ds_regridded = ds.regridder.horizontal(var, target_grid, tool="regrid2")
        SLP_train_full = ds_regridded[var].values
        if verbose:
            print("Regridding done")

    start_time = time.time()

    # Preprocess data
    if verbose:
        print("Preprocessing data (normalization, cyclic padding, 5-day window)...")
    normalized_data = normalize_input(SLP_train_full)
    formatted_data = add_channels(normalized_data)

    # Load model
    if verbose:
        print("Loading pre-trained model...")
    model_file = get_model_path(model_path)
    dependencies = {"jaccard_distance": jaccard_distance}
    head_model = keras.models.load_model(model_file, custom_objects=dependencies)
    if verbose:
        print("Preprocessing and model loading done")

    # Run prediction
    if verbose:
        print("Running neural network prediction...")
    Pval = head_model.predict(formatted_data, verbose=0 if not verbose else 1).squeeze()

    # Remove cyclic point extra longitudes (added 6 on each side)
    Pval = Pval[:, :, 6:-6]

    elapsed_time = time.time() - start_time
    if verbose:
        print(f"Prediction complete in {elapsed_time:.1f} seconds")

    # Apply threshold
    if verbose:
        print(f"Applying threshold ({threshold})...")
    Pval_binary = get_binarymaps_from_probabilities(Pval, threshold=threshold)

    # Create output dataset
    # Copy metadata from regridded dataset, remove first and last 2 days
    output_ds = ds_regridded.drop_vars(var).isel(time=slice(2, -2)).copy(deep=True)
    output_ds["pval"] = (("time", "lat", "lon"), Pval)
    output_ds["pval_binary"] = (("time", "lat", "lon"), Pval_binary)

    # Add attributes
    output_ds["pval"].attrs = {
        "long_name": "Blocking probability",
        "units": "1",
        "description": "Probability of atmospheric blocking from neural network (0-1)",
        "threshold": threshold,
    }
    output_ds["pval_binary"].attrs = {
        "long_name": "Binary blocking mask",
        "units": "1",
        "description": f"Binary blocking detection (0=no block, 1=block, threshold={threshold})",
        "threshold": threshold,
    }

    # Add global attributes
    output_ds.attrs["blocking_detection_method"] = (
        "U-Net neural network with ResNet152 backbone"
    )
    output_ds.attrs["blocking_model_file"] = model_file
    output_ds.attrs["blocking_threshold"] = threshold
    output_ds.attrs["blocking_preprocessing"] = (
        "Regridded to 2x2 degrees, per-model normalization, 5-day temporal window"
    )

    # Save to file if requested
    if output_file is not None:
        if verbose:
            print(f"Saving results to {output_file}...")
        output_ds.to_netcdf(output_file)
        if verbose:
            print("Output saved")

    if verbose:
        n_blocked = int(output_ds["pval_binary"].sum())
        total = int(output_ds["pval_binary"].size)
        pct = 100 * n_blocked / total
        print(f"Blocking detected: {n_blocked}/{total} grid points ({pct:.2f}%)")

    return output_ds


def normalize_input(slp_train: np.ndarray) -> np.ndarray:
    """
    Normalize input individually for each model (requirement of the CNN).

    Computes mean and standard deviation across time dimension,
    then normalizes to zero mean and unit variance. Adds cyclic
    padding of 6 grid points on each side of longitude dimension.

    Parameters
    ----------
    slp_train : np.ndarray
        Input data array with shape (time, lat, lon).

    Returns
    -------
    np.ndarray
        Normalized array with cyclic padding, shape (time, lat, lon+12).

    Notes
    -----
    This function preserves the exact computational logic from the original
    implementation. The cyclic padding is removed after neural network prediction.
    """
    meandata = np.nanmean(slp_train, axis=0)
    stddata = np.nanstd(slp_train, axis=0)

    # Normalize the prediction dataset
    PSL_train = (slp_train - meandata) / stddata

    # Add cyclic point - 6 grid points on each side
    # This will be removed after prediction
    PSL_train = np.concatenate(
        (PSL_train[:, :, -6:], PSL_train, PSL_train[:, :, 0:6]), axis=2
    )

    return PSL_train


def add_channels(PSL_train: np.ndarray) -> np.ndarray:
    """
    Add 5-day persistence utilizing channels for lead-lag.

    Creates input array with 5 temporal channels corresponding to
    t-2, t-1, t, t+1, t+2 days for each time step.

    Parameters
    ----------
    PSL_train : np.ndarray
        Normalized input array with shape (time, lat, lon).

    Returns
    -------
    np.ndarray
        Formatted array with 5 temporal channels,
        shape (time-4, lat, lon, 5).

    Notes
    -----
    - Output has 4 fewer time steps (2 at each end)
    - NaN values are replaced with 0
    - This function preserves the exact computational logic from the original
    """
    # Create lead-lag arrays
    temp_minustwo = PSL_train[0:-4, :, :]
    temp_minusone = PSL_train[1:-3, :, :]
    temp_dayof = PSL_train[2:-2, :, :]
    temp_plusone = PSL_train[3:-1, :, :]
    temp_plustwo = PSL_train[4:, :, :]

    X_train = []

    for sample_ind in range(0, PSL_train.shape[0] - 4):
        temp = np.vstack(
            (
                temp_minustwo[sample_ind][np.newaxis, ...],
                temp_minusone[sample_ind][np.newaxis, ...],
                temp_dayof[sample_ind][np.newaxis, ...],
                temp_plusone[sample_ind][np.newaxis, ...],
                temp_plustwo[sample_ind][np.newaxis, ...],
            )
        )
        X_train.append(temp)

    # Reshape the axis
    X_train = np.array(X_train)
    X_train = np.swapaxes(X_train, 1, -1)
    X_train = np.swapaxes(X_train, 1, 2)

    # Replace NaN values with zeros (required for neural network)
    X_train[np.isnan(X_train)] = 0

    return X_train


def jaccard_distance(y_true, y_pred, smooth=1):
    """
    Jaccard distance loss function (IoU).

    This is a custom loss function required for loading the pre-trained model.

    Parameters
    ----------
    y_true : tensor
        True labels.
    y_pred : tensor
        Predicted labels.
    smooth : float, optional
        Smoothing factor. Default 1.

    Returns
    -------
    tensor
        Jaccard distance loss.

    Notes
    -----
    This function must be provided as a custom object when loading the model.
    """
    # Import here to avoid forcing TensorFlow dependency at module load
    from tensorflow.keras import backend as K

    intersection = K.sum(K.abs(y_true * y_pred), axis=-1)
    sum_ = K.sum(K.abs(y_true) + K.abs(y_pred), axis=-1)
    jac = (intersection + smooth) / (sum_ - intersection + smooth)
    return (1 - jac) * smooth


def get_binarymaps_from_probabilities(
    Pval: np.ndarray, threshold: float = 0.34
) -> np.ndarray:
    """
    Convert probability maps to binary blocking masks.

    The model outputs probabilities [0-1]. This function converts them to
    binary masks using a threshold. Default threshold of 0.34 was determined
    empirically based on metrics plots during model development.

    Parameters
    ----------
    Pval : np.ndarray
        Probability array with shape (time, lat, lon).
    threshold : float, optional
        Threshold for binary classification. Default 0.34.

    Returns
    -------
    np.ndarray
        Binary array (0.0 or 1.0) with same shape as input.

    Examples
    --------
    >>> probs = np.array([0.2, 0.5, 0.8])
    >>> binary = get_binarymaps_from_probabilities(probs, threshold=0.4)
    >>> print(binary)
    [0.0 1.0 1.0]
    """
    Pval_binary = np.copy(Pval)
    Pval_binary[Pval_binary >= threshold] = 1.0
    Pval_binary[Pval_binary < threshold] = 0.0

    return Pval_binary


def select_time_range(
    ds: xr.Dataset, start: Optional[str] = None, end: Optional[str] = None
) -> xr.Dataset:
    """
    Subset dataset to specified time range.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to subset.
    start : str, optional
        Starting year and month in format "yyyy-mm". If None, uses first time.
    end : str, optional
        Ending year and month in format "yyyy-mm". If None, uses last time.

    Returns
    -------
    xr.Dataset
        Subsetted dataset.

    Examples
    --------
    >>> ds_subset = select_time_range(ds, start='2000-01', end='2010-12')
    """
    # Parse start date
    if start is not None:
        start_yr = int(start.split("-")[0])
        start_mo = int(start.split("-")[1])
        start_da = 1

        start_yr_str = str(start_yr).zfill(4)
        start_mo_str = str(start_mo).zfill(2)
        start_da_str = str(start_da).zfill(2)
    else:
        start_yr_str = str(ds.time.dt.year[0].values).zfill(4)
        start_mo_str = str(ds.time.dt.month[0].values).zfill(2)
        start_da_str = str(ds.time.dt.day[0].values).zfill(2)

    # Parse end date
    if end is not None:
        end_yr = int(end.split("-")[0])
        end_mo = int(end.split("-")[1])

        ds_tmp = ds.time.dt.days_in_month.sel(time=(ds.time.dt.year == end_yr))
        end_da = int(
            ds_tmp.time.dt.days_in_month.sel(time=(ds_tmp.time.dt.month == end_mo))[-1]
        )

        end_yr_str = str(end_yr).zfill(4)
        end_mo_str = str(end_mo).zfill(2)
        end_da_str = str(end_da).zfill(2)
    else:
        end_yr_str = str(ds.time.dt.year[-1].values).zfill(4)
        end_mo_str = str(ds.time.dt.month[-1].values).zfill(2)
        end_da_str = str(ds.time.dt.day[-1].values).zfill(2)

    start_datetime = f"{start_yr_str}-{start_mo_str}-{start_da_str} 00:00:00"
    end_datetime = f"{end_yr_str}-{end_mo_str}-{end_da_str} 23:59:59"

    # Subset given time period
    ds = ds.sel(time=slice(start_datetime, end_datetime))

    return ds


def extract_layer(ds: xr.Dataset, var: str, level: float) -> xr.DataArray:
    """
    Extract specific pressure level from 4D data.

    Sometimes vertical coordinate in model output is not stored exactly on desired level.
    For example, plev might have 50000.00000001 for 500 hPa layer instead of 50000.
    This function examines if the model layer is close enough to the requested level,
    and if so, extracts the layer.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset with vertical coordinate.
    var : str
        Variable name to extract.
    level : float
        Pressure level to extract in Pa.

    Returns
    -------
    xr.DataArray
        Extracted 3D array (time, lat, lon).

    Raises
    ------
    ValueError
        If vertical coordinate is missing or level difference is too large.

    Examples
    --------
    >>> zg_500 = extract_layer(ds, var='zg', level=50000)
    """
    if level is None:
        return ds[var]

    # Ensure level is numeric
    if not isinstance(level, (int, float)):
        level = float(level)

    # Check vertical coordinate
    vertical_coords = {"plev", "lev", "level", "pressure"}
    found_vertical = vertical_coords.intersection(set(ds.coords.keys()))

    if not found_vertical:
        raise ValueError(
            f"Vertical coordinate not found in dataset.\n"
            f"Expected one of: {vertical_coords}\n"
            f"Found coordinates: {list(ds.coords.keys())}"
        )

    vert_coord = list(found_vertical)[0]

    try:
        # Try exact selection
        ds_level = ds[var].sel({vert_coord: level})
        return ds_level
    except (KeyError, ValueError) as ex:
        warnings.warn(f"Exact level selection failed: {ex}", UserWarning)

        # Find nearest level
        nearest_level = find_nearest(ds[vert_coord].values, level)

        print(f"  Given level: {level}")
        print(f"  Selected nearest level from dataset: {nearest_level}")

        # Check if difference is acceptable (< 0.1%)
        diff_percentage = abs(nearest_level - level) / level * 100
        if diff_percentage < 0.1:
            ds_level = ds[var].sel({vert_coord: level}, method="nearest")
            print("  Difference is in acceptable range.")
            return ds_level
        else:
            raise ValueError(
                f"Difference between requested level ({level}) and "
                f"nearest available level ({nearest_level}) is too large "
                f"({diff_percentage:.2f}%)."
            )
