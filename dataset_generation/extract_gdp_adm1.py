"""
extract_gdp_adm1.py

GDP zonal statistics extraction
Extracts gridded GDP data by administrative units (ADM1), aggregating the gridded GDP data using a mean.

Input: Gridded GDP raster (1990-2022) + GAUL administrative boundaries
Output: A single CSV with GDP values by administrative unit and year

"""

import rioxarray as rio
import geopandas as gpd
from exactextract import exact_extract
import pandas as pd
from tqdm import tqdm
from functools import reduce
import time

DATA_DIR = "../data/"
GDP_FILEPATH = f"{DATA_DIR}gdp/rast_gdpTot_1990_2022_5arcmin.tif"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1/"
GDP_OUTPUT_FILEPATH = f"{DATA_DIR}gdp/gdp_by_adm1.csv"


def main():
    # Read in data
    gdp_ds = rio.open_rasterio(GDP_FILEPATH)
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)

    # Rename to lowercase
    gaul_l1.rename(columns={"ADM1_CODE": "adm1_code"}, inplace=True)

    # Assign year to band (int 0:33) for better readability
    gdp_years = list(gdp_ds.attrs["long_name"])
    gdp_years = [
        year.replace("_tot", "") for year in gdp_years
    ]  # Remove "tot" substring
    gdp_ds["band"] = gdp_years
    gdp_ds = gdp_ds.rename({"band": "year"})

    gdp_years_concat_list = []  # List of pd.DataFrame to append to
    for year_str in tqdm(gdp_years, desc="Processing GDP years"):
        # Extract by every adm1 code for a single year of gdp data
        gdp_year_df = exact_extract(
            rast=gdp_ds.sel(year=year_str),
            vec=gaul_l1,  # vector to extract raster data to
            ops=["mean"],  # Aggregation operation to perform
            include_cols="adm1_code",
            output="pandas",
            progress=False,
        )
        gdp_year_df.rename(columns={"mean": year_str}, inplace=True)

        gdp_years_concat_list.append(gdp_year_df)

    # After loop, merge all DataFrames:
    gdp_merged = reduce(
        lambda left, right: pd.merge(left, right, on="adm1_code", how="outer"),
        gdp_years_concat_list,
    )

    # No data for 2023/2024
    # Assign 2023 and 2024 GDP to 2022 GDP
    gdp_merged["gdp_2023"] = gdp_merged["gdp_2022"]
    gdp_merged["gdp_2024"] = gdp_merged["gdp_2022"]

    # Export file
    gdp_merged.to_csv(GDP_OUTPUT_FILEPATH, index=False)
    print(f"Saved file to {GDP_OUTPUT_FILEPATH}")


if __name__ == "__main__":
    # Start timer
    start_time = time.time()

    # Run main code
    main()

    # Compute elapsed time
    elapsed = time.time() - start_time
    hours, minutes = divmod(elapsed // 60, 60)
    print("Script complete.")
    print(f"Elapsed time: {int(hours)}h {int(minutes)}m")
