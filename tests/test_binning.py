import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import xarray as xr

from map_binning.binning import Binning


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return str(tmp_path)


@pytest.fixture
def test_datasets():
    """Create synthetic high and low resolution datasets for testing."""
    # High resolution dataset (10x10 grid)
    high_lats = np.linspace(30, 40, 10)
    high_lons = np.linspace(-130, -120, 10)
    high_time = np.arange(5)

    # Create synthetic data with some spatial pattern
    high_lat_grid, high_lon_grid = np.meshgrid(high_lats, high_lons, indexing="ij")
    high_data = np.sin(high_lat_grid * 0.1) + np.cos(high_lon_grid * 0.1)

    # Add time dimension
    high_data_time = np.broadcast_to(high_data[np.newaxis, :, :], (5, 10, 10))
    high_data_time = high_data_time + np.random.normal(0, 0.1, (5, 10, 10))

    ds_high = xr.Dataset(
        {
            "sla": (["time", "lat", "lon"], high_data_time),
            "temperature": (["lat", "lon"], high_data),
        },
        coords={"time": high_time, "lat": high_lats, "lon": high_lons},
    )

    # Low resolution dataset (5x5 grid)
    low_lats = np.linspace(30, 40, 5)
    low_lons = np.linspace(-130, -120, 5)
    low_time = np.arange(5)

    ds_low = xr.Dataset(
        {"template": (["time", "lat", "lon"], np.zeros((5, 5, 5)))},
        coords={"time": low_time, "lat": low_lats, "lon": low_lons},
    )

    # Datasets with different dimension names
    ds_high_alt = ds_high.rename({"lat": "latitude", "lon": "longitude"})
    ds_low_alt = ds_low.rename({"lat": "latitude", "lon": "longitude"})

    return {
        "ds_high": ds_high,
        "ds_low": ds_low,
        "ds_high_alt": ds_high_alt,
        "ds_low_alt": ds_low_alt,
    }


def test_init_default_params(test_datasets):
    """Test Binning initialization with default parameters."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    assert binning.var_name == "sla"
    assert binning.xdim_name == "lon"
    assert binning.ydim_name == "lat"
    assert binning.search_radius is None


def test_init_custom_params(test_datasets):
    """Test Binning initialization with custom parameters."""
    binning = Binning(
        ds_high=test_datasets["ds_high_alt"],
        ds_low=test_datasets["ds_low_alt"],
        var_name="sla",
        xdim_name="longitude",
        ydim_name="latitude",
        search_radius=1.0,
    )

    assert binning.var_name == "sla"
    assert binning.xdim_name == "longitude"
    assert binning.ydim_name == "latitude"
    assert binning.search_radius == 1.0


def test_create_binning_index_basic(test_datasets):
    """Test basic functionality of create_binning_index."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    index = binning.create_binning_index()

    # Check that index is a dictionary
    assert isinstance(index, dict)

    # Check that index has exactly 25 entries (5x5 grid)
    assert len(index) == 25

    # Check that keys are tuples of (i, j) coordinates
    for key in index.keys():
        assert isinstance(key, tuple)
        assert len(key) == 2
        assert isinstance(key[0], (int, np.integer))
        assert isinstance(key[1], (int, np.integer))

    # Check that values are lists of coordinate pairs of lon lat indexes
    for value in index.values():
        assert isinstance(value, list)
        for coord_pair in value:
            assert isinstance(coord_pair, tuple)
            assert len(coord_pair) == 2
            assert isinstance(coord_pair[0], (int, np.integer))
            assert isinstance(coord_pair[1], (int, np.integer))


def test_create_binning_index_with_custom_radius(test_datasets):
    """Test create_binning_index with custom search radius."""
    binning = Binning(
        ds_high=test_datasets["ds_high"],
        ds_low=test_datasets["ds_low"],
        var_name="sla",
        search_radius=2.0,
    )

    index = binning.create_binning_index()

    # With a larger radius, we should still have exactly 25 entries (5x5 grid)
    assert len(index) == 25

    # Verify that the search radius was used
    assert binning.search_radius == 2.0


