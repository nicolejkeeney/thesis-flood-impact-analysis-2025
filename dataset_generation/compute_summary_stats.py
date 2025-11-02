"""
compute_event_level_summary_stats.py

Compute average flood event statistics at multiple administrative levels
(admin1, subregion, region) and export summary CSV files.

- Reads event-level flood data and UNSD M49 country/subregion info
- Aggregates population-weighted damages, affected populations, flooded area,
  and precipitation statistics
- Merges ISO codes and regional classifications
- Outputs summary statistics for admin1, subregion, and region levels
- Creates a summary table of the distribution of flags in the data

"""

import pandas as pd
import os
import inspect
from utils.utils_misc import summarize_flags

DATA_DIR = "../data/"
EVENTS_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"
EMDAT_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"
UNSD_M49_FILEPATH = f"{DATA_DIR}UNSD_M49/UNSD_M49.csv"
OUTPUT_DIR = f"{DATA_DIR}summary_stats/"


def build_flags_df(events_df):
    """
    Create a summary DataFrame of flags from an events DataFrame.

    Parameters
    ----------
    events_df : pd.DataFrame

    Returns
    -------
    pd.DataFrame

    """
    # Summarize flags
    flags_dict = summarize_flags(events_df, verbose=False)

    # Convert to DataFrame
    flags_df = pd.DataFrame(flags_dict).T.reset_index()
    flags_df.columns = [
        "flag",
        "mon_yr_adm1_count",
        "mon_yr_adm1_pct",
        "id_count",
        "id_pct",
    ]

    # Convert flag to integer for proper sorting
    flags_df["flag"] = flags_df["flag"].astype(int)
    flags_df = flags_df.sort_values("flag").reset_index(drop=True)

    return flags_df


def aggregate_events_by_group(df, groupby_column, stat_columns, count_columns):
    """
    Aggregate event data by a grouping column.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing event data.
    groupby_column : str
        Column name to group by.
    stat_columns : list
        Column names to compute statistics for.
    count_columns: list
        Column names to count.

    Returns
    -------
    pandas.DataFrame
        DataFrame with aggregated statistics (mean, median, min, max, count).
    """

    # Compute averages
    mean_df = df[[groupby_column] + stat_columns].groupby(groupby_column).mean()
    mean_df.rename(
        columns={col: f"mean_{col}" for col in stat_columns},
        inplace=True,
    )

    # Compute medians
    median_df = df[[groupby_column] + stat_columns].groupby(groupby_column).median()
    median_df.rename(
        columns={col: f"median_{col}" for col in stat_columns},
        inplace=True,
    )

    # Compute minimums
    min_df = df[[groupby_column] + stat_columns].groupby(groupby_column).min()
    min_df.rename(
        columns={col: f"min_{col}" for col in stat_columns},
        inplace=True,
    )

    # Compute maximums
    max_df = df[[groupby_column] + stat_columns].groupby(groupby_column).max()
    max_df.rename(
        columns={col: f"max_{col}" for col in stat_columns},
        inplace=True,
    )

    # Combine all statistics
    grouped_df = pd.concat([mean_df, median_df, min_df, max_df], axis=1)

    # Compute counts per id (flood) and mon-yr-adm1-id (disaggregated event)
    counts_df = (
        df.groupby(groupby_column).nunique()[count_columns].reset_index(drop=False)
    )
    counts_df.rename(
        columns={col: f"{col}_count" for col in count_columns}, inplace=True
    )

    # Compile final dataframe
    agg_df = grouped_df.merge(counts_df, on=groupby_column, how="left")

    return agg_df


