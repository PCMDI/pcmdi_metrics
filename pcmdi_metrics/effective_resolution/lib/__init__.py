"""Effective resolution diagnostic library.

Public API functions:

- ``compute_effective_resolution``: pure computation API accepting xarray Datasets
- ``process_effective_resolution``: file-path-based API for driver scripts

Supporting utilities (also available but considered internal):

- KE spectra from vorticity/divergence spherical-harmonic coefficients
- Sliding-window spectral slope fitting and steepening detection
- Representative grid box distance for regular, Gaussian and reduced grids
- Figure 1 / Figure 2 reproductions
"""

# Public API - exposed at pcmdi_metrics.effective_resolution level
from .compute_effective_resolution import (  # noqa
    SPECTRUM_KEYS,
    compute_effective_resolution,
    process_effective_resolution,
)

# Supporting functions - available but not the primary entry points
from .grid_distance import (  # noqa
    grid_box_distance_from_dataset,
    ratio_to_dx_convention,
    representative_grid_box_distance,
)
from .ke_spectra import (  # noqa
    compute_ke_spectra,
    compute_ke_spectra_timeseries,
    eddy_scale,
    wavenumber_from_eddy_scale,
)
from .plot import plot_resolution_scatter, plot_spectra_and_slope  # noqa
from .spectral_slope import (  # noqa
    detect_steepening,
    fit_spectral_slope,
    reference_steepening_line,
)
from .spherical_harmonics import (  # noqa
    EARTH_RADIUS,
    available_backends,
    normalized_legendre,
    parseval_check,
    resolve_backend,
    scalar_sh_analysis,
    sum_over_m,
    vrtdiv_spectral_coefficients,
)

__all__ = [
    # Primary public API
    "compute_effective_resolution",
    "process_effective_resolution",
    "SPECTRUM_KEYS",
    # Spectra
    "compute_ke_spectra",
    "compute_ke_spectra_timeseries",
    "eddy_scale",
    "wavenumber_from_eddy_scale",
    # Slope and detection
    "fit_spectral_slope",
    "detect_steepening",
    "reference_steepening_line",
    # Grid distance
    "representative_grid_box_distance",
    "grid_box_distance_from_dataset",
    "ratio_to_dx_convention",
    # Spherical harmonics
    "vrtdiv_spectral_coefficients",
    "available_backends",
    "resolve_backend",
    "sum_over_m",
    "scalar_sh_analysis",
    "normalized_legendre",
    "parseval_check",
    "EARTH_RADIUS",
    # Plotting
    "plot_spectra_and_slope",
    "plot_resolution_scatter",
]
