# Testing Instructions for CMCC-CM2-VHR4

## Purpose

Test the temporal averaging fix (`temporal_averaging='slopes'`) with CMCC-CM2-VHR4 data, which shows large discrepancy (-24.9%) that is NOT explained by regridded data (grid distance matches exactly at 38.2 km).

## Hypothesis

The large discrepancy for CMCC-CM2-VHR4 is caused by temporal averaging strategy:
- **Current (old)**: Average spectra first, then fit slopes
- **Klaver et al. (2020)**: Fit slopes to each month, then average slopes

Since fitting is a non-linear operation, these produce different results when monthly spectra have temporal variability.

## Expected Results

### Current Status (temporal_averaging='spectra')
- Effective wavenumber: l=146
- Effective resolution: 136.6 km
- Reference (Klaver et al.): l=110, 182 km
- **Discrepancy**: +36 wavenumbers, -45.4 km (-24.9%)

### After Fix (temporal_averaging='slopes')
- **Prediction**: Should move from l=146 toward l=110
- **Expected improvement**: Significant reduction in discrepancy
- **Target**: Within ±10% of reference (164-200 km range)

## Test Script

Location: `test_cmcc_temporal_averaging.py` (to be created on machine with CMCC data)

```python
#!/usr/bin/env python
"""Test temporal averaging fix with CMCC-CM2-VHR4 data."""

import glob
import sys

# Ensure local version is used
sys.path.insert(0, "/path/to/pcmdi_metrics")

import xarray as xr
from pcmdi_metrics.effective_resolution import compute_effective_resolution

# CMCC-CM2-VHR4 data location (adjust path as needed)
datadir = "/global/cfs/cdirs/m4581/lee1043/DATA/CMIP6/HighResMIP/CMCC-CM2-VHR4/highresSST-present/6hrPlevPt"

# Find native grid (gn) data for target months
data_list = sorted(glob.glob(f"{datadir}/*/*CMCC-CM2-VHR4*_gn_2014*.nc"))
target_months = ("201403", "201406", "201409", "201412")
data_list = [
    data_path
    for data_path in data_list
    if any(month in data_path for month in target_months)
]

print(f"Found {len(data_list)} data files")
print("Verifying native grid (gn) labels:")
for f in data_list[:2]:
    print(f"  {f.split('/')[-1]}")

# Load data
ds = xr.open_mfdataset(data_list)
print(f"\nDataset shape: {ds.dims}")
print(f"Grid: {len(ds.lat)} x {len(ds.lon)}")

# Test 1: Old method (temporal_averaging='spectra')
print("\n" + "="*70)
print("TEST 1: temporal_averaging='spectra' (old method)")
print("="*70)

metrics_old, diags_old = compute_effective_resolution(
    ds,
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    model="CMCC-CM2-VHR4",
    member="r1i1p1f1",
    temporal_averaging="spectra",
)

result_old = metrics_old["CMCC-CM2-VHR4"]["r1i1p1f1"]

print(f"Effective wavenumber:      {result_old['effective_wavenumber']}")
print(f"Effective resolution (km): {result_old['effective_resolution_km']:.2f}")
print(f"Grid box distance (km):    {result_old['grid_box_distance_km']:.2f}")
print(f"Steepening wavenumbers:    {result_old['steepening_wavenumber']}")

# Test 2: New method (temporal_averaging='slopes')
print("\n" + "="*70)
print("TEST 2: temporal_averaging='slopes' (Klaver et al. method)")
print("="*70)

metrics_new, diags_new = compute_effective_resolution(
    ds,
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    model="CMCC-CM2-VHR4",
    member="r1i1p1f1",
    temporal_averaging="slopes",
    debug=True,  # Show monthly processing
)

result_new = metrics_new["CMCC-CM2-VHR4"]["r1i1p1f1"]

print(f"\nEffective wavenumber:      {result_new['effective_wavenumber']}")
print(f"Effective resolution (km): {result_new['effective_resolution_km']:.2f}")
print(f"Grid box distance (km):    {result_new['grid_box_distance_km']:.2f}")
print(f"Steepening wavenumbers:    {result_new['steepening_wavenumber']}")

# Comparison
print("\n" + "="*70)
print("COMPARISON")
print("="*70)
print("Reference (Klaver et al. Table 1): l=110, 182 km")
print("")
print(f"Old method: l={result_old['effective_wavenumber']}, {result_old['effective_resolution_km']:.1f} km")
print(f"  Error: {result_old['effective_resolution_km'] - 182:.1f} km ({(result_old['effective_resolution_km'] - 182)/182 * 100:.1f}%)")
print("")
print(f"New method: l={result_new['effective_wavenumber']}, {result_new['effective_resolution_km']:.1f} km")
print(f"  Error: {result_new['effective_resolution_km'] - 182:.1f} km ({(result_new['effective_resolution_km'] - 182)/182 * 100:.1f}%)")
print("")

# Calculate improvement
wavenumber_improvement = abs(result_old['effective_wavenumber'] - 110) - abs(result_new['effective_wavenumber'] - 110)
resolution_improvement = abs(result_old['effective_resolution_km'] - 182) - abs(result_new['effective_resolution_km'] - 182)

print(f"Wavenumber improvement: {wavenumber_improvement:+.0f} (closer to l=110)")
print(f"Resolution improvement: {resolution_improvement:+.1f} km (closer to 182 km)")

if abs(result_new['effective_resolution_km'] - 182) < abs(result_old['effective_resolution_km'] - 182):
    print("\n✓ SUCCESS: New method is CLOSER to reference!")
else:
    print("\n✗ FAILURE: New method did not improve")

print("\n" + "="*70)
print("INDIVIDUAL SPECTRUM CHANGES")
print("="*70)
for key in ['div_250', 'rot_250', 'rot_500']:
    old_l = result_old['steepening_wavenumber'].get(key)
    new_l = result_new['steepening_wavenumber'].get(key)
    print(f"{key}:")
    print(f"  Old: {old_l}")
    print(f"  New: {new_l}")
    if old_l is not None and new_l is not None:
        print(f"  Change: {new_l - old_l:+.0f}")
    print("")

print("="*70)
```

