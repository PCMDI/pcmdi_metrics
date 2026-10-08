#!/usr/bin/env python
"""Comprehensive parameter sensitivity test for CMCC-CM2-VHR4.

Tests steepening_factor, fit_window, and aggregation method (mean vs median)
to identify which parameters Klaver et al. may have used differently.
"""

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

# Load data
print("\nLoading dataset...")
ds = xr.open_mfdataset(data_list)
print(f"Dataset shape: {ds.dims}")
print(f"Grid: {len(ds.lat)} x {len(ds.lon)}")

print("\n" + "=" * 70)
print("COMPREHENSIVE PARAMETER SENSITIVITY TEST FOR CMCC-CM2-VHR4")
print("=" * 70)
print("Reference (Klaver et al. Table 1): l=110, 182 km")
print("Current implementation: l=146, 136.6 km")
print("Discrepancy: +36 wavenumbers, -45.4 km (-24.9%)")
print("=" * 70)

# Test parameters
steepening_factors = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
fit_windows = [15, 20, 25, 30]

results = []

# Test steepening_factor (MOST PROMISING)
print("\n" + "=" * 70)
print("TEST 1: STEEPENING FACTOR SENSITIVITY")
print("=" * 70)
print("Hypothesis: Klaver et al. may have used higher threshold for CMCC")
print("Paper says 0.25 is 'ad hoc and somewhat arbitrary'")
print("=" * 70)

for factor in steepening_factors:
    print(f"\nTesting steepening_factor={factor:.2f}...")
    start_time = time.time()

    try:
        metrics, diags = compute_effective_resolution(
            ds,
            uvar="ua",
            vvar="va",
            levels=(250.0, 500.0),
            model="CMCC-CM2-VHR4",
            member="r1i1p1f1",
            steepening_factor=factor,
            temporal_averaging="slopes",
        )

        result = metrics["CMCC-CM2-VHR4"]["r1i1p1f1"]
        elapsed = time.time() - start_time

        l_eff = result["effective_wavenumber"]
        L_eff = result["effective_resolution_km"]
        steep = result["steepening_wavenumber"]

        print(f"  l_eff: {l_eff}, L_eff: {L_eff:.1f} km")
        print(
            f"  Steepening: div={steep.get('div_250')}, rot_250={steep.get('rot_250')}, rot_500={steep.get('rot_500')}"
        )
        print(f"  Error: {L_eff - 182:.1f} km ({(L_eff - 182) / 182 * 100:.1f}%)")
        print(f"  Time: {elapsed:.1f}s")

        results.append(
            {
                "test": "steepening_factor",
                "param_value": factor,
                "l_eff": l_eff,
                "L_eff": L_eff,
                "error_km": L_eff - 182,
                "error_pct": (L_eff - 182) / 182 * 100,
                "div_250": steep.get("div_250"),
                "rot_250": steep.get("rot_250"),
                "rot_500": steep.get("rot_500"),
            }
        )

    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(
            {
                "test": "steepening_factor",
                "param_value": factor,
                "error": str(e),
            }
        )

# Test fit_window
print("\n" + "=" * 70)
print("TEST 2: FIT WINDOW SENSITIVITY")
print("=" * 70)
print("Paper uses 20, but might vary for different models")
print("=" * 70)

for window in fit_windows:
    print(f"\nTesting fit_window={window}...")
    start_time = time.time()

    try:
        metrics, diags = compute_effective_resolution(
            ds,
            uvar="ua",
            vvar="va",
            levels=(250.0, 500.0),
            model="CMCC-CM2-VHR4",
            member="r1i1p1f1",
            fit_window=window,
            temporal_averaging="slopes",
        )

        result = metrics["CMCC-CM2-VHR4"]["r1i1p1f1"]
        elapsed = time.time() - start_time

        l_eff = result["effective_wavenumber"]
        L_eff = result["effective_resolution_km"]
        steep = result["steepening_wavenumber"]

        print(f"  l_eff: {l_eff}, L_eff: {L_eff:.1f} km")
        print(
            f"  Steepening: div={steep.get('div_250')}, rot_250={steep.get('rot_250')}, rot_500={steep.get('rot_500')}"
        )
        print(f"  Error: {L_eff - 182:.1f} km ({(L_eff - 182) / 182 * 100:.1f}%)")
        print(f"  Time: {elapsed:.1f}s")

        results.append(
            {
                "test": "fit_window",
                "param_value": window,
                "l_eff": l_eff,
                "L_eff": L_eff,
                "error_km": L_eff - 182,
                "error_pct": (L_eff - 182) / 182 * 100,
                "div_250": steep.get("div_250"),
                "rot_250": steep.get("rot_250"),
                "rot_500": steep.get("rot_500"),
            }
        )

    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(
            {
                "test": "fit_window",
                "param_value": window,
                "error": str(e),
            }
        )

