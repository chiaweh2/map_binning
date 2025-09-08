# Tutorial: Getting Started with Map Binning

This tutorial will walk you through the basic usage of the Map Binning package, from installation to performing your first spatial resampling operation.

## Prerequisites

Before starting, make sure you have:
- Python 3.11 or higher
- Basic familiarity with xarray and NumPy
- Geospatial data in NetCDF or similar format

## Installation

Install the package using pip or conda:

```bash
# Using pip
pip install map-binning

# Using conda
conda install -c conda-forge map-binning
```

## Tutorial Overview

This tutorial covers:
1. Loading and preparing your data
2. Creating a binning instance
3. Generating binning indices
4. Performing different types of binning
5. Saving and loading results
6. Working with time series data

## Step 1: Import Required Libraries

```python
import numpy as np
import xarray as xr
from map_binning.binning import Binning
import matplotlib.pyplot as plt
```

## Step 2: Prepare Your Data

### Loading Sample Data

```python
# Load high-resolution dataset
ds_high = xr.open_dataset('path/to/high_resolution_data.nc')

# Load low-resolution target grid
ds_low = xr.open_dataset('path/to/low_resolution_grid.nc')

# Inspect your data
print("High-res shape:", ds_high.dims)
print("Low-res shape:", ds_low.dims)
print("Variables:", list(ds_high.data_vars))
```

### Creating Sample Data (for testing)

If you don't have real data, create sample datasets:

```python
# Create high-resolution sample data
lon_high = np.linspace(-180, 180, 360)
lat_high = np.linspace(-90, 90, 180)
temp_high = 15 + 10 * np.random.randn(180, 360)

ds_high = xr.Dataset({
    'temperature': (['lat', 'lon'], temp_high)
}, coords={
    'lat': lat_high,
    'lon': lon_high
})

# Create low-resolution target grid
lon_low = np.linspace(-180, 180, 72)
lat_low = np.linspace(-90, 90, 36)
temp_low = np.zeros((36, 72))

ds_low = xr.Dataset({
    'temperature': (['lat', 'lon'], temp_low)
}, coords={
    'lat': lat_low,
    'lon': lon_low
})
```

## Step 3: Create Binning Instance and Perform Binning

```python
# Initialize the binning object and perform mean binning
>>> import xarray as xr
>>> from map_binning.binning import Binning
>>> ds_high = xr.open_dataset('high_res_data.nc')
>>> ds_low = xr.open_dataset('low_res_grid.nc')
>>> binning = Binning(ds_high, ds_low, var_name='temperature')
>>> binned_data = binning.mean_binning()
>>> print(binned_data)

print("Binning completed successfully!")
```

### Using a Custom Search Radius

```python
# You can also specify a custom search radius
binning_custom = Binning(
    ds_high=ds_high,
    ds_low=ds_low,
    var_name='temperature',
    radius=2.0  # Optional: search radius in degrees
)
binned_data_custom = binning_custom.mean_binning()
```

## Step 4: Perform Additional Binning Operations

### Using Precomputed Binning Index for Better Performance

For multiple operations on the same grids, you can use precomputed indices:

```python
# Create a binning index for reuse
binning = Binning(ds_high, ds_low, var_name='temperature')
index = binning.create_binning_index()

# Now use the precomputed index for faster binning
result_with_index = binning.mean_binning(precomputed_binning_index=index)
print("Binning with precomputed index completed!")
```

## Step 5: Perform Different Types of Binning

### Basic Mean Binning

```python
# Perform mean binning (most common operation)
binning = Binning(ds_high, ds_low, var_name='temperature')
result_mean = binning.mean_binning()
print("Mean binning completed!")

# Inspect the result
print("Result shape:", result_mean.dims)
print("Result variables:", list(result_mean.data_vars))
```

## Step 6: Visualize Results

```python
# Plot original high-resolution data
fig, axes = plt.subplots(1, 2, figsize=(15, 4))

# Original high-res data
ds_high.temperature.plot(ax=axes[0], cmap='coolwarm')
axes[0].set_title('High Resolution (Original)')

# Mean binning result
result_mean.temperature.plot(ax=axes[1], cmap='coolwarm')
axes[1].set_title('Mean Binning Result')

plt.tight_layout()
plt.show()
```

## Step 7: Save and Load Binning Index

### Saving for Reuse

```python
# Save the binning index for future use
from map_binning.index_store import save, load

# First create the index
binning = Binning(ds_high, ds_low, var_name='temperature')
index = binning.create_binning_index()

# Save the binning index
save(index, 'temperature_binning_index.pkl')
print("Binning index saved!")

# Save the results
result_mean.to_netcdf('temperature_mean_binned.nc')
print("Results saved!")
```

### Loading Previously Saved Index

```python
# Load the saved binning index
loaded_index = load('temperature_binning_index.pkl')
print("Binning index loaded!")

# Use the loaded index for new binning operations
binning = Binning(ds_high, ds_low, var_name='temperature')
new_result = binning.mean_binning(precomputed_binning_index=loaded_index)
print("Binning with loaded index completed!")
```

## Step 8: Working with Time Series

When working with time series data:

```python
# For time series data, iterate over time steps
if 'time' in ds_high.dims:
    binned_timeseries = []
    
    for t in ds_high.time:
        # Create binning index once (outside the loop)
        if t == ds_high.time[0]:
            binning_index = Binning(ds_high.sel(time=t), ds_low, 'temperature').create_binning_index()
        
        # Extract single time step
        ds_high_t = ds_high.sel(time=t)
        
        # Create binning instance for this time step
        binning_t = Binning(ds_high_t, ds_low, 'temperature')
        
        # Perform binning using the precomputed index
        result_t = binning_t.mean_binning(precomputed_binning_index=binning_index)
        binned_timeseries.append(result_t)

    # Concatenate results along time dimension
    final_result = xr.concat(binned_timeseries, dim='time')
    print("Time series binning completed!")
```

## Best Practices

### Performance Tips

1. **Reuse binning indices**: Create the index once and reuse it for multiple variables or time steps
2. **Choose appropriate radius**: Smaller radius = more precise but potentially more gaps
3. **Memory management**: For large datasets, consider processing in chunks

### Quality Control

```python
# Check for gaps in binned data
result_stats = result_mean.temperature.isnull().sum()
print(f"Number of NaN values: {result_stats.values}")

# Compare statistics
print("\nOriginal data stats:")
print(f"Mean: {ds_high.temperature.mean().values:.2f}")
print(f"Std: {ds_high.temperature.std().values:.2f}")

print("\nBinned data stats:")
print(f"Mean: {result_mean.temperature.mean().values:.2f}")
print(f"Std: {result_mean.temperature.std().values:.2f}")
```

## Next Steps

Now that you've completed the basic tutorial, you can:

1. Explore the [API Reference](api_reference.md) for advanced features
2. Check out more complex examples with real-world data
3. Learn about optimization techniques for large datasets
4. Integrate Map Binning into your analysis workflows

## Troubleshooting

### Common Issues

**Issue**: "No points found within radius"
- **Solution**: Increase the search radius or check coordinate system compatibility

**Issue**: "Memory error with large datasets"
- **Solution**: Process data in smaller chunks or increase system memory

**Issue**: "Inconsistent coordinate systems"
- **Solution**: Ensure both datasets use the same coordinate reference system

For more help, check the project's GitHub issues or documentation.