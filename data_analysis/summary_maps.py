"""
summary_maps.py

Generate choropleth maps of flood events at admin1, subregion, and region levels (2000-2024).

"""

import os
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from time import time
from datetime import timedelta
import inspect

# Figure settings
FIG_DPI = 600
plt.rcParams["font.family"] = "Georgia"

# Input paths
DATA_DIR = "../data/"
SUMMARY_STATS_DIR = f"{DATA_DIR}summary_stats/"
EVENTS_ADM1_FILEPATH = f"{SUMMARY_STATS_DIR}adm1_event_summary_stats.csv"
EVENTS_SUBREGION_FILEPATH = f"{SUMMARY_STATS_DIR}emdat_subregion_summary_stats.csv"
EVENTS_REGION_FILEPATH = f"{SUMMARY_STATS_DIR}emdat_region_summary_stats.csv"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1/"
UNSD_M49_FILEPATH = f"{DATA_DIR}UNSD_M49/UNSD_M49.csv"
COUNTRY_BOUNDARIES_FILEPATH = f"{DATA_DIR}/ne_110m_admin_0_countries"

# Output paths
MAPS_DIR = "../figures/summary_stats/maps/"  # Save the maps in their own folder
MAPS_DIR_ADM1 = f"{MAPS_DIR}adm1_maps/"
MAPS_DIR_REGION = f"{MAPS_DIR}region_maps/"
MAPS_DIR_SUBREGION = f"{MAPS_DIR}subregion_maps/"


def read_and_prepare_data():
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    # Read in data
    events_adm1_df = pd.read_csv(EVENTS_ADM1_FILEPATH)
    events_subregion_df = pd.read_csv(EVENTS_SUBREGION_FILEPATH)
    events_region_df = pd.read_csv(EVENTS_REGION_FILEPATH)
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)
    m49_df = pd.read_csv(UNSD_M49_FILEPATH)
    countries_gdf = gpd.read_file(COUNTRY_BOUNDARIES_FILEPATH)

    # Rename columns for better ease of coding
    m49_df = m49_df[["ISO-alpha3 Code", "Sub-region Name", "Region Name"]].rename(
        columns={
            "ISO-alpha3 Code": "ISO",
            "Sub-region Name": "Subregion",
            "Region Name": "Region",
        }
    )
    countries_gdf.rename(columns={"ISO_A3": "ISO"}, inplace=True)

    # Drop Antarctica from countries...
    countries_gdf = countries_gdf[countries_gdf["ADMIN"] != "Antarctica"]

    # Get geometry for Regions and Subregions
    m49_gdf = m49_df.merge(countries_gdf[["ISO", "geometry"]], on="ISO", how="left")
    m49_gdf = gpd.GeoDataFrame(m49_gdf)
    region_geoms = m49_gdf[["Region", "geometry"]].dissolve(by="Region")
    subregion_geoms = m49_gdf[["Subregion", "geometry"]].dissolve(by="Subregion")

    # Add geometries to events df
    events_subregion_df = events_subregion_df.merge(
        subregion_geoms, on="Subregion", how="left"
    )
    events_region_df = events_region_df.merge(region_geoms, on="Region", how="left")
    events_subregion_df = gpd.GeoDataFrame(events_subregion_df)
    events_region_df = gpd.GeoDataFrame(events_region_df)

    # Clean up gaul gdp so it can be easily merged
    gaul_l1 = gaul_l1[["ADM1_CODE", "geometry"]].rename(
        columns={"ADM1_CODE": "adm1_code"}
    )

    # Add in GAUL geometry for adm1 regions
    events_adm1_df = events_adm1_df.merge(gaul_l1, on="adm1_code", how="left")
    events_adm1_df = gpd.GeoDataFrame(events_adm1_df)

    print(f"{inspect.currentframe().f_code.co_name}: Complete.")

    return [events_adm1_df, events_subregion_df, events_region_df, countries_gdf]