def test_create_binning_index_validation_errors(test_datasets):
    """Test that create_binning_index raises appropriate errors."""
    # Test case where high-res has fewer latitude points than low-res
    ds_high_small = test_datasets["ds_high"].isel(lat=slice(0, 3))  # Only 3 lat points

    binning = Binning(
        ds_high=ds_high_small, ds_low=test_datasets["ds_low"], var_name="sla"
    )

    with pytest.raises(ValueError, match="latitude must have more grid points"):
        binning.create_binning_index()


def test_create_binning_index_no_valid_points():
    """Test error when no valid binning index is found."""
    # Create datasets with non-overlapping coordinates
    high_lats = np.linspace(0, 10, 10)
    high_lons = np.linspace(0, 10, 10)
    ds_high_separate = xr.Dataset(
        {"sla": (["lat", "lon"], np.random.rand(10, 10))},
        coords={"lat": high_lats, "lon": high_lons},
    )

    low_lats = np.linspace(50, 60, 5)
    low_lons = np.linspace(50, 60, 5)
    ds_low_separate = xr.Dataset(
        {"template": (["lat", "lon"], np.zeros((5, 5)))},
        coords={"lat": low_lats, "lon": low_lons},
    )

    binning = Binning(
        ds_high=ds_high_separate,
        ds_low=ds_low_separate,
        var_name="sla",
        search_radius=1.0,  # Small radius to ensure no overlap
    )

    with pytest.raises(ValueError, match="No valid binning index found"):
        binning.create_binning_index()


def test_mean_binning_without_time(test_datasets):
    """Test mean_binning on data without time dimension."""
    binning = Binning(
        ds_high=test_datasets["ds_high"],
        ds_low=test_datasets["ds_low"],
        var_name="temperature",  # No time dimension
    )

    result = binning.mean_binning()

    # Check result properties
    assert isinstance(result, xr.DataArray)
    assert result.name == "temperature"
    assert result.shape == (5, 5)  # Low-res grid shape
    assert "lat" in result.dims
    assert "lon" in result.dims
    assert "time" not in result.dims


def test_mean_binning_with_time(test_datasets):
    """Test mean_binning on data with time dimension."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning()

    # Check result properties
    assert isinstance(result, xr.DataArray)
    assert result.name == "sla"
    assert result.shape == (5, 5, 5)  # (time, lat, lon)
    assert "time" in result.dims
    assert "lat" in result.dims
    assert "lon" in result.dims


@patch("map_binning.binning.save")
def test_mean_binning_save_index(mock_save, test_datasets, temp_dir):
    """Test that mean_binning saves the index when specified."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning(
        pickle_filename="test_index.pkl", pickle_location=temp_dir
    )

    # Verify save was called
    mock_save.assert_called_once()
    args, kwargs = mock_save.call_args
    assert kwargs["filename"] == "test_index.pkl"
    assert kwargs["location"] == temp_dir


@patch("map_binning.binning.load")
def test_mean_binning_load_index(mock_load, test_datasets, temp_dir):
    """Test that mean_binning loads precomputed index when specified."""
    # Create a mock binning index
    mock_index = {(0, 0): [(0, 0), (0, 1)], (1, 1): [(2, 2), (2, 3)]}
    mock_load.return_value = mock_index

    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning(
        precomputed_binning_index=True,
        pickle_filename="test_index.pkl",
        pickle_location=temp_dir,
    )

    # Verify load was called
    mock_load.assert_called_once()
    args, kwargs = mock_load.call_args
    assert kwargs["filename"] == "test_index.pkl"
    assert kwargs["location"] == temp_dir


