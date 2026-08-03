# QBO-MJO Metric

This module provides functions to compute the QBO-MJO teleconnection metric, which quantifies how Madden-Julian Oscillation (MJO) activity differs between easterly and westerly phases of the stratospheric Quasi-Biennial Oscillation.

## Public API

The two main functions are available at the package level:

```python
from pcmdi_metrics.qbo import compute_qbo_mjo_metrics, process_qbo_mjo_metrics
```

### `compute_qbo_mjo_metrics()`

Pure computation API that accepts already-opened xarray Datasets. Performs no file I/O. Suitable for use in Jupyter notebooks, pipelines, and unit tests.

**Example:**
```python
from pcmdi_metrics.qbo import compute_qbo_mjo_metrics

output, diagnostics = compute_qbo_mjo_metrics(
    ds_u50,           # Monthly zonal wind Dataset
    ds_olr,           # Daily OLR Dataset
    varname="u50",
    varname2="olr",
    start="1979-01",
    end="2010-12",
    model="MyModel",
    member="r1i1p1f1",
)

# output: dict with metrics
# diagnostics: dict with intermediate xarray objects for plotting
```

### `process_qbo_mjo_metrics()`

File-path-based API for driver scripts. Handles file loading, regridding, and writes diagnostic files (NetCDF, PNG, JSON).

**Example:**
```python
from pcmdi_metrics.qbo import process_qbo_mjo_metrics

params = {
    "model": "MyModel",
    "exp": "historical",
    "member": "r1i1p1f1",
    "input_file": "/path/to/ua_monthly.nc",
    "input_file2": "/path/to/olr_daily.nc",
    "varname": "ua",
    "level": 50,
    "varname2": "rlut",
    "start": "1979-01",
    "end": "2010-12",
    "regrid": True,
    "target_grid": "2x2",
    "output_dir": "./output",
}

output = process_qbo_mjo_metrics(params)
```

## Supporting Utilities

Additional utilities for plotting and data processing are available from `pcmdi_metrics.qbo.lib`:

```python
from pcmdi_metrics.qbo.lib import (
    KFfilter,                           # Wheeler-Kiladis filtering
    diag_plot,                          # QBO-MJO diagnostic figure
    test_plot_time_series,              # QBO index time series plot
    test_plot_maps,                     # OLR maps plot
    generate_target_grid,               # Grid generation utility
    select_time_range,                  # Time subsetting utility
    standardize_lat_lon_name_in_dataset, # Coordinate standardization
)
```

## References

- Kim, H., Kim, D., Lee, M.-I., and Zhao, J., 2020: Impact of the QBO on MJO prediction skill in the subseasonal-to-seasonal (S2S) prediction models. *J. Climate*, 33, 4141-4155.
- Son, S.-W., Y. Lim, C. Yoo, H. H. Hendon, and J. Kim, 2017: Stratospheric control of the Madden-Julian oscillation. *J. Climate*, 30, 1909-1922.

## Examples

See:
- `doc/jupyter/Demo/Demo_10_qbo_mjo.ipynb` - Jupyter notebook demonstration
- `pcmdi_metrics/qbo/param/example_qbo_compute.py` - Standalone example script
- `pcmdi_metrics/qbo/param/myParam_qbo.py` - Example parameter file for driver
