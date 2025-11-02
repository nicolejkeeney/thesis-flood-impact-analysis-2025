"""
compute_zonal_stats.py

This script computes daily MSWEP/MSWX zonal statistics by administrative level 1 (admin 1) code
for a given year. It extracts raster data for precipitation, temperature, wind, and humidity, and
computes daily mean and quantile statistics for each administrative region. The results are saved
as a NetCDF file.

Parameters
----------
--year : int
    The year of precipitation data to process.
-- day: int
    The day of the year

Returns
-------
None
    Outputs a NetCDF file containing the clipped and averaged data for each admin 1 region.
"""

import argparse
import geopandas as gpd
import xarray as xr
import os
import numpy as np
from datetime import date
from exactextract import exact_extract
import inspect
import time

# Run local or in the cluster?
LOCAL = False  # Run in the cluster
# LOCAL = True # Run on local machine, for testing

# Local data directory
LOCAL_DATA_DIR = "../data/"
LOCAL_OUTPUT_DIR = f"{LOCAL_DATA_DIR}zonal_stats/"  # Directory for output netcdf

# Cashew HPC data directorys
DAV_CASHEW_DATA_DIR = (
    "../../../DATA/"  # Davenport shared data dir, where the MSWX/MSWEP data is located
)
NK_CASHEW_DATA_DIR = "../data/"  # My data, where the GAUL data is located
HPC_OUTPUT_DIR = f"{NK_CASHEW_DATA_DIR}zonal_stats/"  # Directory for output netcdf


def generate_filepaths(day, year, local):
    """
    Generate file paths for various datasets based on the given year and day.

    This function constructs file paths for multiple data files (such as precipitation, temperature, etc.)
    for a specific year and day of the year.

    Parameters
    ----------
    day : float
        The day of the year (1-365/366) to generate file paths for.
    year : int
        The year of the data.
    local: boolean, optional
        If True, retrieve local data directories (Nicole's local)
        If False, retrieve cluster data directories (CSU casher)
        Default to False

    Returns
    -------
    dict
        A dictionary containing the file paths for the required data variables.
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    day_padded = (
        f"{int(day):03d}"  # Convert day to a zero-padded string (e.g., 1 → "001")
    )

    if local:
        gaul_data_dir = f"{LOCAL_DATA_DIR}GAUL_2015/"
        mswep_data_dir = f"{LOCAL_DATA_DIR}MSWEP/"
        mswx_data_dir = f"{LOCAL_DATA_DIR}MSWX_V100/"
        filepaths_dict = {
            "gaul": f"{gaul_data_dir}g2015_2014_1",
            "precip": f"{mswep_data_dir}{year}{day_padded}.nc",
            "temp": f"{mswx_data_dir}Temp/{year}{day_padded}.nc",
            "tmin": f"{mswx_data_dir}Tmin/{year}{day_padded}.nc",
            "tmax": f"{mswx_data_dir}Tmax/{year}{day_padded}.nc",
            "wind": f"{mswx_data_dir}Wind/{year}{day_padded}.nc",
            "rh": f"{mswx_data_dir}RelHum/{year}{day_padded}.nc",
        }

    else:
        gaul_data_dir = f"{NK_CASHEW_DATA_DIR}GAUL_2015/"
        mswep_NRT_data_dir = (
            f"{DAV_CASHEW_DATA_DIR}MSWEP/NRT/Daily/"  # 2020332 --> 2025026
        )
        mswep_past_data_dir = (
            f"{DAV_CASHEW_DATA_DIR}MSWEP/Past/Daily/"  # 1979002 --> 2020365
        )
        # mswx_NRT_data_dir = f"{DAV_CASHEW_DATA_DIR}MSWX_V100/NRT/" # 2024055 --> 2024227
        mswx_past_data_dir = (
            f"{DAV_CASHEW_DATA_DIR}MSWX_V100/Past/"  # 1979001 --> 2024222
        )

        # MSWEP 2020 data is split in two directories
        if year == 2020:
            if day < 332:
                precip = f"{mswep_past_data_dir}{year}{day_padded}.nc"
            else:
                precip = f"{mswep_NRT_data_dir}{year}{day_padded}.nc"
        elif year < 2020:
            precip = f"{mswep_past_data_dir}{year}{day_padded}.nc"
        elif year > 2020:
            precip = f"{mswep_NRT_data_dir}{year}{day_padded}.nc"
        filepaths_dict = {
            "gaul": f"{gaul_data_dir}g2015_2014_1",
            "precip": precip,
            "temp": f"{mswx_past_data_dir}Temp/Daily/{year}{day_padded}.nc",
            "tmin": f"{mswx_past_data_dir}Tmin/Daily/{year}{day_padded}.nc",
            "tmax": f"{mswx_past_data_dir}Tmax/Daily/{year}{day_padded}.nc",
            "wind": f"{mswx_past_data_dir}Wind/Daily/{year}{day_padded}.nc",
            "rh": f"{mswx_past_data_dir}RelHum/Daily/{year}{day_padded}.nc",
        }

    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")

    return filepaths_dict


def parse_args():
    """
    Parse the command-line arguments for the year of data to process.

    Returns
    -------
    argparse.Namespace
        The parsed arguments containing the year of data to process.
    """
    parser = argparse.ArgumentParser(
        description="Compute daily MSWEP precipitation by admin 1 code for an entire year."
    )
    parser.add_argument(
        "--year", type=int, required=True, help="Year of data to process"
    )
    parser.add_argument(
        "--day", type=int, required=True, help="Day of year of data to process"
    )
    return parser.parse_args()


def _extract_by_adm1(rast, vec, ops=["mean"], progress=False):
    """
    Extract values from the raster for each administrative level 1 (admin 1) region
    based on the geometry in the vector (admin1 code).

    Parameters
    ----------
    rast : xarray.DataArray
        The input raster data to extract from.
    vec : geopandas.GeoDataFrame
        The vector data containing the administrative boundaries.
    ops : list of str, optional
        The operations to perform on the raster data (e.g., "mean").
    progress : bool, optional
        If True, display a progress bar during extraction.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with the extracted values for each administrative level 1 region.
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    df = exact_extract(
        rast=rast,
        vec=vec,
        ops=ops,
        include_cols="ADM1_CODE",
        output="pandas",
        progress=progress,
    )
    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")

    return df


