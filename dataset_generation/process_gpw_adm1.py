"""
process_gpw_adm1.py

This script processes population data from the GPW (Gridded Population of the World) dataset
by clipping it to a single ADM1 zone using the GAUL shapefiles. It performs the following:

1. Clips the GPW 250m population density raster to the specified ADM1 zone.
2. Computes gridcell areas (in km²) on the MODIS-like EPSG:4326 grid.
3. Computes total population per grid cell (density × area).
4. Exports one NetCDF file per year containing population density, population count, and gridcell area.

Input:
- ADM1 code (provided via command-line argument)
- GPW population density NetCDFs (one file per year)
- GAUL Level 1 shapefile directory

Output:
- NetCDF files: gpw_adm1_<ADM1_CODE>_year_<YEAR>.nc, stored in GPW_by_adm1/<year>/

Expected runtime:
~10 sec to 30 min, depending on admin1 geometry size (tested on CSU Cluster with 1 CPU)

"""

import os
import time
import argparse

import numpy as np
import pandas as pd
import xesmf as xe
import geopandas as gpd
import xarray as xr
import rioxarray as rio
from datetime import datetime

from utils.utils_misc import check_file_exists, check_dir_exists

# Constants
DATA_DIR = "../data/"
GPW_DIR = f"{DATA_DIR}GPW_pop_density/"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1/"
OUTPUT_DIR = f"{DATA_DIR}GPW_by_adm1/"
SUCCESS_REPORT_DIR = f"{OUTPUT_DIR}success_reports_by_adm1/"

# Years to process data for
YEARS = [2000, 2005, 2010, 2015, 2020]


def parse_args():
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Process GPW data by adm1 code")
    parser.add_argument("adm1_code", type=int, help="Adm1 code")
    return parser.parse_args()


def main():
    print("Starting script process_gpw_adm1.py...")

    # Log start time
    start_time = time.time()

    # Parse command line arguments
    args = parse_args()
    adm1_code = args.adm1_code

    # Make success report directory
    os.makedirs(SUCCESS_REPORT_DIR, exist_ok=True)

    print(f"Admin 1 code: {adm1_code}")

    # Track success and errors for each year
    success_dict = dict(
        zip(YEARS, [False] * len(YEARS))
    )  # Success of each individual year
    success_dict = {"adm1_code": adm1_code} | success_dict
    errors = []

    try:
        # Read in GAUL data
        check_dir_exists(GAUL_L1_FILEPATH)
        gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)

        # Get GAUL info for selected adm1 code
        print("Getting geometry for selected admin 1 code...")
        adm1_row = gaul_l1[gaul_l1["ADM1_CODE"] == int(adm1_code)]
        adm1_name, adm0_name = (
            adm1_row["ADM1_NAME"].item(),
            adm1_row["ADM0_NAME"].item(),
        )

        # Get geometry info
        adm1_geom = adm1_row.geometry
        minx, miny, maxx, maxy = adm1_geom.total_bounds
        print("Successfully read in geometry")

        proceed = True  # Proceed to the years loop

    except Exception as e:
        errors.append(f"{type(e).__name__}: {e}")  # Append error
        proceed = False  # Don't run the years loop

    # Loop through each year
    area_km2 = None
    if proceed:
        for year in YEARS:
            try:
                print(f"Processing data for year: {year}")

                # Set filepaths by year
                OUTPUT_DIR_BY_YEAR = f"{OUTPUT_DIR}{year}/"
                os.makedirs(OUTPUT_DIR_BY_YEAR, exist_ok=True)
                GPW_FILEPATH_BY_YEAR = f"{GPW_DIR}gpw_population_density_250m_{year}.nc"
                check_file_exists(GPW_FILEPATH_BY_YEAR)

                # Read in GPW data
                gpw_ds = (
                    rio.open_rasterio(GPW_FILEPATH_BY_YEAR, masked=True)
                    .squeeze()
                    .drop_vars("band")
                )

                # Clip data to adm1 bounding box to avoid exploding memory
                gpw_bounding_box = gpw_ds.rio.clip_box(
                    minx=minx, miny=miny, maxx=maxx, maxy=maxy
                )

                # Now, clip to adm1 zone
                gpw_adm1 = gpw_bounding_box.rio.clip(
                    adm1_geom, adm1_geom.crs, drop=True, all_touched=True
                )

                if year == 2000:
                    # Area in km² for each grid cell
                    area_km2 = xe.util.cell_area(
                        gpw_adm1.to_dataset(), earth_radius=6357
                    )  # Earth's mean radius in km
                    area_km2.attrs["long_name"] = "gridcell area"

                else:
                    if area_km2 is None:
                        raise ValueError(
                            "Year 2000 failed to compute gridcell area, unable to compute other years"
                        )

                # Get total people per grid cell
                population_per_cell = gpw_adm1 * area_km2
                population_per_cell.name = "population_count"
                population_per_cell.attrs["units"] = "people"

                # Combine all the info
                ds_all = xr.merge([gpw_adm1, population_per_cell, area_km2])
                ds_all.attrs = {
                    "adm1_code": str(adm1_code),
                    "adm1_name": str(adm1_name),
                    "adm0_name": str(adm0_name),
                    "year": str(year),
                }

                # Export to netcdf
                OUTPUT_FILENAME = (
                    f"{OUTPUT_DIR_BY_YEAR}gpw_adm1_{adm1_code}_year_{year}.nc"
                )
                ds_all.to_netcdf(OUTPUT_FILENAME)
                print(f"Exported netcdf file to: {OUTPUT_FILENAME}")

                # Report success to the dictionary
                success_dict[year] = True

            except Exception as e:
                errors.append(f"{type(e).__name__}: {e}")  # Append error

    # Create DataFrame from success report dict
    success_report_df = pd.DataFrame(pd.DataFrame(success_dict, index=[0]))

    # Add error and timestamp to success report DataFrame
    success_report_df["errors"] = ["; ".join(errors)]
    success_report_df["timestamp"] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    # Save information to success report csv
    output_filepath = f"{SUCCESS_REPORT_DIR}{adm1_code}_success_report.csv"
    success_report_df.to_csv(output_filepath, index=False)
    print(f"File saved to: {output_filepath}")

    # Compute elapsed time
    elapsed = time.time() - start_time
    hours, minutes = divmod(elapsed // 60, 60)
    print("Script complete.")
    print(f"Elapsed time: {int(hours)}h {int(minutes)}m")


if __name__ == "__main__":
    main()
