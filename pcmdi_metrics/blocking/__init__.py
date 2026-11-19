"""
Atmospheric Blocking Metrics
=============================

Deep learning-based detection of atmospheric blocking patterns.

This module provides automated detection of atmospheric blocking events using a
U-Net neural network with ResNet152 backbone. It identifies blocking patterns
from 500 hPa geopotential height fields and computes regional/seasonal statistics
for climate model evaluation.

Main Functions
--------------
detect_blocking : Identify blocking events using neural network
compute_blocking_metrics : Calculate regional/seasonal statistics

Installation
------------
Standard installation (without blocking):
    conda install -c conda-forge pcmdi_metrics

With blocking support:
    conda install -c conda-forge pcmdi_metrics tensorflow>=2

Or:
    pip install pcmdi_metrics[blocking]

Pre-trained Model
-----------------
The blocking detection requires a 246 MB pre-trained model file.
Download with:
    download_blocking_model.py

Or manually from:
    https://pcmdiweb.llnl.gov/pss/pmpdata/blocking_models/falco_fulldata_oct11.h5

Examples
--------
>>> from pcmdi_metrics.blocking import detect_blocking, compute_blocking_metrics
>>> import xarray as xr
>>>
>>> # Load 500 hPa geopotential height
>>> ds = xr.open_mfdataset('zg_day_*.nc')
>>>
>>> # Detect blocking
>>> blocking = detect_blocking(ds, var='zg', start='2000-01', end='2010-12')
>>>
>>> # Calculate metrics
>>> metrics, spatial = compute_blocking_metrics(blocking, historical=True)
>>> print(metrics.groupby('Season').mean())

See Also
--------
pcmdi_metrics.blocking.lib : Core library functions

References
----------
Valkonen, E., Lee, J., et al. (2023). U-Net based atmospheric blocking detection
for climate model evaluation. In preparation.

Wiedenmann, J. M., Lupo, A. R., Mokhov, I. I., & Tikhonova, E. A. (2002).
The climatology of blocking anticyclones for the Northern and Southern
Hemispheres: Block intensity as a diagnostic. Journal of Climate, 15(23),
3459-3473.
"""

import warnings

# Check TensorFlow availability
_HAS_TENSORFLOW = False
_TENSORFLOW_ERROR = None

try:
    from .lib.blocking_utils import validate_tensorflow

    validate_tensorflow()
    _HAS_TENSORFLOW = True
except ImportError as e:
    _TENSORFLOW_ERROR = str(e)
    _HAS_TENSORFLOW = False

# Import functions if TensorFlow is available
if _HAS_TENSORFLOW:
    try:
        from .lib.blocking_detection import detect_blocking
        from .lib.blocking_metrics import (
            compute_blocking_metrics,
            metrics_to_csv,
            metrics_to_json,
            spatial_means_to_npy,
        )
        from .lib.blocking_utils import get_model_path, validate_tensorflow

        __all__ = [
            "detect_blocking",
            "compute_blocking_metrics",
            "metrics_to_csv",
            "metrics_to_json",
            "spatial_means_to_npy",
            "get_model_path",
            "validate_tensorflow",
        ]

    except ImportError as e:
        # Unexpected import error after TensorFlow validated
        warnings.warn(
            f"Blocking metrics module partially unavailable: {e}\n"
            "Please report this issue.",
            ImportWarning,
        )
        _HAS_TENSORFLOW = False
        _TENSORFLOW_ERROR = str(e)

# Provide helpful error messages if TensorFlow is not available
if not _HAS_TENSORFLOW:
    # Create stub functions that provide clear error messages
    def _make_tensorflow_stub(func_name):
        def stub(*args, **kwargs):
            raise ImportError(
                f"Function '{func_name}' requires TensorFlow.\n"
                f"Error: {_TENSORFLOW_ERROR}\n\n"
                "Install TensorFlow to use blocking metrics:\n"
                "  conda install -c conda-forge 'tensorflow>=2'\n"
                "Or:\n"
                "  pip install 'pcmdi_metrics[blocking]'\n\n"
                "See: pcmdi_metrics/blocking/data/README_model.md"
            )

        stub.__name__ = func_name
        stub.__doc__ = f"{func_name} (TensorFlow required)"
        return stub

    # Create stubs for main functions
    detect_blocking = _make_tensorflow_stub("detect_blocking")
    compute_blocking_metrics = _make_tensorflow_stub("compute_blocking_metrics")
    metrics_to_csv = _make_tensorflow_stub("metrics_to_csv")
    metrics_to_json = _make_tensorflow_stub("metrics_to_json")
    spatial_means_to_npy = _make_tensorflow_stub("spatial_means_to_npy")
    get_model_path = _make_tensorflow_stub("get_model_path")
    validate_tensorflow = _make_tensorflow_stub("validate_tensorflow")

    __all__ = [
        "detect_blocking",
        "compute_blocking_metrics",
        "metrics_to_csv",
        "metrics_to_json",
        "spatial_means_to_npy",
        "get_model_path",
        "validate_tensorflow",
    ]

    # Warn at import time
    warnings.warn(
        f"Blocking metrics unavailable: {_TENSORFLOW_ERROR}\n"
        "Install TensorFlow to enable: conda install -c conda-forge 'tensorflow>=2'",
        ImportWarning,
    )


# Module metadata
__version__ = "1.0.0"
__author__ = "Elina Valkonen, Jiwoo Lee"
