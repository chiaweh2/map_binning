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

## Citation
[![DOI](https://zenodo.org/badge/1050687709.svg)](https://doi.org/10.5281/zenodo.17095448)

If you use this tool in your research, please cite:

```bibtex
@software{map_binning_2025,
  author = {Chia-Wei Hsu},
  title = {Map Binning Tool: Spatial Resampling for Oceanographic Data},
  url = {https://github.com/chiaweh2/map_binning},
  doi = {10.5281/zenodo.17095448},
  year = {2025}
}
```

```{tableofcontents}
```
