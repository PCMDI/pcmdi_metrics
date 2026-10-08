#!/usr/bin/env python
"""Test CMCC-CM2-VHR4 with different ntrunc values to identify root cause."""

import glob
import sys
import time

# Ensure local version is used
sys.path.insert(
    0,
    "/global/homes/l/lee1043/git/pcmdi_metrics_20260331/pcmdi_metrics",
)

import xarray as xr  # noqa: E402

from pcmdi_metrics.effective_resolution import (  # noqa: E402
    compute_effective_resolution,
)

# CMCC-CM2-VHR4 data location on NERSC
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
print("\nLoading dataset...")
ds = xr.open_mfdataset(data_list)
print(f"Dataset shape: {ds.dims}")
print(f"Grid: {len(ds.lat)} x {len(ds.lon)}")
print(f"Default ntrunc would be: {len(ds.lat) - 1}")

print("\n" + "=" * 70)
print("NTRUNC SENSITIVITY TEST FOR CMCC-CM2-VHR4")
print("=" * 70)
print("Reference (Klaver et al. Table 1): l=110, 182 km")
print("Current implementation: l=146, 136.6 km")
print("Discrepancy: +36 wavenumbers, -45.4 km (-24.9%)")
print("=" * 70)

# Test different ntrunc values
# Start with None (default = 767), then progressively lower values
ntrunc_values = [None, 400, 300, 250, 200, 150, 120, 110, 100, 80]

results = []

for ntrunc in ntrunc_values:
    ntrunc_str = str(ntrunc) if ntrunc is not None else "None (767)"
    print(f"\n{'=' * 70}")
    print(f"Testing ntrunc={ntrunc_str}")
    print(f"{'=' * 70}")

    start_time = time.time()

    try:
        metrics, diags = compute_effective_resolution(
            ds,
            uvar="ua",
            vvar="va",
            levels=(250.0, 500.0),
            model="CMCC-CM2-VHR4",
            member="r1i1p1f1",
            ntrunc=ntrunc,
            temporal_averaging="slopes",  # Use Klaver et al. method
        )

        result = metrics["CMCC-CM2-VHR4"]["r1i1p1f1"]
        elapsed = time.time() - start_time

        l_eff = result["effective_wavenumber"]
        L_eff = result["effective_resolution_km"]
        steep = result["steepening_wavenumber"]

        print(f"  Effective wavenumber:      {l_eff}")
        print(f"  Effective resolution:      {L_eff:.2f} km")
        print("  Steepening wavenumbers:")
        print(f"    div_250: {steep.get('div_250')}")
        print(f"    rot_250: {steep.get('rot_250')}")
        print(f"    rot_500: {steep.get('rot_500')}")
        print(
            f"  Error from reference (182 km): {L_eff - 182:.1f} km ({(L_eff - 182) / 182 * 100:.1f}%)"
        )
        print(f"  Computation time: {elapsed:.1f} seconds")

        results.append(
            {
                "ntrunc": ntrunc if ntrunc is not None else 767,
                "l_eff": l_eff,
                "L_eff": L_eff,
                "error_km": L_eff - 182,
                "error_pct": (L_eff - 182) / 182 * 100,
                "div_250": steep.get("div_250"),
                "rot_250": steep.get("rot_250"),
                "rot_500": steep.get("rot_500"),
                "time": elapsed,
            }
        )

    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(
            {
                "ntrunc": ntrunc if ntrunc is not None else 767,
                "error": str(e),
            }
        )

print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print(
    f"{'ntrunc':>8} | {'l_eff':>6} | {'L_eff (km)':>10} | {'Error (km)':>11} | {'Error (%)':>10} | div_250 | rot_250 | rot_500"
)
print("-" * 70)

for r in results:
    if "error" in r:
        print(f"{r['ntrunc']:>8} | ERROR: {r['error']}")
    else:
        print(
            f"{r['ntrunc']:>8} | {r['l_eff']:>6.0f} | {r['L_eff']:>10.1f} | {r['error_km']:>11.1f} | {r['error_pct']:>9.1f}% | {r['div_250']:>7} | {r['rot_250']:>7} | {r['rot_500']:>7}"
        )

print("-" * 70)
print("Reference:  110      182.0         0.0          0.0%")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

# Find closest match to reference
valid_results = [r for r in results if "error" not in r]
if valid_results:
    best = min(valid_results, key=lambda r: abs(r["error_km"]))
    print("\nClosest match to reference (182 km):")
    print(f"  ntrunc = {best['ntrunc']}")
    print(f"  l_eff = {best['l_eff']:.0f}")
    print(f"  L_eff = {best['L_eff']:.1f} km")
    print(f"  Error: {best['error_km']:+.1f} km ({best['error_pct']:+.1f}%)")

    if abs(best["error_pct"]) < 5:
        print(f"\n✓ SUCCESS: ntrunc={best['ntrunc']} gives < 5% error from reference!")
    elif abs(best["error_pct"]) < 10:
        print(
            f"\n~ PARTIAL SUCCESS: ntrunc={best['ntrunc']} gives < 10% error from reference"
        )
    else:
        print("\n✗ No ntrunc value tested brings error below 10%")
        print(
            "Consider: data version differences, time period mismatch, or other parameters"
        )

    # Check if there's a trend
    print("\nTrend analysis:")
    errors = [r["error_km"] for r in valid_results]
    ntrunc_vals = [r["ntrunc"] for r in valid_results]

    # Check if error decreases with lower ntrunc
    if len(errors) >= 3:
        # Check first 3 and last 3
        early_avg = sum(errors[:3]) / 3
        late_avg = sum(errors[-3:]) / 3

        if late_avg > early_avg:
            print("  Lower ntrunc → HIGHER error (moving away from reference)")
            print("  Hypothesis: ntrunc is NOT the primary cause")
        else:
            print("  Lower ntrunc → LOWER error (moving toward reference)")
            print("  Hypothesis: ntrunc IS contributing to discrepancy")

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

if valid_results:
    best = min(valid_results, key=lambda r: abs(r["error_km"]))

    if abs(best["error_pct"]) < 5:
        print(f"1. Set default ntrunc={best['ntrunc']} for CMCC-CM2-VHR4")
        print("2. Test other high-resolution models with same ntrunc")
        print("3. Consider adding model-specific ntrunc defaults to the code")
    else:
        print("1. ntrunc alone does not resolve the discrepancy")
        print("2. Investigate other possibilities:")
        print("   - Different data version (check CMIP6 version dates)")
        print("   - Different experiment (hist-1950 vs highresSST-present)")
        print("   - Different time periods (verify exact months)")
        print("   - Pre-processing or filtering before spectral analysis")
        print("   - Combination of multiple parameters (ntrunc + fit_window + ...)")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("If ntrunc test successful:")
print("  - Document the appropriate ntrunc value")
print("  - Add to CMCC_parameter_sensitivity.md")
print("  - Consider implementing model-specific defaults")
print("")
print("If ntrunc test unsuccessful:")
print("  - Check Klaver et al. paper for other parameter details")
print("  - Contact paper authors for clarification")
print("  - Test combination of ntrunc + other parameters")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
