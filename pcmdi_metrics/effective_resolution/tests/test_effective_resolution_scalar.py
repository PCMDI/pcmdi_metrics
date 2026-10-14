# ==============================================================================
# Tests for scalar field effective resolution
# ==============================================================================

import numpy as np
import pandas as pd
import xarray as xr


def test_field_to_spherical_harmonics_shape():
    """Test that field_to_spherical_harmonics returns correct shape."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import (
        field_to_spherical_harmonics,
    )

    nlat, nlon = 48, 96
    lat = np.linspace(-89.5, 89.5, nlat)
    field = np.random.randn(nlat, nlon)

    # Default truncation
    coeffs = field_to_spherical_harmonics(field, lat, ntrunc=None, gridtype="regular")
    assert coeffs.shape == (
        nlat,
        nlat,
    ), f"Expected shape ({nlat}, {nlat}), got {coeffs.shape}"
    assert coeffs.dtype == np.complex128

    # Explicit truncation
    ntrunc = 30
    coeffs = field_to_spherical_harmonics(field, lat, ntrunc=ntrunc, gridtype="regular")
    assert coeffs.shape == (ntrunc + 1, ntrunc + 1)


def test_compute_power_spectrum_structure():
    """Test that compute_power_spectrum returns correct structure."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import compute_power_spectrum

    nlat, nlon = 48, 96
    lat = np.linspace(-89.5, 89.5, nlat)
    field = np.random.randn(nlat, nlon)

    ds = compute_power_spectrum(field, lat, ntrunc=None, gridtype="regular")

    # Check structure
    assert isinstance(ds, xr.Dataset)
    assert "power_spectrum" in ds.data_vars
    assert "eddy_scale" in ds.data_vars
    assert "wavenumber" in ds.coords

    # Check dimensions
    assert ds["power_spectrum"].dims == ("wavenumber",)
    assert len(ds["wavenumber"]) == nlat


def test_compute_power_spectrum_known_harmonic():
    """Test power spectrum detects known harmonic correctly."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import compute_power_spectrum

    nlat, nlon = 96, 192
    lat = np.linspace(-89.5, 89.5, nlat)
    lon = np.linspace(0, 360, nlon, endpoint=False)

    # Create field with single harmonic: sin(5*lat)*cos(3*lon)
    lat_rad = np.deg2rad(lat)
    lon_rad = np.deg2rad(lon)
    l_target, m_target = 5, 3
    field = np.sin(l_target * lat_rad[:, None]) * np.cos(m_target * lon_rad[None, :])

    ds = compute_power_spectrum(field, lat, gridtype="regular")

    # Power should peak near l=5
    power = ds["power_spectrum"].values
    peak_l = int(ds["wavenumber"].values[np.argmax(power)])

    # Allow some tolerance due to discretization
    assert (
        abs(peak_l - l_target) <= 2
    ), f"Expected peak near l={l_target}, got l={peak_l}"


def test_compute_power_spectrum_timeseries_structure():
    """Test that compute_power_spectrum_timeseries returns expected structure."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import (
        compute_power_spectrum_timeseries,
    )

    nlat, nlon, ntime = 48, 96, 5
    lat = np.linspace(-89, 89, nlat)

    # Create 3D field with time dimension
    np.random.seed(42)
    field_data = np.random.randn(ntime, nlat, nlon)

    field = xr.DataArray(
        field_data,
        dims=["time", "lat", "lon"],
        coords={
            "time": pd.date_range("2020-01-01", periods=ntime, freq="D"),
            "lat": lat,
            "lon": np.linspace(0, 360, nlon, endpoint=False),
        },
    )

    # Compute time-averaged spectrum
    ds = compute_power_spectrum_timeseries(field, time_mean=True)

    # Check structure
    assert "power_spectrum" in ds
    assert "wavenumber" in ds
    assert "eddy_scale" in ds
    assert "n_times_averaged" in ds.attrs
    assert ds.attrs["n_times_averaged"] == ntime
    assert ds["power_spectrum"].ndim == 1  # Time-averaged, so 1D


