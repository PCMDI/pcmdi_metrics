# CMCC-CM2-VHR4 Discrepancy: Temporal Averaging Hypothesis

## The Problem

CMCC-CM2-VHR4 shows a **large discrepancy** even with native grid data:

| Metric | Reference | Test | Difference |
|--------|-----------|------|------------|
| Grid distance | 38.2 km | 38.2 km | ✓ **MATCH** |
| Effective wavenumber | l=110 | l=146 | **+36** |
| Effective resolution | 182 km | 136.6 km | **-45.4 km (-24.9%)** |

**Key observation**: The grid distance matches exactly, confirming native grid data is used. Therefore, the "regridded data" hypothesis does NOT explain this case.

## Temporal Averaging: The Prime Suspect

### What Klaver et al. (2020) Paper Says

From Appendix S3:
> "Fit monthly mean spectrum to y = c * l^(-n)"
> "compute slope for each monthly spectrum separately, average slopes across 4 months"

This clearly describes:
1. Compute spectrum for **each month** separately
2. Fit slopes to **each monthly spectrum**
3. **Average the SLOPES** across months
4. Detect steepening from the **averaged slope curve**

### What Current Implementation Does

From [lib/compute_effective_resolution.py:210](../lib/compute_effective_resolution.py#L210):
```python
spectra = {
    float(level): compute_ke_spectra_timeseries(
        ds,
        time_mean=True,  # ← Averages SPECTRA first
        ...
    )
}
```

The implementation:
1. Computes spectrum for **each time step**
2. **Averages the SPECTRA** across all time steps
3. Fits slope to the **time-averaged spectrum**
4. Detects steepening from this single slope curve

## Why This Matters

### Mathematical Difference

**Averaging spectra then fitting**:
```
E_avg(l) = mean[E_1(l), E_2(l), E_3(l), E_4(l)]
n = fit(E_avg)
```

**Fitting then averaging slopes**:
```
n_1 = fit(E_1), n_2 = fit(E_2), n_3 = fit(E_3), n_4 = fit(E_4)
n_avg = mean[n_1, n_2, n_3, n_4]
```

These are **NOT mathematically equivalent** because:
1. Fitting is a **non-linear operation** (least squares)
2. If individual months have different spectral shapes, averaging spectra smooths transitions
3. Smoothed spectra may show steepening at **higher wavenumbers** (finer scales)

### Effect on Steepening Detection

If monthly spectra have temporal variability:
- **Averaging spectra first**: Smooths out month-to-month variations
- **Smoother transitions**: May delay detection of steepening to higher wavenumbers
- **Result**: Detects steepening at higher l (finer resolution) than it should

This matches the observed pattern:
- Test finds l=146 (higher wavenumber)
- Reference finds l=110 (lower wavenumber)  
- Test result is "too fine" by 36 wavenumbers

## Evidence Supporting This Hypothesis

### 1. CMCC-CM2-VHR4 Specifics

Looking at the test results:
```python
'steepening_wavenumber': {'div_250': 80.0, 'rot_250': 146.0, 'rot_500': 156.0}
```

All three spectra show steepening, and they're spread over a wide range (80-156). This suggests:
- Different spectra steepen at different wavenumbers
- The median (l=146) is quite high
- Monthly variability might show different patterns

### 2. Model-Specific Sensitivity

The discrepancy varies by model:
- ECMWF-IFS-LR: -2.9% (minimal)
- CMCC-CM2-VHR4: -24.9% (severe)
- MPI-ESM1-2-HR: -4.4% (small)

This model-specific pattern makes sense if:
- Models with more temporal variability in their spectra show larger discrepancies
- CMCC-CM2-VHR4 might have stronger month-to-month spectral variations
- ECMWF-IFS-LR spectra might be more temporally stable

### 3. The Klaver et al. Methodology is Explicit

The paper specifically mentions:
- "**Monthly** mean spectrum" (not overall time mean)
- "**Each monthly spectrum separately**" (emphasizes separation)
- "**Average slopes across 4 months**" (not average spectra)

This detailed specification suggests it matters for their results.

## Why This Wasn't Caught by ECMWF-IFS-LR Testing

ECMWF-IFS-LR shows only -2.9% bias, which seemed acceptable. But:
1. ECMWF-IFS-LR might have more temporally stable spectra
2. The effect might be model-dependent
3. We need to test with a model showing large discrepancy (like CMCC)

## Prediction

If we implement per-month slope averaging:
1. CMCC-CM2-VHR4: Should move from l=146 toward l=110 (closer to reference)
2. ECMWF-IFS-LR: Should show minimal change (already close)
3. Other high-discrepancy models: Should improve significantly

## Implementation Strategy

### Option 1: Per-Month Processing (Klaver et al. exact)

```python
def compute_effective_resolution_monthly_averaged(...):
    # Split data by month
    months = split_by_month(ds, target_months=['03', '06', '09', '12'])
    
    # For each month:
    monthly_slopes = {}
    for month_name, month_ds in months.items():
        # Compute spectrum for this month
        spec = compute_ke_spectra_timeseries(month_ds, time_mean=True)
        
        # Fit slope for this month
        slopes = fit_spectral_slope(spec['ke_rot'], ...)
        monthly_slopes[month_name] = slopes
    
    # Average slopes across months
    avg_slope = average_slopes(monthly_slopes)
    
    # Detect steepening from averaged slope
    detection = detect_steepening(avg_slope, ...)
```

### Option 2: Configurable Parameter

Add parameter to `compute_effective_resolution()`:
```python
temporal_averaging: Literal['spectra', 'slopes'] = 'slopes'
```

- `'spectra'` (old): Current implementation, averaging spectra
- `'slopes'` (new default): Klaver et al. methodology, averaging slopes
- Maintains backward compatibility via parameter

## Testing Plan

1. **Implement per-month slope averaging**
2. **Re-run CMCC-CM2-VHR4**: Should show improvement toward l=110
3. **Re-run ECMWF-IFS-LR**: Should show minimal change
4. **Test with other models** if data available
5. **Compare all results** to reference Table 1

## Confidence Level

**HIGH** - This is likely the primary cause for CMCC-CM2-VHR4 because:
1. Grid distance matches exactly (native grid confirmed)
2. Paper methodology is explicitly different
3. Explains model-specific discrepancy patterns
4. Mathematical reasoning is sound (non-linear fitting operation)
5. The paper took care to specify this detail

## Next Step

Implement per-month slope averaging as described in Option 2, making it the new default while preserving backward compatibility.
