"""add_data_flags.py

Add data processing flags to a dataset as a new column "flags".
Flags are integer values; see the accompanying flag description CSV for details.

Description
-----------
- Reads event metrics and EMDAT flood data.
- Merges metrics and logs into a single dataframe.
- Cleans up temporary columns and exports the final dataframe.
- Adds event duration (days)

"""

import pandas as pd
import numpy as np
from utils.emdat_toolbox import add_event_dates
from utils.utils_misc import summarize_flags


DATA_DIR = "../data/"
OUTPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/event_metrics_with_pop_weighted_damages_and_flags.csv"
METRICS_FILEPATH = (
    f"{DATA_DIR}event_intermediate_files/event_metrics_with_pop_weighted_damages.csv"
)
EMDAT_DISAGGREGATED_FILEPATH = f"{DATA_DIR}emdat/emdat_floods_by_mon_yr_adm1.csv"
EMDAT_NONDISAGREGGATED_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"  # Original, un-disagreggated data


def regex(flag):
    """
    Create a regex pattern to match a specific flag in a semicolon-separated string.
    """
    return rf"(?:^|;\s*){flag}(?:$|;\s*)"


def get_missing_rows(emdat_orig_df, emdat_processed_df):
    """
    Identify flood events missing from a processed EMDAT dataset and flag issues.
    Also adds start and end date

    Parameters
    ----------
    emdat_orig_df : pd.DataFrame
        Original EMDAT dataset with all disaster records.
    emdat_processed_df : pd.DataFrame
        Processed EMDAT dataset to compare against.

    Returns
    -------
    pd.DataFrame
        Subset of `emdat_orig_df` for missing events, with added
        `data_processing_flags`, `flags`, `Start Date`, and `End Date` columns.
    """

    # Get IDs that are missing from the final dataset
    orig_ids = emdat_orig_df["id"].unique()
    final_df_ids = emdat_processed_df["id"].unique()
    missing_ids = [id for id in orig_ids if id not in final_df_ids]

    # Create flags column
    missing_df = emdat_orig_df[emdat_orig_df["id"].isin(missing_ids)].copy()
    missing_df["data_processing_flags"] = (
        ""  # This is required for the add_event_dates function
    )
    missing_df["flags"] = ""

    # Get Start and End Date columns
    missing_df = add_event_dates(missing_df)

    # Add flags
    mask9 = missing_df["Start Date"].isna() | missing_df["End Date"].isna()
    missing_df.loc[mask9, "flags"] += "; 9"
    print("Added flag 9")

    mask10 = missing_df["Admin Units"].isna()
    missing_df.loc[mask10, "flags"] += "; 10"
    print("Added flag 10")

    mask11 = missing_df["flags"] == ""
    missing_df.loc[mask11, "flags"] += "; 11"
    print("Added flag 11")

    # Format the date same as the metrics, as a string
    for col in ["Start Date", "End Date"]:
        missing_df[col] = pd.to_datetime(missing_df[col], errors="coerce")
        # Format as MM-DD-YYYY, keep empty string for missing dates
        missing_df[col] = missing_df[col].dt.strftime("%m/%d/%Y")

    return missing_df


def sort_flags(flag_str):
    """
    Sort numbers in a semicolon-separated flag string in ascending order.

    Parameters
    ----------
    flag_str : str
        String of numbers separated by semicolons, e.g., "12; 2; 1".
        Can be empty or contain extra spaces.

    Returns
    -------
    str
        Sorted numbers as a semicolon-separated string, e.g., "1; 2; 12".
        Returns empty string if input is empty or contains no valid numbers.
    """
    if not flag_str:  # handle empty strings or NaN
        return ""
    nums = [int(f) for f in flag_str.split(";") if f.strip()]
    return "; ".join(map(str, sorted(nums)))


