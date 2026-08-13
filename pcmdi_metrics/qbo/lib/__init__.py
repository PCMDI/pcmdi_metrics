"""QBO-MJO metric computation library.

Public API functions:
- compute_qbo_mjo_metrics: Pure computation API accepting xarray Datasets
- process_qbo_mjo_metrics: File-path-based API for driver scripts

Supporting utilities (also available but considered internal):
- KFfilter: Wheeler-Kiladis wavenumber-frequency filtering
- Utility functions for regridding, time selection, and plotting
"""

# Public API - exposed at pcmdi_metrics.qbo level
from .compute_qbo_mjo_metrics import (  # noqa
    compute_qbo_mjo_metrics,
    process_qbo_mjo_metrics,
)

# Supporting classes and functions - available but not in main __all__
from .kf_filter import KFfilter  # noqa
from .utils import (  # noqa
    diag_plot,
    find_coord_key,
    generate_target_grid,
    mycolormap,
    select_time_range,
    standardize_lat_lon_name_in_dataset,
    test_plot_maps,
    test_plot_time_series,
)
from .utils_parallel import (  # noqa
    configure_logger,
    LoggerWriter,
    process,
)

__all__ = [
    # Primary public API
    "compute_qbo_mjo_metrics",
    "process_qbo_mjo_metrics",
    # Supporting utilities
    "KFfilter",
    "generate_target_grid",
    "select_time_range",
    "standardize_lat_lon_name_in_dataset",
    "find_coord_key",
    "diag_plot",
    "test_plot_time_series",
    "test_plot_maps",
    "mycolormap",
    "configure_logger",
    "LoggerWriter",
    "process",
]
