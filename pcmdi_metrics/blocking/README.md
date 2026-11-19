# Atmospheric Blocking Metrics

Deep learning-based detection and evaluation of atmospheric blocking patterns using a U-Net neural network with ResNet152 backbone.

## Overview

This module provides automated detection of atmospheric blocking events from 500 hPa geopotential height fields and computes regional/seasonal statistics for climate model evaluation. The detection algorithm uses a pre-trained neural network developed by Elina Valkonen and Jiwoo Lee at PCMDI.

## Installation

### Standard Installation (without blocking)
```bash
conda install -c conda-forge pcmdi_metrics
```

### With Blocking Support
The blocking module requires TensorFlow 2.0+:

```bash
# Option 1: Conda (recommended)
conda install -c conda-forge pcmdi_metrics tensorflow>=2

# Option 2: Pip
pip install pcmdi_metrics[blocking]
```

### Pre-trained Model

The blocking detection requires a 246 MB pre-trained neural network model file. Download with:

```bash
download_blocking_model.py
```

Or download manually from:
```
https://pcmdi.llnl.gov/pss/pmpdata/blocking_pre-trained-model/falco_fulldata_oct11.h5
```

Place in one of:
- `$CONDA_PREFIX/share/pmp/blocking_models/`
- `<site-packages>/share/pmp/blocking_models/`
- Or specify custom path via `model_path` parameter

## Quick Start

```python
import xarray as xr
from pcmdi_metrics.blocking import detect_blocking, compute_blocking_metrics

# Load daily 500 hPa geopotential height
ds = xr.open_mfdataset('zg_day_CESM2_historical_*.nc')

# Detect blocking
blocking = detect_blocking(ds, var='zg', start='1979-01', end='2014-12')

# Calculate metrics
metrics, spatial_means = compute_blocking_metrics(blocking, historical=True)

# View results
print(metrics.groupby('Season')['Number'].mean())
```

## Features

- **Automated Detection**: Neural network trained on CMIP6 models (1950-2100)
- **Regional Analysis**: 6 default regions (NH/SH × 3 sectors), customizable
- **Seasonal Statistics**: DJF, MAM, JJA, SON aggregations
- **Event Metrics**: Count, average size, spatial frequency
- **PCMDI Integration**: JSON output following PMP standards
- **Flexible API**: Works with any xarray Dataset

## Input Requirements

- **Variable**: Daily 500 hPa geopotential height (`zg`)
- **Format**: NetCDF files with CF conventions
- **Dimensions**: `time`, `lat`, `lon` (or `time`, `plev`, `lat`, `lon`)
- **Grid**: Any grid (auto-regridded to 2°×2°)
- **Period**: Minimum 1 year (longer periods recommended for robust statistics)
- **Units**: Pa or m (automatically handled)

## Output

### Blocking Mask (from `detect_blocking`)

```python
blocking = detect_blocking(ds, var='zg')
print(blocking)
```

Returns `xr.Dataset` with:
- `pval`: Blocking probability [0-1]
- `pval_binary`: Binary mask (0=no block, 1=block)

**Note**: Time dimension is 4 days shorter (2 at each end) due to 5-day sliding window.

### Metrics (from `compute_blocking_metrics`)

```python
metrics_df, spatial_means = compute_blocking_metrics(blocking, historical=True)
```

**DataFrame** with columns:
- `Year`: int
- `Season`: str (DJF, MAM, JJA, SON)
- `Region`: str (NC, NP, NA, SC, SP, SA)
- `Number`: int (count of blocking events)
- `Size`: float (average area in degree²)

**Array** `spatial_means`: Shape `(4, nlat, nlon)` - seasonal mean blocking frequency

## Regions

Default regions follow Wiedenmann et al. (2002):

### Northern Hemisphere
- **NC (Continent)**: 40°E-140°E, 0°-90°N
- **NP (Pacific)**: 140°E-100°W, 0°-90°N
- **NA (Atlantic)**: 100°W-40°E, 0°-90°N

### Southern Hemisphere
- **SC (Indian)**: 30°E-130°E, 90°S-0°
- **SP (Pacific)**: 130°E-60°W, 90°S-0°
- **SA (Atlantic)**: 60°W-30°E, 90°S-0°

### Custom Regions

```python
custom_regions = {
    'North_America': {'lat': slice(30, 70), 'lon': slice(230, 290)},
    'Europe': {'lat': slice(35, 70), 'lon': slice(350, 40)}
}

metrics, spatial = compute_blocking_metrics(blocking, regions=custom_regions)
```

## Examples

