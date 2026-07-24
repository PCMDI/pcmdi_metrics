# Variability Mode Standard API

This document describes the new standard API for computing climate variability modes in PMP.

## Overview

The new API provides a simple, standardized interface for computing variability modes (NAO, NAM, SAM, PNA, NPO, PDO, NPGO, AMO) using xarray datasets. Each mode is accessible as a simple function that returns diagnostics and metrics as Python dictionaries.

## Key Features

- **Simple function-based API**: Each mode (NAO, NAM, etc.) is a standalone function
- **No file I/O**: Functions take xarray datasets as input and return Python dicts
- **Optional metrics**: Provide reference dataset to compute comparison metrics
- **Flexible**: Support for EOF and CBF methods, custom seasons, time subsetting
- **Non-invasive**: Does not modify any existing computation code or driver scripts

## Available Functions

| Function | Mode Name | Variable | EOF # | Domain | Default Season |
|----------|-----------|----------|-------|--------|----------------|
| `NAO()` | North Atlantic Oscillation | psl | 1 | 20-80N, 90W-40E | DJF, MAM, JJA, SON |
| `NAM()` | Northern Annular Mode | psl | 1 | 20-90N, 180W-180E | DJF, MAM, JJA, SON |
| `SAM()` | Southern Annular Mode | psl | 1 | 90S-20S, 0-360E | DJF, MAM, JJA, SON |
| `PNA()` | Pacific North American | psl | 1 | 20-85N, 120-240E | DJF, MAM, JJA, SON |
| `NPO()` | North Pacific Oscillation | psl | 2 | 20-85N, 120-240E | DJF, MAM, JJA, SON |
| `PSA1()` | Pacific-South American Pattern 1 | psl | 2 | 90S-20S, 0-360E | DJF, MAM, JJA, SON |
| `PSA2()` | Pacific-South American Pattern 2 | psl | 3 | 90S-20S, 0-360E | DJF, MAM, JJA, SON |
| `PDO()` | Pacific Decadal Oscillation | ts | 1 | 20-70N, 110-260E | **monthly** |
| `NPGO()` | North Pacific Gyre Oscillation | ts | 2 | 20-70N, 110-260E | **monthly** |
| `AMO()` | Atlantic Multidecadal Oscillation | ts | 1 | 0-70N, 80W-0E | **yearly** |

## Basic Usage

### Import

```python
from pcmdi_metrics.variability_mode import (
    NAO, NAM, SAM, PNA, NPO, PSA1, PSA2,
    PDO, NPGO, AMO
)
import xarray as xr
```

### Simple Example (EOF only, no metrics)

```python
# Load model data
model_ds = xr.open_dataset('model_psl.nc')

# Compute NAO for all seasons
results = NAO(model_ds)

# Access diagnostics
print(f"DJF variance fraction: {results['DJF']['diagnostics']['frac']}")
print(f"DJF PC stdv: {results['DJF']['diagnostics']['stdv_pc']}")

# Access EOF pattern and PC time series
eof_pattern = results['DJF']['diagnostics']['eof_pattern']
pc_timeseries = results['DJF']['diagnostics']['pc_timeseries']
```

### With Reference Data (includes metrics)

```python
# Load model and reference data
model_ds = xr.open_dataset('model_psl.nc')
obs_ds = xr.open_dataset('obs_psl.nc')

# Compute NAM with metrics
results = NAM(model_ds, reference_ds=obs_ds)

# Access metrics
print(f"DJF correlation: {results['DJF']['metrics']['cor']}")
print(f"DJF RMS error: {results['DJF']['metrics']['rms']}")
print(f"DJF bias: {results['DJF']['metrics']['bias']}")
```

### Specific Seasons

```python
# Compute only winter (DJF) and summer (JJA)
results = SAM(model_ds, seasons=['DJF', 'JJA'])

# Only winter
results = PNA(model_ds, seasons=['DJF'])
```

### Time Subsetting

```python
# Analyze specific time period
results = NAO(model_ds, start_year=1950, end_year=2000)
```

### CBF Method

```python
# Use Common Basis Function approach (requires reference data)
results = NAM(model_ds, reference_ds=obs_ds, method='cbf')

# Access CBF pattern
cbf_pattern = results['DJF']['diagnostics']['cbf_pattern']
```

### SST-based Modes

