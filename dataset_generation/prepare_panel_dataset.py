"""
prepare_panel_dataset.py

This script creates a panel dataset combining flood event data with climate variables
for econometric analysis of disaster impacts.

Workflow:
1. Load and clean event-level flood data
   - Drop events missing temporal/spatial information
   - Rename columns for clarity
   - Filter out flagged events (flags 9, 10, 11)

2. Create event impact indicators
    - Did an event occur in that admin1-month? (1=Yes, 2=No)

3. Handle missing impact data
   - Fill missing damages/affected population with 5th percentile values
   - Conservative approach to avoid overestimating disaster effects

4. Create panel structure
   - Aggregate multiple events within same admin1_code-month
   - Generate complete admin1_code × month-year grid (2000-2024)
   - Fill non-event periods with 2nd percentile values

5. Add climate variables
   - Process precipitation data to monthly standardized anomalies
   - Merge with panel dataset

Output: Balanced panel dataset for regression analysis with flood impacts and climate controls.
Binary flags preserve distinction between true events and infilled values.
"""

import pandas as pd
import xarray as xr
import sys
import numpy as np
import geopandas as gpd

sys.path.append("../data_analysis")
from data_analysis_utils import filter_by_flags

DATA_DIR = "../data/"
EVENT_LEVEL_FLOOD_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"
ZONAL_STATS_FILEPATH = f"{DATA_DIR}zonal_stats_all.nc"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1"
OUTPUT_FILEPATH = f"{DATA_DIR}panel_dataset.csv"


