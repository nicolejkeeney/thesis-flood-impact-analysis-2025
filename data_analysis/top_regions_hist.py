"""
top_regions_hist.py

Generate horizontal bar plots of top regions by selected flood statistics.

"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 18
TICK_FONTSIZE = 13
LABEL_FONTSIZE = 14
plt.rcParams["font.family"] = "Georgia"


# Input paths
DATA_DIR = "../data/"
FIGS_DIR = "../figures/"
SUMMARY_STATS_DIR = f"{DATA_DIR}summary_stats/"
EVENTS_ADM1_FILEPATH = f"{SUMMARY_STATS_DIR}adm1_event_summary_stats.csv"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1/"
OUTPUT_DIR = f"{FIGS_DIR}summary_stats/top_regions_hist/"


def plot_top_regions(
    df,
    bar_var,
    color_var=None,
    num_events=10,
    colormap=None,
    figsize=(12, 7),
    title_info=None,
    log_scale=False,
    savepath=None,
    geographic_coloring=False,  # New parameter
):
    """
    Create a horizontal bar plot of top regions by any variable.

    Parameters:
    -----------
    df : DataFrame
        Your events dataframe
    bar_var : str
        Column name to use for bar lengths (what you're ranking by)
    color_var : str or None
        Column name to use for bar coloring, or None for single color
    num_events : int
        Number of top regions to display
    colormap : str
        Matplotlib colormap name or color name
    figsize : tuple, optional
        Figure size (width, height)
    title_info: str, optional
        Add additional info to title, below the default title
    log_scale : bool, optional
        Use logarithmic scale for x-axis (useful for wide-ranging data)
    savepath : str, optional
        If provided, save the figure to this path instead of displaying it
    geographic_coloring : bool, optional
        If True, color bars by country (adm0_name) instead of color_var
    """

    # Dictionary for nice labels
    label_dict = {
        "id_count": "Number of Flood Events",
        "mon-yr-adm1-id_count": "Number of Admin1-Month Events",
        "mean_total_affected": "Mean People Affected",
        "mean_total_affected_normalized": "Mean People Affected (Normalized)",
        "median_total_affected": "Median People Affected",
        "max_total_affected": "Max People Affected",
        "mean_flooded_area_normalized": "Mean Flooded Area (Normalized)",
        "mean_flooded_area": "Mean Flooded Area (km²)",
        "mean_event_precip_mean (mm/day)": "Mean Precipitation (mm/day)",
        "mean_event_duration (days)": "Mean Duration (days)",
        "mean_damages": "Mean Damages ('000 US$)",
        "median_damages": "Median Damages ('000 US$)",
        "max_damages": "Max Damages ('000 US$)",
        "max_damages_gdp_standardized": "Max Damages as % of GDP",
        "mean_damages_gdp_standardized": "Mean Damages as % of GDP",
    }

    # Get top regions based on bar variable
    top_regions = df.nlargest(num_events, bar_var)

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)

    # Handle coloring
    if geographic_coloring:
        # Color by country
        unique_countries = top_regions["adm0_name"].unique()

        # Define a colorblind-friendly palette with high contrast
        # Avoiding red-green combinations for accessibility
        country_colors = {
            "China": "#6a0dad",
            "Colombia": "#bcbd22",
            "India": "#5191df",
            "Pakistan": "#0f610f",
        }

        # If there are countries not in our predefined palette, add more colors
        # Using Paul Tol's colorblind-friendly palette
        additional_colors = [
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]
        for i, country in enumerate(unique_countries):
            if country not in country_colors:
                country_colors[country] = additional_colors[i % len(additional_colors)]

        colors = [country_colors[country] for country in top_regions["adm0_name"]]
        color_label = "Country"

    elif color_var is None:
        color_label = None
        colors = "darkblue" if colormap is None else colormap
    else:
        # Color bars based on selected variable (original functionality)
        colormap = "viridis" if colormap is None else colormap
        colors = plt.colormaps[colormap](
            (top_regions[color_var] - top_regions[color_var].min())
            / (top_regions[color_var].max() - top_regions[color_var].min())
        )
        color_label = label_dict.get(color_var, color_var.replace("_", " ").title())

    # Create bars
    bars = ax.barh(range(len(top_regions)), top_regions[bar_var], color=colors)

    # Create location labels with fallback for missing adm0_name
    top_regions["loc"] = top_regions.apply(
        lambda row: (
            f"{row['adm1_name']}, {row['adm0_name']}"
            if row["adm1_name"] != "Administrative unit not available"
            else f"Unnamed region {int(row['adm1_code'])}, {row['adm0_name']}"
        ),
        axis=1,
    )

    # Set up plot
    ax.tick_params(labelsize=TICK_FONTSIZE)
    ax.set_yticks(range(len(top_regions)))
    ax.set_yticklabels(top_regions["loc"], fontsize=TICK_FONTSIZE)

    # Dynamic labels
    bar_label = label_dict.get(bar_var, bar_var.replace("_", " ").title())

    ax.set_xlabel(bar_label, fontsize=LABEL_FONTSIZE)

    # Dynamic title
    title = f"Top {num_events} Admin1 Regions by {bar_label}"
    if title_info is not None:
        title += f"\n{title_info}"
    ax.set_title(title, fontsize=TITLE_FONTSIZE)

    # Flip the y-axis so that the first item appears at the top of the plot instead of the bottom.
    ax.invert_yaxis()

    # Apply log scale to x-axis
    if log_scale:
        ax.set_xscale("log")

    # Add legend for geographic coloring or colorbar for continuous variables
    if geographic_coloring:
        # Create legend for countries
        unique_countries = top_regions["adm0_name"].unique()
        legend_elements = [
            plt.Rectangle(
                (0, 0), 1, 1, facecolor=country_colors[country], label=country
            )
            for country in unique_countries
        ]
        ax.legend(handles=legend_elements, loc="lower right", fontsize=TICK_FONTSIZE)

    elif color_var is not None:
        # Add colorbar for continuous variables (original functionality)
        sm = plt.cm.ScalarMappable(
            cmap=plt.colormaps[colormap],
            norm=plt.Normalize(
                vmin=top_regions[color_var].min(), vmax=top_regions[color_var].max()
            ),
        )
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label(color_label, fontsize=LABEL_FONTSIZE)
        cbar.ax.tick_params(labelsize=TICK_FONTSIZE)

        # Fix tiny scientific notation on colorbar
        if hasattr(cbar.formatter, "set_powerlimits"):
            cbar.formatter.set_powerlimits((-3, 3))
            cbar.ax.yaxis.get_offset_text().set_fontsize(TICK_FONTSIZE)

    plt.tight_layout()

    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to: {savepath}")


def main():
    def make_savepath(num_events, bar_var, color_var=None):
        """Make path for saving figure based on plot inputs"""
        savepath = f"{OUTPUT_DIR}top_{num_events}_events_by_{bar_var}"
        if color_var is not None:
            savepath += f"_coloredby_{color_var}"
        savepath += ".png"
        return savepath.replace(" ", "_")

    # Make output dir if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read in data
    events_df = pd.read_csv(EVENTS_ADM1_FILEPATH)
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)

    # Add gaul admin 1 names to events df
    gaul_l1.columns = gaul_l1.columns.str.lower()
    events_df = events_df.merge(
        gaul_l1[["adm1_code", "adm1_name", "adm0_name"]], on="adm1_code", how="left"
    )

    # Make and save plots
    num_events = 15
    bar_var = "id_count"
    color_var = "mean_total_affected_normalized"
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        df=events_df,
        bar_var=bar_var,
        color_var=color_var,
        num_events=num_events,
        savepath=savepath,
    )

    num_events = 15
    bar_var = "mon-yr-adm1-id_count"
    color_var = "mean_total_affected_normalized"
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        df=events_df,
        bar_var=bar_var,
        color_var=color_var,
        num_events=num_events,
        savepath=savepath,
    )

    num_events = 20
    bar_var = "mon-yr-adm1-id_count"
    color_var = None
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        df=events_df,
        bar_var=bar_var,
        color_var=color_var,
        num_events=num_events,
        savepath=savepath,
        geographic_coloring=True,
        figsize=(9, 6),
    )

    num_events = 15
    bar_var = "max_damages"
    color_var = "max_damages_gdp_standardized"
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        df=events_df,
        bar_var=bar_var,
        color_var=color_var,
        num_events=num_events,
        savepath=savepath,
    )

    num_events = 15
    bar_var = "max_damages_gdp_standardized"
    color_var = "max_damages"
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        df=events_df,
        bar_var=bar_var,
        color_var=color_var,
        num_events=num_events,
        savepath=savepath,
    )

    min_events = 5
    filtered_df = events_df[events_df["id_count"] >= min_events]
    num_events = 15
    bar_var = "mean_damages"
    color_var = "id_count"
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        filtered_df,
        bar_var=bar_var,
        color_var=color_var,
        # log_scale=True,
        num_events=num_events,
        title_info=f"Filtered for regions with >= {min_events} floods",
        savepath=savepath,
    )

    min_events = 5
    filtered_df = events_df[events_df["id_count"] >= min_events]
    num_events = 15
    bar_var = "mean_damages_gdp_standardized"
    color_var = "id_count"
    savepath = make_savepath(num_events, bar_var, color_var)
    plot_top_regions(
        filtered_df,
        bar_var=bar_var,
        color_var=color_var,
        # log_scale=True,
        num_events=num_events,
        title_info=f"Filtered for regions with >= {min_events} floods",
        savepath=savepath,
    )


if __name__ == "__main__":
    main()
