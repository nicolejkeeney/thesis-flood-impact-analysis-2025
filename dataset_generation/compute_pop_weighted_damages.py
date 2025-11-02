"""
compute_pop_weighted_damages.py

Takes aggregated EMDAT flood damages and distributes them across disaggregated
administrative admin1-month events based on flooded population proportions or equal weighting
depending on data availability.

"""

import pandas as pd
import numpy as np
from utils.utils_misc import check_file_exists

DATA_DIR = "../data/"
EMDAT_CSV = f"{DATA_DIR}emdat/emdat_floods_by_mon_yr_adm1.csv"
METRICS_CSV = f"{DATA_DIR}event_intermediate_files/event_metrics.csv"
OUTPUT_FILEPATH = (
    f"{DATA_DIR}event_intermediate_files/event_metrics_with_pop_weighted_damages.csv"
)


def main():
    print("Starting script compute_pop_weighted_damages.py")

    # Check input files exist
    check_file_exists(EMDAT_CSV)
    check_file_exists(METRICS_CSV)

    # Load data
    emdat_df = pd.read_csv(EMDAT_CSV)
    metrics_df = pd.read_csv(METRICS_CSV)

    # Get all unique event ids
    event_ids = emdat_df["id"].unique()

    # Loop through each event id, compute population-weighted damages
    combined_dfs = []
    for event_id in event_ids:
        emdat_subset = emdat_df[emdat_df["id"] == event_id]

        # mon-yr-adm1-id contains event_id as a substring
        metrics_subset = metrics_df[
            metrics_df["mon-yr-adm1-id"].str.contains(event_id, na=False)
        ]

        # Merge on keys (make sure keys exist in both dfs)
        # This will give you all the info for all the disagreggated events in a flood
        emdat_subset = pd.merge(
            emdat_subset,
            metrics_subset,
            on=["mon-yr-adm1-id", "adm1_code"],
            how="inner",
        )

        # Convert to type string, fill nans with empty string (just in case)
        emdat_subset["data_processing_flags"] = (
            emdat_subset["data_processing_flags"].fillna("").astype(str)
        )

        # Check for flooded area cases and assign appropriate flags
        flooded_areas = emdat_subset["flooded_area"]
        all_nonzero = (flooded_areas > 0).all()
        any_nonzero = (flooded_areas > 0).any()
        any_zeros_or_nans = ((flooded_areas == 0) | flooded_areas.isna()).any()
        all_zeroes_or_nans = ((flooded_areas == 0) | flooded_areas.isna()).all()

        # All events have detected flooded pixels (no zeroes or nans)
        if all_nonzero:
            emdat_subset = allocate_impacts(emdat_subset, method=1)

        # All events are zeros and nans, do equal split
        elif all_zeroes_or_nans:
            emdat_subset = allocate_impacts(emdat_subset, method=2)

        # Mixed: some disagreggated events have zero or nan maps
        elif any_nonzero and any_zeros_or_nans:
            print(f"Using method 3 for event {event_id}")
            emdat_subset = allocate_impacts(emdat_subset, method=3)

        combined_dfs.append(emdat_subset)

    # Concatenate all event dfs
    df_all = pd.concat(combined_dfs, ignore_index=True)

    # Optionally save to CSV
    print(f"Outputting final csv file to {OUTPUT_FILEPATH}")
    df_all.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print("Successfully output file. Script complete")


def allocate_impacts(df, method):
    """
    Allocate impacts to subevents in flood using different methods.

    Method 1: All flood maps have flooded pixels detected
        - Allocate impacts using population weight based on flooded population
        - Adds data processing flag 14

    Method 2: No flood maps have flooded pixels detected
        - Allocate using equal distribution across all subevents
        - Adds data processing flag 13

    Method 3: Mixed scenario - some disaggregated events have zero or NaN maps
        - Assigns 5% of total impact to missing/zero flood map events (equal distribution)
        - Assigns 95% of total impact to non-zero flood map events (population weighted)
        - Adds data processing flag 15

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing flood event data with columns:
        - 'flooded_population': Population in flooded areas
        - 'flooded_area': Area of flooding
        - 'Total Affected': Number of people affected
        - 'Total Damage, Adjusted (\'000 US$)': Economic damage
        - 'data_processing_flags': Existing processing flags
    method : int
        Allocation method to use (1, 2, or 3)

    Returns
    -------
    pandas.DataFrame
        Modified DataFrame with population-weighted impact allocations and updated flags.
        Contains new columns with suffix " (population-weighted)" for each impact variable.
    """

    def _allocate_using_pop_weight(df, impact_var):
        """Allocate impacts using population weight"""
        df_pop_weight = df.copy()
        df_pop_weight[f"{impact_var} (population-weighted)"] = (
            df_pop_weight[impact_var] * df_pop_weight["population_weight"]
        )
        return df_pop_weight

    if method == 1:
        # All flood maps have flooded pixels detected
        # Allocate impacts using population weight
        df["population_weight"] = (
            df["flooded_population"] / df["flooded_population"].sum()
        )
        df["data_processing_flags"] += "; 14"
        for impact_var in ["Total Affected", "Total Damage, Adjusted ('000 US$)"]:
            df = _allocate_using_pop_weight(df, impact_var)
        return df

    elif method == 2:
        # No flood maps have flooded pixels detected
        # Allocate using equal distribution
        df["population_weight"] = 1 / len(df)
        df["data_processing_flags"] += "; 13"  # Add flag
        for impact_var in ["Total Affected", "Total Damage, Adjusted ('000 US$)"]:
            df = _allocate_using_pop_weight(df, impact_var)
        return df

    elif method == 3:
        # Mixed: some disagreggated events have zero or nan maps

        # Procedure for non-zero flood maps
        subset_nonzero = df[df["flooded_area"] > 0].copy()
        subset_nonzero["population_weight"] = (
            subset_nonzero["flooded_population"]
            / subset_nonzero["flooded_population"].sum()
        )

        # Procedure for missing or zero maps
        subset_zero_or_nan = df[~(df["flooded_area"] > 0)].copy()
        subset_zero_or_nan["population_weight"] = 1 / len(subset_zero_or_nan)

        for impact_var in ["Total Affected", "Total Damage, Adjusted ('000 US$)"]:
            # Percent of impact to assign missing events
            percent_impact = 0.05

            # Just get the value from the first row
            # These are the same for every event
            impact_val = df[impact_var].iloc[0]

            # Re-assign impacts
            subset_nonzero[impact_var] = impact_val * (1 - percent_impact)
            subset_nonzero = _allocate_using_pop_weight(subset_nonzero, impact_var)
            subset_zero_or_nan[impact_var] = impact_val * percent_impact
            subset_zero_or_nan = _allocate_using_pop_weight(
                subset_zero_or_nan, impact_var
            )

            # Reassign impact to the original value
            subset_zero_or_nan[impact_var] = impact_val
            subset_nonzero[impact_var] = impact_val

        df_method_3 = pd.concat([subset_nonzero, subset_zero_or_nan]).reset_index(
            drop=True
        )
        df_method_3["population_weight"] = np.nan
        df_method_3["data_processing_flags"] += "; 15"  # Add flag
        return df_method_3


if __name__ == "__main__":
    main()