def main():
    # Read in data
    print("Reading in data...")
    metrics_df = pd.read_csv(METRICS_FILEPATH)
    emdat_df = pd.read_csv(EMDAT_DISAGGREGATED_FILEPATH)
    emdat_orig_df = pd.read_csv(EMDAT_NONDISAGREGGATED_FILEPATH)

    ## CREATE DATAFRAME FOR COMPILING FLAGS INTO

    # Fill error column with empty string instead of NaN
    metrics_df["metrics_error"] = metrics_df["metrics_error"].fillna("")
    metrics_df["data_processing_flags"] = metrics_df["data_processing_flags"].fillna("")
    emdat_df.drop("data_processing_flags", axis=1, inplace=True)

    print("Got here")
    # Merge metrics into emdat dataframe
    flags_df = emdat_df.merge(
        metrics_df, on=list(emdat_df.columns), how="left"  # column to merge on
    )
    flags_df["flags"] = ""

    ## GET THE ROWS THAT ARE MISSING FROM EMDAT_ORIG_DF
    ## AND ADD APPROPRIATE FLAGS

    print("Got here2")
    missing_df = get_missing_rows(emdat_orig_df, metrics_df)
    missing_df = missing_df[
        [col for col in missing_df.columns if col in flags_df.columns]
    ]
    flags_df = pd.concat([flags_df, missing_df])

    ## REPLACE EMDAT PREPROCESSING STRING FLAGS WITH APPROPRIATE NUMERICAL FLAGS

    # Map substrings to flag numbers and their target columns
    mask1 = flags_df["data_processing_flags"].str.contains(
        "Start day originally NaN", na=False
    )
    flags_df.loc[mask1, "flags"] += "; 1"
    print("Added flag 1")

    mask2 = flags_df["data_processing_flags"].str.contains(
        "End day originally NaN", na=False
    )
    flags_df.loc[mask2, "flags"] += "; 2"
    print("Added flag 2")

    # Just copy these over directly to flags
    mask7 = flags_df["data_processing_flags"].str.contains(regex(7), na=False)
    flags_df.loc[mask7, "flags"] += "; 7"
    print("Added flag 7")

    mask8 = flags_df["data_processing_flags"].str.contains(regex(8), na=False)
    flags_df.loc[mask8, "flags"] += "; 8"
    print("Added flag 8")

    mask13 = flags_df["data_processing_flags"].str.contains(regex(13), na=False)
    flags_df.loc[mask13, "flags"] += "; 13"
    print("Added flag 13")

    mask14 = flags_df["data_processing_flags"].str.contains(regex(14), na=False)
    flags_df.loc[mask14, "flags"] += "; 14"
    print("Added flag 14")

    mask15 = flags_df["data_processing_flags"].str.contains(regex(15), na=False)
    flags_df.loc[mask15, "flags"] += "; 15"
    print("Added flag 15")

    # Multiple substrings for flag 5
    mask5 = flags_df["metrics_error"].str.contains(
        "data/GPW_by_adm1/", na=False
    ) & flags_df["metrics_error"].str.contains("FileNotFound", na=False)
    flags_df.loc[mask5, "flags"] += "; 5"
    print("Added flag 5")

    # Multiple substrings for flag 6
    mask6 = (
        flags_df["metrics_error"].str.contains("ValueError", na=False)
        & flags_df["metrics_error"].str.contains("Coordinate", na=False)
        & flags_df["metrics_error"].str.contains("has mismatched shapes", na=False)
    )
    flags_df.loc[mask6, "flags"] += "; 6"
    print("Added flag 6")

    ## No EE tif generated flags 3 & 4

    # Flag 3
    mask3 = pd.to_datetime(flags_df["Start Date"], format="mixed") < pd.to_datetime(
        "2000-02-25"
    )
    flags_df.loc[mask3, "flags"] += "; 3"
    print("Added flag 3")

    # No tif found for reasons other than 3
    mask4_metrics = (
        flags_df["metrics_error"].str.contains("RasterioIOError", na=False)
        & flags_df["metrics_error"].str.contains(
            ".tif: No such file or directory", na=False
        )
        & (mask3 == False)
    )
    flags_df.loc[mask4_metrics, "flags"] += "; 4"
    print("Added flag 4")

    # Drop emdat preprocessing flag column
    flags_df.drop(columns=["data_processing_flags", "metrics_error"], inplace=True)

    # Flag 12
    mask12 = flags_df["flooded_area"] == 0
    flags_df.loc[mask12, "flags"] += "; 12"
    print("Added flag 12")

    ## COMPILE AND CLEAN FINAL DATASET FOR EXPORT

    # Sort the numbers in each string into ascending order
    flags_df["flags"] = flags_df["flags"].apply(sort_flags)

    # Remove leading "; " from flags column
    flags_df["flags"] = flags_df["flags"].str.lstrip("; ")

    # Print some info about all the flags found
    summarize_flags(flags_df, verbose=True)

    # Export file
    flags_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"File export to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    print("Starting script add_data_flags.py")

    main()

    print("Script complete")