def test_compute_power_spectrum_timeseries_vs_single():
    """Test that timeseries function gives same result as single for 2D field."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import (
        compute_power_spectrum,
        compute_power_spectrum_timeseries,
    )

    nlat, nlon = 48, 96
    lat = np.linspace(-89, 89, nlat)

    np.random.seed(123)
    field_2d = np.random.randn(nlat, nlon)

    # 2D array (no time dimension)
    field_da = xr.DataArray(
        field_2d, dims=["lat", "lon"], coords={"lat": lat, "lon": np.arange(nlon)}
    )

    # Compute with both functions
    ds_single = compute_power_spectrum(field_2d, lat)
    ds_timeseries = compute_power_spectrum_timeseries(field_da)

    # Should give identical results
    np.testing.assert_allclose(
        ds_single["power_spectrum"].values,
        ds_timeseries["power_spectrum"].values,
        rtol=1e-10,
    )


def test_compute_power_spectrum_timeseries_time_mean_false():
    """Test compute_power_spectrum_timeseries with time_mean=False preserves time."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import (
        compute_power_spectrum_timeseries,
    )

    nlat, nlon, ntime = 48, 96, 4
    lat = np.linspace(-89, 89, nlat)

    np.random.seed(456)
    field_data = np.random.randn(ntime, nlat, nlon)

    field = xr.DataArray(
        field_data,
        dims=["time", "lat", "lon"],
        coords={
            "time": pd.date_range("2020-01-01", periods=ntime, freq="6H"),
            "lat": lat,
            "lon": np.linspace(0, 360, nlon, endpoint=False),
        },
    )

    # Don't average over time
    ds = compute_power_spectrum_timeseries(field, time_mean=False)

    # Should have time dimension
    assert "time" in ds.dims
    assert ds.sizes["time"] == ntime
    assert ds["power_spectrum"].ndim == 2  # (time, wavenumber)


def test_compute_power_spectrum_timeseries_averages_spectra_not_fields():
    """Critical test: verify we average spectra, not fields (scientific correctness)."""
    from pcmdi_metrics.effective_resolution.lib.ke_spectra import (
        compute_power_spectrum,
        compute_power_spectrum_timeseries,
    )

    nlat, nlon, ntime = 48, 96, 3
    lat = np.linspace(-89, 89, nlat)

    # Create field with strong temporal variability at small scales
    np.random.seed(789)
    # Large-scale component (same for all times)
    base = np.sin(3 * np.linspace(0, 2 * np.pi, nlat))[:, None]
    # Small-scale transient noise (different each time)
    noise = np.random.randn(ntime, nlat, nlon) * 0.5

    field_data = base[None, :, :] + noise

    field = xr.DataArray(
        field_data,
        dims=["time", "lat", "lon"],
        coords={
            "time": pd.date_range("2020-01-01", periods=ntime, freq="D"),
            "lat": lat,
            "lon": np.linspace(0, 360, nlon, endpoint=False),
        },
    )

    # Correct approach: average spectra (what timeseries function does)
    ds_correct = compute_power_spectrum_timeseries(field, time_mean=True)

    # Wrong approach: average fields first, then compute spectrum
    field_mean = field.mean(dim="time")
    ds_wrong = compute_power_spectrum(field_mean.values, lat)

    # The spectra should be different!
    # Correct approach preserves more variance at high wavenumbers
    power_correct = ds_correct["power_spectrum"].values
    power_wrong = ds_wrong["power_spectrum"].values

    # At high wavenumbers (small scales), correct should have MORE power
    # because it preserves transient variance
    high_l_indices = ds_correct["wavenumber"].values > 20
    high_l_correct = power_correct[high_l_indices].sum()
    high_l_wrong = power_wrong[high_l_indices].sum()

    assert (
        high_l_correct > high_l_wrong
    ), "Averaging spectra should preserve more high-wavenumber variance than averaging fields!"


