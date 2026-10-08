#!/usr/bin/env python
"""Test the temporal averaging fix comparing 'spectra' vs 'slopes' methods."""

import sys

# Ensure we use the local version, not installed
sys.path.insert(
    0, "/Users/lee1043/Documents/Research/git/pcmdi_metrics_20260331/pcmdi_metrics"
)

import glob  # noqa: E402

import xarray as xr  # noqa: E402

from pcmdi_metrics.effective_resolution import (  # noqa: E402
    compute_effective_resolution,
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

print(f"Found {len(data_list)} data files")
print("Loading dataset...")

# Open dataset
ds = xr.open_mfdataset(data_list)

print(f"Dataset shape: {ds.dims}")
print(
    "\nComputing effective resolution with temporal_averaging='spectra' (old method)..."
)

# Compute with old method (average spectra first)
metrics_spectra, diagnostics_spectra = compute_effective_resolution(
    ds,
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    model="ECMWF-IFS-LR",
    member="r1i1p1f1",
    temporal_averaging="spectra",
    save_interim_netcdf=False,
)

result_spectra = metrics_spectra["ECMWF-IFS-LR"]["r1i1p1f1"]

print("\n" + "=" * 70)
print("RESULTS WITH temporal_averaging='spectra' (old method)")
print("=" * 70)
print(f"Effective wavenumber:      {result_spectra['effective_wavenumber']}")
print(f"Effective resolution (km): {result_spectra['effective_resolution_km']:.2f}")
print(f"Grid box distance (km):    {result_spectra['grid_box_distance_km']:.2f}")
print(f"Resolution ratio:          {result_spectra['resolution_ratio']:.2f}")
print(f"Number of spectra steepening: {result_spectra['n_spectra_steepening']}")
print(f"Steepening wavenumbers:    {result_spectra['steepening_wavenumber']}")

print(
    "\nComputing effective resolution with temporal_averaging='slopes' (Klaver method)..."
)

# Compute with new method (fit slopes to each month, then average)
metrics_slopes, diagnostics_slopes = compute_effective_resolution(
    ds,
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    model="ECMWF-IFS-LR",
    member="r1i1p1f1",
    temporal_averaging="slopes",
    save_interim_netcdf=False,
)

result_slopes = metrics_slopes["ECMWF-IFS-LR"]["r1i1p1f1"]

print("\n" + "=" * 70)
print("RESULTS WITH temporal_averaging='slopes' (Klaver et al. method)")
print("=" * 70)
print(f"Effective wavenumber:      {result_slopes['effective_wavenumber']}")
print(f"Effective resolution (km): {result_slopes['effective_resolution_km']:.2f}")
print(f"Grid box distance (km):    {result_slopes['grid_box_distance_km']:.2f}")
print(f"Resolution ratio:          {result_slopes['resolution_ratio']:.2f}")
print(f"Number of spectra steepening: {result_slopes['n_spectra_steepening']}")
print(f"Steepening wavenumbers:    {result_slopes['steepening_wavenumber']}")

print("\n" + "=" * 70)
print("COMPARISON")
print("=" * 70)
print("Reference (Klaver et al. Table 1): 253 km at l=79")
print("")
print(
    f"Old method (temporal_averaging='spectra'): {result_spectra['effective_resolution_km']:.2f} km at l={result_spectra['effective_wavenumber']}"
)
print(
    f"  Difference from reference: {result_spectra['effective_resolution_km'] - 253:.2f} km ({((result_spectra['effective_resolution_km'] - 253) / 253 * 100):.1f}%)"
)
print("")
print(
    f"New method (temporal_averaging='slopes'): {result_slopes['effective_resolution_km']:.2f} km at l={result_slopes['effective_wavenumber']}"
)
if result_slopes["effective_resolution_km"] is not None:
    print(
        f"  Difference from reference: {result_slopes['effective_resolution_km'] - 253:.2f} km ({((result_slopes['effective_resolution_km'] - 253) / 253 * 100):.1f}%)"
    )
else:
    print("  Difference from reference: N/A (no detection)")
print("")

if (
    result_spectra["effective_resolution_km"] is not None
    and result_slopes["effective_resolution_km"] is not None
):
    improvement = abs(result_spectra["effective_resolution_km"] - 253) - abs(
        result_slopes["effective_resolution_km"] - 253
    )
    print(f"Improvement: {improvement:.2f} km")

    if abs(result_slopes["effective_resolution_km"] - 253) < abs(
        result_spectra["effective_resolution_km"] - 253
    ):
        print("✓ New method is CLOSER to reference!")
    else:
        print("✗ New method is FARTHER from reference")
elif result_slopes["effective_resolution_km"] is None:
    print("✗ New method FAILED to detect (fewer than 2 spectra steepening)")

print("\n" + "=" * 70)
print("INDIVIDUAL SPECTRUM CHANGES")
print("=" * 70)
for key in ["div_250", "rot_250", "rot_500"]:
    old_l = result_spectra["steepening_wavenumber"].get(key)
    new_l = result_slopes["steepening_wavenumber"].get(key)
    print(f"{key}:")
    print(f"  Old (spectra): {old_l}")
    print(f"  New (slopes):  {new_l}")
    if old_l is not None and new_l is not None:
        diff = new_l - old_l
        print(f"  Change: {diff:+.0f} wavenumbers")
    print("")

print("=" * 70)
