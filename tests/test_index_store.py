import os
import pickle
from pathlib import Path

import numpy as np
import pytest

from map_binning.index_store import PickleHandler, load, save


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing using pytest's tmp_path."""
    return str(tmp_path)


@pytest.fixture
def test_data():
    """Create test data for pickle operations."""
    return {
        (0, 0): [(0, 0), (0, 1), (1, 0)],
        (0, 1): [(0, 2), (1, 1), (1, 2)],
        (1, 0): [(2, 0), (2, 1)],
        (1, 1): [(2, 2), (3, 2), (3, 3)],
    }


class TestPickleHandler:
    """Test suite for the PickleHandler class."""

    def test_pickle_handler_init_default(self):
        """Test PickleHandler initialization with default directory."""
        handler = PickleHandler()

        # Should use current working directory as default
        assert handler.default_dir == Path.cwd()

    def test_pickle_handler_init_custom(self, temp_dir):
        """Test PickleHandler initialization with custom directory."""
        handler = PickleHandler(default_dir=temp_dir)

        assert handler.default_dir == Path(temp_dir)
        assert handler.default_dir.exists()

    def test_pickle_handler_init_creates_directory(self, temp_dir):
        """Test that PickleHandler creates the directory if it doesn't exist."""
        new_dir = os.path.join(temp_dir, "new_subdir")
        assert not os.path.exists(new_dir)

        handler = PickleHandler(default_dir=new_dir)

        assert os.path.exists(new_dir)
        assert handler.default_dir == Path(new_dir)

    def test_save_index_dict_default_location(self, temp_dir, test_data):
        """Test saving index dictionary to default location."""
        handler = PickleHandler(default_dir=temp_dir)

        result_path = handler.save_index_dict(
            index_dict=test_data, filename="test_index.pkl"
        )

        expected_path = Path(temp_dir) / "test_index.pkl"
        assert result_path == expected_path
        assert result_path.exists()

    def test_save_index_dict_custom_location(self, temp_dir, test_data):
        """Test saving index dictionary to custom location."""
        handler = PickleHandler()
        custom_dir = os.path.join(temp_dir, "custom")

        result_path = handler.save_index_dict(
            index_dict=test_data, filename="test_index.pkl", location=custom_dir
        )

        expected_path = Path(custom_dir) / "test_index.pkl"
        assert result_path == expected_path
        assert result_path.exists()

    def test_load_index_dict_default_location(self, temp_dir, test_data):
        """Test loading index dictionary from default location."""
        handler = PickleHandler(default_dir=temp_dir)

        # First save the data
        save_path = handler.save_index_dict(
            index_dict=test_data, filename="test_index.pkl"
        )

        # Then load it back
        loaded_data = handler.load_index_dict(filename="test_index.pkl")

        assert loaded_data == test_data

    def test_load_index_dict_custom_location(self, temp_dir, test_data):
        """Test loading index dictionary from custom location."""
        handler = PickleHandler()
        custom_dir = os.path.join(temp_dir, "custom")

        # First save the data
        save_path = handler.save_index_dict(
            index_dict=test_data, filename="test_index.pkl", location=custom_dir
        )

        # Then load it back from custom location
        loaded_data = handler.load_index_dict(
            filename="test_index.pkl", location=custom_dir
        )

        assert loaded_data == test_data

    def test_load_nonexistent_file(self, temp_dir):
        """Test that loading a nonexistent file raises appropriate error."""
        handler = PickleHandler(default_dir=temp_dir)

        with pytest.raises(FileNotFoundError):
            handler.load_index_dict(filename="nonexistent.pkl")

    def test_save_load_roundtrip(self, temp_dir):
        """Test that save and load operations preserve data integrity."""
        handler = PickleHandler(default_dir=temp_dir)

        # Test with various data types
        complex_data = {
            (0, 0): [(0, 0), (0, 1)],
            (1, 1): [(2, 2)],
            (2, 3): [],  # Empty list
        }

        # Save and load
        save_path = handler.save_index_dict(complex_data, "complex_test.pkl")
        loaded_data = handler.load_index_dict("complex_test.pkl")

        assert loaded_data == complex_data
        assert isinstance(loaded_data, dict)

        # Test that tuples are preserved as tuples
        for key in loaded_data.keys():
            assert isinstance(key, tuple)

        for value_list in loaded_data.values():
            assert isinstance(value_list, list)
            for item in value_list:
                if item:  # Skip empty items
                    assert isinstance(item, tuple)

    def test_save_invalid_input_type(self, temp_dir):
        """Test error handling when input is not a dictionary."""
        handler = PickleHandler(default_dir=temp_dir)

        # Test with non-dictionary input
        with pytest.raises(ValueError, match="index_dict must be a dictionary"):
            handler.save_index_dict(
                index_dict="not a dictionary",  # String instead of dict
                filename="test.pkl",
            )

        with pytest.raises(ValueError, match="index_dict must be a dictionary"):
            handler.save_index_dict(
                index_dict=[1, 2, 3], filename="test.pkl"  # List instead of dict
            )

    def test_filename_without_pkl_extension(self, temp_dir, test_data):
        """Test that .pkl extension is automatically added."""
        handler = PickleHandler(default_dir=temp_dir)

        # Save without .pkl extension
        result_path = handler.save_index_dict(
            index_dict=test_data, filename="test_file"  # No .pkl extension
        )

        # Should automatically add .pkl extension
        expected_path = Path(temp_dir) / "test_file.pkl"
        assert result_path == expected_path
        assert result_path.exists()

        # Load without .pkl extension should also work
        loaded_data = handler.load_index_dict(filename="test_file")  # No .pkl
        assert loaded_data == test_data

    def test_load_corrupted_file(self, temp_dir):
        """Test error handling when loading corrupted pickle file."""
        handler = PickleHandler(default_dir=temp_dir)

        # Create a corrupted file
        corrupted_file = Path(temp_dir) / "corrupted.pkl"
        with open(corrupted_file, "w") as f:
            f.write("This is not a valid pickle file")

        with pytest.raises(OSError, match="Unable to load pickle file"):
            handler.load_index_dict(filename="corrupted.pkl")

    def test_load_non_dictionary_pickle(self, temp_dir):
        """Test error handling when pickle contains non-dictionary data."""
        handler = PickleHandler(default_dir=temp_dir)

        # Save a non-dictionary object
        non_dict_file = Path(temp_dir) / "non_dict.pkl"
        with open(non_dict_file, "wb") as f:
            pickle.dump([1, 2, 3], f)  # Save a list instead of dict

        with pytest.raises(OSError, match="Loaded object is not a dictionary"):
            handler.load_index_dict(filename="non_dict.pkl")


