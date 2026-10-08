# Effective Resolution Discrepancy Analysis

## Summary

Systematic comparison of implementation results against Klaver et al. (2020) reference values reveals consistent negative bias (-3% to -25%) across multiple models. This document details the investigation into root causes and potential solutions.

## Reference Comparison

| Model | Reference | Implementation | Difference | % Difference |
|-------|-----------|----------------|------------|--------------|
| CMCC-CM2-VHR4 | l=110, 182 km | l=146, 136.6 km | -45.4 km | **-24.9%** |
| ECMWF-IFS-LR | l=79, 253 km | l=81, 245.6 km | -7.4 km | -2.9% |
| ECMWF-IFS-HR | l=108, 185 km | l=?, 147 km | -38 km | -20.5% |
| MPI-ESM1-2-XR | l=78, 256 km | l=?, 228.7 km | -27.3 km | -10.6% |
| MPI-ESM1-2-HR | l=55, 364 km | l=?, 348.1 km | -15.9 km | -4.4% |

**Pattern**: Implementation consistently finds **finer (smaller) effective resolutions** than reference, indicating detection occurs at **higher wavenumbers** than in Klaver et al. (2020).

## Investigation History

### Phase 1: Fit Anchor Parameter (REJECTED)

**Hypothesis**: Klaver et al. used `fit_anchor='center'` instead of `'right'`

**Test**: Changed default from `'right'` to `'center'` in [compute_effective_resolution.py](lib/compute_effective_resolution.py)

**Result**: **FAILED**
- ECMWF-IFS-LR: Breaks detection (only 1 of 3 spectra steepen, fails 2-of-3 rule)
- Changing anchor shifts wavenumber by ~10 units but in wrong direction
- Reverted in commit 70f8da2e

**Conclusion**: `fit_anchor='right'` is correct interpretation of paper's methodology

**Documentation**: [FINDINGS_anchor_investigation.md](FINDINGS_anchor_investigation.md)

### Phase 2: Temporal Averaging Strategy (FAILED)

**Hypothesis**: Klaver et al. averaged slopes across months, not spectra

**Implementation**: Added `temporal_averaging` parameter with two modes:
- `'spectra'` (old): Average spectra first, then fit slopes
- `'slopes'` (new): Fit slopes to each month, then average slopes (Appendix S3)

**Test Models**:
1. **ECMWF-IFS-LR**: NO CHANGE (l=81 both methods)
   - Indicates temporally stable spectra
   
2. **CMCC-CM2-VHR4**: NO CHANGE (l=146 both methods)
   - User tested on NERSC with full data
   - Results remained at l=146, 136.6 km
   - Discrepancy persists

**Result**: **FAILED** - Temporal averaging strategy is not the root cause

**Code Changes**: 
- Added `temporal_averaging` parameter (default `'slopes'` to match paper)
- Committed in branch `1413_lee1043_effective_resolution_anchor_fix`

**Documentation**: 
- [CMCC_temporal_averaging_hypothesis.md](CMCC_temporal_averaging_hypothesis.md)
- [TESTING_CMCC.md](TESTING_CMCC.md)

### Phase 3: Truncation Parameter (FAILED)

**Hypothesis**: Klaver et al. used lower `ntrunc` for high-resolution models

**Rationale**:
- Paper states: "truncate below the model's nominal limit"
- CMCC default: ntrunc = 767 (from 768 lats)
- Maybe they used ntrunc ~ 200-300 to suppress high-wavenumber artifacts

**Test**: `test_cmcc_ntrunc_sensitivity.py`
- Tested ntrunc: None (767), 400, 300, 250, 200, 150, 120, 110, 100, 80

**Results**: **FAILED** - No sensitivity
```
ntrunc=767:  l=146, 136.6 km (-24.9% error)
ntrunc=400:  l=146, 136.6 km (-24.9% error)
ntrunc=300:  l=146, 136.6 km (-24.9% error)
```

**Conclusion**: CMCC steepening occurs at l~80-156, well below even ntrunc=300, so truncation doesn't affect detection

### Phase 4: Wavenumber Range Restriction (SUCCESS)

