#!/usr/bin/env python
"""Test the anchor fix by recomputing ECMWF-IFS-LR effective resolution."""

import glob

import xarray as xr

from pcmdi_metrics.effective_resolution import compute_effective_resolution

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
print("Computing effective resolution with NEW anchor='center' (default)...")

# Compute with new default (center)
metrics_center, diagnostics_center = compute_effective_resolution(
    ds,
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    model="ECMWF-IFS-LR",
    member="r1i1p1f1",
    save_interim_netcdf=False,
)

result_center = metrics_center["ECMWF-IFS-LR"]["r1i1p1f1"]

print("\n" + "=" * 70)
print("RESULTS WITH NEW ANCHOR='center' (default)")
print("=" * 70)
print(f"Effective wavenumber:      {result_center['effective_wavenumber']}")
print(f"Effective resolution (km): {result_center['effective_resolution_km']:.2f}")
print(f"Grid box distance (km):    {result_center['grid_box_distance_km']:.2f}")
print(f"Resolution ratio:          {result_center['resolution_ratio']:.2f}")
print(f"Number of spectra steepening: {result_center['n_spectra_steepening']}")
print(f"Steepening wavenumbers:    {result_center['steepening_wavenumber']}")

print("\nComputing effective resolution with OLD anchor='right' for comparison...")

# Compute with old default (right) for comparison
metrics_right, diagnostics_right = compute_effective_resolution(
    ds,
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    model="ECMWF-IFS-LR",
    member="r1i1p1f1",
    save_interim_netcdf=False,
    fit_anchor="right",  # Explicitly use old default
)

result_right = metrics_right["ECMWF-IFS-LR"]["r1i1p1f1"]

print("\n" + "=" * 70)
print("RESULTS WITH OLD ANCHOR='right' (for comparison)")
print("=" * 70)
print(f"Effective wavenumber:      {result_right['effective_wavenumber']}")
print(f"Effective resolution (km): {result_right['effective_resolution_km']:.2f}")
print(f"Grid box distance (km):    {result_right['grid_box_distance_km']:.2f}")
print(f"Resolution ratio:          {result_right['resolution_ratio']:.2f}")
print(f"Number of spectra steepening: {result_right['n_spectra_steepening']}")
print(f"Steepening wavenumbers:    {result_right['steepening_wavenumber']}")

print("\n" + "=" * 70)
print("COMPARISON")
print("=" * 70)
print("Reference (Klaver et al. Table 1): 253 km at l=79")
print("")
print(
    f"Old implementation (anchor='right'): {result_right['effective_resolution_km']:.2f} km at l={result_right['effective_wavenumber']}"
)
print(
    f"  Difference from reference: {result_right['effective_resolution_km'] - 253:.2f} km ({((result_right['effective_resolution_km'] - 253) / 253 * 100):.1f}%)"
)
print("")
print(
    f"New implementation (anchor='center'): {result_center['effective_resolution_km']:.2f} km at l={result_center['effective_wavenumber']}"
)
print(
    f"  Difference from reference: {result_center['effective_resolution_km'] - 253:.2f} km ({((result_center['effective_resolution_km'] - 253) / 253 * 100):.1f}%)"
)
print("")
print(
    f"Improvement: {abs(result_right['effective_resolution_km'] - 253) - abs(result_center['effective_resolution_km'] - 253):.2f} km"
)

if abs(result_center["effective_resolution_km"] - 253) < abs(
    result_right["effective_resolution_km"] - 253
):
    print("✓ New anchor='center' is CLOSER to reference!")
else:
    print("✗ New anchor='center' is FARTHER from reference")

print("\n" + "=" * 70)
