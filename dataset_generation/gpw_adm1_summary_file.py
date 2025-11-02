"""
gpw_adm1_summary_file.py

Summarize GPW population and area metrics by GAUL ADM1 units.

This script:
- Reads GAUL ADM1 boundaries and computes area (km²).
- Extracts population and density metrics from GPW NetCDF files.
- Joins results by ADM1 code and saves a summary CSV.
"""

import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
from glob import glob

DATA_DIR = "../data/"
GPW_BY_ADM1_DIR = f"{DATA_DIR}GPW_by_adm1/"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1"
OUTPUT_FILEPATH = f"{DATA_DIR}GPW_summary_by_adm1.csv"


def extract_gpw_admin_data(gpw_dir):
    """
    Process GPW NetCDF files to extract population and area metrics by admin unit and year.

    Parameters
    ----------
    gpw_dir : str
        Path to directory containing GPW NetCDF files organized by year subdirectories.
        Expected structure: gpw_dir/YYYY/*.nc

    Returns
    -------
    pandas.DataFrame
        DataFrame with admin units as index and metrics by year as columns.
        Columns follow pattern: {year}_{metric} where metric is one of:
        - total_pop_count: Total population in admin unit
        - average_pop_density: Mean population density (persons/area unit)
        - total_area: Total area of admin unit (in original units)
    """

    # Get all files at once
    all_files = glob(f"{gpw_dir}/*/*.nc")

    results = []

    for filepath in all_files:
        try:
            # Read file
            gpw_ds = xr.open_dataset(filepath)

            # Extract info
            adm1_code = gpw_ds.attrs["adm1_code"]
            year = gpw_ds.attrs["year"]

            # Calculate metrics
            total_pop = gpw_ds["population_count"].sum().item()
            mean_density = gpw_ds["population_count"].mean().item()

            # Store as dict
            results.append(
                {
                    "adm1_code": adm1_code,
                    "year": year,
                    "total_pop_count": total_pop,
                    "average_pop_density": mean_density,
                }
            )

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    # Convert to DataFrame and pivot
    df = pd.DataFrame(results)
    df_pivot = df.pivot(
        index="adm1_code",
        columns="year",
        values=["total_pop_count", "average_pop_density"],
    )

    # Flatten column names
    df_pivot.columns = [f"{col[1]}_{col[0]}" for col in df_pivot.columns]

    # Convert index type to integer
    df_pivot.index = df_pivot.index.astype(int)

    # Add area

    return df_pivot


def main():
    # Calculate areas in km2 for every adm1
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)
    gaul_l1.rename(columns={"ADM1_CODE": "adm1_code"}, inplace=True)
    gaul_l1.set_index("adm1_code", inplace=True)
    gaul_l1["area_km2"] = gaul_l1.to_crs("EPSG:6933").geometry.area / 1e6

    # Extract population count and average density per admin1
    gpw_df = extract_gpw_admin_data(GPW_BY_ADM1_DIR)

    # Combine with GAUL area to get final dataframe
    gpw_df_final = gaul_l1[["area_km2"]].join(gpw_df, how="left")

    # Save file
    gpw_df_final.to_csv(OUTPUT_FILEPATH, index=True)
    print(f"File saved to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    print("Starting script gpw_adm1_summary_file.py")

    main()

    print("Script complete")
