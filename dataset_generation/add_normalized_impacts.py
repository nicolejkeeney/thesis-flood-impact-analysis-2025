"""
add_normalized_impacts.py

Add the following columns:
- GDP standardized economic damages (using the GDP for the year of the event)
- Flooded area normalized by admin 1 area
- People affected by population count (using the population count for the closest year with available data)


"""

import pandas as pd
import numpy as np
import geopandas as gpd
from utils.utils_misc import map_years_to_gpw_intervals


DATA_DIR = "../data/"
EVENTS_FILEPATH = f"{DATA_DIR}event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags.csv"
GDP_FILEPATH = f"{DATA_DIR}gdp/gdp_by_adm1.csv"
GPW_FILEPATH = f"{DATA_DIR}GPW_summary_by_adm1.csv"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1/"
OUTPUT_FILEPATH = f"{DATA_DIR}event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags_and_normalized_impacts.csv"


def fill_gdp_with_country_means(gdp_df):
    """
    Fill missing GDP values with the country mean for each year column.

    Parameters
    ----------
    gdp_df : pd.DataFrame
        DataFrame containing 'country', 'adm1_code', and yearly GDP columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with missing GDP values filled by country means.
    """
    # Get mean GDP by country
    gdp_country_mean = gdp_df.groupby("country").mean()
    gdp_country_mean.drop(columns="adm1_code", inplace=True)

    # Fill missing values for each GDP year column
    gdp_cols = [f"gdp_{year}" for year in np.arange(1990, 2025, 1)]
    for col in gdp_cols:
        country_mean_map = gdp_country_mean[col].to_dict()
        gdp_df[col] = gdp_df[col].fillna(gdp_df["country"].map(country_mean_map))

    return gdp_df


def damages_gdp_standardized(
    row, gdp_df, damages_colname="Total Damage, Adjusted ('000 US$)"
):
    """
    Compute GDP-standardized damages

    Parameters
    ----------
    row : pandas.Series
        Row from events dataframe
    gdp_df: DataFrame
        Table with GDP per year per admin1 code
    damages_colname = str
        Name of the column for damages

    Returns
    -------
    float
        GDP-standardized damages
    """
    mon_yr = row["mon-yr"]
    adm1_code = row["adm1_code"]
    damages = row[damages_colname]

    # Skip if missing
    if pd.isna(mon_yr) or pd.isna(adm1_code) or pd.isna(damages):
        return np.nan

    # GDP for that year and adm1 region
    year = int(mon_yr[-4:])
    gdp_yr_adm1 = gdp_df[gdp_df["adm1_code"] == adm1_code][f"gdp_{year}"].item()

    # Return normalized value
    return (damages / gdp_yr_adm1) * 100


def ppl_affected_normalized(row, pop_yr_dict, gpw_df):
    """
    Normalize people affected by total population of administrative region.

    Parameters
    ----------
    row : pandas.Series
        Row from events DataFrame containing people affected, mon-yr, and adm1_code.
    pop_yr_dict : dict
        Dictionary mapping years to GPW reference years.
    gpw_df : pandas.DataFrame
        Table containing area (km2) per admin1 and population counts by admin1 and year.

    Returns
    -------
    float
        People affected as percentage of total population, or NaN if missing data.
    """
    mon_yr = row["mon-yr"]
    adm1_code = row["adm1_code"]
    people_affected = row["Total Affected"]

    # Skip if missing
    if pd.isna(mon_yr) or pd.isna(adm1_code) or pd.isna(people_affected):
        return np.nan

    # Population count for that year and adm1 region
    gpw_year = pop_yr_dict[int(mon_yr[-4:])]
    pop_count_yr_adm1 = gpw_df[gpw_df["adm1_code"] == adm1_code][
        f"{gpw_year}_total_pop_count"
    ].item()

    # Return normalized value
    return (people_affected / pop_count_yr_adm1) * 100


def flooded_area_normalized(row, gpw_df):
    """
    Normalize flooded area by total administrative region area.

    Parameters
    ----------
    row : pandas.Series
        Row from events DataFrame containing flooded area and adm1_code.
    gpw_df : pandas.DataFrame
        Table containing area (km2) per admin1 and population counts by admin1 and year.

    Returns
    -------
    float
        Flooded area divided by total admin1 area, or NaN if missing data.
    """

    adm1_code = row.get("adm1_code")
    flooded_area = row["flooded_area"]

    # Skip if missing
    if pd.isna(adm1_code) or pd.isna(flooded_area):
        return np.nan

    area_km2_adm1 = gpw_df.loc[gpw_df["adm1_code"] == adm1_code, "area_km2"].item()

    return (flooded_area / area_km2_adm1) * 100


def main():

    # Read in data
    events_df = pd.read_csv(EVENTS_FILEPATH)
    gpw_df = pd.read_csv(GPW_FILEPATH)
    gdp_df = pd.read_csv(GDP_FILEPATH)
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)

    # Clean up gaul df
    gaul_l1.rename(
        columns={"ADM1_CODE": "adm1_code", "ADM0_NAME": "country"}, inplace=True
    )
    countries = gaul_l1[["adm1_code", "country"]]

    # Add country into gdp as column
    gdp_df = gdp_df.merge(
        countries[["adm1_code", "country"]], on="adm1_code", how="left"
    )

    # Fill missing data with country means
    # Some admin 1 codes (~70) were not filled by the gridded data zonal extraction
    gdp_df = fill_gdp_with_country_means(gdp_df)

    # Years that correspond to a GPW file
    pop_yr_dict = map_years_to_gpw_intervals()

    # Normalize people affected by population count
    events_df["Total Affected (population-weighted, normalized)"] = events_df.apply(
        ppl_affected_normalized, axis=1, args=(pop_yr_dict, gpw_df)
    )

    # Normalize flooded area by adm1 area
    events_df["flooded_area (normalized by adm1 area)"] = events_df.apply(
        flooded_area_normalized, axis=1, args=(gpw_df,)
    )

    # Normalize economic impacts by GDP
    events_df[
        "Total Damage, Adjusted ('000 US$) (population-weighted, normalized by GDP)"
    ] = events_df.apply(damages_gdp_standardized, axis=1, args=(gdp_df,))

    # Export
    events_df.to_csv(OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"Output file to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
