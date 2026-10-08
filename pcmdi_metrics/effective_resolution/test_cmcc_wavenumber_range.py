#!/usr/bin/env python
"""Test CMCC-CM2-VHR4 with different wavenumber range limits.

This tests whether Klaver et al. used different min_wavenumber or
max_wavenumber limits for steepening detection.
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

from pcmdi_metrics.effective_resolution.lib import (  # noqa: E402
    compute_ke_spectra_timeseries,
    detect_steepening,
    fit_spectral_slope,
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
print("WAVENUMBER RANGE SENSITIVITY TEST FOR CMCC-CM2-VHR4")
print("=" * 70)
print("Reference (Klaver et al. Table 1): l=110, 182 km")
print("Current implementation: l=146, 136.6 km")
print("Hypothesis: Klaver et al. may have used restricted wavenumber range")
print("=" * 70)

# Compute spectra once (expensive operation)
print("\nComputing kinetic energy spectra...")
start_time = time.time()

spectra_250 = compute_ke_spectra_timeseries(
    ds, uvar="ua", vvar="va", level_hpa=250.0, time_mean=True
)
spectra_500 = compute_ke_spectra_timeseries(
    ds, uvar="ua", vvar="va", level_hpa=500.0, time_mean=True
)

elapsed = time.time() - start_time
print(f"Spectra computed in {elapsed:.1f} seconds")
print(
    f"Wavenumber range: {spectra_250.wavenumber.min().values:.0f} to {spectra_250.wavenumber.max().values:.0f}"
)

# Test different max_wavenumber values
print("\n" + "=" * 70)
print("TEST 1: MAX_WAVENUMBER SENSITIVITY")
print("=" * 70)
print("Testing if Klaver et al. limited detection to lower wavenumbers")
print("=" * 70)

max_wavenumber_values = [None, 200, 150, 120, 110, 100, 90, 80]

results = []

for max_l in max_wavenumber_values:
    max_str = str(max_l) if max_l is not None else "None (default)"
    print(f"\nTesting max_wavenumber={max_str}")

    # Fit slopes
    slope_div_250 = fit_spectral_slope(spectra_250["ke_div"], window=20, anchor="right")
    slope_rot_250 = fit_spectral_slope(spectra_250["ke_rot"], window=20, anchor="right")
    slope_rot_500 = fit_spectral_slope(spectra_500["ke_rot"], window=20, anchor="right")

    # Detect steepening with specified max_wavenumber
    steep_div_250 = detect_steepening(
        slope_div_250, max_wavenumber=max_l, steepening_factor=0.25
    )
    steep_rot_250 = detect_steepening(
        slope_rot_250, max_wavenumber=max_l, steepening_factor=0.25
    )
    steep_rot_500 = detect_steepening(
        slope_rot_500, max_wavenumber=max_l, steepening_factor=0.25
    )

    # Get steepening wavenumbers
    l_div_250 = steep_div_250["wavenumber"]
    l_rot_250 = steep_rot_250["wavenumber"]
    l_rot_500 = steep_rot_500["wavenumber"]

    print(
        f"  Steepening: div_250={l_div_250}, rot_250={l_rot_250}, rot_500={l_rot_500}"
    )

    # Apply 2-of-3 rule (median)
    steepening_l = [l_div_250, l_rot_250, l_rot_500]
    valid_l = [ell for ell in steepening_l if ell is not None]  # noqa: E741

    if len(valid_l) >= 2:
        import numpy as np

        l_eff = float(np.median(valid_l))
        # Compute effective resolution
        L_eff = 20000.0 / l_eff  # Approximate formula
        error = L_eff - 182
        error_pct = error / 182 * 100

        print(f"  l_eff: {l_eff:.0f}, L_eff: {L_eff:.1f} km")
        print(f"  Error: {error:+.1f} km ({error_pct:+.1f}%)")

        results.append(
            {
                "max_wavenumber": max_l if max_l is not None else 383.5,
                "l_eff": l_eff,
                "L_eff": L_eff,
                "error_km": error,
                "error_pct": error_pct,
                "div_250": l_div_250,
                "rot_250": l_rot_250,
                "rot_500": l_rot_500,
                "n_steepening": len(valid_l),
            }
        )
    else:
        print("  INSUFFICIENT STEEPENING (< 2 of 3 spectra)")
        results.append(
            {
                "max_wavenumber": max_l if max_l is not None else 383.5,
                "error": "Insufficient steepening",
            }
        )

# Test different min_wavenumber values
print("\n" + "=" * 70)
print("TEST 2: MIN_WAVENUMBER SENSITIVITY")
print("=" * 70)
print("Paper uses min_wavenumber=32, testing if different for CMCC")
print("=" * 70)

min_wavenumber_values = [25, 32, 40, 50]

for min_l in min_wavenumber_values:
    print(f"\nTesting min_wavenumber={min_l}")

    # Fit slopes
    slope_div_250 = fit_spectral_slope(spectra_250["ke_div"], window=20, anchor="right")
    slope_rot_250 = fit_spectral_slope(spectra_250["ke_rot"], window=20, anchor="right")
    slope_rot_500 = fit_spectral_slope(spectra_500["ke_rot"], window=20, anchor="right")

    # Detect steepening with specified min_wavenumber
    steep_div_250 = detect_steepening(
        slope_div_250, min_wavenumber=min_l, steepening_factor=0.25
    )
    steep_rot_250 = detect_steepening(
        slope_rot_250, min_wavenumber=min_l, steepening_factor=0.25
    )
    steep_rot_500 = detect_steepening(
        slope_rot_500, min_wavenumber=min_l, steepening_factor=0.25
    )

    # Get steepening wavenumbers
    l_div_250 = steep_div_250["wavenumber"]
    l_rot_250 = steep_rot_250["wavenumber"]
    l_rot_500 = steep_rot_500["wavenumber"]

    print(
        f"  Steepening: div_250={l_div_250}, rot_250={l_rot_250}, rot_500={l_rot_500}"
    )

# Summary
print("\n" + "=" * 70)
print("SUMMARY: MAX_WAVENUMBER SENSITIVITY")
print("=" * 70)
print(
    f"{'max_l':>8} | {'l_eff':>6} | {'L_eff':>8} | {'Error':>10} | div | rot_250 | rot_500"
)
print("-" * 70)

for r in results:
    if "error" in r and isinstance(r["error"], str):
        print(f"{r['max_wavenumber']:>8.1f} | {r['error']}")
    else:
        print(
            f"{r['max_wavenumber']:>8.1f} | {r['l_eff']:>6.0f} | {r['L_eff']:>8.1f} | {r['error_km']:>9.1f} | {r['div_250']:>3} | {r['rot_250']:>7} | {r['rot_500']:>7}"
        )

print("-" * 70)
print("Ref     -     110      182.0        0.0")

# Find best match
valid_results = [
    r for r in results if "error" not in r or not isinstance(r["error"], str)
]
if valid_results:
    best = min(valid_results, key=lambda r: abs(r["error_km"]))

    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    print("\nBest match to reference (182 km):")
    print(f"  max_wavenumber = {best['max_wavenumber']:.1f}")
    print(f"  l_eff = {best['l_eff']:.0f}")
    print(f"  L_eff = {best['L_eff']:.1f} km")
    print(f"  Error: {best['error_km']:+.1f} km ({best['error_pct']:+.1f}%)")

    if abs(best["error_pct"]) < 5:
        print(
            f"\n✓ SUCCESS: max_wavenumber={best['max_wavenumber']:.0f} gives < 5% error!"
        )
        print("Recommendation: Use this max_wavenumber for CMCC-CM2-VHR4")
    elif abs(best["error_pct"]) < 10:
        print(
            f"\n~ PARTIAL: max_wavenumber={best['max_wavenumber']:.0f} gives < 10% error"
        )
    else:
        print("\n✗ max_wavenumber alone does not resolve discrepancy")

    # Check for pattern
    print("\nTrend analysis:")
    errors = [r["error_km"] for r in valid_results]
    max_vals = [r["max_wavenumber"] for r in valid_results]

    if len(errors) >= 3:
        # Check if error decreases with lower max_wavenumber
        early_avg = sum(errors[:3]) / 3
        late_avg = sum(errors[-3:]) / 3

        if late_avg > early_avg:
            print("  Lower max_wavenumber → HIGHER error (away from reference)")
            print("  Conclusion: max_wavenumber restriction is NOT the cause")
        else:
            print("  Lower max_wavenumber → LOWER error (toward reference)")
            print("  Conclusion: max_wavenumber IS contributing to discrepancy")

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

if valid_results and abs(best["error_pct"]) < 10:
    print(f"1. Use max_wavenumber={best['max_wavenumber']:.0f} for CMCC-CM2-VHR4")
    print(
        "2. This may indicate Klaver et al. used restricted range for high-res models"
    )
    print("3. Check if other high-resolution models need similar restriction")
else:
    print("1. Wavenumber range restrictions do not resolve the discrepancy")
    print("2. Continue investigating other parameters")
    print("3. Consider data version or methodology differences")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
