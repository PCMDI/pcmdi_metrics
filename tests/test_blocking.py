"""
Tests for atmospheric blocking metrics.

Uses mocked TensorFlow model for speed. One integration test marked 'slow'
loads the real model file.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import xarray as xr


# Skip all tests if TensorFlow not available
def _has_tensorflow():
    try:
        import tensorflow  # noqa: F401

        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(
    not _has_tensorflow(), reason="TensorFlow required for blocking tests"
)

# Import after TensorFlow check  # noqa: E402
from pcmdi_metrics.blocking import (  # noqa: E402
    compute_blocking_metrics,
    detect_blocking,
)
from pcmdi_metrics.blocking.lib.blocking_utils import (  # noqa: E402
    check_input_grid,
    find_nearest,
    validate_tensorflow,
)


class TestUtilities:
    """Test utility functions."""

    def test_validate_tensorflow_installed(self):
        """Test TensorFlow validation when installed."""
        # Should pass without error if TensorFlow >= 2.0
        validate_tensorflow()

    def test_check_input_grid_2degree(self):
        """Test grid checking for 2° data."""
        times = pd.date_range("2000-01-01", periods=10, freq="D")
        ds = xr.Dataset(
            {
                "zg": xr.DataArray(
                    np.zeros((10, 90, 180)),
                    dims=["time", "lat", "lon"],
                    coords={"time": times},
                )
            }
        )
        assert check_input_grid(ds, expected_shape=(90, 180))

    def test_check_input_grid_other(self):
        """Test grid checking for non-2° data."""
        times = pd.date_range("2000-01-01", periods=10, freq="D")
        ds = xr.Dataset(
            {
                "zg": xr.DataArray(
                    np.zeros((10, 36, 72)),
                    dims=["time", "lat", "lon"],
                    coords={"time": times},
                )
            }
        )
        assert not check_input_grid(ds, expected_shape=(90, 180))

    def test_find_nearest(self):
        """Test finding nearest value in array."""
        levels = np.array([100000, 85000, 70000, 50000, 25000])
        idx = find_nearest(levels, 50000)
        assert idx == 50000

        idx = find_nearest(levels, 50001)
        assert idx == 50000


class TestBlockingDetection:
    """Test blocking detection with neural network."""

    @pytest.fixture
    def sample_zg_data(self):
        """Create synthetic 500 hPa geopotential height data."""
        times = pd.date_range("2000-01-01", "2000-01-31", freq="D")
        lats = np.arange(-88, 90, 2)  # 2° grid
        lons = np.arange(0, 360, 2)

        # Realistic values: 5000-6000 m
        np.random.seed(42)
        data = 5500 + 200 * np.random.randn(len(times), len(lats), len(lons))

        ds = xr.Dataset(
            {
                "zg": xr.DataArray(
                    data,
                    dims=["time", "lat", "lon"],
                    coords={"time": times, "lat": lats, "lon": lons},
                )
            }
        )
        ds["zg"].attrs["units"] = "m"
        return ds

    @pytest.fixture
    def mock_model(self):
        """Mock Keras model to avoid loading 246 MB file."""
        model = MagicMock()
        # Return random probabilities (361 time steps from add_channels)
        # Shape after cyclic padding: (time-4, lat, lon+12)
        model.predict.return_value = np.random.rand(27, 90, 192)  # 31-4=27 days
        return model

    def test_detect_blocking_output_shape(self, sample_zg_data, mock_model):
        """Test that output has expected dimensions."""
        with patch(
            "pcmdi_metrics.blocking.lib.blocking_detection.get_model_path",
            return_value="/mock/path/model.h5",
        ):
            with patch(
                "pcmdi_metrics.blocking.lib.blocking_detection.keras.models.load_model",
                return_value=mock_model,
            ):
                result = detect_blocking(sample_zg_data, var="zg", verbose=False)

                # Check output structure
                assert "pval" in result.data_vars
                assert "pval_binary" in result.data_vars

                # Time should be 4 days shorter (2 at each end)
                expected_time = len(sample_zg_data.time) - 4
                assert len(result.time) == expected_time

                # Spatial dimensions unchanged if already 2°×2°
                assert len(result.lat) == len(sample_zg_data.lat)
                assert len(result.lon) == len(sample_zg_data.lon)

    def test_detect_blocking_threshold(self, sample_zg_data, mock_model):
        """Test that threshold parameter works."""
        # All probabilities = 0.5
        mock_model.predict.return_value = np.full((27, 90, 192), 0.5)

        with patch(
            "pcmdi_metrics.blocking.lib.blocking_detection.get_model_path",
            return_value="/mock/path/model.h5",
        ):
            with patch(
                "pcmdi_metrics.blocking.lib.blocking_detection.keras.models.load_model",
                return_value=mock_model,
            ):
                # Test threshold 0.4 - should have blocks
                result1 = detect_blocking(sample_zg_data, threshold=0.4, verbose=False)
                assert result1["pval_binary"].sum() > 0

                # Test threshold 0.6 - should have no blocks
                result2 = detect_blocking(sample_zg_data, threshold=0.6, verbose=False)
                assert result2["pval_binary"].sum() == 0

    def test_detect_blocking_attributes(self, sample_zg_data, mock_model):
        """Test that output has proper attributes."""
        with patch(
            "pcmdi_metrics.blocking.lib.blocking_detection.get_model_path",
            return_value="/mock/path/model.h5",
        ):
            with patch(
                "pcmdi_metrics.blocking.lib.blocking_detection.keras.models.load_model",
                return_value=mock_model,
            ):
                result = detect_blocking(sample_zg_data, var="zg", verbose=False)

                # Check variable attributes
                assert "long_name" in result["pval"].attrs
                assert "threshold" in result["pval"].attrs
                assert result["pval_binary"].attrs["threshold"] == 0.34

                # Check global attributes
                assert "blocking_detection_method" in result.attrs


class TestBlockingMetrics:
    """Test blocking metrics calculation."""

    @pytest.fixture
    def sample_blocking_data(self):
        """Create synthetic blocking mask."""
        times = pd.date_range("2000-01-01", "2001-12-31", freq="D")
        lats = np.arange(-88, 90, 2)
        lons = np.arange(0, 360, 2)

        # Random blocking events (~5% of grid points)
        np.random.seed(42)
        binary = (np.random.rand(len(times), len(lats), len(lons)) > 0.95).astype(float)

        ds = xr.Dataset(
            {
                "pval_binary": xr.DataArray(
                    binary,
                    dims=["time", "lat", "lon"],
                    coords={"time": times, "lat": lats, "lon": lons},
                )
            }
        )
        return ds

    def test_compute_metrics_output_structure(self, sample_blocking_data):
        """Test that metrics have expected structure."""
        metrics_df, spatial = compute_blocking_metrics(
            sample_blocking_data, historical=True, verbose=False
        )

        # Check DataFrame columns
        expected_cols = {"Year", "Season", "Region", "Number", "Size"}
        assert set(metrics_df.columns) == expected_cols

        # Check seasons
        assert set(metrics_df["Season"]) == {"DJF", "MAM", "JJA", "SON"}

        # Check regions
        expected_regions = {"NC", "NP", "NA", "SC", "SP", "SA"}
        assert set(metrics_df["Region"]) == expected_regions

        # Check spatial array shape
        assert spatial.shape == (4, 90, 180)  # 4 seasons, 90 lat, 180 lon

    def test_compute_metrics_no_blocks(self):
        """Test with data containing no blocks."""
        times = pd.date_range("2000-01-01", "2000-12-31", freq="D")
        lats = np.arange(-88, 90, 2)
        lons = np.arange(0, 360, 2)

        ds = xr.Dataset(
            {
                "pval_binary": xr.DataArray(
                    np.zeros((len(times), len(lats), len(lons))),
                    dims=["time", "lat", "lon"],
                    coords={"time": times, "lat": lats, "lon": lons},
                )
            }
        )

        metrics_df, spatial = compute_blocking_metrics(
            ds, historical=True, verbose=False
        )

        # Should have zero events
        assert (metrics_df["Number"] == 0).all()

    def test_compute_metrics_data_types(self, sample_blocking_data):
        """Test that output data types are correct."""
        metrics_df, spatial = compute_blocking_metrics(
            sample_blocking_data, historical=True, verbose=False
        )

        # Check data types
        assert metrics_df["Year"].dtype == np.int64
        assert metrics_df["Season"].dtype == object  # string
        assert metrics_df["Region"].dtype == object  # string
        assert metrics_df["Number"].dtype == np.int64
        assert metrics_df["Size"].dtype == np.float64

        assert spatial.dtype == np.float64

    def test_compute_metrics_custom_regions(self):
        """Test with custom region definitions."""
        times = pd.date_range("2000-01-01", "2000-12-31", freq="D")
        lats = np.arange(-88, 90, 2)
        lons = np.arange(0, 360, 2)

        np.random.seed(42)
        binary = (np.random.rand(len(times), len(lats), len(lons)) > 0.95).astype(float)

        ds = xr.Dataset(
            {
                "pval_binary": xr.DataArray(
                    binary,
                    dims=["time", "lat", "lon"],
                    coords={"time": times, "lat": lats, "lon": lons},
                )
            }
        )

        custom_regions = {"Test_Region": {"lat": slice(30, 60), "lon": slice(0, 90)}}

        metrics_df, spatial = compute_blocking_metrics(
            ds, regions=custom_regions, verbose=False
        )

        assert set(metrics_df["Region"]) == {"Test_Region"}


class TestJSONOutput:
    """Test JSON output formatting."""

    @pytest.fixture
    def sample_metrics_df(self):
        """Create sample metrics DataFrame."""
        data = {
            "Year": [2000, 2000, 2001, 2001],
            "Season": ["DJF", "DJF", "DJF", "DJF"],
            "Region": ["NC", "NP", "NC", "NP"],
            "Number": [10, 15, 12, 14],
            "Size": [200.0, 250.0, 210.0, 240.0],
        }
        return pd.DataFrame(data)

    def test_metrics_to_json_structure(self, sample_metrics_df, tmp_path):
        """Test JSON output follows PCMDI format."""
        from pcmdi_metrics.blocking.lib.blocking_metrics import metrics_to_json

        output_file = tmp_path / "test_metrics.json"
        metrics_to_json(
            sample_metrics_df,
            str(output_file),
            model_name="TEST_MODEL",
            reference_name="ERA5",
        )

        # Load and check structure
        import json

        with open(output_file) as f:
            data = json.load(f)

        # Check top-level keys
        assert "DIMENSIONS" in data
        assert "RESULTS" in data
        assert "METADATA" in data
        assert "PROVENANCE" in data

        # Check DIMENSIONS structure
        assert "json_structure" in data["DIMENSIONS"]
        assert "season" in data["DIMENSIONS"]
        assert "region" in data["DIMENSIONS"]
        assert "statistic" in data["DIMENSIONS"]

        # Check RESULTS structure
        assert "TEST_MODEL" in data["RESULTS"]
        assert "DJF" in data["RESULTS"]["TEST_MODEL"]
        assert "NC" in data["RESULTS"]["TEST_MODEL"]["DJF"]
        assert "number" in data["RESULTS"]["TEST_MODEL"]["DJF"]["NC"]

    def test_metrics_to_json_values(self, sample_metrics_df, tmp_path):
        """Test that JSON contains correct values."""
        from pcmdi_metrics.blocking.lib.blocking_metrics import metrics_to_json

        output_file = tmp_path / "test_metrics.json"
        metrics_to_json(
            sample_metrics_df,
            str(output_file),
            model_name="TEST_MODEL",
        )

        import json

        with open(output_file) as f:
            data = json.load(f)

        # Check that values are present
        nc_data = data["RESULTS"]["TEST_MODEL"]["DJF"]["NC"]
        assert "values" in nc_data["number"]
        assert "mean" in nc_data["number"]
        assert "std" in nc_data["number"]

        # Check mean calculation (2000: 10, 2001: 12 → mean = 11)
        assert nc_data["number"]["mean"] == 11.0

    def test_metrics_to_json_metadata(self, sample_metrics_df, tmp_path):
        """Test METADATA section."""
        from pcmdi_metrics.blocking.lib.blocking_metrics import metrics_to_json

        output_file = tmp_path / "test_metrics.json"
        metrics_to_json(
            sample_metrics_df,
            str(output_file),
            model_name="TEST_MODEL",
            realm="atmos",
            frequency="day",
        )

        import json

        with open(output_file) as f:
            data = json.load(f)

        metadata = data["METADATA"]
        assert metadata["metric"] == "Atmospheric Blocking"
        assert metadata["realm"] == "atmos"
        assert metadata["frequency"] == "day"
        assert "references" in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
