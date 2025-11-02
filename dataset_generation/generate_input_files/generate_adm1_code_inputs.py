"""
generate_adm1_code_inputs.py

Split Admin 1 codes into lists of large and small areas
Used for processing in HPC

"""

import geopandas as gpd
import pandas as pd
import os
import sys
import math

sys.path.append("../")  # Add one directory up, so you can import the utils module
from utils.utils_misc import check_dir_exists, check_file_exists

DATA_DIR = "../../data/"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1"  # This is a shapefile directory (not a single .shp file) — it contains .shp, .shx, .dbf, etc.
EMDAT_FILEPATH = f"{DATA_DIR}emdat/emdat_floods_by_mon_yr_adm1.csv"
OUTPUT_DIR = "../../text_inputs/adm1_codes/"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    check_dir_exists(GAUL_L1_FILEPATH)
    check_file_exists(EMDAT_FILEPATH)

    # Read in data
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)
    emdat_df = pd.read_csv(EMDAT_FILEPATH)

    # Get unique adm1 codes from emdat only
    # i.e. drop adm1 codes that dont correspond to a flood event
    emdat_adm1_codes = emdat_df["adm1_code"].dropna().astype(int).unique()
    gaul_l1_emdat = gaul_l1[gaul_l1["ADM1_CODE"].isin(emdat_adm1_codes)]

    # Split into large and small areas
    threshold_area = 25
    gaul_l1_emdat = gaul_l1_emdat.sort_values(by="SHAPE_AREA", ascending=False)
    big_adm1_df = gaul_l1_emdat[gaul_l1_emdat["SHAPE_AREA"] >= threshold_area]
    smol_adm1_df = gaul_l1_emdat[gaul_l1_emdat["SHAPE_AREA"] < threshold_area]

    big_adm1 = big_adm1_df["ADM1_CODE"].values  # Get adm1 codes of large area regions
    big_adm1 = [str(int(code)) for code in big_adm1]  # Convert to string
    smol_adm1 = smol_adm1_df["ADM1_CODE"].values  # Get adm1 codes of small area regions
    smol_adm1 = [str(int(code)) for code in smol_adm1]  # Convert to string

    # Construct the output filepaths
    big_adm1_filepath = f"{OUTPUT_DIR}large_adm1_codes.txt"

    # Write each ID to a new line in the output file
    with open(big_adm1_filepath, "w") as f:
        f.write("\n".join(big_adm1))
        print(
            f"Wrote {len(big_adm1)} Admin 1 codes with large areas to {big_adm1_filepath}"
        )

    # Split small codes into batches
    # These will be run in parallel
    # Calculate total batches needed
    batch_size = 440
    num_batches = math.ceil(len(smol_adm1) / batch_size)
    for i in range(num_batches):
        batch_codes = smol_adm1[i * batch_size : (i + 1) * batch_size]
        output_filepath = f"{OUTPUT_DIR}smol_adm1_codes_{i+1}.txt"

        with open(output_filepath, "w") as f:
            f.write("\n".join(batch_codes))
        print(
            f"Wrote {len(batch_codes)} Admin 1 codes with small areas to {output_filepath}"
        )


if __name__ == "__main__":
    main()