@patch("map_binning.binning.save")
@patch("os.makedirs")
def test_mean_binning_default_pickle_location(mock_makedirs, mock_save, test_datasets):
    """Test that default pickle location is created when not specified."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning()

    # Verify default directory creation
    mock_makedirs.assert_called_with("pickle_folder", exist_ok=True)

    # Verify save was called with default filename and location
    mock_save.assert_called_once()
    args, kwargs = mock_save.call_args
    assert kwargs["filename"] == "default_binning_index.pkl"
    assert kwargs["location"] == "pickle_folder"


def test_mean_binning_preserves_coordinates(test_datasets):
    """Test that mean_binning preserves coordinate information."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning()

    # Check coordinates are preserved
    np.testing.assert_array_equal(result.lat.values, test_datasets["ds_low"].lat.values)
    np.testing.assert_array_equal(result.lon.values, test_datasets["ds_low"].lon.values)
    np.testing.assert_array_equal(
        result.time.values, test_datasets["ds_high"].time.values
    )


def test_mean_binning_handles_nans(test_datasets):
    """Test that mean_binning properly handles NaN values."""
    # Create dataset with NaN values
    ds_high_nan = test_datasets["ds_high"].copy()
    ds_high_nan["sla"].values[0, 0:2, 0:2] = np.nan

    binning = Binning(
        ds_high=ds_high_nan, ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning()

    # Result should still be valid (nanmean should handle NaNs)
    assert isinstance(result, xr.DataArray)
    # Check that we have some valid (non-NaN) values
    assert np.any(~np.isnan(result.values))


def test_alternative_dimension_names(test_datasets):
    """Test binning with alternative dimension names."""
    binning = Binning(
        ds_high=test_datasets["ds_high_alt"],
        ds_low=test_datasets["ds_low_alt"],
        var_name="sla",
        xdim_name="longitude",
        ydim_name="latitude",
    )

    result = binning.mean_binning()

    # Check that result uses the correct dimension names
    assert "latitude" in result.dims
    assert "longitude" in result.dims


def test_automatic_radius_calculation(test_datasets):
    """Test that search radius is automatically calculated when not provided."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    # Initially, search_radius should be None
    assert binning.search_radius is None

    # After creating binning index, it should be calculated
    binning.create_binning_index()
    assert binning.search_radius is not None
    assert isinstance(binning.search_radius, float)
    assert binning.search_radius > 0


def test_binning_data_consistency(test_datasets):
    """Test that binned data maintains reasonable values."""
    binning = Binning(
        ds_high=test_datasets["ds_high"], ds_low=test_datasets["ds_low"], var_name="sla"
    )

    result = binning.mean_binning()

    # Check that binned values are within reasonable range of original data
    original_min = float(test_datasets["ds_high"]["sla"].min())
    original_max = float(test_datasets["ds_high"]["sla"].max())

    result_min = float(result.min())
    result_max = float(result.max())

    # Binned values should be within the range of original data
    assert result_min >= original_min - 1e-10  # Allow for small numerical errors
    assert result_max <= original_max + 1e-10


# Integration tests
def test_full_workflow_with_persistence(temp_dir):
    """Test complete workflow including index persistence."""
    # Create test datasets
    high_lats = np.linspace(30, 40, 20)
    high_lons = np.linspace(-130, -120, 20)
    low_lats = np.linspace(30, 40, 10)
    low_lons = np.linspace(-130, -120, 10)

    ds_high = xr.Dataset(
        {"sla": (["lat", "lon"], np.random.rand(20, 20))},
        coords={"lat": high_lats, "lon": high_lons},
    )

    ds_low = xr.Dataset(
        {"template": (["lat", "lon"], np.zeros((10, 10)))},
        coords={"lat": low_lats, "lon": low_lons},
    )

    binning = Binning(ds_high=ds_high, ds_low=ds_low, var_name="sla")

    # First run: create and save index
    result1 = binning.mean_binning(
        pickle_filename="integration_test.pkl", pickle_location=temp_dir
    )

    # Verify pickle file was created
    pickle_path = os.path.join(temp_dir, "integration_test.pkl")
    assert os.path.exists(pickle_path)

    # Second run: load existing index
    binning2 = Binning(ds_high=ds_high, ds_low=ds_low, var_name="sla")

    result2 = binning2.mean_binning(
        precomputed_binning_index=True,
        pickle_filename="integration_test.pkl",
        pickle_location=temp_dir,
    )

    # Results should be identical
    np.testing.assert_array_equal(result1.values, result2.values)