**Hypothesis**: Klaver et al. limited `max_wavenumber` for steepening detection

**Background**:
- Current CMCC steepening: div_250=80, rot_250=146, rot_500=156
- Huge spread (76 wavenumbers) suggests rot_500=156 may be spurious
- Code already has `max_wavenumber` parameter (default: max(l)/2.0 = 383.5)

**Test**: `test_cmcc_wavenumber_range.py`

**Results**:

| max_wavenumber | l_eff | L_eff (km) | Error | Steepening detected |
|---|---|---|---|---|
| None (383.5) | 146 | 137.0 | -45.0 km (-24.9%) | div=80, rot_250=146, rot_500=156 |
| 200 | 146 | 137.0 | -45.0 km (-24.9%) | div=80, rot_250=146, rot_500=156 |
| **150** | **113** | **177.0** | **-5.0 km (-2.8%)** | div=80, rot_250=146, rot_500=None |
| 120 | — | — | Insufficient | Only div=80 |

**Key Finding**: 
- **max_wavenumber=150 brings results within 2.8% of reference**
- Excludes rot_500=156 detection, keeping div_250=80 and rot_250=146
- Median([80, 146]) = 113, very close to reference l=110

**Mechanism**:
```
With max_wavenumber=150:
  div_250 = 80   ✓ (below 150, included)
  rot_250 = 146  ✓ (below 150, included)
  rot_500 = 156  ✗ (above 150, EXCLUDED)
  
  Median([80, 146]) = 113
  L_eff = 20000/113 = 177 km
  Reference: 182 km
  Error: -2.8%
```

### Phase 5: Steepening Factor (ALSO SUCCESS, but less defensible)

**Test**: `test_cmcc_parameter_sweep.py`

**Results**:

| steepening_factor | l_eff | L_eff (km) | Error | Steepening detected |
|---|---|---|---|---|
| 0.25 (paper) | 146 | 137.0 | -45.0 km (-24.9%) | div=79, rot_250=146, rot_500=156 |
| **0.20** | **109** | **182.8** | **+0.8 km (+0.4%)** | div=79, rot_250=146, **rot_500=109** |
| **0.15** | **109** | **182.8** | **+0.8 km (+0.4%)** | div=79, rot_250=146, **rot_500=109** |

**Key Finding**:
- steepening_factor=0.15-0.20 gives **near-perfect match** (0.4% error!)
- Shifts rot_500 detection from l=156 to l=109
- All 3 spectra contribute: median([79, 146, 109]) = 109

**Why NOT Implemented**:
- Paper explicitly uses 0.25 for all models in Table 1
- Changing threshold modifies the detection criterion, not just the range
- Less justifiable than max_wavenumber restriction

## Why We're NOT Changing the Code

### Scientific Reasons

1. **Purpose of the Metric**: 
   - The diagnostic is meant to **discover** effective resolution, not impose it
   - Different models should have different L_eff/L_box ratios (2.7 to 4.8 in paper)
   - Constraining detection defeats the purpose

2. **Unknown Generalizability**:
   - max_wavenumber=150 works for CMCC but we tested only one model
   - No clear physical principle for choosing 150 vs other values
   - Would need testing across all HighResMIP models to validate

3. **Potential Data Differences**:
   - We used highresSST-present, reference may have used hist-1950
   - Different CMIP6 data versions (publication vs current)
   - Different months or time periods (though both use Mar/Jun/Sep/Dec 2014)

4. **Uncertainty About Reference**:
   - Without code from Klaver et al., we can't verify their exact parameters
   - rot_500=156 detection may be real, not artifact
   - Our implementation may actually be more accurate

### Practical Reasons

1. **Backward Compatibility**: Changing defaults would alter published results

2. **Parameter Already Exposed**: Users can set `max_wavenumber` if needed

3. **Conservative Approach**: Better to document than to impose questionable restrictions

## Recommendations for Users

### For CMCC-CM2-VHR4

If matching Klaver et al. (2020) reference value is critical:

```python
metrics, diags = compute_effective_resolution(
    ds,
    max_wavenumber=150,  # Brings l=146 → l=113 (reference: l=110)
    temporal_averaging='slopes',  # Use Klaver et al. Appendix S3 method
)
```

