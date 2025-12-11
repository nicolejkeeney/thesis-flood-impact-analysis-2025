"""
event_metrics_cleanup.py

Add event duration
Reorder index
Correct countries where adm0 does not match GAUL naming

"""

import pandas as pd

DATA_DIR = "../data/"
EMDAT_NONDISAGREGGATED_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"  # Original, un-disagreggated data
INPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/event_metrics_with_pop_weighted_damages_and_flags.csv"
OUTPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags.csv"

# Dictionary mapping problematic adm1_codes to correct countries per GAUL
# These codes appear in multiple countries in the source data but should be assigned to one country
COUNTRY_CORRECTIONS = {
    2720: "Spain",
    2961: "Timor-Leste",
    25351: "Montenegro",
    25355: "Montenegro",
    25356: "Montenegro",
    25365: "Montenegro",
    25372: "Serbia",
    25373: "Serbia",
    25375: "Serbia",
    25376: "Serbia",
    25378: "Serbia",
    25379: "Serbia",
    25381: "Serbia",
    25385: "Serbia",
    25389: "Serbia",
    25394: "Serbia",
    25395: "Serbia",
    40408: "Jammu and Kashmir",
    40409: "Jammu and Kashmir",
    40422: "Jammu and Kashmir",
    40423: "Jammu and Kashmir",
    40424: "Jammu and Kashmir",
    40425: "Jammu and Kashmir",
    40426: "Jammu and Kashmir",
    40427: "Jammu and Kashmir",
    40428: "Jammu and Kashmir",
    40429: "Jammu and Kashmir",
    40430: "Jammu and Kashmir",
    40431: "Jammu and Kashmir",
}


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

    # Correct country assignments for problematic admin1 codes
    print(
        "Correcting country assignments for admin1 codes where theres a mismatch between EM-DAT and GAUL..."
    )
    for code, correct_country in COUNTRY_CORRECTIONS.items():
        mask = input_df["adm1_code"] == code
        if mask.any():
            input_df.loc[mask, "Country"] = correct_country
    print(f"Corrected {len(COUNTRY_CORRECTIONS)} admin1 codes")

    # Export
    input_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"File exported to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
