"""
precip_distribution.py

Make a stack of 5 histograms, showing:
1. Histogram standard deviation of precipitation of all months.
2. Histogram of standard deviation of precipitation for months with floods only.
3. Histogram of standard deviation of precipitation for ALL months, weighted by economic damages.
4. Histogram of standard deviation of precipitation for ALL months, weighted by people affected.
5. Probability of a food being recorded given a given standard deviation of precipitation

"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 24
TICK_FONTSIZE = 20
LABEL_FONTSIZE = 23
plt.rcParams["font.family"] = "Georgia"

DATA_DIR = "../data/"
PANEL_FILEPATH = f"{DATA_DIR}panel_dataset.csv"
FIGS_DIR = "../figures/"
PANEL_FIGS_DIR = f"{FIGS_DIR}panel_model/"
OUTPUT_FILEPATH = f"{PANEL_FIGS_DIR}precip_distr_all.png"


def plot_precipitation_histograms(
    panel_df, savepath=None, title=None, panel_labels=False
):
    """
    Create three-panel histogram showing precipitation anomaly distributions.

    Parameters
    ----------
    panel_df : pandas.DataFrame
        Panel dataset containing precipitation and impact data
    savepath : str, optional
        Path to save figure. If None, displays figure
    title : str, optional
        Optional suptitle for the entire figure.
    panel_labels : bool, optional
        If True, add a-e labels to panels. Default False.
    """

    bins = np.linspace(-2, 5, 21)  # 20 bins with uniform spacing
    color_alpha = (
        0.7  # See-through-ness of the histogram color (makes it a paler color)
    )
    edge_linewidth = 0.8

    # Filter data for months with impact events
    event_months = panel_df[panel_df["event_occurrance"] == 1]
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(
        5, 1, figsize=(5.8, 14), sharex=True, dpi=FIG_DPI
    )

    # 1. Distribution of all monthly precipitation anomalies
    counts_all_months_per_precip_bin, bins_edges, _ = ax1.hist(
        panel_df["precip_std_anom"],
        bins=bins,
        color="skyblue",
        edgecolor="skyblue",
        linewidth=edge_linewidth,
        alpha=color_alpha,
    )
    ax1.set_title("dist. of monthly precip", fontsize=TITLE_FONTSIZE - 1, loc="left")
    ax1.set_ylabel("event count", fontsize=LABEL_FONTSIZE)

    # 2. Distribution during months with impact events
    event_counts_per_precip_bin, _, _ = ax2.hist(
        event_months["precip_std_anom"],
        bins=bins,
        color="darkblue",
        edgecolor="darkblue",
        linewidth=edge_linewidth,
        alpha=color_alpha,
    )
    ax2.set_title(
        f"dist. of monthly precip\nmonths with floods only",
        fontsize=TITLE_FONTSIZE - 1,
        loc="left",
    )
    ax2.set_ylabel("event count", fontsize=LABEL_FONTSIZE)

    # 3. Distribution of damages weighted by precipitation anomalies
    sum_damages_per_precip_bin, _, _ = ax3.hist(
        panel_df["precip_std_anom"],
        bins=bins,
        color="forestgreen",
        edgecolor="forestgreen",
        linewidth=edge_linewidth,
        alpha=color_alpha,
        weights=panel_df["damages"],
    )
    ax3.set_title(
        f"dist. of economic damages\nby precip anomaly bin",
        fontsize=TITLE_FONTSIZE - 1,
        loc="left",
    )
    ax3.set_ylabel(f"damages ('000 $US)", fontsize=LABEL_FONTSIZE)

    # 3. Distribution of people affected weighted by precipitation anomalies
    sum_affected_per_precip_bin, _, _ = ax4.hist(
        panel_df["precip_std_anom"],
        bins=bins,
        color="darkmagenta",
        edgecolor="darkmagenta",
        linewidth=edge_linewidth,
        alpha=color_alpha,
        weights=panel_df["total_affected"],
    )
    ax4.set_title(
        f"dist. of total people affected\nby precipitation anomaly bin",
        fontsize=TITLE_FONTSIZE - 1,
        loc="left",
    )
    ax4.set_ylabel(f"people affected", fontsize=LABEL_FONTSIZE)

    # 5. Fraction of months with an event per bin
    fraction = np.divide(
        event_counts_per_precip_bin,
        counts_all_months_per_precip_bin,
        out=np.zeros_like(event_counts_per_precip_bin, dtype=float),
        where=counts_all_months_per_precip_bin != 0,
    )
    bin_centers = (
        bins_edges[:-1] + bins_edges[1:]
    ) / 2  # Use bin centers since its poorly aligned otherwise
    ax5.bar(
        bin_centers,
        fraction,
        width=np.diff(bins_edges),
        color="dimgrey",
        edgecolor="dimgrey",
        linewidth=edge_linewidth,
        alpha=color_alpha,
    )
    ax5.set_ylim(0, 0.3)
    ax5.set_title(
        "prob. of a flood by\nprecipitation anomaly",
        fontsize=TITLE_FONTSIZE - 1,
        loc="left",
    )
    ax5.set_xlabel("monthly precip anomaly (s.d.)", fontsize=LABEL_FONTSIZE)
    ax5.set_ylabel("fraction (0-1)", fontsize=LABEL_FONTSIZE)

    # Format all axes
    labels = ["a)", "b)", "c)", "d)", "e)"]
    for i, ax in enumerate([ax1, ax2, ax3, ax4, ax5]):
        ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)
        ax.set_xlim(-2, 5)
        ax.yaxis.get_offset_text().set_fontsize(TICK_FONTSIZE)

        if ax == ax5:
            ax.set_xticks(np.arange(-1, 6, 1))
            ax.tick_params(axis="x", labelsize=TICK_FONTSIZE)
        else:
            ax.set_xticks([])

        # Add panel labels
        if panel_labels:
            ax.text(
                -0.15,
                1.15,
                labels[i],
                transform=ax.transAxes,
                fontsize=TITLE_FONTSIZE,
                fontweight="bold",
                verticalalignment="top",
                horizontalalignment="right",
            )

    if title is not None:
        plt.suptitle(title, fontsize=TITLE_FONTSIZE + 1)
    plt.tight_layout()  # Adjust this value to control vertical spacing

    # Save figure
    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to {savepath}")


def main():
    # Make output dir if it doesn't already exist
    os.makedirs(PANEL_FIGS_DIR, exist_ok=True)

    # Read in data
    panel_df = pd.read_csv(PANEL_FILEPATH)

    plot_precipitation_histograms(
        panel_df,
        # title="Monthly Precipitation Anomaly Distributions",
        savepath=OUTPUT_FILEPATH,
        panel_labels=False,  # Add a,b,c,d,e to plots
    )


if __name__ == "__main__":
    main()
