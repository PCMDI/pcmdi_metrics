"""
Example script to test the new variability mode API.

This demonstrates how to use the new standard API without running the full driver.
"""


# Example usage (requires actual data and proper environment)
def example_usage():
    """
    Example of how to use the new API.

    Note: This requires xarray, xcdat, and other dependencies to be installed,
    and data files to be available.
    """
    import xarray as xr

    from pcmdi_metrics.variability_mode import NAM, NAO, PDO, SAM

    # Example 1: Simple NAM computation without reference
    print("Example 1: Computing NAM without reference data")
    model_ds = xr.open_dataset("path/to/model_psl.nc")
    results = NAM(model_ds, seasons=["DJF"])

    print(f"NAM DJF variance fraction: {results['DJF']['diagnostics']['frac']}")
    print(f"NAM DJF PC stdv: {results['DJF']['diagnostics']['stdv_pc']}")

    # Example 2: NAO with reference data and metrics
    print("\nExample 2: Computing NAO with reference data")
    obs_ds = xr.open_dataset("path/to/obs_psl.nc")
    results = NAO(model_ds, reference_ds=obs_ds, seasons=["DJF", "JJA"])

    print(f"NAO DJF correlation: {results['DJF']['metrics']['cor']}")
    print(f"NAO DJF RMS: {results['DJF']['metrics']['rms']}")

    # Example 3: PDO using SST data (defaults to monthly analysis)
    print("\nExample 3: Computing PDO with SST data")
    model_sst = xr.open_dataset("path/to/model_ts.nc")
    results = PDO(model_sst, data_var="ts")  # Defaults to seasons=['monthly']
    print(f"PDO monthly variance fraction: {results['monthly']['diagnostics']['frac']}")

    # Example 4: CBF method
    print("\nExample 4: Computing NAM using CBF method")
    results = NAM(model_ds, reference_ds=obs_ds, method="cbf", seasons=["DJF"])
    print(
        f"NAM CBF pattern shape: {results['DJF']['diagnostics']['cbf_pattern'].shape}"
    )

    # Example 5: Time subsetting
    print("\nExample 5: Computing SAM for specific time period")
    results = SAM(model_ds, start_year=1950, end_year=2000, seasons=["DJF"])

    # Example 6: Detrending control
    print("\nExample 6: Computing NAO without removing domain mean")
    results = NAO(model_ds, remove_domain_mean=False, seasons=["DJF"])

    # Example 7: Land masking for SST-based modes
    print("\nExample 7: Computing PDO with land masking")
    results = PDO(model_sst, data_var="ts", land_mask=True)

    # Example 8: Land masking with provided land fraction
    print("\nExample 8: Computing NPGO with explicit land fraction data")
    landfrac_ds = xr.open_dataset("path/to/sftlf.nc")
    results = PDO(model_sst, data_var="ts", land_mask=True, landfrac_ds=landfrac_ds)

    # Example 9: Unit conversion (Pa to hPa)
    print("\nExample 9: Computing NAO with unit conversion (Pa to hPa)")
    results = NAO(model_ds, data_var="psl", units_adjust=(True, "divide", 100.0))

    # Example 10: Unit conversion for both model and reference data
    print("\nExample 10: Computing NAM with unit conversion for model and reference")
    results = NAM(
        model_ds,
        reference_ds=obs_ds,
        data_var="psl",
        units_adjust=(True, "divide", 100.0),
        reference_units_adjust=(True, "divide", 100.0),
    )


def print_api_info():
    """Print information about the API."""
    print("=" * 70)
    print("PCMDI Metrics Variability Mode Standard API")
    print("=" * 70)
    print("\nAvailable functions:")
    print("  - NAO: North Atlantic Oscillation (default: 4 seasons)")
    print("  - NAM: Northern Annular Mode (default: 4 seasons)")
    print("  - SAM: Southern Annular Mode (default: 4 seasons)")
    print("  - PNA: Pacific North American Pattern (default: 4 seasons)")
    print("  - NPO: North Pacific Oscillation (default: 4 seasons)")
    print("  - PSA1: Pacific-South American Pattern 1 (default: 4 seasons)")
    print("  - PSA2: Pacific-South American Pattern 2 (default: 4 seasons)")
    print("  - PDO: Pacific Decadal Oscillation (default: monthly)")
    print("  - NPGO: North Pacific Gyre Oscillation (default: monthly)")
    print("  - AMO: Atlantic Multidecadal Oscillation (default: yearly)")

    print("\nCommon parameters:")
    print("  - model_ds: xarray.Dataset (required)")
    print("  - data_var: str (default: 'psl' or 'ts' depending on mode)")
    print("  - seasons: list of str")
    print("    * Atmospheric modes: default ['DJF', 'MAM', 'JJA', 'SON']")
    print("    * PDO, NPGO: default ['monthly']")
    print("    * AMO: default ['yearly']")
    print("  - reference_ds: xarray.Dataset (optional, enables metrics)")
    print("  - method: 'eof' or 'cbf' (default: 'eof')")
    print("  - start_year: int (optional)")
    print("  - end_year: int (optional)")
    print("  - remove_domain_mean: bool (default: True)")
    print("    * Removes spatial mean at each time step (detrending)")
    print("  - land_mask: bool (default: False)")
    print("    * Masks out land regions (recommended for SST modes)")
    print("  - landfrac_ds: xarray.Dataset (optional)")
    print("    * Explicit land fraction data (contains 'sftlf' variable)")
    print("  - units_adjust: tuple (optional)")
    print("    * Unit conversion: (enable, operation, value)")
    print("    * Example: (True, 'divide', 100.0) for Pa to hPa")
    print("  - reference_units_adjust: tuple (optional)")
    print("    * Same as units_adjust but for reference dataset")

    print("\nReturn structure:")
    print("  {")
    print("    'SEASON': {")
    print("      'diagnostics': {")
    print("        'eof_pattern': xr.DataArray,")
    print("        'pc_timeseries': xr.DataArray,")
    print("        'frac': float,")
    print("        'stdv_pc': float,")
    print("      },")
    print("      'metrics': {...}  # only if reference_ds provided")
    print("    }")
    print("  }")

    print("\nBasic usage:")
    print("  from pcmdi_metrics.variability_mode import NAO")
    print("  import xarray as xr")
    print("  ")
    print("  model_ds = xr.open_dataset('model_psl.nc')")
    print("  results = NAO(model_ds)")
    print("  print(results['DJF']['diagnostics']['frac'])")

    print("\nWith reference data:")
    print("  obs_ds = xr.open_dataset('obs_psl.nc')")
    print("  results = NAO(model_ds, reference_ds=obs_ds)")
    print("  print(results['DJF']['metrics']['cor'])")
    print("=" * 70)


if __name__ == "__main__":
    print_api_info()

    print("\n\nNote: To actually run the examples, you need:")
    print("  1. A Python environment with xarray, xcdat, eofs, and other dependencies")
    print("  2. Actual data files (NetCDF format with proper CF conventions)")
    print("  3. Uncomment and modify the example_usage() function call below")
    print("\n# example_usage()  # Uncomment when you have data and environment ready")
