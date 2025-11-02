"""
plot_impact_allocation_approaches.py

Generate summary statistics and visualizations comparing the three impact allocation
approaches used for disaggregating flood damages across admin1-month events.

Creates population weight distribution histograms and splits-per-flood stripplots
for each approach:
- Approach #1 (Flag 14): Population-weighted allocation when all events have flood maps
- Approach #2 (Flag 13): Equal allocation when no events have flood maps
- Approach #3 (Flag 15): Hybrid allocation when some events have flood maps

Outputs plots to figures/summary_stats/impact_allocation_approaches/
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

from data_analysis_utils import filter_by_flags

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 18
TICK_FONTSIZE = 13
LABEL_FONTSIZE = 14
plt.rcParams["font.family"] = "Georgia"

# Filepaths
DATA_DIR = "../data/"
EVENTS_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"
FIGS_DIR = "../figures/"
OUTPUT_DIR = f"{FIGS_DIR}impact_allocation_approaches/"


def _plot_population_weight_distribution(
    df, flags, descrip_str=None, savepath=None, color="skyblue", bin_number=30
):
    """
    Plot histogram of population weights for events with specified flags.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing event data with population_weight column.
    flags : list of str
        List of flag values to filter events by.
    descrip_str : str, optional
        Description string for plot title. If None, uses flag values.
    savepath : str, optional
        Path to save the plot. If None, plot is not saved.
    color : str, optional
        Color for histogram bars. Default is "skyblue".
    bin_number : int, optional
        Number of bins for histogram. Default is 30.

    """
    # Set default description if not provided
    if descrip_str is None:
        descrip_str = f"Flag(s) {', '.join(flags)}"

    # Filter events by flag
    df_filtered = filter_by_flags(df, flags=flags)

    # Get non-nan population weights
    pop_weights = np.sort(
        df_filtered[~df_filtered["population_weight"].isna()]["population_weight"]
    )

    # Exit if all are NaN
    if np.isnan(pop_weights).all():
        print(f"All population weights are NaN for {descrip_str}\nReturning None")
        return

    # Print stats
    print(f"Population weight distribution for {descrip_str}")
    print(f"Minimum population weight: {np.min(pop_weights[np.nonzero(pop_weights)])}")
    print(f"5% percentile: {np.percentile(pop_weights, 5):.05f}")
    print(f"15% percentile: {np.percentile(pop_weights, 15):.05f}")

    # Make plot
    plt.hist(
        pop_weights,
        bins=bin_number,
        edgecolor="black",
        linewidth=0.5,
        color=color,
        zorder=9,
    )
    plt.title(f"{descrip_str}: population weight distribution", fontsize=TITLE_FONTSIZE)
    plt.grid(axis="y", linestyle="-", alpha=0.6, zorder=0)
    plt.xlabel("Weight", fontsize=LABEL_FONTSIZE)
    plt.ylabel("Frequency", fontsize=LABEL_FONTSIZE)

    # Save plot if path provided
    if savepath is not None:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to {savepath}")
        plt.close()


def _plot_splits_per_flood_distribution(
    df, flags, descrip_str=None, savepath=None, color="teal"
):
    """
    Plot stripplot showing distribution of number of splits per flood.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing event data with id and mon-yr-adm1-id columns.
    flags : list of str
        List of flag values to filter events by.
    descrip_str : str, optional
        Description string for plot title. If None, uses flag values.
    savepath : str, optional
        Path to save the plot. If None, plot is not saved.
    color : str, optional
        Color for strip plot points. Default is "teal".

    """
    # Set default description if not provided
    if descrip_str is None:
        descrip_str = f"Flag(s) {', '.join(flags)}"

    # Filter events by flag
    df_filtered = filter_by_flags(df, flags=flags)

    # Count number of splits
    count_num_splits_df = df_filtered.groupby("id").count()
    count_num_splits = count_num_splits_df["mon-yr-adm1-id"].values

    # Create stripplot
    plt.figure(figsize=(8, 4))  # wider for horizontal
    sns.stripplot(x=count_num_splits, color=color, size=4, alpha=0.5)
    plt.title(
        f"{descrip_str}: distribution of number of splits per flood",
        fontsize=TITLE_FONTSIZE,
    )
    plt.xlabel("Number of splits", fontsize=LABEL_FONTSIZE)
    plt.yticks([])  # remove y-axis ticks since it's horizontal
    plt.xticks(fontsize=TICK_FONTSIZE)
    plt.tight_layout()

    # Save plot if path provided
    if savepath is not None:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to {savepath}")
        plt.close()


def main():
    # Make output dir if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read in data
    events_df = pd.read_csv(EVENTS_FILEPATH)

    # Approach #1
    approach_str = "Approach #1"
    flags = ["14"]
    _plot_population_weight_distribution(
        df=events_df,
        flags=flags,
        descrip_str=approach_str,
        savepath=f"{OUTPUT_DIR}{approach_str.replace(' ','').replace('#','').lower()}_pop_weight_distribution.png",
        color="skyblue",
        bin_number=30,
    )
    _plot_splits_per_flood_distribution(
        df=events_df,
        flags=flags,
        descrip_str=approach_str,
        savepath=f"{OUTPUT_DIR}{approach_str.replace(' ','').replace('#','').lower()}_splits_per_flood_distribution.png",
        color="teal",
    )

    # Approach #2
    approach_str = "Approach #2"
    flags = ["13"]
    _plot_population_weight_distribution(
        df=events_df,
        flags=flags,
        descrip_str=approach_str,
        savepath=f"{OUTPUT_DIR}{approach_str.replace(' ','').replace('#','').lower()}_pop_weight_distribution.png",
        color="skyblue",
        bin_number=30,
    )
    _plot_splits_per_flood_distribution(
        df=events_df,
        flags=flags,
        descrip_str=approach_str,
        savepath=f"{OUTPUT_DIR}{approach_str.replace(' ','').replace('#','').lower()}_splits_per_flood_distribution.png",
        color="teal",
    )

    # Approach #3
    approach_str = "Approach #3"
    flags = ["15"]
    _plot_population_weight_distribution(
        df=events_df,
        flags=flags,
        descrip_str=approach_str,
        savepath=f"{OUTPUT_DIR}{approach_str.replace(' ','').replace('#','').lower()}_pop_weight_distribution.png",
        color="skyblue",
        bin_number=30,
    )
    _plot_splits_per_flood_distribution(
        df=events_df,
        flags=flags,
        descrip_str=approach_str,
        savepath=f"{OUTPUT_DIR}{approach_str.replace(' ','').replace('#','').lower()}_splits_per_flood_distribution.png",
        color="teal",
    )


if __name__ == "__main__":
    main()
