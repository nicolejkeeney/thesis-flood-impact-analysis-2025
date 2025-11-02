"""
event_metrics_cleanup.py

Add event duration
Reorder index

"""

import pandas as pd

DATA_DIR = "../data/"
EMDAT_NONDISAGREGGATED_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"  # Original, un-disagreggated data
INPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/event_metrics_with_pop_weighted_damages_and_flags.csv"
OUTPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags.csv"


def add_event_duration(emdat_df):
    """
    Add event duration

    Parameters
    ----------
    emdat_df : pandas.DataFrame

    Returns
    -------
    emdat_df: pandas.DataFrame
        Dataframe with new "event duration" column

    """

    event_duration = (
        emdat_df["End Date"] - emdat_df["Start Date"] + pd.Timedelta(days=1)
    )
    emdat_df["event_duration (days)"] = event_duration.dt.days

    return emdat_df


def main():
    # Read in data
    input_df = pd.read_csv(INPUT_FILEPATH)
    emdat_orig_df = pd.read_csv(EMDAT_NONDISAGREGGATED_FILEPATH)

    # Convert Start and End Date to datetime
    # I'm not sure why the format is mixed...
    input_df["Start Date"] = pd.to_datetime(input_df["Start Date"], format="mixed")
    input_df["End Date"] = pd.to_datetime(input_df["End Date"], format="mixed")

    # Add event duration
    input_df = add_event_duration(input_df)

    # Sort by original order
    input_df["id"] = pd.Categorical(
        input_df["id"], categories=emdat_orig_df["id"].values, ordered=True
    )
    input_df = input_df.sort_values("id").reset_index(drop=True)

    # Export
    input_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"File exported to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
