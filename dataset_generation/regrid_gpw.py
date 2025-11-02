"""
regrid_gpw.py

Regrids a GPW (Gridded Population of the World) population raster
to match the spatial resolution and extent of a global MODIS-based grid.

- Input:  GPW population density raster (tif)
- Output: Regridded population density raster matching MODIS global grid specifications

Expected runtime:
~9 min (tested on CSU Cluster with 64 CPUs)

"""

import rioxarray as rio
from affine import Affine
from rasterio.crs import CRS
from rasterio.enums import Resampling
import argparse
import time

DATA_DIR = "../data/"  # Path to data in cluster
GPW_DATA_DIR = f"{DATA_DIR}GPW_pop_density/"  # Path to GPW data


def parse_args():
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Regrid GPW rasters to MODIS 250m grid"
    )
    parser.add_argument("year", type=int, help="Year corresponding to GPW file")
    return parser.parse_args()


def get_filepaths(year):
    """
    Construct input and output file paths for GPW population density data.

    Parameters
    ----------
    year : int
        The year of the population dataset to construct paths for.

    Returns
    -------
    tuple of str
        A tuple containing:
        - gpw_filepath: path to the raw input GeoTIFF file
        - output_filepath: path to the output NetCDF file
    """
    gpw_filepath = (
        f"{GPW_DATA_DIR}gpw_v4_population_density_rev11_{year}_30_sec_{year}.tif"
    )
    output_filepath = f"{GPW_DATA_DIR}gpw_population_density_250m_{year}.nc"
    return gpw_filepath, output_filepath


def get_modis_global_grid():
    """
    Returns the spatial reference and grid parameters for the global MODIS data grid.

    This includes the coordinate reference system (CRS) in WGS 84 geographic
    coordinates, the affine transformation mapping pixel coordinates to
    geographic coordinates, the pixel resolution, grid dimensions, and the
    geographic bounding box.

    Returns
    -------
    dict
        A dictionary with the following keys:
        - "crs": rasterio.crs.CRS object representing the WGS 84 geographic CRS.
        - "transform": affine.Affine object defining the geotransform from
          pixel space to longitude/latitude coordinates.
        - "resolution": tuple of float (x_resolution, y_resolution) in degrees.
        - "width": int, number of pixels in the x (longitude) direction.
        - "height": int, number of pixels in the y (latitude) direction.
        - "bounds": tuple (min_lon, min_lat, max_lon, max_lat) defining the
          geographic extent of the grid in degrees.
    """
    return {
        "crs": CRS.from_wkt(
            'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
            'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,'
            'AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,'
            'AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],'
            'AUTHORITY["EPSG","4326"]]'
        ),
        "transform": Affine(
            0.002245788210298804, 0.0, -180.0, 0.0, -0.002245788210298804, 90.0
        ),
        "resolution": (0.002245788210298804, 0.002245788210298804),
        "width": 160300,
        "height": 80150,
        "bounds": (-180.0, -90.0, 180.0, 90.0),
    }


def main():
    """
    Main execution function to regrid GPW population rasters to the MODIS grid.

    Loads population density rasters for multiple years, regrids them to match
    a predefined MODIS-based global grid, and exports each regridded raster to netcdf format.

    Also prints progress updates and total elapsed time.
    """

    start_time = time.time()

    # Parse command line arguments
    args = parse_args()
    year = args.year

    print(f"Starting script for year: {year}")

    # Get modis grid
    modis_global_grid = get_modis_global_grid()

    # Get filepaths
    gpw_filepath, output_filepath = get_filepaths(year)

    # Load GPW population dataset as an xarray object
    # Convert no data value -9999 to nan
    gpw_da = rio.open_rasterio(gpw_filepath, masked=True).isel(band=0, drop=True)
    print("Regridding data...")

    # Reproject to match MODIS global grid
    pop_regridded = gpw_da.rio.reproject(
        dst_crs=modis_global_grid["crs"],  # Target CRS (WGS84)
        transform=modis_global_grid["transform"],  # Affine transform for MODIS grid
        shape=(
            modis_global_grid["height"],
            modis_global_grid["width"],
        ),  # Output raster shape
        resampling=Resampling.bilinear,
    )
    print("Successfully regridded data")

    # Add attributes and reformat dataset
    print("Adding attributes and exporting file...")
    pop_regridded.attrs["long_name"] = "Human population density"
    pop_regridded.attrs["transform"] = tuple(modis_global_grid["transform"])
    pop_regridded.attrs["units"] = "people per km^2"
    pop_regridded.attrs["description"] = (
        "GPW human population density, regridded from 30 arc seconds to MODIS 250m resolution"
    )
    pop_regridded.attrs["original_source"] = (
        "https://www.earthdata.nasa.gov/data/projects/gpw"
    )
    pop_regridded["year"] = year
    pop_regridded.name = "population_density"
    pop_regridded = pop_regridded.to_dataset()

    # Output file
    pop_regridded.to_netcdf(output_filepath)
    print(f"Saved file for year {year} to: {output_filepath}")

    # Compute elapsed time
    elapsed = time.time() - start_time
    hours, minutes = divmod(elapsed // 60, 60)
    print("Script complete.")
    print(f"Elapsed time: {int(hours)}h {int(minutes)}m")


if __name__ == "__main__":
    main()
