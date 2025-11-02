"""
add_zonal_stats.py

Compute event-level climate statistics from daily zonal climate data.
Exports a csv file containing event metrics + the climate as new columns

"""

import xarray as xr
import pandas as pd
import numpy as np

DATA_DIR = "../data/"
CLIMATE_DATA_FILEPATH = f"{DATA_DIR}zonal_stats_all.nc"  # Zonal statistics netcdf
EVENTS_FILEPATH = f"{DATA_DIR}event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags_and_normalized_impacts.csv"
OUTPUT_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"


def get_climate_stats(row, clim_ds):
    """
    Compute event-level precipitation statistics for a given event row.
    Parameters
    ----------
    row : pandas.Series
        A row from the events DataFrame containing:
        - 'Start Date' (datetime): Event start date.
        - 'End Date' (datetime): Event end date.
        - 'adm1_code' (int): Administrative unit code.
    clim_ds : xarray.Dataset
        Dataset containing climate info
    Returns
    -------
    pandas.Series
        Event statistics or NaN values if dates or adm1_code are missing
    """
    # Check if Start Date, End Date, or adm1_code is NaN
    if (
        pd.isna(row["Start Date"])
        or pd.isna(row["End Date"])
        or pd.isna(row["adm1_code"])
    ):
        return pd.Series(
            {
                "event_precip_mean (mm/day)": np.nan,
                "event_precip_max (mm/day)": np.nan,
                "event_precip_75_quant_mean (mm/day)": np.nan,
                "event_precip_75_quant_max (mm/day)": np.nan,
            }
        )

    # Original logic if dates are valid
    clim_for_event = clim_ds.sel(
        time=slice(row["Start Date"], row["End Date"]), adm1_code=row["adm1_code"]
    )

    return pd.Series(
        {
            "event_precip_mean (mm/day)": clim_for_event["precipitation_mean"]
            .mean()
            .item(),
            "event_precip_max (mm/day)": clim_for_event["precipitation_mean"]
            .max()
            .item(),
            "event_precip_75_quant_mean (mm/day)": clim_for_event[
                "precipitation_quantile_75"
            ]
            .mean()
            .item(),
            "event_precip_75_quant_max (mm/day)": clim_for_event[
                "precipitation_quantile_75"
            ]
            .max()
            .item(),
        }
    ).round(3)


def reorder_columns(df):
    """
    Reorder DataFrame columns to move specific columns to the end.
    All other columns maintain their original relative order at the beginning.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to reorder columns for.

    Returns
    -------
    pandas.DataFrame
        DataFrame with the same data but reordered columns, with the three
        specified columns moved to the end.

    """
    # Define the columns you want at the end
    end_cols = [
        "Total Affected (population-weighted)",
        "Total Damage, Adjusted ('000 US$) (population-weighted)",
        "flags",
    ]

    # Get all other columns, then add the end columns
    other_cols = [col for col in df.columns if col not in end_cols]
    new_col_order = other_cols + end_cols

    return df[new_col_order]


def main():
    # Read in data
    clim_ds = xr.open_dataset(CLIMATE_DATA_FILEPATH)
    events_df = pd.read_csv(EVENTS_FILEPATH)

    # Add climate columns
    events_df[
        [
            "event_precip_mean (mm/day)",
            "event_precip_max (mm/day)",
            "event_precip_75_quant_mean (mm/day)",
            "event_precip_75_quant_max (mm/day)",
        ]
    ] = ""

    # Convert to datetime
    events_df["Start Date"] = pd.to_datetime(events_df["Start Date"])
    events_df["End Date"] = pd.to_datetime(events_df["End Date"])

    # Apply the function to each row
    events_df[
        [
            "event_precip_mean (mm/day)",
            "event_precip_max (mm/day)",
            "event_precip_75_quant_mean (mm/day)",
            "event_precip_75_quant_max (mm/day)",
        ]
    ] = events_df.apply(get_climate_stats, clim_ds=clim_ds, axis=1)

    # Reorder columns
    events_df = reorder_columns(events_df)

    events_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"Output file to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
