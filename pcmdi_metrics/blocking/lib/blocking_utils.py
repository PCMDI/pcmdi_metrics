"""
Utility functions for atmospheric blocking metrics.

This module provides helper functions for model loading, validation,
and data preparation used by the blocking detection and metrics modules.

Created by: Claude (adapted from Elina Valkonen and Jiwoo Lee's work)
Last Updated: November 2026
"""

import os
import warnings
from typing import Optional, Tuple

import numpy as np
import xarray as xr


def validate_tensorflow() -> None:
    """
    Check TensorFlow availability and version.

    Raises
    ------
    ImportError
        If TensorFlow is not installed or version is < 2.0.

    Examples
    --------
    >>> validate_tensorflow()  # Passes if TensorFlow >= 2.0 installed
    """
    try:
        import tensorflow as tf

        version = tf.__version__
        major_version = int(version.split(".")[0])

        if major_version < 2:
            raise ImportError(
                f"TensorFlow 2.0+ required, found version {version}.\n"
                "Upgrade with: conda install -c conda-forge 'tensorflow>=2'\n"
                "Or: pip install 'tensorflow>=2.0'"
            )
    except ImportError as e:
        raise ImportError(
            "TensorFlow 2.0+ is required for blocking detection.\n"
            "Install with:\n"
            "  conda install -c conda-forge 'tensorflow>=2'\n"
            "Or:\n"
            "  pip install 'pcmdi_metrics[blocking]'"
        ) from e


def get_model_path(model_path: Optional[str] = None) -> str:
    """
    Get path to pre-trained blocking detection model.

    Searches for model file in the following order:
    1. User-specified path (if provided)
    2. $CONDA_PREFIX/share/pmp/blocking_models/
    3. <site-packages>/share/pmp/blocking_models/
    4. Raises error with download instructions

    Parameters
    ----------
    model_path : str, optional
        User-specified path to model file. If provided, this path
        is validated and returned. Default None (use standard locations).

    Returns
    -------
    str
        Absolute path to model file.

    Raises
    ------
    FileNotFoundError
        If model file cannot be found in any location.

    Examples
    --------
    >>> # Use default location
    >>> model_path = get_model_path()

    >>> # Use custom location
    >>> model_path = get_model_path('/path/to/custom_model.h5')
    """
    model_filename = "falco_fulldata_oct11.h5"

    # If user provided path, validate it
    if model_path is not None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at specified path: {model_path}"
            )
        return model_path

    # Search standard locations
    search_paths = []

    # 1. Check CONDA_PREFIX/share/pmp/blocking_models/
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        search_paths.append(
            os.path.join(
                conda_prefix, "share", "pmp", "blocking_models", model_filename
            )
        )

    # 2. Check package resource location
    try:
        from pcmdi_metrics import resources

        resource_base = resources.resource_path()
        search_paths.append(
            os.path.join(resource_base, "blocking_models", model_filename)
        )
    except (ImportError, AttributeError):
        pass

    # 3. Check relative to this file (for development)
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    search_paths.append(os.path.join(package_dir, "data", model_filename))

    # Try each path
    for path in search_paths:
        if os.path.exists(path):
            return path

    # Model not found - provide helpful error
    raise FileNotFoundError(
        "\nPre-trained blocking detection model not found.\n\n"
        "Searched locations:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        "Download the model:\n"
        "  1. Automatic: download_blocking_model.py\n"
        "  2. Manual: https://pcmdi.llnl.gov/pss/pmpdata/blocking_pre-trained-model/falco_fulldata_oct11.h5\n"
        "\n"
        "Or specify path explicitly:\n"
        "  detect_blocking(ds, model_path='/path/to/model.h5')\n"
        "\n"
        "See: pcmdi_metrics/blocking/data/README_model.md"
    )


def check_input_grid(
    ds: xr.Dataset, expected_shape: Tuple[int, int] = (90, 180)
) -> bool:
    """
    Check if dataset is already on expected grid.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset to check.
    expected_shape : tuple of int, optional
        Expected (nlat, nlon) shape. Default (90, 180) for 2°×2° grid.

    Returns
    -------
    bool
        True if dataset matches expected grid, False otherwise.

    Examples
    --------
    >>> ds = xr.Dataset({'zg': (('time', 'lat', 'lon'), data)})
    >>> if not check_input_grid(ds):
    ...     ds = regrid_to_target(ds)
    """
    lat_shape = ds.sizes.get("lat", 0)
    lon_shape = ds.sizes.get("lon", 0)

    return (lat_shape, lon_shape) == expected_shape


def validate_blocking_input(
    ds: xr.Dataset, var: str, level: Optional[float] = None
) -> None:
    """
    Validate input dataset for blocking detection.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset to validate.
    var : str
        Variable name to check.
    level : float, optional
        Pressure level expected in Pa. Only checked if data is 4D.

    Raises
    ------
    TypeError
        If ds is not an xarray.Dataset.
    ValueError
        If required variable or dimensions are missing.

    Examples
    --------
    >>> validate_blocking_input(ds, var='zg', level=50000)
    """
    # Check type
    if not isinstance(ds, xr.Dataset):
        raise TypeError(
            f"Input must be an xarray.Dataset, got {type(ds).__name__}.\n"
            "If you have a file path, use: ds = xr.open_dataset(path)"
        )

    # Check variable exists
    if var not in ds.data_vars:
        raise ValueError(
            f"Variable '{var}' not found in dataset.\n"
            f"Available variables: {list(ds.data_vars.keys())}"
        )

    # Check required dimensions
    var_dims = set(ds[var].dims)
    if "time" not in var_dims:
        raise ValueError(
            f"Variable '{var}' must have 'time' dimension.\n"
            f"Found dimensions: {list(var_dims)}"
        )

    if not {"lat", "lon"}.issubset(var_dims):
        raise ValueError(
            f"Variable '{var}' must have 'lat' and 'lon' dimensions.\n"
            f"Found dimensions: {list(var_dims)}"
        )

    # Check time coordinate
    if len(ds.time) < 5:
        warnings.warn(
            f"Dataset has only {len(ds.time)} time steps. "
            "Blocking detection requires at least 5 days (for 5-day window). "
            "Results will have {len(ds.time) - 4} time steps.",
            UserWarning,
        )

    # Check for vertical dimension if 4D
    if ds[var].ndim == 4:
        # Should have a vertical coordinate
        vertical_coords = {"plev", "lev", "level", "pressure"}
        found_vertical = vertical_coords.intersection(set(ds.coords.keys()))

        if not found_vertical:
            raise ValueError(
                f"4D data requires a vertical coordinate.\n"
                f"Expected one of: {vertical_coords}\n"
                f"Found coordinates: {list(ds.coords.keys())}"
            )

        if level is not None:
            # Check if requested level exists
            vertical_coord = list(found_vertical)[0]
            levels = ds[vertical_coord].values

            # Allow some tolerance for floating point comparison
            level_exists = np.any(np.isclose(levels, level, rtol=1e-4))

            if not level_exists:
                closest_level = levels[np.argmin(np.abs(levels - level))]
                warnings.warn(
                    f"Requested level {level} Pa not found exactly.\n"
                    f"Available levels: {levels}\n"
                    f"Closest level: {closest_level} Pa\n"
                    f"Will use closest level for extraction.",
                    UserWarning,
                )


# Removed: find_nearest() - functionality now in pcmdi_metrics.utils.extract_level