def test_compute_effective_resolution_scalar_basic():
    """Test compute_effective_resolution_scalar with simple field."""
    from pcmdi_metrics.effective_resolution import compute_effective_resolution_scalar

    nlat, nlon = 96, 192
    lat = np.linspace(-89.5, 89.5, nlat)
    lon = np.linspace(0, 360, nlon, endpoint=False)

    # Random field (unlikely to show steepening)
    np.random.seed(123)
    field = np.random.randn(nlat, nlon)

    field_da = xr.DataArray(
        field,
        dims=["lat", "lon"],
        coords={"lat": lat, "lon": lon},
        name="temperature",
    )

    metrics, diagnostics = compute_effective_resolution_scalar(
        field_da, field_name="temperature", model="TEST", member="r1i1p1f1"
    )

    # Check structure
    assert "TEST" in metrics
    assert "r1i1p1f1" in metrics["TEST"]
    result = metrics["TEST"]["r1i1p1f1"]

    # Check required keys
    required_keys = [
        "effective_wavenumber",
        "effective_resolution_km",
        "grid_box_distance_km",
        "resolution_ratio",
        "is_upper_limit",
        "steepening_wavenumber",
        "steepening_eddy_scale_km",
        "field_name",
        "analysis_type",
        "criterion",
        "reference",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

    # Check specific values
    assert result["analysis_type"] == "scalar_field"
    assert result["field_name"] == "temperature"
    assert result["grid_box_distance_km"] > 0
    assert "temperature" in result["steepening_wavenumber"]

    # Check diagnostics
    assert "spectrum" in diagnostics
    assert "slope" in diagnostics
    assert "detection" in diagnostics


def test_compute_effective_resolution_scalar_with_time():
    """Test compute_effective_resolution_scalar with time dimension."""
    from pcmdi_metrics.effective_resolution import compute_effective_resolution_scalar

    nlat, nlon = 48, 96
    ntime = 4
    lat = np.linspace(-89.5, 89.5, nlat)
    lon = np.linspace(0, 360, nlon, endpoint=False)

    # Create time-varying field
    np.random.seed(456)
    field_3d = np.random.randn(ntime, nlat, nlon)

    field_da = xr.DataArray(
        field_3d,
        dims=["time", "lat", "lon"],
        coords={
            "time": pd.date_range("2014-01-01", periods=ntime, freq="6H"),
            "lat": lat,
            "lon": lon,
        },
        name="sst",
    )

    metrics, diagnostics = compute_effective_resolution_scalar(
        field_da, field_name="SST", model="TEST_3D"
    )

    # Should work and average over time
    assert "TEST_3D" in metrics
    result = metrics["TEST_3D"]["unspecified"]
    assert result["field_name"] == "SST"
    assert result["analysis_type"] == "scalar_field"


def test_compute_effective_resolution_scalar_output_consistency():
    """Test that scalar field output format matches wind-based analysis."""
    from pcmdi_metrics.effective_resolution import compute_effective_resolution_scalar

    nlat, nlon = 64, 128
    lat = np.linspace(-89.5, 89.5, nlat)
    lon = np.linspace(0, 360, nlon, endpoint=False)
    field = np.random.randn(nlat, nlon)

    field_da = xr.DataArray(
        field,
        dims=["lat", "lon"],
        coords={"lat": lat, "lon": lon},
        name="test",
    )

    metrics, diagnostics = compute_effective_resolution_scalar(
        field_da, model="MODEL", member="member1"
    )

    result = metrics["MODEL"]["member1"]

    # Check types match wind-based analysis
    assert isinstance(result["effective_wavenumber"], (int, float, type(None)))
    assert isinstance(result["effective_resolution_km"], (float, type(None)))
    assert isinstance(result["grid_box_distance_km"], float)
    assert isinstance(result["resolution_ratio"], (float, type(None)))
    assert isinstance(result["is_upper_limit"], bool)
    assert isinstance(result["steepening_wavenumber"], dict)
    assert isinstance(result["steepening_eddy_scale_km"], dict)
    assert isinstance(result["field_name"], str)
    assert isinstance(result["analysis_type"], str)
    assert isinstance(result["criterion"], dict)
    assert isinstance(result["reference"], str)

    # Check criterion dict has expected keys
    assert "fit_window" in result["criterion"]
    assert "fit_anchor" in result["criterion"]
    assert "steepening_factor" in result["criterion"]