def make_map(
    df,
    col,
    label="",
    vmin=None,
    vmax=None,
    title=None,
    cmap="Blues",
    save_path=None,
    borders=None,
    border_linewidth=0.15,
):
    """
    Plot a geospatial DataFrame on a Robinson projection map.

    Parameters
    ----------
    df : geopandas.GeoDataFrame
        GeoDataFrame containing geometry and the data column to plot.
    col : str
        Column name in `df` to visualize.
    label : str, optional
        Label for the legend colorbar. Default is "".
    vmin : float, optional
        Minimum value for the colormap scaling. If None, inferred from data.
    vmax : float, optional
        Maximum value for the colormap scaling. If None, inferred from data.
    title : str, optional
        Map title. Default is None.
    cmap : str, optional
        Matplotlib colormap to use. Default is "Blues".
    save_path : str, optional
        Path to save the figure. Include file extension (i.e. ".png")
        If provided, the figure is saved to disk.
    borders : geopandas.GeoDataFrame, optional
        GeoDataFrame of boundaries for overlay. Default is None.
    border_linewidth: float, optional
        Linewidth of the borders. Default to 0.15

    Notes
    -----
    The function creates a matplotlib figure but does not return it.
    The plot is displayed inline in interactive environments and
    optionally saved if `save_path` is provided.
    """
    # Initialize figure
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={"projection": ccrs.Robinson()})

    # Compute vmin, vmax if not provided
    if vmin is None:
        vmin = df[col].quantile(0.05)  # 5th percentile
    if vmax is None:
        vmax = df[col].quantile(0.95)  # 95th percentile

    # Plot data
    df.plot(
        column=col,
        cmap=cmap,
        legend=True,
        ax=ax,
        vmin=vmin,
        vmax=vmax,
        legend_kwds={"shrink": 0.5, "label": label, "extend": "max"},
        transform=ccrs.PlateCarree(),
    )

    # Plot additional borders
    if borders is not None:
        borders.boundary.plot(
            ax=ax,
            linewidth=border_linewidth,
            color="grey",
            transform=ccrs.PlateCarree(),
        )

    # Make map pretty
    if title is not None:
        ax.set_title(title, fontsize=14)
    ax.set_axis_off()

    # Save figure
    if save_path is not None:
        plt.savefig(save_path, dpi=FIG_DPI, bbox_inches="tight")
        print(f"{inspect.currentframe().f_code.co_name}: Saved figure to {save_path}")