# Summary
print("\n" + "=" * 70)
print("SUMMARY: STEEPENING FACTOR")
print("=" * 70)
print(
    f"{'Factor':>8} | {'l_eff':>6} | {'L_eff':>8} | {'Error':>10} | div | rot_250 | rot_500"
)
print("-" * 70)

for r in [
    res for res in results if res["test"] == "steepening_factor" and "error" not in res
]:
    print(
        f"{r['param_value']:>8.2f} | {r['l_eff']:>6.0f} | {r['L_eff']:>8.1f} | {r['error_km']:>9.1f} | {r['div_250']:>3} | {r['rot_250']:>7} | {r['rot_500']:>7}"
    )

print("-" * 70)
print("Ref 0.25    110      182.0        0.0")

print("\n" + "=" * 70)
print("SUMMARY: FIT WINDOW")
print("=" * 70)
print(
    f"{'Window':>8} | {'l_eff':>6} | {'L_eff':>8} | {'Error':>10} | div | rot_250 | rot_500"
)
print("-" * 70)

for r in [res for res in results if res["test"] == "fit_window" and "error" not in res]:
    print(
        f"{r['param_value']:>8} | {r['l_eff']:>6.0f} | {r['L_eff']:>8.1f} | {r['error_km']:>9.1f} | {r['div_250']:>3} | {r['rot_250']:>7} | {r['rot_500']:>7}"
    )

print("-" * 70)
print("Ref   20    110      182.0        0.0")

# Find best matches
print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

valid_results = [r for r in results if "error" not in r]
if valid_results:
    best = min(valid_results, key=lambda r: abs(r["error_km"]))

    print("\nBest match to reference (182 km):")
    print(f"  Test: {best['test']}")
    print(f"  Parameter: {best['param_value']}")
    print(f"  l_eff: {best['l_eff']:.0f}")
    print(f"  L_eff: {best['L_eff']:.1f} km")
    print(f"  Error: {best['error_km']:+.1f} km ({best['error_pct']:+.1f}%)")

    if abs(best["error_pct"]) < 5:
        print(f"\n✓ SUCCESS: {best['test']}={best['param_value']} gives < 5% error!")
        print(
            f"Recommendation: Use {best['test']}={best['param_value']} for CMCC-CM2-VHR4"
        )
    elif abs(best["error_pct"]) < 10:
        print(f"\n~ PARTIAL: {best['test']}={best['param_value']} gives < 10% error")
    else:
        print("\n✗ No parameter combination tested resolves discrepancy")

# Check for trends
print("\nTrend Analysis:")

steep_results = [
    r for r in results if r["test"] == "steepening_factor" and "error" not in r
]
if len(steep_results) >= 2:
    errors_steep = [r["error_km"] for r in steep_results]
    factors_steep = [r["param_value"] for r in steep_results]

    if errors_steep[-1] > errors_steep[0]:
        print("  Higher steepening_factor → HIGHER error (away from reference)")
        print("  Conclusion: steepening_factor is NOT the cause")
    else:
        print("  Higher steepening_factor → LOWER error (toward reference)")
        print("  Conclusion: steepening_factor IS contributing")

window_results = [r for r in results if r["test"] == "fit_window" and "error" not in r]
if len(window_results) >= 2:
    errors_win = [r["error_km"] for r in window_results]

    if max(errors_win) - min(errors_win) < 5:
        print("  fit_window shows minimal effect (< 5 km variation)")
        print("  Conclusion: fit_window is NOT the cause")
    else:
        print(
            f"  fit_window shows {max(errors_win) - min(errors_win):.1f} km variation"
        )
        print("  Conclusion: fit_window might be contributing")

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

if valid_results and abs(best["error_pct"]) < 10:
    print(f"1. Use {best['test']}={best['param_value']} for CMCC-CM2-VHR4")
    print("2. Document this as model-specific parameter")
    print("3. Test if other high-resolution models need similar adjustment")
else:
    print("1. Neither steepening_factor nor fit_window resolves discrepancy")
    print("2. Next steps:")
    print("   - Test mean vs median aggregation method")
    print("   - Verify data version and experiment match")
    print("   - Check if Klaver et al. used different time periods")
    print("   - Consider contacting paper authors for clarification")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
