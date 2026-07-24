# Reused Utilities in Variability Mode API

This document lists all utilities from `pcmdi_metrics.io` and `pcmdi_metrics.utils` that are reused in the new API implementation.

## Overview

The API implementation (`api.py`) is designed to maximize code reuse from existing PMP utilities. Rather than implementing custom logic, it leverages well-tested functions from the `io` and `utils` modules, as well as computation functions from `variability_mode.lib`.

## Utilities from `pcmdi_metrics.io`

### Used in api.py

1. **`get_grid(ds)`**
   - **Source**: `pcmdi_metrics.io.xcdat_dataset_io`
   - **Purpose**: Extract grid information from dataset
   - **Used for**: Getting reference grid for regridding in CBF method
   - **Location in api.py**: Line ~210 (`ref_grid_global = get_grid(reference_ds)`)

2. **`get_time_key(ds)`**
   - **Source**: `pcmdi_metrics.io.xcdat_dataset_io`
   - **Purpose**: Robustly find the time coordinate key name
   - **Used for**: Time subsetting validation in `_subset_time_range()`
   - **Benefits**: Handles variations like 'time', 'TIME', etc.
   - **Location in api.py**: Line ~104 in `_subset_time_range()`

3. **`load_regions_specs()`**
   - **Source**: `pcmdi_metrics.io.regions`
   - **Purpose**: Load predefined geographic region specifications
   - **Used for**: Get domain specifications for each variability mode
   - **Returns**: Dictionary with region domains (lat/lon bounds)
   - **Location in api.py**: Line ~220 (`regions_specs = load_regions_specs()`)

4. **`region_subset(ds, region, regions_specs)`**
   - **Source**: `pcmdi_metrics.io.regions`
   - **Purpose**: Subset dataset by geographic region
   - **Used for**: Extract mode-specific domain (e.g., NAO domain: 20-80N, 90W-40E)
   - **Handles**: Longitude convention conversion (0-360 vs -180-180)
   - **Location in api.py**: Multiple locations in computation loop

### Available but not yet used

These utilities are available and could be added in future enhancements:

- **`select_subset(ds, lat, lon, time)`** - Alternative subsetting approach
- **`get_latitude(ds)`, `get_longitude(ds)`** - Get coordinate arrays
- **`da_to_ds(da, var)`** - Convert DataArray to Dataset (if we want to support DataArray input)

## Utilities from `pcmdi_metrics.utils`

### Used in api.py

1. **`regrid(ds, data_var, target_grid, regrid_tool, ...)`**
   - **Source**: `pcmdi_metrics.utils.grid`
   - **Purpose**: Regrid dataset to target grid
   - **Used for**: CBF method (regrid model to reference grid)
   - **Supports**: Multiple regridding tools (regrid2, xesmf, etc.)
   - **Location in api.py**: Line ~310 in CBF computation

### Used in variability_mode.lib (indirectly used by API)

2. **`calculate_grid_area(ds)`**
   - **Source**: `pcmdi_metrics.utils.grid`
   - **Used by**: `eof_analysis_get_variance_mode()` in lib
   - **Purpose**: Calculate grid cell areas for area weighting

3. **`calculate_area_weights(grid_area)`**
   - **Source**: `pcmdi_metrics.utils.grid`
   - **Used by**: `eof_analysis_get_variance_mode()` in lib
   - **Purpose**: Convert grid areas to weights for EOF analysis

4. **`custom_season_departure(ds, data_var, ...)`**
   - **Source**: `pcmdi_metrics.utils.custom_season`
   - **Used by**: `adjust_timeseries()` in lib
   - **Purpose**: Calculate seasonal anomalies

5. **`apply_landmask(ds, ...)`**
   - **Source**: `pcmdi_metrics.utils.land_sea_mask`
   - **Used by**: `read_data_in()` in lib (via driver, not API)
   - **Purpose**: Mask land regions for ocean-only analysis

6. **`check_monthly_time_axis(ds, time_key)`**
   - **Source**: `pcmdi_metrics.utils.qc`
   - **Used by**: `read_data_in()` in lib (via driver, not API)
   - **Purpose**: Validate monthly time axis sequence

### Available for future enhancements

- **`check_daily_time_axis()`** - Validate daily time sequences
- **`find_overlapping_dates()`** - Find common date ranges
- **`create_target_grid()`** - Generate uniform/gaussian grids
- **`apply_oceanmask()`** - Mask land for ocean-only analysis

## Computation Functions from `variability_mode.lib`

All core computation logic comes from existing `lib/` functions:

### Primary Functions

1. **`adjust_timeseries(ds, data_var, mode, season, regions_specs, RmDomainMean)`**
   - Removes annual cycle
   - Extracts seasonal mean
   - Removes domain/global mean
   - **Used**: For both model and reference data preprocessing

2. **`eof_analysis_get_variance_mode(mode, ds, data_var, eofn, ...)`**
   - Performs EOF analysis using `eofs` package
   - Applies area weighting
   - Handles arbitrary sign control
   - **Used**: Core EOF computation for both model and reference