def make_adm1_maps(events_adm1_df, countries_gdf):
    """
    Generate choropleth maps for admin1-level flood statistics (2000-2024).

    Parameters
    ----------
    events_adm1_df : geopandas.GeoDataFrame
       Admin1 flood events data with geometry and statistics columns.
    countries_gdf : geopandas.GeoDataFrame
       Country boundaries for map borders.
    """

    start_time = time()
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    make_map(
        df=events_adm1_df,
        col="mean_total_affected",
        label="# People",
        vmin=0,
        vmax=80000,
        title="Average Number of People Affected by Admin1-Month Event (2000-2024)",
        cmap="Purples",
        save_path=f"{MAPS_DIR_ADM1}av_affected_adm1.png",
        borders=countries_gdf,
    )

    make_map(
        df=events_adm1_df,
        col="mean_total_affected_normalized",
        label="% of Admin1 Population",
        vmin=0,
        vmax=18,
        title="Average % of Population Affected by Admin1-Month Event (2000-2024)",
        cmap="Purples",
        save_path=f"{MAPS_DIR_ADM1}av_affected_norm_adm1.png",
        borders=countries_gdf,
    )

    # make_map(
    #     df=events_adm1_df,
    #     col="median_total_affected",
    #     label="# people",
    #     vmin=0,
    #     vmax=80000,
    #     title="Median number of people affected by admin1-month flood (2000-2024)",
    #     cmap="Purples",
    #     save_path=f"{MAPS_DIR_ADM1}median_affected_adm1.png",
    #     borders=countries_gdf,
    # )

    make_map(
        df=events_adm1_df,
        col="mean_damages",
        label="Adjusted Damages ('000 US$)",
        vmin=0,
        vmax=350000,
        title="Average Economic Damages by Admin1-Month Event (2000-2024)",
        cmap="Greens",
        save_path=f"{MAPS_DIR_ADM1}av_damages_adm1.png",
        borders=countries_gdf,
    )

    make_map(
        df=events_adm1_df,
        col="mean_damages_gdp_standardized",
        label="Flood Damages as % of GDP",
        vmin=0,
        vmax=5,
        title="Average GDP-Standardized Economic Damages by Admin1-Month Event (2000-2024)",
        cmap="Greens",
        save_path=f"{MAPS_DIR_ADM1}av_damages_norm_adm1.png",
        borders=countries_gdf,
    )

    # make_map(
    #     df=events_adm1_df,
    #     col="max_damages",
    #     label="Damages ('000 US$)",
    #     vmin=0,
    #     vmax=450000,
    #     title="Maximum Economic Damages by Admin1-Month Flood (2000-2024)",
    #     cmap="Greens",
    #     save_path=f"{MAPS_DIR_ADM1}max_damages_adm1.png",
    #     borders=countries_gdf,
    # )

    # make_map(
    #     df=events_adm1_df,
    #     col="max_damages_gdp_standardized",
    #     label="Damages ('000 US$)",
    #     vmin=0,
    #     vmax=5,
    #     title="Maximum GDP-standardized economic damages by admin1-month flood (2000-2024)",
    #     cmap="Greens",
    #     save_path=f"{MAPS_DIR_ADM1}max_damages_adm1.png",
    #     borders=countries_gdf,
    # )

    make_map(
        df=events_adm1_df,
        col="mean_flooded_area",
        label="Area (km)²",
        vmin=0,
        vmax=1000,
        title="Average Flooded Area by Admin1-Month Event (2000-2024)",
        cmap="Blues",
        save_path=f"{MAPS_DIR_ADM1}av_flooded_area_adm1.png",
        borders=countries_gdf,
    )

    make_map(
        df=events_adm1_df,
        col="mean_flooded_area_normalized",
        label="% of Admin1 Area",
        vmin=0,
        vmax=0.5,
        title="Flooded Area by % of Admin 1 Area by Admin1-Month Event (2000-2024)",
        cmap="Blues",
        save_path=f"{MAPS_DIR_ADM1}av_flooded_area_norm_adm1.png",
        borders=countries_gdf,
    )

    # make_map(
    #     df=events_adm1_df,
    #     col="mean_event_duration (days)",
    #     label="Duration (days)",
    #     vmin=0,
    #     vmax=25,
    #     title="Average event duration by admin1-month flood (2000-2024)",
    #     cmap="Oranges",
    #     save_path=f"{MAPS_DIR_ADM1}av_event_duration_adm1.png",
    #     borders=countries_gdf,
    # )

    # make_map(
    #     df=events_adm1_df,
    #     col="mon-yr-adm1-id_count",
    #     label="Number of events",
    #     vmin=0,
    #     vmax=25,
    #     title="Total number of admin1-month flood events (2000-2024)",
    #     cmap="Oranges",
    #     save_path=f"{MAPS_DIR_ADM1}event_count_adm1.png",
    #     borders=countries_gdf,
    # )

    td = timedelta(seconds=int(time() - start_time))
    print(f"{inspect.currentframe().f_code.co_name}: Complete.")
    print(f"{inspect.currentframe().f_code.co_name}: Time elapsed: {td}")


