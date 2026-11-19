# Blocking Detection Pre-Trained Model

The atmospheric blocking detection requires a pre-trained neural network model that is not included in the package due to its size (246 MB).

## Quick Download

### Automatic (Recommended)

```bash
download_blocking_model.py
```

This will download the model to the default location where the blocking detection will find it automatically.

### Manual Download

Download from:
```
https://pcmdi.llnl.gov/pss/pmpdata/blocking_pre-trained-model/falco_fulldata_oct11.h5
```

Place the file in one of these locations (in order of preference):

1. **Conda environment** (if using conda):
   ```
   $CONDA_PREFIX/share/pmp/blocking_models/falco_fulldata_oct11.h5
   ```

2. **Package share directory**:
   ```
   <site-packages>/share/pmp/blocking_models/falco_fulldata_oct11.h5
   ```

3. **User home directory**:
   ```
   ~/.pcmdi_metrics/blocking_models/falco_fulldata_oct11.h5
   ```

4. **Custom path** (specify explicitly):
   ```python
   detect_blocking(ds, model_path='/path/to/falco_fulldata_oct11.h5')
   ```

## Model Details

### Architecture
- **Type**: U-Net with ResNet152 backbone
- **Input**: 5-day window of 500 hPa geopotential height (normalized)
- **Input shape**: (time, 90, 192, 5) where 192 includes cyclic padding
- **Output**: Blocking probability map [0-1]
- **Output shape**: (time, 90, 192)

### Training Data
- **Models**: CMIP6 (CESM2, MPI-ESM1-2-LR, MIROC6)
- **Period**: 1950-2100
- **Variable**: Daily 500 hPa geopotential height (zg)
- **Grid**: 2°×2° uniform (90 lat × 180 lon)

### Performance
- **Loss function**: Jaccard distance (IoU)
- **Threshold**: 0.34 (optimized for F1 score)
- **Training**: Supervised learning with expert-labeled blocking events

### File Information
- **Filename**: `falco_fulldata_oct11.h5`
- **Size**: 246 MB
- **Format**: HDF5 (Keras model)
- **Version**: October 2023
- **Checksum**: MD5 (verify after download if needed)

## Verification

After downloading, verify the model loads correctly:

```python
from pcmdi_metrics.blocking import detect_blocking
import xarray as xr

# Create sample data
ds = xr.Dataset({
    'zg': (['time', 'lat', 'lon'], 
           np.random.randn(10, 90, 180) * 100 + 5500)
})

# Test detection (will fail if model not found)
try:
    blocking = detect_blocking(ds, var='zg', verbose=True)
    print("✓ Model loaded successfully!")
except FileNotFoundError as e:
    print(f"✗ Model not found: {e}")
```

## Troubleshooting

### Model Not Found Error

If you see:
```
FileNotFoundError: Pre-trained blocking detection model not found.
```

**Solution**:
1. Run `download_blocking_model.py`
2. Or download manually and place in one of the locations listed above
3. Or specify path explicitly: `detect_blocking(ds, model_path='/path/to/model.h5')`

### Download Issues

If automatic download fails:

1. **Check internet connection**
2. **Check firewall settings** (ensure https://pcmdi.llnl.gov is accessible)
3. **Download manually** with curl or wget:
   ```bash
   wget https://pcmdi.llnl.gov/pss/pmpdata/blocking_pre-trained-model/falco_fulldata_oct11.h5
   ```
   Or:
   ```bash
   curl -O https://pcmdi.llnl.gov/pss/pmpdata/blocking_pre-trained-model/falco_fulldata_oct11.h5
   ```

### File Size Verification

Expected file size: ~246 MB

Check with:
```bash
ls -lh falco_fulldata_oct11.h5
```

If size differs significantly, re-download the file.

## Custom Models

You can use custom-trained models by specifying the path:

```python
blocking = detect_blocking(
    ds,
    var='zg',
    model_path='/path/to/custom_model.h5'
)
```

**Requirements for custom models**:
- Must be a Keras HDF5 model
- Must use the same input/output format
- Must include `jaccard_distance` loss function

## Version History

- **oct11 (October 2023)**: Initial release
  - Trained on CMIP6 historical and scenario runs
  - Optimized threshold: 0.34
  - ResNet152 encoder + U-Net decoder

## References

**Model Development**:
> Valkonen, E., Lee, J., et al. (2023). U-Net based atmospheric blocking detection for climate model evaluation. *In preparation*.

**Training Methodology**:
- Supervised learning with expert-labeled events
- Data augmentation: temporal shifts, spatial flips
- Validation: Cross-model validation (leave-one-out)

## Support

For issues with model download or usage:
- **Issues**: https://github.com/PCMDI/pcmdi_metrics/issues
- **Discussions**: https://github.com/PCMDI/pcmdi_metrics/discussions
- **Email**: pcmdi-metrics@llnl.gov
