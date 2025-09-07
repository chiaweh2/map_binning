import os

import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

from map_binning.index_store import load, save


class Binning:
    """
    Class for binning high-resolution data onto a low-resolution grid.

    Parameters
    ----------
    ds_high : xr.Dataset
        High-resolution dataset containing the source data to be binned.
        dimension order has to be ['time','lat','lon']
    ds_low : xr.Dataset
        Low-resolution dataset defining the target grid for binning.
        dimension order has to be ['time','lat','lon']
    xdim_name : str, optional
        Name of the x (longitude) dimension in the datasets. Default is 'lon'.
    ydim_name : str, optional
        Name of the y (latitude) dimension in the datasets. Default is 'lat'.
    search_radius : float or None, optional
        Radius in degrees to search for high-resolution points around each low-resolution grid point.
        If None, the radius is automatically calculated based on the spacing of the low-resolution grid.

    Methods
    -------
    create_binning_index()
        Creates a mapping from each low-resolution grid point to the
        indices of high-resolution grid points within the specified search radius.

    Examples
    --------
    >>> import xarray as xr
    >>> from map_binning.binning import Binning
    >>> ds_high = xr.open_dataset('high_res_data.nc')
    >>> ds_low = xr.open_dataset('low_res_grid.nc')
    >>> binning = Binning(ds_high, ds_low, var_name='temperature')
    >>> binning_index = binning.create_binning_index()
    >>> binned_data = binning.mean_binning()
    >>> print(binned_data)
    xr.DataArray with binned mean values on the low-resolution grid.
    """

    def __init__(
        self,
        ds_high: xr.Dataset,
        ds_low: xr.Dataset,
        var_name: str,
        xdim_name: str = "lon",
        ydim_name: str = "lat",
        search_radius=None,
    ):
        self.ds_high = ds_high
        self.ds_low = ds_low
        self.var_name = var_name
        self.xdim_name = xdim_name
        self.ydim_name = ydim_name
        self.search_radius = search_radius

    def create_binning_index(self):
        """
        Create a mapping dictionary where each low-res point maps to
        indices of high-res points within a certain radius.

        Returns
        -------
        dict
            A dictionary mapping each low-res grid point to
            a list of high-res points within the search radius.

        """
        # Get coordinate arrays
        high_lats = self.ds_high[self.ydim_name].values
        high_lons = self.ds_high[self.xdim_name].values
        low_lats = self.ds_low[self.ydim_name].values
        low_lons = self.ds_low[self.xdim_name].values

        # check high-res is having more grid than low-res
        if len(high_lats) < len(low_lats):
            raise ValueError(
                "High-resolution dataset latitude must have more grid points than low-resolution dataset."
            )
        if len(high_lons) < len(low_lons):
            raise ValueError(
                "High-resolution dataset longitude must have more grid points than low-resolution dataset."
            )

        # Create meshgrids for high-res points
        high_lon_grid, high_lat_grid = np.meshgrid(high_lons, high_lats)
        high_points = np.column_stack([high_lat_grid.ravel(), high_lon_grid.ravel()])

        # Build KDTree (Binary tree) for fast spatial queries
        tree = cKDTree(high_points)

        # Auto-calculate search radius if not provided
        if self.search_radius is None:
            # Use half the distance between low-res points as radius
            lat_spacing = np.abs(np.diff(low_lats)).mean()
            lon_spacing = np.abs(np.diff(low_lons)).mean()
            self.search_radius = max(lat_spacing, lon_spacing) * 0.6

        binning_index = {}

        # For each low-res point, find nearby high-res points
        for i, lat in enumerate(low_lats):
            for j, lon in enumerate(low_lons):
                # Find all high-res points within radius
                indices = tree.query_ball_point([lat, lon], self.search_radius)

                if indices:  # Only store if there are points to bin
                    # Convert 1D indices back to 2D indices for high-res grid
                    lat_indices = np.array(indices) // len(high_lons)
                    lon_indices = np.array(indices) % len(high_lons)
                    binning_index[(i, j)] = list(zip(lat_indices, lon_indices))

        # raise error if no valid binning index is found
        if not binning_index:
            raise ValueError("No valid binning index found.")

        return binning_index

    def mean_binning(
        self,
        precomputed_binning_index: bool = False,
        pickle_filename=None,
        pickle_location=None,
    ):
        """
        Apply the precomputed binning index to aggregate high-res data.

        Parameters
        ----------
        precomputed_binning_index : bool
            A precomputed binning index mapping high-res points to low-res points.
            Defaults to False.
        pickle_location : str, optional
            If provided, the binning index will be saved to/loaded from this file.
        pickle_filename : str, optional
            If provided, the binning index will be saved to/loaded from this file.


        Returns
        -------
        xr.DataArray
            DataArray containing the binned mean values on the low-resolution grid.
        Notes
        -----
        This method assumes that the binning index has been computed in advance and that
        the variable specified by `var_name` exists in `ds_high`.
        """

        # Initialize output array
        output_shape = (
            len(self.ds_low[self.ydim_name]),
            len(self.ds_low[self.xdim_name]),
        )
        if "time" in self.ds_high[self.var_name].dims:
            output_shape = (len(self.ds_high[self.var_name].time),) + output_shape
            output = np.full(output_shape, np.nan)
        else:
            output = np.full(output_shape, np.nan)

        high_data = self.ds_high[self.var_name].values

        if precomputed_binning_index:
            binning_index = load(filename=pickle_filename, location=pickle_location)
        else:
            binning_index = self.create_binning_index()
            if pickle_filename and pickle_location:
                save(binning_index, filename=pickle_filename, location=pickle_location)
            else:
                # save to default name
                pickle_filename = "default_binning_index.pkl"
                # create pickle folder if it doesn't exist
                pickle_location = "pickle_folder"
                os.makedirs(pickle_location, exist_ok=True)
                # save to default location
                save(binning_index, filename=pickle_filename, location=pickle_location)

        # Apply binning for each low-res point
        for (i, j), high_indices in binning_index.items():
            if high_indices:
                # Extract values from high-res points
                lat_idx, lon_idx = zip(*high_indices)

                if "time" in self.ds_high[self.var_name].dims:
                    # Handle time dimension
                    values = high_data[:, lat_idx, lon_idx]
                    # Calculate mean ignore NaN across spatial dimensions, preserving time
                    output[:, i, j] = np.nanmean(values, axis=1)
                else:
                    values = high_data[lat_idx, lon_idx]
                    output[i, j] = np.nanmean(values)

        # Create output DataArray with proper coordinates
        if "time" in self.ds_high[self.var_name].dims:
            coords = {
                "time": self.ds_high[self.var_name].time,
                self.ydim_name: self.ds_low[self.ydim_name],
                self.xdim_name: self.ds_low[self.xdim_name],
            }
            dims = ["time", self.ydim_name, self.xdim_name]
        else:
            coords = {
                self.ydim_name: self.ds_low[self.ydim_name],
                self.xdim_name: self.ds_low[self.xdim_name],
            }
            dims = [self.ydim_name, self.xdim_name]

        return xr.DataArray(output, coords=coords, dims=dims, name=self.var_name)