```python
# Load SST data (variable named 'ts')
model_sst = xr.open_dataset('model_ts.nc')
obs_sst = xr.open_dataset('obs_ts.nc')

# Compute PDO (defaults to monthly analysis)
results = PDO(model_sst, data_var='ts', reference_ds=obs_sst)
print(results['monthly']['diagnostics']['frac'])

# Compute NPGO (2nd EOF, defaults to monthly analysis)
results = NPGO(model_sst, data_var='ts')
print(results['monthly']['diagnostics']['frac'])

# Compute AMO (defaults to yearly analysis)
results = AMO(model_sst, data_var='ts')
print(results['yearly']['diagnostics']['frac'])

# You can override defaults if needed
results = PDO(model_sst, seasons=['DJF', 'JJA'])  # Compute specific seasons instead
```

## Function Parameters

All functions share the same signature:

```python
def MODE_NAME(
    model_ds: xr.Dataset,
    data_var: str = 'psl' or 'ts',  # default depends on mode
    seasons: List[str] = ['DJF', 'MAM', 'JJA', 'SON'],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = 'eof',
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict
```

### Parameters

- **model_ds** (required): xarray Dataset containing the variable to analyze
- **data_var** (optional): Variable name in the dataset
  - Default: `'psl'` for atmospheric modes (NAO, NAM, SAM, PNA, NPO)
  - Default: `'ts'` for SST-based modes (PDO, NPGO, AMO)
- **seasons** (optional): List of seasons to compute
  - Default for atmospheric modes: `['DJF', 'MAM', 'JJA', 'SON']` (all four seasons)
  - Default for PDO, NPGO: `['monthly']` (monthly analysis)
  - Default for AMO: `['yearly']` (yearly analysis)
  - Valid values: `'DJF'`, `'MAM'`, `'JJA'`, `'SON'`, `'monthly'`, `'yearly'`
- **reference_ds** (optional): xarray Dataset for reference/observational data
  - If provided, metrics will be computed
  - Required for `method='cbf'`
- **method** (optional): Analysis method
  - `'eof'` (default): Standard EOF analysis
  - `'cbf'`: Common Basis Function (requires reference_ds)
- **start_year** (optional): Start year for time subsetting
  - Default: None (use all available data)
- **end_year** (optional): End year for time subsetting
  - Default: None (use all available data)

## Return Structure

The function returns a nested dictionary:

```python
{
    'SEASON': {
        'diagnostics': {
            'eof_pattern': xr.DataArray,      # EOF spatial pattern
            'pc_timeseries': xr.DataArray,    # PC time series
            'frac': float,                     # Variance fraction
            'stdv_pc': float,                  # PC standard deviation
            # If method='cbf':
            'cbf_pattern': xr.DataArray,      # CBF spatial pattern
        },
        'metrics': {  # Only present if reference_ds provided
            'frac': float,
            'stdv_pc': float,
            'mean': float,
            'mean_glo': float,
            'cor': float,                      # Spatial correlation
            'cor_glo': float,                  # Global correlation
            'rms': float,                      # RMS error
            'rms_glo': float,                  # Global RMS error
            'rmsc': float,                     # Centered RMS error
            'rmsc_glo': float,                 # Global centered RMS error
            'bias': float,                     # Bias
            'bias_glo': float,                 # Global bias
            'stdv_pc_ratio_to_obs': float,    # PC stdv ratio
        }
    },
    # ... for each season
}
```

## Input Data Requirements

### Dataset Structure

- Must be an xarray Dataset
- Must contain the specified variable (`psl` or `ts`)
- Must have dimensions: time, latitude, longitude
- Should follow CF conventions for coordinate names

### Variable Requirements

- **Atmospheric modes** (NAO, NAM, SAM, PNA, NPO): Sea level pressure (`psl`)
- **SST-based modes** (PDO, NPGO, AMO): Sea surface temperature (`ts`)

### Time Coordinate

- Must have a time coordinate named `'time'` or `'TIME'`
- Should have proper date/time encoding for year extraction

## Implementation Notes

### Non-Invasive Design

The API is implemented as a thin wrapper layer in `pcmdi_metrics/variability_mode/api.py`. It:

- **Does not modify** any existing computation code in `lib/`
- **Does not alter** the driver script (`variability_modes_driver.py`)
- **Reuses** all existing functions from `lib/`
- **Maintains** backward compatibility with existing workflows

### Mode Configuration

EOF numbers and regions are automatically determined based on the mode:

- **EOF1 modes**: NAO, NAM, SAM, PNA, PDO, AMO
- **EOF2 modes**: NPO, NPGO, PSA1
- **EOF3 modes**: PSA2