def compute_adm1_level_stats(events_df):
    """
    Compute administrative level 1 statistics for flood events.

    Parameters
    ----------
    events_df : pandas.DataFrame
        DataFrame containing flood event data.

    Returns
    -------
    pandas.DataFrame
        DataFrame with aggregated statistics by administrative level 1 code.
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    # Names to remap columns for better readability
    rename_map = {
        "Total Affected (population-weighted)": "total_affected",
        "Total Affected (population-weighted, normalized)": "total_affected_normalized",
        "Total Damage, Adjusted ('000 US$) (population-weighted)": "damages",
        "Total Damage, Adjusted ('000 US$) (population-weighted, normalized by GDP)": "damages_gdp_standardized",
        "flooded_area (normalized by adm1 area)": "flooded_area_normalized",
    }
    events_df.rename(columns=rename_map, inplace=True)

    # Columns to compute statistics for
    stat_columns = [
        "total_affected",
        "total_affected_normalized",
        "damages",
        "damages_gdp_standardized",
        "flooded_area",
        "flooded_area_normalized",
        "event_precip_mean (mm/day)",
        "event_duration (days)",
    ]

    # Compute stats by region
    events_adm1_df = aggregate_events_by_group(
        df=events_df,
        groupby_column="adm1_code",
        stat_columns=stat_columns,
        count_columns=["id", "mon-yr-adm1-id"],
    )

    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")

    return events_adm1_df


def compute_emdat_stats(emdat_df, m49_df):
    """
    Compute regional and subregional statistics from EM-DAT flood data.

    Parameters
    ----------
    emdat_df : pandas.DataFrame
        Raw EM-DAT disaster events DataFrame.
    m49_df : pandas.DataFrame
        UN M49 country classification DataFrame with regions and subregions.

    Returns
    -------
    tuple of pandas.DataFrame
        Region-level and subregion-level aggregated statistics (region_df, subregion_df).
    """
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    # Names to remap columns for better readability
    rename_map = {
        "Total Affected": "total_affected",
        "Total Damage, Adjusted ('000 US$)": "damages",
    }

    emdat_df.rename(columns=rename_map, inplace=True)

    # Clean up dataframes so they can be easily merged
    m49_df = m49_df[["ISO-alpha3 Code", "Sub-region Name", "Region Name"]].rename(
        columns={
            "ISO-alpha3 Code": "ISO",
            "Sub-region Name": "Subregion",
            "Region Name": "Region",
        }
    )

    # Drop emdat regions since we are mapping to m49 polygons
    emdat_df.drop(columns=["Region", "Subregion"], inplace=True)

    # Merge m49 regions into emdat table in ISO code
    emdat_df = emdat_df.merge(m49_df, on=["ISO"], how="left")

    # These countries do not map, so force them into m49 subregions and regions
    emdat_df.loc[emdat_df["ISO"] == "SCG", ["Region", "Subregion"]] = [
        "Europe",
        "Southern Europe",
    ]  # Serbia Montenegro
    emdat_df.loc[emdat_df["ISO"] == "SPI", ["Region", "Subregion"]] = [
        "Africa",
        "Northern Africa",
    ]  # Canary Islands (Spain, but off the coast of Africa )
    emdat_df.loc[emdat_df["ISO"] == "TWN", ["Region", "Subregion"]] = [
        "Asia",
        "Eastern Asia",
    ]  # Taiwan

    # Columns to compute statistics for
    stat_columns = [
        "total_affected",
        "damages",
    ]

    # Compute stats by region
    emdat_region_df = aggregate_events_by_group(
        df=emdat_df,
        groupby_column="Region",
        stat_columns=stat_columns,
        count_columns=["id"],
    )

    # Compute stats by subregion
    emdat_subregion_df = aggregate_events_by_group(
        df=emdat_df,
        groupby_column="Subregion",
        stat_columns=stat_columns,
        count_columns=["id"],
    )

    print(f"{inspect.currentframe().f_code.co_name}: Completed successfully")

    return (emdat_region_df, emdat_subregion_df)


def main():

    # Read in data
    emdat_df = pd.read_csv(EMDAT_FILEPATH)
    m49_df = pd.read_csv(UNSD_M49_FILEPATH)
    events_df = pd.read_csv(EVENTS_FILEPATH)

    # Make output dir if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate and output flags summary dataframe
    flags_filepath = f"{OUTPUT_DIR}flags_by_event_count.csv"
    flags_df = build_flags_df(events_df)
    flags_df.to_csv(flags_filepath, index=False)
    print(f"Exported flags summary file to {flags_filepath}")

    # Compute & export summary stats by admin 1 region using event-level dataset
    # Population and area normalized columns also computed
    adm1_summary_output_path = f"{OUTPUT_DIR}adm1_event_summary_stats.csv"
    adm1_summary_df = compute_adm1_level_stats(events_df)
    adm1_summary_df.to_csv(adm1_summary_output_path, index=True)
    print(f"Admin1 event summary statistics saved to {adm1_summary_output_path}")

    # Compute & export regional and subregional summary stats using emdat dataset
    subregion_summary_output_path = f"{OUTPUT_DIR}emdat_subregion_summary_stats.csv"
    region_summary_output_path = f"{OUTPUT_DIR}emdat_region_summary_stats.csv"
    emdat_region_df, emdat_subregion_df = compute_emdat_stats(emdat_df, m49_df)
    emdat_region_df.to_csv(region_summary_output_path, index=True)
    emdat_subregion_df.to_csv(subregion_summary_output_path, index=True)
    print(
        f"Subregional EM-DAT flood summary statistics saved to {subregion_summary_output_path}"
    )
    print(
        f"Regional EM-DAT flood summary statistics saved to {region_summary_output_path}"
    )


if __name__ == "__main__":
    main()