def make_subregion_maps(events_subregion_df):
    """
    Generate choropleth maps for subregional flood statistics.

    Parameters
    ----------
    events_subregion_df : geopandas.GeoDataFrame
        Subregional flood events data with geometry and statistics columns.

    """
    start_time = time()
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    make_map(
        df=events_subregion_df,
        col="mean_total_affected",
        label="# people",
        vmin=0,
        vmax=150000,
        title="Average number of people affected (2000-2024)",
        cmap="Purples",
        save_path=f"{MAPS_DIR_SUBREGION}av_affected_subregion.png",
        borders=events_subregion_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_subregion_df,
        col="median_total_affected",
        label="# people",
        vmin=0,
        vmax=150000,
        title="Median number of people affected (2000-2024)",
        cmap="Purples",
        save_path=f"{MAPS_DIR_SUBREGION}median_affected_subregion.png",
        borders=events_subregion_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_subregion_df,
        col="mean_damages",
        label="Adjusted damages ('000 US$)",
        vmin=0,
        vmax=350000,
        title="Average economic damages (2000-2024)",
        cmap="Greens",
        save_path=f"{MAPS_DIR_SUBREGION}av_damages_subregion.png",
        borders=events_subregion_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_subregion_df,
        col="max_damages",
        label="Adjusted damages ('000 US$)",
        vmin=0,
        vmax=10000000,
        title="Maximum economic damages (2000-2024)",
        cmap="Greens",
        save_path=f"{MAPS_DIR_SUBREGION}max_damages_subregion.png",
        borders=events_subregion_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_subregion_df,
        col="id_count",
        label="Number of events",
        vmin=0,
        vmax=800,
        title="Total number inland floods (2000-2024)",
        cmap="Oranges",
        save_path=f"{MAPS_DIR_SUBREGION}event_count_subregion.png",
        borders=events_subregion_df,
        border_linewidth=0.25,
    )

    td = timedelta(seconds=int(time() - start_time))
    print(f"{inspect.currentframe().f_code.co_name}: Complete.")
    print(f"{inspect.currentframe().f_code.co_name}: Time elapsed: {td}")


def make_region_maps(events_region_df):
    """
    Generate choropleth maps for regional flood statistics.

    Parameters
    ----------
    events_region_df : geopandas.GeoDataFrame
        Regional flood events data with geometry and statistics columns.

    """
    start_time = time()
    print(f"{inspect.currentframe().f_code.co_name}: Starting...")

    make_map(
        df=events_region_df,
        col="mean_total_affected",
        label="# people",
        vmin=10000,
        vmax=150000,
        title="Average number of people affected (2000-2024)",
        cmap="Purples",
        save_path=f"{MAPS_DIR_REGION}av_affected_region.png",
        borders=events_region_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_region_df,
        col="mean_damages",
        label="Damages ('000 US$)",
        vmin=600000,
        vmax=2000000,
        title="Average economic damages (2000-2024)",
        cmap="Greens",
        save_path=f"{MAPS_DIR_REGION}av_damages_region.png",
        borders=events_region_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_region_df,
        col="max_damages",
        label="Adjusted damages ('000 US$)",
        vmin=0,
        vmax=20000000,
        title="Maximum economic damages (2000-2024)",
        cmap="Greens",
        save_path=f"{MAPS_DIR_REGION}max_damages_region.png",
        borders=events_region_df,
        border_linewidth=0.25,
    )

    make_map(
        df=events_region_df,
        col="id_count",
        label="Number of events",
        vmin=100,
        vmax=1500,
        title="Total number inland floods (2000-2024)",
        cmap="Oranges",
        save_path=f"{MAPS_DIR_REGION}event_count_region.png",
        borders=events_region_df,
        border_linewidth=0.25,
    )

    td = timedelta(seconds=int(time() - start_time))
    print(f"{inspect.currentframe().f_code.co_name}: Complete.")
    print(f"{inspect.currentframe().f_code.co_name}: Time elapsed: {td}")


def main():
    # Make output dir if it doesn't already exist
    for dir in MAPS_DIR_ADM1, MAPS_DIR_REGION, MAPS_DIR_SUBREGION:
        os.makedirs(dir, exist_ok=True)

    # Read and prepare data
    (
        events_adm1_df,
        events_subregion_df,
        events_region_df,
        countries_gdf,
    ) = read_and_prepare_data()

    # Make maps!
    # Figure output path is set in these functions
    make_region_maps(events_region_df)
    make_subregion_maps(events_subregion_df)
    make_adm1_maps(events_adm1_df, countries_gdf)


if __name__ == "__main__":
    main()
