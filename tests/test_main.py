import map_binning
from map_binning.binning import Binning
from map_binning.index_store import PickleHandler, load, save


def test_package_version():
    """Test that the package has a version attribute."""
    # Check that __version__ exists
    assert hasattr(map_binning, "__version__")

    # Check that version is a string
    assert isinstance(map_binning.__version__, str)

    # Check that version is not empty
    assert len(map_binning.__version__) > 0

    # Check that version follows semantic versioning pattern (basic check)
    version_parts = map_binning.__version__.split(".")
    assert len(version_parts) >= 2  # At least major.minor

    # Check that major and minor are numeric
    assert version_parts[0].isdigit()
    assert version_parts[1].isdigit()


def test_binning_import():
    """Test that Binning class can be imported."""
    assert hasattr(map_binning.binning, "Binning")
    assert callable(Binning)


def test_binning_hasattr():
    """Test hasattr for Binning class and object."""
    # Check class attributes
    assert hasattr(Binning, "__init__")
    assert hasattr(Binning, "create_binning_index")
    assert hasattr(Binning, "mean_binning")


def test_index_store_imports():
    """Test that index store functions can be imported."""
    # Test that save and load functions exist
    assert callable(save)
    assert callable(load)
    assert callable(PickleHandler)


def test_index_store_hasattr():
    """Test hasattr for PickleHandler class and object."""
    # Check class attributes (PickleHandler methods)
    assert hasattr(PickleHandler, "__init__")
    assert hasattr(PickleHandler, "save_index_dict")  # Correct method name
    assert hasattr(PickleHandler, "load_index_dict")  # Correct method name
    # Check object attributes
    handler = PickleHandler()
    assert hasattr(handler, "default_dir")


def test_package_structure():
    """Test that the package has the expected structure."""
    # Test that required modules exist and can be imported
    from map_binning import binning, index_store

    # Module imports should work without error
    assert binning
    assert index_store
