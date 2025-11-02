"""
combine_csvs.py

This script combines multiple CSV files from a specified directory into a single consolidated CSV file.

It performs the following:
1. Verifies the existence of the input directory.
2. Collects all CSV files from the directory.
3. Reads each CSV file into a pandas DataFrame.
4. Concatenates all individual DataFrames into one.
5. Saves the combined DataFrame to a specified output filepath.

Usage:
Run the script directly. The combined CSV will be saved to the path specified in `OUTPUT_FILEPATH`.
"""

import pandas as pd
from glob import glob

from utils.utils_misc import check_dir_exists


# Data directory
DATA_DIR = "../data/"

# Combine emdat data
# INPUT_DATA_DIR = f"{DATA_DIR}emdat/emdat_split/"
# OUTPUT_FILEPATH = f"{DATA_DIR}emdat_floods_by_mon_yr_adm1.csv"

# Combine event metrics csv files
INPUT_DATA_DIR = f"{DATA_DIR}event_metrics/"
OUTPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/event_metrics.csv"

# Combine GPW by Admin 1 success report csv files
# INPUT_DATA_DIR = f"{DATA_DIR}GPW_by_adm1/success_reports_by_adm1/"
# OUTPUT_FILEPATH = f"{DATA_DIR}GPW_by_adm1/success_report_all.csv"


def main():
    print("Starting script combine_gpw_adm1_success_reports.py")
    print(f"Input data directory: {INPUT_DATA_DIR}\nOutput filepath: {OUTPUT_FILEPATH}")

    # Ensure that the directory containing the input csvs exists
    check_dir_exists(INPUT_DATA_DIR)

    # Get a list of all CSV files in the folder
    csv_files_all = glob(f"{INPUT_DATA_DIR}*.csv")

    # Read each CSV into a DataFrame and store in a list
    print(f"Reading in {len(csv_files_all)} csv files from directory {INPUT_DATA_DIR}")
    if len(csv_files_all) > 0:
        dfs = [pd.read_csv(file) for file in csv_files_all]
    else:
        raise ValueError(f"No files found")

    # Combine into a single DataFrame
    print("Combining individual DataFrames into a single DataFrame")
    combined_df = pd.concat(dfs, ignore_index=True)

    # Export to csv file
    print("Outputting DataFrame as csv")
    combined_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"File saved to {OUTPUT_FILEPATH}")

    print("Script complete")


if __name__ == "__main__":
    main()