def _convert_adm1_df_to_xr(df_adm1, rast):
    """
    Convert the extracted DataFrame with administrative level 1 data to an xarray.Dataset.

    This function sets the ADM1_CODE as the index and assigns the time coordinate from the raster to the
    resulting xarray.Dataset.

    Parameters
    ----------
    df_adm1 : pandas.DataFrame
        The DataFrame containing extracted data for admin 1 regions.
    rast : xarray.DataArray
        The raster data used to assign the time coordinate.

    Returns
    -------
    xarray.Dataset
        The xarray dataset with the extracted values and time coordinates.
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    df_adm1 = df_adm1.set_index("ADM1_CODE")
    daily_mean_da = xr.Dataset.from_dataframe(df_adm1)
    daily_mean_da = daily_mean_da.assign_coords({"time": rast.time})

    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")

    return daily_mean_da


def extract_and_convert_to_xr(rast, vec, ops=["mean"], progress=False):
    """
    Extract values from the raster data for each admin 1 region and convert to xarray.

    This function handles the renaming of the raster dimensions, performs extraction for each region,
    and converts the extracted data to xarray format, adding necessary attributes.

    Parameters
    ----------
    rast : xarray.DataArray
        The input raster data to extract from.
    vec : geopandas.GeoDataFrame
        The vector data containing the administrative boundaries.
    ops : list of str, optional
        The operations to perform on the raster data (e.g., "mean").
    progress : bool, optional
        If True, display a progress bar during extraction.

    Returns
    -------
    xarray.Dataset
        The extracted data converted to an xarray dataset with time coordinates.
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    rast = rast.rename(
        {"lat": "y", "lon": "x"}
    )  # exact_extract requires x, y coordinates; otherwise, a MissingSpatialDimensionError will be raised.
    df_adm1 = _extract_by_adm1(rast, vec, ops, progress)
    extracted_da = _convert_adm1_df_to_xr(df_adm1, rast)

    extracted_da["ADM1_CODE"].attrs = {
        "description": "GAUL admin 1 identification code"
    }
    extracted_da.attrs = {
        "description": "Daily statistics by GAUL admin1 region",
        "date_processed": date.today().strftime("%Y-%m-%d"),
    }

    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")
    return extracted_da


