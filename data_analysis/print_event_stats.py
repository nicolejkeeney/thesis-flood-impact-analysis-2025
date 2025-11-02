"""
print_event_stats.py

Print to console missing statistics for use in thesis

To redirect output to a textfile:
python print_event_stats.py > ../data/data_stats_for_paper.txt

"""

import pandas as pd
from data_analysis_utils import filter_by_flags

# Define filepaths
DATA_DIR = "../data/"
EMDAT_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"
DISAG_EVENTS_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"
# PANEL_FILEPATH = f"{DATA_DIR}panel_dataset.csv"


def main():
    # Read in data
    emdat_df = pd.read_csv(EMDAT_FILEPATH)
    events_df = pd.read_csv(DISAG_EVENTS_FILEPATH)
    # panel_df = pd.read_csv(PANEL_FILEPATH)

    print(
        "The following text provides values for infilling statistics about the data.\n"
    )

    ## =========== INTRODUCTION ===========
    print("1. INTRODUCTION\n")
    impact_vars = ["Total Affected", "Total Damage, Adjusted ('000 US$)"]

    # EM-DAT
    print("EM-DAT\n===================")

    id_col = "id"
    num_floods = emdat_df[id_col].nunique()
    print(f"Total number of floods: {num_floods}\n")

    print("Percent floods by subtype:")
    for subtype in emdat_df["Disaster Subtype"].unique():
        emdat_subtype_df = emdat_df[emdat_df["Disaster Subtype"] == subtype]
        percent_of_total = (emdat_subtype_df[id_col].nunique() / num_floods) * 100
        print(f"- {subtype}: {(percent_of_total):.1f}%")

    # ADMIN1-MONTH EVENTS
    print("\nADMIN1-MONTH EVENTS\n===================")

    id_col = "id"
    num_events = events_df[id_col].nunique()
    print(f"Number of unique floods in disagreggated dataset: {num_events}")

    print("\nDate infilling: ")
    for flag, date_type in zip([1, 2], ["Start day", "End day"]):
        date_num_events_infilled = filter_by_flags(events_df, flags=[flag])[
            id_col
        ].nunique()
        perc_infilled = (date_num_events_infilled / num_events) * 100
        print(f"- {date_type}: {date_num_events_infilled} events; {perc_infilled:.1f}%")

    missing_all_date_info = filter_by_flags(events_df, flags=[9])
    perc_missing_all_date_info = (
        missing_all_date_info[id_col].nunique() / num_events
    ) * 100
    print(f"\nMissing all date info: {perc_missing_all_date_info:.1f}%")

    print("\nLocation infilling:")
    for flags, descrip in zip(
        [[7, 8], 7, 8],
        [
            "Total missing admin units field",
            "Infilled with Location string",
            "Infilled with literature",
        ],
    ):
        num_events_infilled = filter_by_flags(events_df, flags=flags)[id_col].nunique()
        perc_infilled = (num_events_infilled / num_events) * 100
        print(f"- {descrip}: {num_events_infilled} events; {perc_infilled:.2f}%")

    print("\nRegional overview")
    for region_column, region_pretty in zip(
        ["adm1_code", "Country"], ["admin1 regions", "countries"]
    ):
        num_by_region = events_df[region_column].nunique()
        print(f"- Unique {region_pretty}: {num_by_region}")

    print("\nImpact allocation approaches:")
    for flag, approach_num in zip([14, 13, 15], [1, 2, 3]):
        num_events_by_approach = filter_by_flags(events_df, flags=flag)[
            id_col
        ].nunique()
        perc_by_approach = (num_events_by_approach / num_events) * 100
        print(f"- Approach #{approach_num}: {perc_by_approach:.2f}%")

    ## =========== METHODS ===========

    print("\n\n2. METHODS\n")

    # EM-DAT
    print("EM-DAT\n===================")

    print("Statistics by impact variable\n----------------------------")
    for impact_var in impact_vars + ["Total Deaths"]:
        impact_var_col = emdat_df[~emdat_df[impact_var].isna()][impact_var]
        has_data = emdat_df[~(emdat_df[impact_var].isna())]["id"].nunique()
        if impact_var == "Total Damage, Adjusted ('000 US$)":
            impact_var_col = impact_var_col * 1000
            impact_var = "Total Damage, Adjusted"
        print(f"{impact_var}:")
        print(f"- Total: {impact_var_col.sum().item():.0f}")
        print(f"- Mean: {impact_var_col.mean().item():.0f}")
        print(f"- Median: {impact_var_col.median().item():.0f}")
        print(f"- % Floods with Reported Value: {(has_data/num_floods)*100:.1f}%\n")

    print("Statistics by country and subregion\n----------------------------")
    num_regions = 5
    for region_col, region_pretty in zip(
        ["Country", "Subregion"], ["COUNTRIES", "SUBREGIONS"]
    ):
        print(f"{region_pretty}")
        region_count = emdat_df.groupby(region_col)["id"].count()

        print("Highest number of floods: ")
        for region, count in region_count.nlargest(num_regions).items():
            print(f"- {region}: {count}")

        print("\nLowest number of floods: ")
        for region, count in region_count.nsmallest(num_regions).items():
            print(f"- {region}: {count}")

        print("\nLargest percentage of missing damage data:")
        emdat_nancount = (
            emdat_df[emdat_df["Total Damage, Adjusted ('000 US$)"].isna()]
            .groupby(region_col)["id"]
            .count()
        )
        emdat_count = emdat_df.groupby(region_col)["id"].count()
        for region, percentage in (
            (emdat_nancount / emdat_count).nlargest(num_regions).items()
        ):
            print(f"- {region}: {percentage:.2f}")

        print("\nLargest percentage of missing people affected data:")
        emdat_nancount = (
            emdat_df[emdat_df["Total Affected"].isna()]
            .groupby(region_col)["id"]
            .count()
        )
        emdat_count = emdat_df.groupby(region_col)["id"].count()
        for region, percentage in (
            (emdat_nancount / emdat_count).nlargest(num_regions).items()
        ):
            print(f"- {region}: {percentage:.2f}")

        print("\n")

    # ADMIN1-MONTH EVENTS
    print("ADMIN1-MONTH EVENTS\n===================")

    no_pixels_detected = filter_by_flags(events_df, flags=12)
    pixels_detected = events_df[events_df["num_flooded_pixels"] > 0]
    perc_no_pixels = (
        no_pixels_detected["mon-yr-adm1-id"].nunique()
        / events_df["mon-yr-adm1-id"].nunique()
    ) * 100
    print(
        f"Percentage of admin1-month events with no flooded pixels detected: {perc_no_pixels:.2f}%"
    )

    print("\nEvent duration statistics:")
    print(f"- Mean event duration: {events_df['event_duration (days)'].mean():.2f}")
    print(f"- Median event duration: {events_df['event_duration (days)'].median()}")
    print(
        f"- Median event duration for events with flooded pixels detected: {pixels_detected['event_duration (days)'].median()}"
    )
    print(
        f"- Median event duration for events with no flooded pixels detected: {no_pixels_detected['event_duration (days)'].median()}"
    )

    print("\nEvent counts by admin1 region")
    event_counts = events_df.groupby("adm1_code")["mon-yr-adm1-id"].count()
    print(f"- Mean event count by admin1 region: {event_counts.mean():2f}")
    print(f"- Median event count by admin1 region: {event_counts.median()}")


if __name__ == "__main__":
    main()