3. **`linear_regression_on_globe_for_teleconnection(pc, ds, data_var, stdv_pc, ...)`**
   - Linear regression of PC onto global field
   - Extends EOF pattern globally for teleconnection analysis
   - **Used**: After EOF analysis to get full global pattern

4. **`calcSTD(pc)`**
   - Calculate standard deviation of PC time series
   - Uses ddof=1 (unbiased estimator)
   - **Used**: For normalizing PC time series

### CBF-Specific Functions

5. **`gain_pseudo_pcs(solver, field, eofn, reverse_sign, EofScaling)`**
   - Projects data onto reference EOFs
   - Generates pseudo-PCs (CBF PCs)
   - **Used**: CBF method only

6. **`gain_pcs_fraction(ds_full, varname_full, ds_eof, varname_eof, pcs)`**
   - Calculates variance fraction explained by CBF
   - **Used**: CBF method only

### Metrics Functions

7. **`calc_stats_save_dict(mode, dict_head, model_ds, eof, pc, ...)`**
   - Computes spatial correlation (cor, cor_glo)
   - Computes RMS error (rms, rms_glo)
   - Computes centered RMS (rmsc, rmsc_glo)
   - Computes bias (bias, bias_glo)
   - Handles automatic sign flipping for EOF method
   - **Used**: When reference_ds is provided

## Import Structure in api.py

```python
# Standard library
from typing import Dict, List, Optional, Union
import xarray as xr

# Import utilities from pcmdi_metrics.io
from pcmdi_metrics.io import (
    get_grid,              # Grid information
    get_time_key,          # Time coordinate name
    load_regions_specs,    # Region definitions
    region_subset,         # Geographic subsetting
)

# Import utilities from pcmdi_metrics.utils
from pcmdi_metrics.utils import regrid  # Regridding

# Import computation functions from variability_mode.lib
from pcmdi_metrics.variability_mode.lib import (
    adjust_timeseries,                              # Preprocessing
    calc_stats_save_dict,                           # Metrics
    calcSTD,                                        # Statistics
    eof_analysis_get_variance_mode,                # EOF analysis
    gain_pcs_fraction,                              # CBF variance
    gain_pseudo_pcs,                                # CBF projection
    linear_regression_on_globe_for_teleconnection,  # Teleconnection
)
```

## Utilities NOT Reimplemented

The following were **NOT** reimplemented in api.py because they already exist:

- ✅ Coordinate name handling → Use `get_time_key()`, `get_latitude_key()`, etc.
- ✅ Geographic subsetting → Use `region_subset()`
- ✅ Grid information → Use `get_grid()`
- ✅ Regridding → Use `regrid()`
- ✅ EOF analysis → Use `eof_analysis_get_variance_mode()`
- ✅ CBF computation → Use `gain_pseudo_pcs()`, `gain_pcs_fraction()`
- ✅ Metrics calculation → Use `calc_stats_save_dict()`
- ✅ Time series preprocessing → Use `adjust_timeseries()`

## Code Statistics

### api.py Breakdown
- **Total lines**: ~850
- **Import statements**: 40 lines (reusing existing code)
- **Helper functions**: 50 lines (validation, time subsetting)
- **Core computation**: 250 lines (orchestration, calling lib functions)
- **Public API functions**: 500 lines (8 functions × ~60 lines each, mostly docstrings)

### Code Reuse Ratio
- **New logic**: ~100 lines (validation + time subsetting helper)
- **Reused utilities**: All core computation from `lib/`, `io/`, and `utils/`
- **Reuse ratio**: >90% of functionality comes from existing code

## Benefits of Reusing Utilities

### 1. Consistency
- Same behavior as driver script (uses same lib functions)
- Same coordinate handling as other PMP metrics
- Same regridding approach throughout PMP

### 2. Maintainability
- Bug fixes in utilities automatically benefit API
- No duplicate code to maintain
- Single source of truth for each operation

### 3. Reliability
- Well-tested utilities (used by driver script for years)
- Edge cases already handled
- Consistent error handling

### 4. Performance
- Optimized implementations (e.g., area-weighted EOF)
- No redundant computations
- Efficient regridding via established tools

### 5. Standards Compliance
- CF conventions handled by existing utilities
- Consistent with CMIP data standards
- Proper handling of calendars, bounds, etc.

## Future Enhancement Opportunities

The modular design allows easy integration of additional utilities:

1. **Input validation**: Add `check_monthly_time_axis()` for time axis validation
2. **Date handling**: Use `find_overlapping_dates()` for automatic time range detection
3. **Custom regions**: Expose `region_from_file()` for user-defined regions
4. **Land masking**: Add `apply_landmask()` as optional parameter
5. **Custom grids**: Allow `create_target_grid()` for custom regridding

These can be added without modifying existing lib functions.

## Conclusion

The API implementation achieves its goal of providing a simple, user-friendly interface while:
- Reusing >90% of existing functionality
- Maintaining consistency with driver script
- Following DRY (Don't Repeat Yourself) principle
- Ensuring backward compatibility
- Providing same scientific results

**No computation code was modified or duplicated** - the API is purely a reorganization layer on top of existing, well-tested utilities.
