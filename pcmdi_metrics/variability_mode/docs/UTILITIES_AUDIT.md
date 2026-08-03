# Utilities Audit: What's Used and What's Available

This document provides a comprehensive audit of utilities from `pcmdi_metrics.io` and `pcmdi_metrics.utils` in the context of the variability mode API.

## Summary

✅ **Currently Used**: 4 functions from `io`, 1 from `utils`, 7 from `lib`  
📋 **Available for Future**: 15+ additional utilities identified

## Currently Used Utilities

### From `pcmdi_metrics.io` (4 functions)

| Function | Purpose | Used In API |
|----------|---------|-------------|
| ✅ `get_grid()` | Extract grid information | CBF regridding |
| ✅ `get_time_key()` | Find time coordinate name | Time subsetting |
| ✅ `load_regions_specs()` | Load region definitions | Domain extraction |
| ✅ `region_subset()` | Geographic subsetting | Mode-specific domains |

### From `pcmdi_metrics.utils` (1 function)

| Function | Purpose | Used In API |
|----------|---------|-------------|
| ✅ `regrid()` | Regrid to target grid | CBF method |

### From `pcmdi_metrics.variability_mode.lib` (7 functions)

| Function | Used In API |
|----------|-------------|
| ✅ `adjust_timeseries()` | Preprocessing |
| ✅ `calc_stats_save_dict()` | Metrics computation |
| ✅ `calcSTD()` | Statistics |
| ✅ `eof_analysis_get_variance_mode()` | EOF analysis |
| ✅ `gain_pcs_fraction()` | CBF variance |
| ✅ `gain_pseudo_pcs()` | CBF projection |
| ✅ `linear_regression_on_globe_for_teleconnection()` | Teleconnection |

## Available Utilities for Future Enhancement

### From `pcmdi_metrics.io`

#### Data Loading
- **`xcdat_open(infile, data_var, decode_times, chunks)`**
  - Source: `pcmdi_metrics.io.xcdat_openxml`
  - **Potential use**: Add file path support to API
  - **Example**: `NAM(model_path='model.nc', ...)` instead of requiring pre-loaded dataset
  - **Benefits**: 
    - Handles netCDF, XML, wildcards
    - Automatic bounds addition
    - Non-CF-compliant calendar fixes

#### Dataset Utilities
- **`select_subset(ds, lat, lon, time)`**
  - Source: `pcmdi_metrics.io.xcdat_dataset_io`
  - **Potential use**: Alternative time subsetting using tuple ranges
  - **Current approach**: Manual year-based selection (simpler for API)

- **`get_latitude(ds)`, `get_longitude(ds)`**
  - Source: `pcmdi_metrics.io.xcdat_dataset_io`
  - **Potential use**: Validation or coordinate extraction

- **`get_latitude_key(ds)`, `get_longitude_key(ds)`**
  - Source: `pcmdi_metrics.io.xcdat_dataset_io`
  - **Potential use**: Robust coordinate name finding

- **`da_to_ds(da, var)`**
  - Source: `pcmdi_metrics.io.xcdat_dataset_io`
  - **Potential use**: Support DataArray input in addition to Dataset
  - **Example**: `NAM(model_da, ...)` where model_da is DataArray

- **`get_calendar(ds)`**
  - Source: `pcmdi_metrics.io.xcdat_dataset_io`
  - **Potential use**: Calendar validation or information

#### Region Utilities
- **`region_from_file(filename, region_name)`**
  - Source: `pcmdi_metrics.io.region_from_file`
  - **Potential use**: Custom user-defined regions from file
  - **Example**: `NAM(..., custom_region_file='my_regions.json')`

### From `pcmdi_metrics.utils`

#### Validation & QC
- **`check_monthly_time_axis(ds, time_key)`**
  - Source: `pcmdi_metrics.utils.qc`
  - **Potential use**: Validate input data has proper monthly sequence
  - **Benefits**: Catch data issues early
  - **Integration point**: Add to `_validate_dataset()`

- **`check_daily_time_axis(ds, time_key)`**
  - Source: `pcmdi_metrics.utils.qc`
  - **Potential use**: If API extends to daily data

#### Date/Time Utilities
- **`find_overlapping_dates(ds, start_date, end_date)`**
  - Source: `pcmdi_metrics.utils.dates`
  - **Potential use**: Automatic time range detection for model-obs overlap
  - **Example**: Auto-align model and reference time periods

