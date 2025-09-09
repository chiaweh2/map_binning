# Map Binning Tool Documentation

Map Binning is a Python package for efficient spatial resampling using binning methods. It provides tools for transforming high-resolution geospatial data to low-resolution grids with proper handling of coordinate systems and time dimensions.

## Key Features

- **Spatial Resampling**: Efficient transformation from high-resolution to low-resolution data
- **Binning Methods**: Multiple binning algorithms for different use cases
- **Coordinate System Support**: Proper handling of spatial coordinate transformations
- **Time Dimension Support**: Maintains temporal structure during resampling
- **Data Persistence**: Save and load binning indices for reuse
- **Performance Optimized**: Built with NumPy and SciPy for fast computation

## Installation

Install Map Binning from PyPI:

```bash
pip install map-binning
```

Or from conda-forge:

```bash
conda install -c conda-forge map-binning
```

## Quick Start

```python
from map_binning import Binning, save, load
import xarray as xr

# Load your high and low resolution datasets
ds_high = xr.open_dataset('high_res_data.nc')
ds_low = xr.open_dataset('low_res_grid.nc')

# Create binning instance
binning = Binning(ds_high, ds_low, 'temperature')

# Create binning index
index = binning.create_binning_index()

# Perform mean binning
result = binning.mean_binning(index)

# Save binning index for reuse
save(index, 'binning_index.pkl')
```

## Documentation Structure

This documentation is organized into several sections:

- **Tutorials**: Step-by-step guides for common use cases
- **API Reference**: Complete reference for all classes and functions

```{tableofcontents}
```
