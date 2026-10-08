#!/usr/bin/env python
"""Diagnose why anchor parameter doesn't affect steepening detection."""

import glob

import xarray as xr

from pcmdi_metrics.effective_resolution.lib import (
    compute_ke_spectra_timeseries,
    detect_steepening,
    fit_spectral_slope,
)

# Data paths
datadir = "/Users/lee1043/Documents/Research/DATA/HighResMIP/ECMWF-IFS-LR/highresSST-present/6hrPlevPt"

# Find input files
data_list = sorted(glob.glob(f"{datadir}/*/*ECMWF-IFS-LR*_2014*.nc"))

# Filter to target months (March, June, September, December)
target_months = ("201403", "201406", "201409", "201412")
data_list = [
    data_path
    for data_path in data_list
    if any(month in data_path for month in target_months)
]

print("Loading dataset...")
ds = xr.open_mfdataset(data_list)

print("Computing KE spectra at 250 hPa...")
spec_250 = compute_ke_spectra_timeseries(
    ds,
    uvar="ua",
    vvar="va",
    level_hpa=250.0,
    time_mean=True,
)

# Test different anchoring for the rotational spectrum at 500 hPa
print("\nComputing KE spectra at 500 hPa...")
spec_500 = compute_ke_spectra_timeseries(
    ds,
    uvar="ua",
    vvar="va",
    level_hpa=500.0,
    time_mean=True,
)

# Focus on the key spectrum: rotational at 500 hPa (the one that gives l=81)
ke_rot_500 = spec_500["ke_rot"]

print("\n" + "=" * 80)
print("TESTING DIFFERENT ANCHORING ON ROTATIONAL SPECTRUM AT 500 hPa")
print("=" * 80)

for anchor in ["left", "center", "right"]:
    print(f"\n--- Anchor: {anchor} ---")

    # Fit slope with this anchor
    slope = fit_spectral_slope(ke_rot_500, window=20, anchor=anchor)

    # Detect steepening
    detection = detect_steepening(
        slope,
        steepening_factor=0.25,
        wavenumber_ratio=2.0,
        min_wavenumber=32,
    )

    print(f"Steepening wavenumber: {detection['wavenumber']}")
    if detection["slope_at_detection"] is not None:
        print(f"Slope at detection: {detection['slope_at_detection']:.3f}")
    else:
        print("Slope at detection: None")
    print(f"Is upper limit: {detection['is_upper_limit']}")

    # Show slope values around the detection point
    if detection["wavenumber"] is not None:
        l_det = int(detection["wavenumber"])
        print(f"\nSlope values around l={l_det}:")
        for lnum in range(max(60, l_det - 10), min(100, l_det + 10)):
            if lnum < len(slope):
                s_val = slope.sel(wavenumber=lnum).values
                marker = " <-- DETECTION" if lnum == l_det else ""
                print(f"  l={lnum:3d}: slope={s_val:.3f}{marker}")

# Also check divergent at 250 hPa
print("\n" + "=" * 80)
print("TESTING DIFFERENT ANCHORING ON DIVERGENT SPECTRUM AT 250 hPa")
print("=" * 80)

ke_div_250 = spec_250["ke_div"]

for anchor in ["left", "center", "right"]:
    print(f"\n--- Anchor: {anchor} ---")

    # Fit slope with this anchor
    slope = fit_spectral_slope(ke_div_250, window=20, anchor=anchor)

    # Detect steepening
    detection = detect_steepening(
        slope,
        steepening_factor=0.25,
        wavenumber_ratio=2.0,
        min_wavenumber=32,
    )

    print(f"Steepening wavenumber: {detection['wavenumber']}")
    if detection["slope_at_detection"] is not None:
        print(f"Slope at detection: {detection['slope_at_detection']:.3f}")
    else:
        print("Slope at detection: None")
    print(f"Is upper limit: {detection['is_upper_limit']}")

    # Show slope values around the detection point
    if detection["wavenumber"] is not None:
        l_det = int(detection["wavenumber"])
        print(f"\nSlope values around l={l_det}:")
        for lnum in range(max(50, l_det - 10), min(80, l_det + 10)):
            if lnum < len(slope):
                s_val = slope.sel(wavenumber=lnum).values
                marker = " <-- DETECTION" if lnum == l_det else ""
                print(f"  l={lnum:3d}: slope={s_val:.3f}{marker}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print(
    """
If anchoring produces identical detection wavenumbers, it means:
1. The steepening is so pronounced that detection happens at the same
   wavenumber regardless of where the slope is assigned within the window
2. OR the spectrum has discrete jumps/plateaus that make detection
   insensitive to the ~10 wavenumber shift from anchoring

This suggests the ECMWF-IFS-LR case is not sensitive to anchoring choice.
We need to test with other models where the discrepancy is larger.
"""
)