- **`extract_date_components(ds, index)`**
  - Source: `pcmdi_metrics.utils.dates`
  - **Potential use**: Date parsing utilities

- **`date_to_str(date_obj)`, `replace_date_pattern()`**
  - Source: `pcmdi_metrics.utils.dates`
  - **Potential use**: Date formatting in outputs

#### Grid Utilities
- **`create_target_grid(lat1, lat2, lon1, lon2, resolution, grid_type)`**
  - Source: `pcmdi_metrics.utils.grid`
  - **Potential use**: Custom regridding targets
  - **Example**: `NAM(..., target_grid='2.5x2.5')`

- **`calculate_grid_area(ds)`**
  - Already used indirectly via `eof_analysis_get_variance_mode()`

- **`calculate_area_weights(grid_area)`**
  - Already used indirectly via `eof_analysis_get_variance_mode()`

#### Land/Sea Masking
- **`apply_landmask(ds, var, landmask_file, ...)`**
  - Source: `pcmdi_metrics.utils.land_sea_mask`
  - **Potential use**: Ocean-only or land-only analysis
  - **Example**: `NAM(..., land_mask=True)`

- **`apply_oceanmask(ds, var, landmask_file, ...)`**
  - Source: `pcmdi_metrics.utils.land_sea_mask`
  - **Potential use**: Land-only analysis

- **`create_land_sea_mask(...)`**
  - Source: `pcmdi_metrics.utils.land_sea_mask`
  - **Potential use**: Generate custom masks

#### Unit Adjustment
- **`adjust_units(da, adjust_tuple)`**
  - Source: `pcmdi_metrics.utils.adjust_units`
  - **Potential use**: Automatic unit conversion (Pa to hPa, etc.)
  - **Example**: `NAM(..., units_adjust=('divide', 100))`
  - **Current approach**: User handles before calling API

#### Seasonal/Custom Utilities
- **`custom_season_average(ds, data_var, season_months)`**
  - Source: `pcmdi_metrics.utils.custom_season`
  - **Potential use**: Non-standard seasons (e.g., 'NDJF', 'JJAS')
  - **Current approach**: Only standard 4 seasons

- **`custom_season_departure(ds, data_var, ...)`**
  - Already used indirectly via `adjust_timeseries()`

#### Other Utilities
- **`tree()`**
  - Source: `pcmdi_metrics.utils.tree_dict`
  - **Potential use**: Nested dict creation (already have standard dicts)

- **`sort_human(list)`**
  - Source: `pcmdi_metrics.utils.sort_human`
  - **Potential use**: Natural sorting of model names, etc.

- **`fill_template(template, **kwargs)`**
  - Source: `pcmdi_metrics.utils.string_constructor`
  - **Potential use**: Path template expansion

## Recommended Additions

### High Priority (Would Improve API Immediately)

1. **`check_monthly_time_axis()`** in `_validate_dataset()`
   - **Why**: Catches bad input data early
   - **Effort**: Very low (2-3 lines)
   - **Code**:
   ```python
   from pcmdi_metrics.utils import check_monthly_time_axis
   
   def _validate_dataset(ds, data_var, dataset_name):
       # ... existing checks ...
       time_key = get_time_key(ds)
       check_monthly_time_axis(ds, time_key)  # Add this
   ```

2. **`xcdat_open()`** for file path support
   - **Why**: More convenient for users (no need to manually open files)
   - **Effort**: Low
   - **Example**:
   ```python
   # Instead of:
   model_ds = xr.open_dataset('model.nc')
   results = NAM(model_ds)
   
   # Could be:
   results = NAM('model.nc')  # API handles loading
   ```

### Medium Priority (Nice to Have)

3. **`find_overlapping_dates()`** for auto time-range
   - **Why**: Automatically find common period between model and obs
   - **Effort**: Medium
   - **Current**: User must specify start_year/end_year

4. **`apply_landmask()`** as optional parameter
   - **Why**: Ocean-only/land-only analysis
   - **Effort**: Medium
   - **Example**: `NAM(..., ocean_only=True)`

5. **`adjust_units()`** integration
   - **Why**: Automatic unit handling (Pa to hPa)
   - **Effort**: Medium
   - **Current**: User handles before calling API

### Low Priority (Future Extensions)