def load_climate_datasets(paths):
    """
    Load individual climate datasets and apply naming corrections.

    Parameters
    ----------
    paths : dict
        Dictionary with keys "precip", "temp", "tmin", "tmax", "wind", and "rh",
        each mapping to the path of a NetCDF file.

    Returns
    -------
    list
        List of xarray.Dataset objects: [precip, temp, tmin_renamed, tmax_renamed, wind, rh].
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    precip = xr.open_dataset(paths["precip"])
    temp = xr.open_dataset(paths["temp"])
    tmin = xr.open_dataset(paths["tmin"])
    tmax = xr.open_dataset(paths["tmax"])
    wind = xr.open_dataset(paths["wind"])
    rh = xr.open_dataset(paths["rh"])

    tmin = tmin.rename({"air_temperature": "min_air_temperature"})
    tmax = tmax.rename({"air_temperature": "max_air_temperature"})

    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")

    return [precip, temp, tmin, tmax, wind, rh]


def merge_datasets(datasets):
    """
    Merge a list of xarray datasets into a single dataset.

    Parameters
    ----------
    datasets : list
        List of xarray.Dataset objects to be merged.

    Returns
    -------
    xarray.Dataset
        Merged dataset containing variables from all input datasets.
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")
    ds = xr.merge(datasets)
    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")
    return ds


def main():
    """
    Main function to process the MSWEP data for a given year-day.

    This function parses the arguments, processes the data for the selected year+day, extracts and computes
    daily statistics for each administrative region, and exports the results to a NetCDF file.
    """
    start_time = time.time()  # Start the timer to track script execution time

    print("Starting main process...")

    # Create output directory if it doesn't already exist
    output_data_dir = LOCAL_OUTPUT_DIR if LOCAL else HPC_OUTPUT_DIR
    os.makedirs(output_data_dir, exist_ok=True)

    # Parse command-line arguments to get the year to process
    args = parse_args()
    year = args.year
    day = args.day

    # Generate file paths
    filepaths = generate_filepaths(day, year, local=LOCAL)

    # Check if all required data files exist; raise error if any file is missing
    for name, filepath in filepaths.items():
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"File not found for variable {name} on day {day}: {filepath}"
            )

    gaul_admin1 = gpd.read_file(filepaths["gaul"])

    # Open the MSWEP and other climate data files as xarray datasets
    precip, temp, tmin, tmax, wind, rh = load_climate_datasets(filepaths)

    # Merge all variables (precip, temp, wind, etc.) into a single xarray object
    all_vars_merged = merge_datasets([precip, temp, tmin, tmax, wind, rh])

    # Extract the mean precipitation statistics by admin1 region
    mean_da = extract_and_convert_to_xr(all_vars_merged, gaul_admin1, ops=["mean"])

    # Extract precipitation quantiles (75th and 90th percentiles) by admin1 region
    precip_quantiles = extract_and_convert_to_xr(
        precip, gaul_admin1, ops=["quantile(q=0.75)", "quantile(q=0.90)"]
    )

    # Set the appropriate attributes for the mean data variables
    for var in mean_da.data_vars:
        varname = var.split("_mean")[0]
        mean_da[var].attrs = all_vars_merged[varname].attrs

    # Rename the quantile variables for clarity
    precip_quantiles = precip_quantiles.rename(
        {
            "quantile_75": "precipitation_quantile_75",
            "quantile_90": "precipitation_quantile_90",
        }
    )

    # Merge the mean and quantile data into a single dataset
    stats_ds = merge_datasets([mean_da, precip_quantiles])

    # Export the merged dataset to a NetCDF file
    print("Exporting data to NetCDF...")
    day_padded = (
        f"{int(day):03d}"  # Convert day to a zero-padded string (e.g., 1 → "001")
    )
    filepath = f"{output_data_dir}{year}{day_padded}_zonal_stats.nc"
    stats_ds.to_netcdf(filepath)
    print("Successfully exported file")

    # Print the total execution time in minutes
    end_time = time.time()
    execution_time_minutes = round(
        (end_time - start_time) / 60
    )  # Convert seconds to minutes
    print(
        f"Execution time: {execution_time_minutes} minutes"
    )  # Print the execution time in minutes


if __name__ == "__main__":
    main()
