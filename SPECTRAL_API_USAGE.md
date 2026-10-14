# Spectral Analysis API Usage

## Overview

Standalone spectral computation functions are now available at the top level for easier access. These functions compute kinetic energy or power spectra without running the full effective resolution diagnostic.

## New Top-Level Imports (v4.3+)

```python
from pcmdi_metrics.effective_resolution import (
    compute_ke_spectra,              # KE spectrum from u/v winds (single time)
    compute_ke_spectra_timeseries,   # KE spectrum with time averaging
    compute_power_spectrum,          # Power spectrum from any scalar field
)
```

**Backward compatible:** Old import paths still work:
```python
from pcmdi_metrics.effective_resolution.lib import compute_ke_spectra  # ✓ Still works
```

## Use Cases

### 1. Kinetic Energy Spectrum from Wind Fields

Compute rotational and divergent KE spectra from a single 2D wind field:

```python
import xarray as xr
from pcmdi_metrics.effective_resolution import compute_ke_spectra

# Load u and v winds (2D fields - time/level already selected)
ds = xr.open_dataset("winds_250hpa_monthly_mean.nc")

# Compute KE spectra
spectra = compute_ke_spectra(ds, uvar="ua", vvar="va")

# Returns xarray.Dataset with:
# - rotational_ke: E_rot(l) 
# - divergent_ke: E_div(l)
# - eddy_scale: Spatial scale in km
# - wavenumber: Total wavenumber l

print(spectra.rotational_ke)
```

### 2. Time-Averaged KE Spectra

For datasets with time dimension (e.g., monthly means):

```python
from pcmdi_metrics.effective_resolution import compute_ke_spectra_timeseries

# Load multi-month data
ds = xr.open_dataset("winds_250hpa_4months.nc")

# Compute time-averaged spectra
spectra = compute_ke_spectra_timeseries(
    ds,
    uvar="ua",
    vvar="va", 
    level_hpa=250.0,
    time_mean=True  # Average over time dimension
)

# Returns same structure as compute_ke_spectra but time-averaged
```

### 3. Power Spectrum from Any Scalar Field

Compute power spectrum from temperature, geopotential, precipitation, SST, etc.:

```python
from pcmdi_metrics.effective_resolution import compute_power_spectrum

# Load any 2D scalar field
ds = xr.open_dataset("temperature_500hpa.nc")
field = ds["ta"].isel(time=0)  # Select single time

# Compute power spectrum
spectrum = compute_power_spectrum(
    field.values,
    lat=field.lat.values,
    gridtype="auto"
)

# Returns xarray.Dataset with:
# - power_spectrum: E(l) = Σ_m |C_lm|²
# - eddy_scale: Spatial scale in km
# - wavenumber: Total wavenumber l

print(spectrum.power_spectrum)
```

## When to Use Each Function

| Function | Input | Use When... |
|----------|-------|-------------|
| `compute_ke_spectra` | u, v (2D) | Single snapshot, need rotational/divergent decomposition |
| `compute_ke_spectra_timeseries` | u, v (3D with time) | Multiple timesteps, want time-averaged spectrum |
| `compute_power_spectrum` | Any scalar field (2D) | Analyzing temperature, GPH, SST, precipitation, etc. |
| `compute_effective_resolution` | u, v at 2 levels + time | Full diagnostic with steepening detection |
| `compute_effective_resolution_scalar` | Scalar field + time | Full diagnostic for any 2D field |

## Advanced Usage

### Custom Truncation

```python
# Limit spectral truncation (e.g., for low-res comparison)
spectra = compute_ke_spectra(ds, ntrunc=85)
```

### Different Grid Types

```python
# Explicitly specify grid type
spectra = compute_ke_spectra(ds, gridtype="gaussian")
```

### Custom Planet Radius

```python
# For other planets or theoretical studies
from pcmdi_metrics.effective_resolution import compute_ke_spectra, EARTH_RADIUS

spectra = compute_ke_spectra(ds, rsphere=EARTH_RADIUS * 0.5)
```

## Visualization

Use the spectral data with standard plotting:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

# Plot raw spectrum
ax.loglog(spectra.wavenumber, spectra.rotational_ke, label='Rotational')
ax.loglog(spectra.wavenumber, spectra.divergent_ke, label='Divergent')

# Or plot flattened (l³E)
ell = spectra.wavenumber.values
ax.loglog(ell, ell**3 * spectra.rotational_ke, label='Rotational (l³E)')

ax.set_xlabel('Total wavenumber l')
ax.set_ylabel('Kinetic energy spectrum')
ax.legend()
plt.show()
```

## Relationship to Full Diagnostic

The standalone spectral functions are the core computational components used by the full diagnostics:

```
compute_effective_resolution():
├── compute_ke_spectra_timeseries()  ← Standalone API
├── fit_spectral_slope()
└── detect_steepening()

compute_effective_resolution_scalar():
├── compute_power_spectrum()         ← Standalone API
├── fit_spectral_slope()
└── detect_steepening()
```

Use the standalone APIs when you need:
- Just the spectrum, not the resolution metric
- Custom post-processing of spectral data
- Integration into other analysis workflows
- Spectral comparisons across models or datasets

Use the full diagnostic APIs when you need:
- Complete effective resolution metric
- Steepening detection
- JSON output for CMEC
- Standardized analysis following Klaver et al. (2020)

## See Also

- Full effective resolution diagnostic: `compute_effective_resolution()`
- Scalar field diagnostic: `compute_effective_resolution_scalar()`
- Plotting utilities: `plot_spectra_and_slope()`, `plot_resolution_scatter()`
- Demo notebooks in `pcmdi_metrics/effective_resolution/`