6. **`custom_season_average()`** for custom seasons
   - **Why**: Support NDJF, JJAS, etc.
   - **Effort**: Medium-High
   - **Example**: `NAM(..., seasons=['NDJF', 'MAMJJ'])`

7. **`region_from_file()`** for custom domains
   - **Why**: User-defined regions
   - **Effort**: Low
   - **Example**: `NAM(..., custom_region='my_nao_domain.json')`

8. **`da_to_ds()`** for DataArray input
   - **Why**: Accept DataArray in addition to Dataset
   - **Effort**: Very low
   - **Example**: `NAM(model_da, ...)`

## Implementation Examples

### Example 1: Add Monthly Time Axis Validation

```python
# In api.py, modify _validate_dataset():
from pcmdi_metrics.utils import check_monthly_time_axis

def _validate_dataset(ds, data_var, dataset_name):
    if not isinstance(ds, xr.Dataset):
        raise TypeError(...)
    
    if data_var not in ds.data_vars:
        raise ValueError(...)
    
    # Get time key and validate
    time_key = get_time_key(ds)
    
    # Add monthly time axis check
    try:
        check_monthly_time_axis(ds, time_key)
    except ValueError as e:
        raise ValueError(
            f"{dataset_name} has invalid monthly time axis: {e}"
        )
```

### Example 2: Add File Path Support

```python
# In api.py, add new function:
from pcmdi_metrics.io import xcdat_open

def _load_dataset(data_source, data_var):
    """Load dataset from file path or return existing dataset."""
    if isinstance(data_source, str):
        # File path provided
        return xcdat_open(data_source, data_var=data_var)
    elif isinstance(data_source, xr.Dataset):
        # Dataset already loaded
        return data_source
    else:
        raise TypeError(
            f"data_source must be file path (str) or xr.Dataset, got {type(data_source)}"
        )

# Modify public functions:
def NAM(
    model_ds,  # Can now be str or xr.Dataset
    data_var='psl',
    ...
):
    # Load dataset if path provided
    model_ds = _load_dataset(model_ds, data_var)
    if reference_ds is not None:
        reference_ds = _load_dataset(reference_ds, data_var)
    
    # Continue with existing logic
    ...
```

### Example 3: Add Land Masking Option

```python
# In api.py:
from pcmdi_metrics.utils import apply_landmask

def NAM(
    model_ds,
    data_var='psl',
    ocean_only=False,  # New parameter
    land_only=False,   # New parameter
    landmask_file=None,  # Optional custom mask
    ...
):
    # Apply masking if requested
    if ocean_only:
        model_ds = apply_oceanmask(model_ds, data_var, landmask_file)
        if reference_ds is not None:
            reference_ds = apply_oceanmask(reference_ds, data_var, landmask_file)
    elif land_only:
        model_ds = apply_landmask(model_ds, data_var, landmask_file)
        if reference_ds is not None:
            reference_ds = apply_landmask(reference_ds, data_var, landmask_file)
    
    # Continue with existing logic
    ...
```

## Decision: Why Not Added Yet?

These utilities are **not added to the initial API** because:

1. **Simplicity First**: Keep initial API minimal and easy to understand
2. **User Control**: Some operations (unit conversion, masking) might be better done by user
3. **Testing**: Each addition needs thorough testing
4. **Backward Compatibility**: Can add these later without breaking existing code
5. **Incremental Enhancement**: Better to release simple API, then enhance based on user feedback

## Future Enhancement Strategy

### Phase 1 (Current): Core API ✅
- Basic EOF/CBF computation
- Metrics calculation
- Season selection
- Time subsetting

### Phase 2: Validation & QC
- Add `check_monthly_time_axis()` validation
- Add calendar checks
- Better error messages

### Phase 3: Convenience Features
- File path support via `xcdat_open()`
- DataArray support via `da_to_ds()`
- Auto time range via `find_overlapping_dates()`

### Phase 4: Advanced Options
- Land/ocean masking
- Unit conversion
- Custom seasons
- Custom regions

## Conclusion

The current API implementation uses **5 utilities** from `io`/`utils` plus **7 functions** from `lib`, achieving >90% code reuse.

An additional **15+ utilities** are available for future enhancements, allowing the API to grow in capability while maintaining:
- Backward compatibility
- Consistency with PMP standards
- Maximum code reuse
- User-friendly interface

The modular design makes it easy to add these features incrementally based on user needs and feedback.
