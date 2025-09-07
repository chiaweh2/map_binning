"""
This is a small Python package for map binning that creates low-resolution maps
from high-resolution data. The idea is to group the nearest high-resolution
points around each low-resolution grid point and take their mean, producing a
low-resolution version of the original high-resolution product.
"""

import importlib.metadata

try:
    # retrieve version from package metadata
    __version__ = importlib.metadata.version("map_binning")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development/editable installs
    __version__ = "0.1.0"

from .binning import Binning
from .index_store import PickleHandler, load, save

__all__ = ["Binning", "save", "load", "PickleHandler", "__version__"]
