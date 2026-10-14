# Using the `flatten` Parameter in `plot_spectra_and_slope()`

## Overview

The `flatten` parameter provides a simple, intuitive way to toggle between flattened (l³E) and raw (E) spectrum visualization.

## Usage

### Default Behavior (Flattened Spectrum)

By default, spectra are plotted as **l³E(l)** to emphasize spectral slope changes:

```python
from pcmdi_metrics.effective_resolution.lib.plot import plot_spectra_and_slope

# Default: flattened spectrum (l³E)
fig = plot_spectra_and_slope(diagnostics, result)
```

### Raw Spectrum

To plot the **raw E(l)** spectrum before l³ compensation:

```python
# Raw spectrum (E)
fig = plot_spectra_and_slope(diagnostics, result, flatten=False)
```

### Side-by-Side Comparison

```python
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Left: Raw spectrum E(l)
from pcmdi_metrics.effective_resolution.lib.plot import plot_spectra_and_slope

# Create custom plotting with subplots
# Note: plot_spectra_and_slope creates its own figure, so we need to call it twice

fig1 = plot_spectra_and_slope(
    diagnostics, result,
    flatten=False,
    title="Raw Spectrum E(l)",
    spec_ylim=(1e-2, 1e2)
)

fig2 = plot_spectra_and_slope(
    diagnostics, result, 
    flatten=True,  # or omit (default)
    title="Flattened Spectrum l³E(l)",
    spec_ylim=(1e0, 1e2)
)

plt.show()
```

## Why Flatten?

**Flattened (l³E):**
- Kinetic energy amplitude drops by orders of magnitude across the wavenumber range
- l³ compensation makes a k⁻³ spectrum appear flat on log-log axes
- Any visible curvature represents real departures from k⁻³
- **Better for detecting spectral steepening** (the key diagnostic metric)

**Raw (E):**
- Shows the actual spectrum before compensation
- Useful for understanding absolute energy magnitudes
- Follows standard atmospheric turbulence conventions
- Better for comparing with other published raw spectra

## Legacy Support

The original `compensate` parameter still works:

```python
# These are equivalent:
fig = plot_spectra_and_slope(diagnostics, result, flatten=False)
fig = plot_spectra_and_slope(diagnostics, result, compensate=None)

# These are equivalent:
fig = plot_spectra_and_slope(diagnostics, result, flatten=True)
fig = plot_spectra_and_slope(diagnostics, result, compensate=3.0)
```

When both are provided, `flatten` takes precedence.

## Recommended Usage

```python
# For diagnostic analysis (default - recommended)
fig = plot_spectra_and_slope(diagnostics, result)

# For publication figures matching other raw spectra
fig = plot_spectra_and_slope(diagnostics, result, flatten=False, spec_ylim=(1e-2, 1e2))

# For advanced custom compensation (e.g., l² for 2D turbulence)
fig = plot_spectra_and_slope(diagnostics, result, compensate=2.0)
```

## Parameters That Change With flatten

| Parameter | flatten=True (default) | flatten=False |
|-----------|----------------------|---------------|
| Y-axis label | l³Eₗ | spectrum (m²/s²) |
| Recommended spec_ylim | (1e0, 1e2) | (1e-2, 1e2) |
| Visual appearance | Flattened, emphasizes slope changes | Steep power law decline |
| Steepening detection | Easy to see | Harder to see |

## Implementation Details

- `flatten=True` sets `compensate=3.0` internally
- `flatten=False` sets `compensate=None` internally  
- `flatten=None` (default) uses the `compensate` parameter value (default 3.0)
- Compensation is applied as: **displayed_spectrum = l^p × E(l)** where p=compensate