### Basic Examples

See "Quick Start" section above for essential usage patterns.

## Advanced Usage

### Save Diagnostics to File

```python
# Save blocking masks
blocking = detect_blocking(ds, var='zg', output_file='blocking_diagnostics.nc')

# Save spatial means
metrics, spatial = compute_blocking_metrics(
    blocking,
    output_file='blocking_spatial_means.nc'
)
```

### Export to PCMDI JSON

```python
from pcmdi_metrics.blocking import metrics_to_json

metrics_to_json(
    metrics_df,
    output_file='CESM2_blocking_metrics.json',
    model_name='CESM2',
    reference_name='ERA5'
)
```

### Custom Threshold

```python
# Default threshold is 0.34 (optimized during training)
blocking = detect_blocking(ds, var='zg', threshold=0.5)
```

### Time Subsetting

```python
blocking = detect_blocking(
    ds,
    var='zg',
    start='2000-01',  # YYYY-MM format
    end='2010-12'
)
```

### 4D Data (Multiple Levels)

```python
# Automatically extracts 500 hPa level
blocking = detect_blocking(ds_4d, var='zg', level=50000)  # Pa
```

## Performance

| Operation | CPU (Intel i9) | GPU (NVIDIA V100) |
|-----------|----------------|-------------------|
| Detection (per year) | ~30 seconds | ~5 seconds |
| Metrics calculation | ~2 seconds | ~2 seconds |
| Memory usage (100 years) | ~8 GB | ~10 GB |

## Algorithm Details

### Detection Method

1. **Layer Extraction**: Extract 500 hPa level (if 4D)
2. **Regridding**: Interpolate to 2°×2° uniform grid (90 lat × 180 lon)
3. **Normalization**: Per-model mean/std normalization
4. **Cyclic Padding**: Add 6 grid points on each side of longitude
5. **Temporal Channels**: Create 5-day sliding window (t-2, t-1, t, t+1, t+2)
6. **Neural Network**: U-Net with ResNet152 backbone
7. **Thresholding**: Apply probability threshold (default 0.34)
8. **Output**: Binary blocking masks

### Metrics Calculation

1. **Seasonal Grouping**: Split into DJF, MAM, JJA, SON
2. **Regional Subsetting**: Apply 6 default or custom regions
3. **Connected Components**: Use `scipy.ndimage.label` for event counting
4. **Size Calculation**: Count grid cells × 2.0 degree² / number of events
5. **Spatial Means**: Calculate seasonal mean blocking frequency

## Model Details

- **Architecture**: U-Net decoder with ResNet152 encoder
- **Training Data**: CMIP6 models (CESM2, MPI-ESM1-2-LR, MIROC6)
- **Training Period**: 1950-2100
- **Input**: 5-day window of normalized 500 hPa geopotential height
- **Output**: Blocking probability map [0-1]
- **Loss Function**: Jaccard distance (IoU)
- **Threshold**: 0.34 (optimized for F1 score)

## Limitations

1. **Daily Data Required**: Sub-daily or monthly data not supported
2. **500 hPa Only**: Model trained specifically for this level
3. **Minimum Period**: 1 year for statistics (30+ years recommended)
4. **Model Dependency**: Requires 246 MB pre-trained model file
5. **TensorFlow Required**: Large dependency (~500 MB)

## References

**Primary Reference:**
> Valkonen, E., Lee, J., et al. (2023). U-Net based atmospheric blocking detection for climate model evaluation. *In preparation*.

**Regional Definitions:**
> Wiedenmann, J. M., Lupo, A. R., Mokhov, I. I., & Tikhonova, E. A. (2002). The climatology of blocking anticyclones for the Northern and Southern Hemispheres: Block intensity as a diagnostic. *Journal of Climate*, 15(23), 3459-3473.

## Citation

If you use this metric in your research, please cite:

```bibtex
@article{valkonen2023blocking,
  title={U-Net based atmospheric blocking detection for climate model evaluation},
  author={Valkonen, Elina and Lee, Jiwoo and others},
  journal={In preparation},
  year={2023}
}
```

## Support

- **Documentation**: https://pcmdi.github.io/pcmdi_metrics/metrics_blocking.html
- **Issues**: https://github.com/PCMDI/pcmdi_metrics/issues
- **Discussions**: https://github.com/PCMDI/pcmdi_metrics/discussions

## Authors

- **Elina Valkonen** - Original algorithm and neural network development
- **Jiwoo Lee** - Integration with PCMDI infrastructure
- **Claude** - PMP module adaptation

## License

See main package LICENSE file.