## Running the Test

### On NERSC (where CMCC data is located):

```bash
# Activate the appropriate conda environment
source /Users/lee1043/miniforge3/bin/activate pmp_devel_20260331

# Or on NERSC:
# module load python
# source activate pmp_devel

# Navigate to the code directory
cd /global/cfs/cdirs/.../pcmdi_metrics/pcmdi_metrics/effective_resolution

# Run the test
python test_cmcc_temporal_averaging.py
```

### Expected Runtime

~1-2 hours (CMCC has 768×1152 grid, 4 months of 6-hourly data)

## Success Criteria

1. **Wavenumber moves closer to l=110**
   - Currently at l=146 (+36 from reference)
   - Success if moves to l=100-120 range

2. **Resolution moves closer to 182 km**
   - Currently at 136.6 km (-45.4 km from reference)
   - Success if moves to 164-200 km range (within ±10%)

3. **Individual spectra shift consistently**
   - All three spectra should shift toward lower wavenumbers
   - Changes should be substantial (5-20 wavenumbers per spectrum)

## If Test Fails

If temporal averaging fix doesn't improve CMCC results, consider:

1. **Truncation parameter**: Klaver et al. may have used different `ntrunc`
2. **Time period mismatch**: Verify same months used (Mar, Jun, Sep, Dec 2014)
3. **Data version**: Check if Klaver used different CMCC data version
4. **Combination of factors**: Both temporal averaging AND another parameter

## Documentation

After successful testing, update:
- `FINDINGS_anchor_investigation.md`: Add CMCC test results
- `README.md`: Confirm temporal_averaging='slopes' is validated
- `CMCC_temporal_averaging_hypothesis.md`: Update with actual results

## Reference

Klaver et al. (2020) Table 1, row for CMCC-CM2-VHR4:
- L_tilde (grid distance): 38.2 km ✓ (matches our calculation)
- l_eff: 110
- L_eff: 182 km  
- Ratio: 4.8