**Caveat**: Scientific justification for max_wavenumber=150 is unclear.

### For Other High-Resolution Models

If systematic negative bias is observed:

1. **Test max_wavenumber sensitivity**: Use `test_cmcc_wavenumber_range.py` as template
2. **Compare individual spectrum steepening**: Large spread suggests potential artifacts
3. **Verify native grid data**: Regridded data will give incorrect results
4. **Check for temporal stability**: Use both temporal_averaging methods

### General Guidance

The implementation follows Klaver et al. (2020) methodology as documented:
- Sliding 20-wavenumber window for slope fitting
- 25% steepening threshold over wavenumber doubling
- 2-of-3 confirmation rule across div_250, rot_250, rot_500
- Monthly averaging of slopes (temporal_averaging='slopes')

Discrepancies of 3-10% are likely within expected uncertainty given:
- Different data versions
- Numerical precision differences
- Potential undocumented parameters in reference

Discrepancies of 20-25% (like CMCC) warrant investigation of:
- Individual spectrum steepening wavenumbers
- Large spreads indicating potential artifacts
- max_wavenumber restrictions if high-wavenumber detections seem spurious

## Future Work

1. **Contact Paper Authors**: Request exact parameters used for CMCC-CM2-VHR4

2. **Test Other Models**: Apply wavenumber range sensitivity test to:
   - ECMWF-IFS-HR (also shows -20% bias)
   - MPI-ESM1-2-XR (shows -10% bias)
   
3. **Physical Validation**: Compare detected wavenumbers to model:
   - Numerical diffusion scales
   - Filter cutoffs
   - Grid spacing in spectral vs physical space

4. **Cross-Validation**: If other HighResMIP groups replicate the metric, compare implementations

## Files Generated During Investigation

### Test Scripts
- `test_anchor_fix.py` - Phase 1: Anchor parameter test
- `diagnose_anchor_effect.py` - Phase 1: Per-spectrum anchor effects
- `test_temporal_averaging.py` - Phase 2: ECMWF-IFS-LR temporal test
- `test_cmcc_ntrunc_sensitivity.py` - Phase 3: Truncation sensitivity
- `test_cmcc_wavenumber_range.py` - Phase 4: **max_wavenumber discovery**
- `test_cmcc_parameter_sweep.py` - Phase 5: steepening_factor/fit_window

### Documentation
- `FINDINGS_anchor_investigation.md` - Phase 1 detailed results
- `CMCC_temporal_averaging_hypothesis.md` - Phase 2 hypothesis
- `TESTING_CMCC.md` - Phase 2 testing instructions
- `CMCC_parameter_sensitivity.md` - Phase 3 ntrunc hypothesis
- `DISCREPANCY_ANALYSIS.md` - **This file**

### Code Changes (Branch: 1413_lee1043_effective_resolution_anchor_fix)
- Added `temporal_averaging` parameter to `compute_effective_resolution()`
- Default changed to `'slopes'` to match Klaver et al. Appendix S3
- No changes to detection algorithm or default parameters
- All existing parameters remain exposed for user control

## Conclusion

After testing 5 major hypotheses across temporal averaging, truncation, fit parameters, and detection range:

**Finding**: `max_wavenumber=150` brings CMCC-CM2-VHR4 within 2.8% of reference (l=113 vs l=110)

**Decision**: **Do not change code defaults**
- Scientific purpose is to discover resolution, not impose it
- Unknown generalizability to other models
- Uncertainty about reference implementation details
- Users can set `max_wavenumber` explicitly if needed

**Recommendation**: Document discrepancy and expose control to users rather than imposing potentially arbitrary restrictions on detection range.

The implementation is scientifically sound and follows the published methodology. Discrepancies likely arise from undocumented parameters or data differences. Future work should focus on cross-validation with other implementations and direct communication with paper authors.

---

**References**:
- Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective resolution in high resolution global atmospheric models for climate studies. *Atmospheric Science Letters*, 21, e952. https://doi.org/10.1002/asl.952
