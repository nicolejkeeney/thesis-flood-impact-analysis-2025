"""
preprocess_emdat.py



"""

import pandas as pd
import numpy as np

DATA_DIR = "../data/"
INPUT_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024.csv"
OUTPUT_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"


def adjust_2024_events(emdat_df):
    """
    EM-DAT economic damages have only been adjusted through 2023
    Need to adjust 2024 damages using consumer price index (CPI)

    """
    # CPI ratio: CPI_2024/CPI_2023
    CPI_ratio = 1.029495111

    # Only modify 2024 rows, preserve existing adjusted values for other years
    emdat_df.loc[
        emdat_df["Start Year"] == 2024, "Total Damage, Adjusted ('000 US$)"
    ] = (
        emdat_df.loc[emdat_df["Start Year"] == 2024, "Total Damage ('000 US$)"]
        / CPI_ratio
    )

    return emdat_df


def main():

    # Read in data
    emdat_df = pd.read_csv(INPUT_FILEPATH)

    # Clean up the table
    emdat_df.rename(columns={"DisNo.": "id"}, inplace=True)
    emdat_df.replace({None: np.nan}, inplace=True)

    # Subset for inland floods
    emdat_df = emdat_df[emdat_df["Disaster Type"] == "Flood"]
    emdat_df = emdat_df[emdat_df["Disaster Subtype"] != "Coastal flood"]

    # Drop rows missing critical date info (Start or End Year/Month)
    before = len(emdat_df)
    required_date_fields = (
        emdat_df["Start Year"].notna()
        & emdat_df["Start Month"].notna()
        & emdat_df["End Year"].notna()
        & emdat_df["End Month"].notna()
    )
    emdat_df = emdat_df[required_date_fields]
    after = len(emdat_df)
    print(f"Dropped {before - after} rows due to missing Start or End Year/Month")

    # Fill in damages in 2024
    emdat_df = adjust_2024_events(emdat_df)

    # Export csv
    emdat_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"File exported to: {OUTPUT_FILEPATH}")

    return emdat_df


if __name__ == "__main__":
    main()