def main():

    # Read in data
    event_df = pd.read_csv(EVENT_LEVEL_FLOOD_FILEPATH)
    zonal_stats_ds = xr.open_dataset(ZONAL_STATS_FILEPATH)
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)

    ## PREPARE EVENT DATA

    # Drop events that don't have a mon-yr
    # This could be due to missing location and/or date information
    event_df = event_df[~event_df["mon-yr"].isna()].reset_index(drop=True)

    # Rename cols for better readability / coding ease
    cols_map = {
        "Total Affected (population-weighted, normalized)": "total_affected_normalized",
        "Total Damage, Adjusted ('000 US$) (population-weighted, normalized by GDP)": "damages_gdp_standardized",
        "Total Affected (population-weighted)": "total_affected",
        "Total Damage, Adjusted ('000 US$) (population-weighted)": "damages",
    }
    event_df.rename(columns=cols_map, inplace=True)

    # Drop events that have no mon-yr or admin1 code information
    event_df = filter_by_flags(event_df, flags=[9, 10, 11], exclude=True)

    ## COMPUTE FILL VALUES USING PERCENTILES

    # get the 5th percentile of impacts, rounded to the 4th decimal
    total_affected_event_fillvalue, damages_event_fillvalue = (
        event_df[["total_affected_normalized", "damages_gdp_standardized"]]
        .quantile(0.05)
        .round(5)
    )
    print(
        f"5th percentile:\n--------------\nTotal affected (normalized): {total_affected_event_fillvalue}\nGDP-standardized damages: {damages_event_fillvalue}\n"
    )

    # get the 2nd percentile of impacts, rounded to the 4th decimal
    total_affected_no_event_fillvalue, damages_no_event_fillvalue = (
        event_df[["total_affected_normalized", "damages_gdp_standardized"]]
        .quantile(0.02)
        .round(5)
    )
    print(
        f"2nd percentile:\n--------------\nTotal affected (normalized): {total_affected_no_event_fillvalue}\nGDP-standardized damages: {damages_no_event_fillvalue}"
    )

    # Infill events with missing damages or people affected
    event_df["total_affected_normalized"] = event_df[
        "total_affected_normalized"
    ].fillna(total_affected_event_fillvalue)
    event_df["damages_gdp_standardized"] = event_df["damages_gdp_standardized"].fillna(
        damages_event_fillvalue
    )

    # Binary flag: event ocurred (1) or no (0)
    event_df["event_occurrance"] = 1

    ## PREPARE PANEL DATASET

    # Get unique admin1_codes from original data
    unique_admin1 = event_df["adm1_code"].unique()

    # Generate all mon-yr combinations from 2000-2024
    years = range(2000, 2025)
    months = range(1, 13)
    all_mon_yr = [f"{month:02d}-{year}" for year in years for month in months]

    # Create complete index
    complete_index = pd.MultiIndex.from_product(
        [unique_admin1, all_mon_yr], names=["adm1_code", "mon-yr"]
    )

    # Sum events that occur in the same mon-yr and admin1_code (before creating complete panel)
    event_df_agg = (
        event_df.groupby(["mon-yr", "adm1_code"])
        .agg(
            {
                "total_affected_normalized": "sum",
                "total_affected": "sum",
                "damages": "sum",
                "damages_gdp_standardized": "sum",
                "event_occurrance": "max",
            }
        )
        .reset_index()
    )

    # Create complete index and merge with aggregated data
    panel_df = pd.DataFrame(index=complete_index).reset_index()
    panel_df = panel_df.merge(event_df_agg, on=["adm1_code", "mon-yr"], how="left")

    # Fill missing values (only once per admin1_code-mon-yr)
    panel_df["damages_gdp_standardized"] = panel_df["damages_gdp_standardized"].fillna(
        damages_no_event_fillvalue
    )
    panel_df["total_affected_normalized"] = panel_df[
        "total_affected_normalized"
    ].fillna(total_affected_no_event_fillvalue)

    # Compute log
    panel_df[f"ln_damages_gdp_standardized"] = panel_df[
        "damages_gdp_standardized"
    ].apply(np.log)
    panel_df[f"ln_total_affected_normalized"] = panel_df[
        "total_affected_normalized"
    ].apply(np.log)

    ## PREPARE CLIMATE DATA

    # Get monthly mean precip from daily data
    precip_da = zonal_stats_ds["precipitation_mean"]
    precip_monthly_da = precip_da.resample(time="MS").mean()

    # Compute standardized anomaly
    std_anom_da = (
        precip_monthly_da - precip_monthly_da.mean(dim="time")
    ) / precip_monthly_da.std(dim="time")
    std_anom_da.name = "precip_std_anom"

    # Format like panel dataset
    std_anom_df = (
        std_anom_da.to_dataframe().reset_index()
    )  # Convert xr.DataArray --> pd.DataFrame
    std_anom_df["mon-yr"] = std_anom_df["time"].dt.strftime(
        "%m-%Y"
    )  # Get mon-yr column from time coordinate
    std_anom_df.drop(columns="time", inplace=True)

    ## AGGREGATE EVENT AND CLIMATE INFO TO FORM PANEL DATASET

    panel_df = panel_df.merge(std_anom_df, on=["mon-yr", "adm1_code"], how="left")

    ## DROP ADM1 CODES WHERE THERE ARE NO FLOODS

    panel_df = panel_df[panel_df["adm1_code"].isin(event_df["adm1_code"].unique())]

    # Merge in country name
    gaul_l1.columns = gaul_l1.columns.str.lower()
    panel_df = panel_df.merge(
        gaul_l1[["adm1_code", "adm1_name", "adm0_code", "adm0_name"]],
        on="adm1_code",
        how="left",
    )

    # Add country fixed effects
    panel_df.rename(columns={"adm0_name": "country"}, inplace=True)
    panel_df["country-yr"] = (
        panel_df["country"] + "_" + panel_df["mon-yr"].str[-4:]
    )  # Extract year
    panel_df["country-mon"] = (
        panel_df["country"] + "_" + panel_df["mon-yr"].str[:2]
    )  # Extract month

    # Fill NaN with zero for people affected and damages (absolute values)
    # These were not infilled
    panel_df[["damages", "total_affected"]] = panel_df[
        ["damages", "total_affected"]
    ].fillna(0)

    # If this is NaN, it means no event occurred
    panel_df["event_occurrance"] = panel_df["event_occurrance"].fillna(0)

    ## EXPORT
    panel_df.to_csv(OUTPUT_FILEPATH, index=False)
    print(f"Panel dataset saved to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