class TestConvenienceFunctions:
    """Test suite for the convenience functions (save and load)."""

    def test_convenience_save_function(self, temp_dir, test_data):
        """Test the convenience save function."""
        result_path = save(
            index_dict=test_data, filename="convenience_test.pkl", location=temp_dir
        )

        expected_path = Path(temp_dir) / "convenience_test.pkl"
        assert result_path == expected_path
        assert result_path.exists()

    def test_convenience_load_function(self, temp_dir, test_data):
        """Test the convenience load function."""
        # First save using convenience function
        save_path = save(
            index_dict=test_data, filename="convenience_test.pkl", location=temp_dir
        )

        # Then load using convenience function
        loaded_data = load(filename="convenience_test.pkl", location=temp_dir)

        assert loaded_data == test_data

    def test_convenience_save_default_location(self, temp_dir, test_data):
        """Test convenience save function with default location."""
        # Change to temp directory to test default behavior
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            result_path = save(
                index_dict=test_data, filename="default_location_test.pkl"
            )

            expected_path = Path(temp_dir) / "default_location_test.pkl"
            assert result_path == expected_path
            assert result_path.exists()
        finally:
            os.chdir(original_cwd)

    def test_convenience_load_default_location(self, temp_dir, test_data):
        """Test convenience load function with default location."""
        # Change to temp directory to test default behavior
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Save first
            save_path = save(index_dict=test_data, filename="default_load_test.pkl")

            # Then load
            loaded_data = load(filename="default_load_test.pkl")

            assert loaded_data == test_data
        finally:
            os.chdir(original_cwd)

    def test_convenience_functions_with_pathlib(self, temp_dir, test_data):
        """Test that convenience functions work with pathlib.Path objects."""
        save_path = save(
            index_dict=test_data, filename="pathlib_test.pkl", location=Path(temp_dir)
        )

        loaded_data = load(filename="pathlib_test.pkl", location=Path(temp_dir))

        assert loaded_data == test_data

    def test_save_creates_directory_if_needed(self, temp_dir, test_data):
        """Test that save function creates directory if it doesn't exist."""
        new_subdir = os.path.join(temp_dir, "new", "nested", "dir")
        assert not os.path.exists(new_subdir)

        save_path = save(
            index_dict=test_data, filename="nested_test.pkl", location=new_subdir
        )

        assert os.path.exists(new_subdir)
        assert save_path.exists()

    def test_error_handling_invalid_data(self, temp_dir):
        """Test error handling for invalid data types."""
        # Test with non-serializable data (lambda function)
        invalid_data = {
            (0, 0): [lambda x: x + 1]
        }  # Lambda functions are not serializable

        with pytest.raises(Exception):  # Could be various pickle-related errors
            save(
                index_dict=invalid_data, filename="invalid_test.pkl", location=temp_dir
            )


class TestIntegrationIndexStore:
    """Integration tests for the index store module."""

    def test_large_index_dictionary(self, temp_dir):
        """Test handling of large index dictionaries."""
        # Create a larger dataset similar to what would be generated
        large_data = {}
        for i in range(100):
            for j in range(100):
                # Simulate binning index with random high-res points
                num_points = np.random.randint(1, 10)
                points = [
                    (np.random.randint(0, 200), np.random.randint(0, 200))
                    for _ in range(num_points)
                ]
                large_data[(i, j)] = points

        # Save and load
        save_path = save(large_data, "large_test.pkl", temp_dir)
        loaded_data = load("large_test.pkl", temp_dir)

        assert len(loaded_data) == len(large_data)
        assert loaded_data == large_data

    def test_empty_index_dictionary(self, temp_dir):
        """Test handling of empty index dictionary."""
        empty_data = {}

        save_path = save(empty_data, "empty_test.pkl", temp_dir)
        loaded_data = load("empty_test.pkl", temp_dir)

        assert loaded_data == {}
        assert isinstance(loaded_data, dict)

    def test_multiple_files_same_directory(self, temp_dir):
        """Test saving and loading multiple index files in the same directory."""
        data1 = {(0, 0): [(0, 0)]}
        data2 = {(1, 1): [(1, 1)]}
        data3 = {(2, 2): [(2, 2)]}

        # Save multiple files
        path1 = save(data1, "file1.pkl", temp_dir)
        path2 = save(data2, "file2.pkl", temp_dir)
        path3 = save(data3, "file3.pkl", temp_dir)

        # Load them back
        loaded1 = load("file1.pkl", temp_dir)
        loaded2 = load("file2.pkl", temp_dir)
        loaded3 = load("file3.pkl", temp_dir)

        assert loaded1 == data1
        assert loaded2 == data2
        assert loaded3 == data3
