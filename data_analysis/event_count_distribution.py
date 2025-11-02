"""
event_count_distribution.py

Generate boxplots and histograms showing the distribution of flood events
and Admin1-Month events per region.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 18
TICK_FONTSIZE = 13
LABEL_FONTSIZE = 14
plt.rcParams["font.family"] = "Georgia"

# Input paths
DATA_DIR = "../data/"
SUMMARY_STATS_DIR = f"{DATA_DIR}summary_stats/"
EVENTS_ADM1_FILEPATH = f"{SUMMARY_STATS_DIR}adm1_event_summary_stats.csv"
OUTPUT_DIR = "../figures/summary_stats/event_count_distributions/"


def plot_id_distribution(df, id_col, bar_color="teal", savepath=None):
    """
    Plot a boxplot and histogram of a selected ID column, with descriptive labels.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the column to plot
    id_col : str
        Column name in df to plot
    bar_color: str, optional
        Matplotlib color for bars on barplot
    savepath : str, optional
        Path to save the figure. If None (default), figure is displayed but not saved.
    """
    # Map column names to descriptive strings
    descrip_dict = {
        "mon-yr-adm1-id_count": "Admin1-Month Event",
        "id_count": "Flood",
    }
    id_descrip = descrip_dict[id_col]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Box plot
    df.boxplot(
        column=id_col,
        vert=False,  # horizontal
        ax=ax1,
        patch_artist=True,
        boxprops=dict(facecolor="#A6CEE3", color="black", linewidth=1),
        medianprops=dict(color="#D55E00", linewidth=1),
        whiskerprops=dict(color="black", linewidth=1),
        capprops=dict(color="black", linewidth=1),
    )

    # Add a vertical line at the median
    median_val = int(df[id_col].median())
    ax1.axvline(median_val, color="#D55E00", linestyle="--", linewidth=0.75)

    # Annotate the median value on the x-axis
    ax1.text(
        median_val,
        -0.031,  # just below the axis
        f"{median_val:.0f}",
        ha="center",
        va="top",
        color="#D55E00",
        fontsize=TICK_FONTSIZE,
        transform=ax1.get_xaxis_transform(),
    )

    ax1.set_title(f"{id_descrip} Count Distribution", fontsize=TITLE_FONTSIZE)
    ax1.set_xlabel(
        f"Number of {id_descrip}s per Admin 1 Region", fontsize=LABEL_FONTSIZE
    )
    ax1.set_yticklabels(["count"])
    ax1.tick_params(labelsize=TICK_FONTSIZE)

    # Histogram
    bins = np.arange(0.5, df[id_col].max() + 1.5, 1)
    df[id_col].hist(
        bins=bins, ax=ax2, zorder=10, linewidth=0.8, edgecolor="black", color=bar_color
    )
    ax2.set_xlabel(
        f"Number of {id_descrip}s per Admin 1 Region", fontsize=LABEL_FONTSIZE
    )
    ax2.set_ylabel("Number of Regions", fontsize=LABEL_FONTSIZE)
    ax2.set_title(f"{id_descrip} Frequency Distribution", fontsize=TITLE_FONTSIZE)
    ax2.tick_params(labelsize=TICK_FONTSIZE)
    ax2.grid(axis="x", visible=False)  # Turn off x gridlines, keep x

    plt.tight_layout(pad=3.0)

    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to: {savepath}")


def distribution_hist_only(df, id_col, bar_color="teal", savepath=None):
    """
    Plot histogram of a selected ID column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the column to plot
    id_col : str
        Column name in df to plot
    bar_color : str, optional
        Matplotlib color for bars
    savepath : str, optional
        Path to save the figure. If None, figure is displayed but not saved.
    """
    # Map column names to descriptive strings
    descrip_dict = {
        "mon-yr-adm1-id_count": "Admin1-Month Event",
        "id_count": "Flood",
    }
    id_descrip = descrip_dict[id_col]

    fig, ax = plt.subplots(1, 1, figsize=(6, 5))

    # Histogram
    bins = np.arange(0.5, df[id_col].max() + 1.5, 1)
    df[id_col].hist(
        bins=bins, ax=ax, zorder=10, linewidth=0.6, edgecolor="black", color=bar_color
    )

    ax.set_xlabel(
        f"Number of {id_descrip}s per Admin 1 Region", fontsize=LABEL_FONTSIZE
    )
    ax.set_ylabel("Number of Regions", fontsize=LABEL_FONTSIZE)
    ax.set_title(f"{id_descrip} Frequency Distribution", fontsize=TITLE_FONTSIZE)
    ax.tick_params(labelsize=TICK_FONTSIZE)
    ax.grid(axis="x", visible=False)

    plt.tight_layout()

    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to: {savepath}")


def main():
    # Make output dir if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read in data
    events_df = pd.read_csv(EVENTS_ADM1_FILEPATH)

    # By admin1-month event
    plot_id_distribution(
        df=events_df,
        id_col="mon-yr-adm1-id_count",
        savepath=f"{OUTPUT_DIR}adm1_month_count_distribution.png",
    )
    distribution_hist_only(
        df=events_df,
        id_col="mon-yr-adm1-id_count",
        bar_color="teal",
        savepath=f"{OUTPUT_DIR}adm1_month_count_histogram.png",
    )

    # By flood event
    plot_id_distribution(
        df=events_df,
        id_col="id_count",
        savepath=f"{OUTPUT_DIR}flood_count_distribution.png",
    )


if __name__ == "__main__":
    main()
