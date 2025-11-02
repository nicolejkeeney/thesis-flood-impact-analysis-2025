"""
flag_summary_plots.py

Create histograms of flag count by mon-yr-adm1-id and id
and horizontal bar charts of flag percentages.

"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 18
TICK_FONTSIZE = 13
LABEL_FONTSIZE = 14
plt.rcParams["font.family"] = "Georgia"

# Filepaths
DATA_DIR = "../data/"
EVENTS_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"
FLAGS_FILEPATH = f"{DATA_DIR}summary_stats/flags_by_event_count.csv"
OUTPUT_FIGS_DIR = "../figures/summary_stats/flags/"


def plot_flag_counts(
    flags_df,
    count_col="id_count",
    y_label=None,
    title=None,
    palette="viridis",
    save_path=None,
):
    """
    Plot a bar chart of counts for each flag, with optional saving.

    Parameters
    ----------
    flags_df : pd.DataFrame
        DataFrame with at least columns ['flag', 'id_count', 'mon_yr_adm1_count'].
    count_col : str, optional
        Column to plot on the y-axis. Options are 'id_count' or 'mon_yr_adm1_count'.
        Default is 'id_count'.
    y_label : str, optional
        Label for the y-axis. If None, a default label will be generated from count_col.
    title : str, optional
        Title for the plot. If None, a default title will be generated.
    palette : str or list, optional
        Color palette to use for the bars. Default is 'viridis'.
    save_path : str or None, optional
        File path to save the figure (e.g., "output/plot.png"). If None, the plot is not saved.

    Returns
    -------
    None
        Displays the bar plot and optionally saves it.
    """
    if count_col not in ["id_count", "mon_yr_adm1_count"]:
        raise ValueError("count_col must be 'id_count' or 'mon_yr_adm1_count'")

    plt.figure(figsize=(8, 5))
    sns.barplot(
        data=flags_df, x="flag", y=count_col, hue="flag", palette=palette, legend=False
    )

    # Set title dynamically if not provided
    if title is None:
        title = f"Number of {count_col.replace('_', ' ')} per Flag"

    # Set y-axis label dynamically if not provided
    if y_label is None:
        y_label = count_col.replace("_", " ").title()

    # Apply labels and style
    plt.title(title, fontsize=TITLE_FONTSIZE)
    plt.xlabel("Flag", fontsize=LABEL_FONTSIZE)
    plt.ylabel(y_label, fontsize=LABEL_FONTSIZE)
    plt.xticks(rotation=0, fontsize=TICK_FONTSIZE)
    plt.yticks(fontsize=TICK_FONTSIZE)

    plt.tight_layout()

    # Save if path is provided
    if save_path:
        plt.savefig(save_path, dpi=FIG_DPI, bbox_inches="tight")


def plot_flag_percentages(
    flags_df,
    pct_col="id_pct",
    x_label=None,
    title=None,
    color="mediumpurple",
    save_path=None,
    figsize=(10, 7),
    show_values=True,
):
    """
    Plot a horizontal bar chart of percentages for each flag.

    Parameters
    ----------
    flags_df : pd.DataFrame
        DataFrame with flag data and percentage columns.
    pct_col : str, optional
        Column to plot as percentages. Default is 'id_pct'.
    x_label : str, optional
        Label for the x-axis. If None, auto-generated from pct_col.
    title : str, optional
        Title for the plot. If None, auto-generated.
    color : str, optional
        Bar color. Default is 'skyblue'.
    save_path : str or None, optional
        File path to save the figure. If None, not saved.
    figsize : tuple, optional
        Figure size (width, height). Default is (10, 7).
    show_values : bool, optional
        Whether to show percentage values on bars. Default is True.
    """

    # Sort by percentage (ascending for better visual flow)
    sorted_df = flags_df.sort_values(by=pct_col, ascending=True)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.barh(sorted_df["flag"], sorted_df[pct_col], color=color)

    # Add percentage labels on bars
    if show_values:
        for bar, pct in zip(bars, sorted_df[pct_col]):
            if pct == 0:  # Don't label 0%
                continue
            # Position label at end of bar or inside for very long bars
            label_x = pct + (sorted_df[pct_col].max() * 0.01)  # Small offset
            ax.text(
                label_x,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.2f}%",
                va="center",
                fontsize=TICK_FONTSIZE,
            )

    # Set labels and title with defaults
    x_label = x_label or pct_col.replace("_", " ").title()
    title = title or f"Percentage by {pct_col.replace('_', ' ').title()}"

    # Plot layout
    ax.set_xlabel(x_label, fontsize=LABEL_FONTSIZE)
    ax.set_ylabel("Flag", fontsize=LABEL_FONTSIZE)
    ax.set_title(title, fontsize=TITLE_FONTSIZE)
    ax.set_yticks(np.arange(1, (len(sorted_df)) + 2, 1))
    ax.set_yticklabels(np.arange(1, (len(sorted_df)) + 2, 1), fontsize=TICK_FONTSIZE)
    ax.tick_params(axis="x", labelsize=TICK_FONTSIZE)
    ax.set_xlim(0, sorted_df[pct_col].max() * 1.1)
    plt.tight_layout()

    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=FIG_DPI, bbox_inches="tight")


def main():
    # Read in data
    flags_df = pd.read_csv(FLAGS_FILEPATH)
    # events_df = pd.read_csv(EVENTS_FILEPATH)

    # Make output dir if it doesn't already exist
    os.makedirs(OUTPUT_FIGS_DIR, exist_ok=True)

    # Make and save flag count histogram by ID
    id_filepath = f"{OUTPUT_FIGS_DIR}flags_by_id_hist.png"
    plot_flag_counts(
        flags_df,
        count_col="id_count",
        title="Number of events per flag",
        y_label="Event count",
        save_path=id_filepath,
    )
    print(f"Saved file to {id_filepath}")

    # Make and save flag count histogram by ID
    adm1_month_filepath = f"{OUTPUT_FIGS_DIR}flags_by_adm1_mon_hist.png"
    plot_flag_counts(
        flags_df,
        count_col="mon_yr_adm1_count",
        title="Number of adm1-month events per flag",
        y_label="adm1-month event count",
        save_path=adm1_month_filepath,
    )
    print(f"Saved file to {adm1_month_filepath}")

    # Make and save horizontal bar chart of percentages by ID
    id_pct_filepath = f"{OUTPUT_FIGS_DIR}flags_by_id_pct.png"
    plot_flag_percentages(
        flags_df,
        pct_col="id_pct",
        color="mediumpurple",
        title="Percentage of events by each flag",
        x_label="Percentage of events (%)",
        save_path=id_pct_filepath,
    )
    print(f"Saved file to {id_pct_filepath}")

    # Make and save horizontal bar chart of percentages by mon-yr-adm1
    adm1_pct_filepath = f"{OUTPUT_FIGS_DIR}flags_by_adm1_mon_pct.png"
    plot_flag_percentages(
        flags_df,
        pct_col="mon_yr_adm1_pct",
        color="forestgreen",
        title="Percentage of adm1-month events by each flag",
        x_label="Percentage of events (%)",
        save_path=adm1_pct_filepath,
    )
    print(f"Saved file to {adm1_pct_filepath}")


if __name__ == "__main__":
    main()
