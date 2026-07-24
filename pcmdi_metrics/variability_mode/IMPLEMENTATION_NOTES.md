# Implementation Notes: Variability Mode API

This document describes how the new API leverages existing utilities from `pcmdi_metrics.io` and `pcmdi_metrics.utils`.

## Design Principle

The API implementation follows the principle of **code reuse** - it does not reinvent the wheel but instead leverages existing, well-tested utilities from the pcmdi_metrics package.

## Utilities Used

### From `pcmdi_metrics.io`

The API uses the following functions from the `io` module:

| Function | Purpose | Used In |
|----------|---------|---------|
| `get_grid()` | Extract grid information from dataset | Getting reference grid for regridding |
| `get_time_key()` | Robustly find time coordinate name | Time subsetting validation |
| `load_regions_specs()` | Load predefined geographic regions | Get domain for each variability mode |
| `region_subset()` | Subset dataset by geographic region | Extract mode-specific domain |

These utilities handle variations in coordinate naming conventions (e.g., 'time' vs 'TIME', 'lat' vs 'latitude') and provide robust dataset operations.

### From `pcmdi_metrics.utils`

| Function | Purpose | Used In |
|----------|---------|---------|
| `regrid()` | Regrid dataset to target grid | CBF method (regrid to reference grid) |

### From `pcmdi_metrics.variability_mode.lib`

The API directly calls computation functions from the existing `lib` module:

| Function | Purpose | Where Used |
|----------|---------|------------|
| `adjust_timeseries()` | Remove annual cycle and domain mean | Preprocessing both model and reference data |
| `eof_analysis_get_variance_mode()` | Perform EOF analysis | Core EOF computation |
| `calcSTD()` | Calculate standard deviation | PC time series statistics |
| `linear_regression_on_globe_for_teleconnection()` | Linear regression for global pattern | Extend EOF pattern globally |
| `gain_pseudo_pcs()` | Project onto reference EOFs | CBF method |
| `gain_pcs_fraction()` | Calculate variance fraction | CBF variance explained |
| `calc_stats_save_dict()` | Compute comparison metrics | Metrics computation |

## Implementation Structure

```
api.py
├── Mode configuration (_MODE_CONFIG)
│   └── Maps mode names to EOF numbers and expected variables
│
├── Helper functions
│   ├── _validate_dataset()        [NEW] Validates input datasets
│   └── _subset_time_range()       [NEW] Time subsetting using get_time_key()
│
├── Core computation (_compute_variability_mode)
│   ├── Input validation
│   ├── Load regions from load_regions_specs()
│   ├── Time subsetting using _subset_time_range()
│   ├── Reference EOF computation (if provided)
│   │   ├── adjust_timeseries()
│   │   ├── region_subset()
│   │   ├── eof_analysis_get_variance_mode()
│   │   └── linear_regression_on_globe_for_teleconnection()
│   │
│   └── Model processing loop (per season)
│       ├── EOF method:
│       │   ├── adjust_timeseries()
│       │   ├── region_subset()
│       │   ├── eof_analysis_get_variance_mode()
│       │   ├── linear_regression_on_globe_for_teleconnection()
│       │   └── calc_stats_save_dict() [if reference provided]
│       │
│       └── CBF method:
│           ├── regrid() to reference grid
│           ├── region_subset()
│           ├── gain_pseudo_pcs() to project onto reference EOFs
│           ├── linear_regression_on_globe_for_teleconnection()
│           ├── gain_pcs_fraction() for variance explained
│           └── calc_stats_save_dict()
│
└── Public API functions (NAO, NAM, SAM, etc.)
    └── Call _compute_variability_mode() with mode name
```

## Code Reuse Benefits

### 1. Robustness
- Existing utilities handle edge cases (coordinate naming, missing values, etc.)
- Well-tested functions from `io` and `utils` modules
- Consistent behavior with other PMP metrics

### 2. Maintainability
- Changes to utilities automatically propagate to the API
- No duplicate implementations to maintain
- Single source of truth for common operations

### 3. Consistency
- Same coordinate handling as other PMP components
- Same regridding approach as other metrics
- Consistent error messages and behavior

### 4. Minimal New Code
- Only added thin wrapper layer
- Most logic already exists in `lib/`
- No reinvention of existing functionality

## What Was NOT Modified

The implementation maintains **complete backward compatibility**:

- **No changes** to any files in `lib/`
- **No changes** to `variability_modes_driver.py`
- **No changes** to parameter file handling
- **No changes** to existing computation algorithms

The only new files are:
- `api.py` - New API layer
- `__init__.py` - Updated to expose API functions (additive change)
- `API_README.md` - Documentation
- `test_api_example.py` - Examples
- `IMPLEMENTATION_NOTES.md` - This file

## Validation Strategy

The API includes input validation that uses existing utilities:

```python
def _validate_dataset(ds, data_var, dataset_name):
    """Validate dataset using pcmdi_metrics.io utilities."""
    # Type check
    if not isinstance(ds, xr.Dataset):
        raise TypeError(...)
    
    # Variable check
    if data_var not in ds.data_vars:
        raise ValueError(...)
    
    # Time dimension check (uses get_time_key from io)
    try:
        get_time_key(ds)
    except Exception as e:
        raise ValueError(...)
```

This ensures:
- Proper xarray Dataset input
- Required variable exists
- Time dimension present (using `get_time_key` for robustness)

## Future Enhancement Opportunities

The modular design allows easy additions:

1. **Additional validation**: Use `check_monthly_time_axis()` from `pcmdi_metrics.utils.qc`
2. **Time range utilities**: Could use `find_overlapping_dates()` from `pcmdi_metrics.utils.dates`
3. **Land masking**: Could expose `apply_landmask()` from `pcmdi_metrics.utils`
4. **Custom regions**: Could expose `region_from_file()` from `pcmdi_metrics.io`

These can be added as optional parameters without breaking existing API.

## Comparison with Driver Script

| Aspect | API | Driver Script |
|--------|-----|---------------|
| **File I/O** | None (uses utilities indirectly) | Direct file operations |
| **Configuration** | Function parameters | Parameter file |
| **Data Loading** | User's responsibility | Built-in via `read_data_in()` |
| **Region Specs** | Via `load_regions_specs()` | Via `load_regions_specs()` |
| **EOF Analysis** | Via `eof_analysis_get_variance_mode()` | Via `eof_analysis_get_variance_mode()` |
| **Regridding** | Via `pcmdi_metrics.utils.regrid()` | Via `pcmdi_metrics.utils.regrid()` |
| **Statistics** | Via `calc_stats_save_dict()` | Via `calc_stats_save_dict()` |

Both use the same underlying computation functions from `lib/`, ensuring identical results.

## Summary

The API implementation is a **thin wrapper** that:
- ✅ Reuses all existing utilities from `io` and `utils`
- ✅ Calls existing computation functions from `lib/`
- ✅ Adds minimal new code (validation, time subsetting helper)
- ✅ Maintains complete backward compatibility
- ✅ Provides same results as driver script
- ✅ Follows PMP coding standards and patterns

The design prioritizes **code reuse over reinvention**, ensuring consistency with the rest of the PMP package while providing a user-friendly programmatic interface.
