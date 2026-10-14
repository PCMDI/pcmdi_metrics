# Demo Notebook Updates for Scientific Correctness Fix

## Summary

The `compute_power_spectrum_timeseries()` function was added to fix a scientific correctness issue. The demo notebooks should be updated to:

1. Explain the importance of proper time averaging
2. Show the new `compute_power_spectrum_timeseries()` function
3. Document that `compute_effective_resolution_scalar()` now uses this internally

## Notebooks to Update

### 1. `demo_scalar_effective_resolution.ipynb` (PRIMARY)

**Current Status:**
- Uses `compute_effective_resolution_scalar()` which has been internally fixed
- Mentions "time-averaged automatically" but doesn't explain the methodology
- No discussion of time averaging approach

**Recommended Updates:**

#### A. Add Note Box After Section 4 Header

Add a new markdown cell after "## 4. Scalar Field Analysis (NEW)":

```markdown
### ⚠️ Important: Time Averaging Methodology

**Scientific Correctness**: When analyzing time-varying fields, it's critical to average **spectra**, not **fields**.

**Why?**
- ❌ **Wrong**: `field_mean = field.mean(dim='time')` → compute spectrum
  - Suppresses transient variance at small scales
  - Leads to biased (smoother) spectra
  
- ✅ **Correct**: Compute spectrum for each time → average spectra
  - Preserves transient variance
  - Follows Klaver et al. (2020) methodology

**Implementation**: `compute_effective_resolution_scalar()` uses `compute_power_spectrum_timeseries()` 
internally to ensure correct time averaging. You don't need to do anything special - it's automatic!

For more details, see [SCIENTIFIC_CORRECTNESS_FIX.md](SCIENTIFIC_CORRECTNESS_FIX.md).
```

#### B. Add New Section 7.5: Direct Spectral Analysis (Optional)

Insert a new section between current section 7 and 8:

```markdown
## 7.5. Advanced: Direct Spectral Analysis

For advanced users who want just the power spectrum without the full effective resolution diagnostic:

```python
from pcmdi_metrics.effective_resolution import (
    compute_power_spectrum_timeseries,
    compute_power_spectrum,
)

# Option 1: Time-varying field (automatically handles time averaging)
temp_3d = ds['ta'].sel(plev=50000)  # (time, lat, lon)
spectrum_timeseries = compute_power_spectrum_timeseries(temp_3d, time_mean=True)

# Option 2: Single snapshot
temp_2d = ds['ta'].sel(plev=50000, time=0)  # (lat, lon)
spectrum_single = compute_power_spectrum(
    temp_2d.values, 
    lat=temp_2d.lat.values
)

# Plot
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5))
ax.loglog(
    spectrum_timeseries.wavenumber, 
    spectrum_timeseries.power_spectrum,
    label='Time-averaged spectrum'
)
ax.set_xlabel('Total wavenumber l')
ax.set_ylabel('Power spectrum')
ax.set_title('Temperature Power Spectrum at 500 hPa')
ax.legend()
ax.grid(alpha=0.3)
```

**When to use:**
- `compute_power_spectrum_timeseries()`: Multi-timestep data, want time-averaged spectrum
- `compute_power_spectrum()`: Single snapshot or already time-averaged field
- `compute_effective_resolution_scalar()`: Want full diagnostic with effective resolution metric
```

#### C. Update Section 7 Header and Text

Change:
```markdown
## 7. General Usage for Other Fields
```

To:
```markdown
## 7. General Usage for Other Fields

The scalar field API works with any 2D atmospheric or oceanic variable. 
Time averaging is handled automatically using the scientifically correct 
approach (averaging spectra, not fields).
```

#### D. Update Imports Cell

Add to the imports:

```python
from pcmdi_metrics.effective_resolution import (
    compute_effective_resolution,
    compute_effective_resolution_scalar,  # NEW scalar field API
    compute_power_spectrum_timeseries,     # NEW for direct spectral analysis
)
```

### 2. `demo_effective_resolution.ipynb` (WIND-BASED)

**Current Status:**
- Uses `compute_effective_resolution()` (wind-based)
- Already uses `compute_ke_spectra_timeseries()` internally (correct)
- No changes needed to functionality

**Recommended Updates:**

#### Add Note in Introduction

Add a note explaining the time averaging is correct:

```markdown
**Note on Time Averaging**: This diagnostic correctly averages kinetic energy spectra 
across timesteps (not wind fields), following Klaver et al. (2020) methodology. 
The `compute_ke_spectra_timeseries()` function ensures transient energy is preserved.
```

### 3. Test Notebooks (Optional)

The test notebooks in `tests/` generally don't need updates as they test real data 
and don't expose the internals. However, if any use `compute_power_spectrum` directly 
with time-varying data, they should be checked.

## Implementation Checklist

- [ ] Update `demo_scalar_effective_resolution.ipynb`:
  - [ ] Add warning box about time averaging methodology
  - [ ] Add section 7.5 showing direct spectral analysis
  - [ ] Update section 7 header text
  - [ ] Add `compute_power_spectrum_timeseries` to imports
  
- [ ] Update `demo_effective_resolution.ipynb`:
  - [ ] Add note about correct time averaging in introduction
  
- [ ] Test notebooks:
  - [ ] Run `demo_scalar_effective_resolution.ipynb` to verify it works
  - [ ] Run `demo_effective_resolution.ipynb` to verify no regressions
  
- [ ] Commit changes:
  - [ ] Commit message: "Update demo notebooks for time averaging correctness"
  - [ ] Reference scientific fix commit

## Testing

Before committing, run both demos to ensure:
1. All cells execute without errors
2. Output looks reasonable
3. No warnings about deprecated functions
4. New sections render properly

## Notes

- The functional behavior hasn't changed for users - `compute_effective_resolution_scalar()` 
  still works the same way externally, just correctly now internally
- The updates are primarily educational - explaining WHY the implementation is correct
- Advanced users can now access `compute_power_spectrum_timeseries()` directly if needed

## Example Test Command

```bash
# Convert notebook to script and run
jupyter nbconvert --to script --execute demo_scalar_effective_resolution.ipynb
# Or run interactively
jupyter notebook demo_scalar_effective_resolution.ipynb
```