Regions are loaded from `pcmdi_metrics.io.regions.load_regions_specs()`.

### Computation Flow

For each season, the function:

1. Adjusts timeseries (removes annual cycle, domain mean)
2. Extracts subdomain based on mode
3. Performs EOF analysis
4. Computes PC statistics
5. Linear regression for teleconnection pattern
6. If reference provided:
   - Repeats steps 1-5 for reference data
   - If method='cbf': projects onto reference EOFs
   - Computes comparison metrics

## Relationship to Driver Script

The new API and the existing driver script are **completely independent**:

| Feature | API Functions | Driver Script |
|---------|---------------|---------------|
| Input | xarray Datasets | File paths (from parameter file) |
| Output | Python dicts | NetCDF + JSON + PNG files |
| Configuration | Function parameters | Parameter file |
| Use case | Programmatic/notebook | Command-line batch processing |
| File I/O | None (user handles) | Built-in |

Users can choose the interface that best fits their workflow. The driver script continues to work exactly as before.

## Examples

### Example 1: Compare Multiple Models

```python
import xarray as xr
from pcmdi_metrics.variability_mode import NAO

# Load reference
obs_ds = xr.open_dataset('obs_psl.nc')

# Compare multiple models
models = ['model1.nc', 'model2.nc', 'model3.nc']
results_all = {}

for model_file in models:
    model_ds = xr.open_dataset(model_file)
    results_all[model_file] = NAO(model_ds, reference_ds=obs_ds, seasons=['DJF'])

# Extract correlations
for model, results in results_all.items():
    cor = results['DJF']['metrics']['cor']
    print(f"{model}: correlation = {cor:.3f}")
```

### Example 2: Time Series Analysis

```python
from pcmdi_metrics.variability_mode import SAM

# Compute SAM for different periods
periods = [(1900, 1950), (1950, 2000), (2000, 2020)]
results_periods = {}

for start, end in periods:
    results = SAM(model_ds, start_year=start, end_year=end, seasons=['DJF'])
    results_periods[f"{start}-{end}"] = results

# Compare variance fractions across periods
for period, results in results_periods.items():
    frac = results['DJF']['diagnostics']['frac']
    print(f"{period}: variance fraction = {frac:.3f}")
```

### Example 3: Plotting

```python
import matplotlib.pyplot as plt
from pcmdi_metrics.variability_mode import NAM

# Compute NAM
results = NAM(model_ds, reference_ds=obs_ds, seasons=['DJF'])

# Plot EOF pattern
eof = results['DJF']['diagnostics']['eof_pattern']
eof.plot(figsize=(12, 6))
plt.title('NAM EOF1 Pattern (DJF)')
plt.savefig('nam_eof_pattern.png')

# Plot PC time series
pc = results['DJF']['diagnostics']['pc_timeseries']
pc.plot()
plt.title('NAM PC1 Time Series (DJF)')
plt.savefig('nam_pc_timeseries.png')
```

## Migration from Driver Script

If you're currently using the driver script, you can transition to the API:

**Before (driver script):**
```python
# Run from command line
variability_modes_driver.py -p my_param.py
```

**After (API):**
```python
import xarray as xr
from pcmdi_metrics.variability_mode import NAM

# Load data
model_ds = xr.open_dataset('model_psl.nc')
obs_ds = xr.open_dataset('obs_psl.nc')

# Compute
results = NAM(
    model_ds,
    reference_ds=obs_ds,
    seasons=['DJF'],
    start_year=1900,
    end_year=2005,
)

# Save if needed
import json
with open('results.json', 'w') as f:
    json.dump(results['DJF']['metrics'], f, indent=2)

# Save EOF pattern
results['DJF']['diagnostics']['eof_pattern'].to_netcdf('nam_eof_djf.nc')
```

## Future Enhancements

Potential additions for future versions:

- [ ] Domain/region specification parameters
- [ ] Detrending options
- [ ] Regridding options
- [ ] Land mask options
- [ ] Additional preprocessing flags
- [ ] Support for PSA1, PSA2 modes

## Questions or Issues

For questions or to report issues with the API:
- GitHub: https://github.com/PCMDI/pcmdi_metrics/issues
- Email: pcmdi-metrics@llnl.gov

## References

Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019:
Quantifying the Agreement Between Observed and Simulated Extratropical Modes of
Interannual Variability. Climate Dynamics.
https://doi.org/10.1007/s00382-018-4355-4
