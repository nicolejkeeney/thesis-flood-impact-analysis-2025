"""
emdat_impact_distribution_stripplots.py

Visualize the distribution of flood impacts from EM-DAT at the event level using
stripplots on both raw and log10 scales.

Creates dual-panel stripplots showing:
- Total Affected (number of people affected by each flood)
- Total Damage, Adjusted ('000 US$) (economic damages per flood)

Each plot shows the same data on both linear and logarithmic scales to better
visualize the wide range of flood impact magnitudes across events.

Uses deduplicated EM-DAT flood records to ensure one observation per flood event.
Outputs plots to figures/summary_stats/emdat_impact_distribution/
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

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
OUTPUT_DIR = f"{FIGS_DIR}emdat_impact_distribution/"


def _stripplot(data, var_name, color="purple", savepath=None):
    """
    Plot 2 strip plots of data (raw and log10 scale).

    Parameters
    ----------
    data : array-like
        Values to plot (numeric).
    var_name : str
        Name of the variable (for labeling).
    color : str, optional
        Color for the strip plots.
    savepath : str or None, optional
        If given, path to save the figure instead of showing it.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Raw scale strip plot
    sns.stripplot(x=data, size=4, alpha=0.6, ax=ax1, color=color)
    ax1.set_title(var_name, fontsize=TITLE_FONTSIZE)
    ax1.set_xlabel(var_name, fontsize=LABEL_FONTSIZE)
    ax1.ticklabel_format(style="plain", axis="x")  # no sci notation
    ax1.tick_params(axis="both", labelsize=TICK_FONTSIZE)  # set tick label fontsize

    # Log scale strip plot (positive values only)
    positive_var = data[data > 0]
    sns.stripplot(x=np.log10(positive_var), size=4, alpha=0.6, ax=ax2, color=color)
    ax2.set_title(f"{var_name} (Log Scale)", fontsize=TITLE_FONTSIZE)
    ax2.set_xlabel(f"Log10({var_name})", fontsize=LABEL_FONTSIZE)
    ax2.tick_params(axis="both", labelsize=TICK_FONTSIZE)  # set tick label fontsize

    plt.tight_layout()
    fig.subplots_adjust(hspace=0.4)  # increase space between plots

    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to to {savepath}")
        plt.close()


def main():
    # Make output dir if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read data
    events_df = pd.read_csv(EVENTS_FILEPATH)

    # Now, look at distribution of impacts at the flood scale
    # Keep the first occurrence of each duplicate ID
    # Total Affected and Total Damages columns are from the original EM-DAT data
    emdat_df = events_df.drop_duplicates(subset=["id"], keep="first")[
        ["id", "Total Affected", "Total Damage, Adjusted ('000 US$)"]
    ]

    # Make stripplots
    impact_var = "Total Affected"
    _stripplot(
        data=emdat_df[impact_var].dropna(),
        var_name=impact_var,
        color="purple",
        savepath=f"{OUTPUT_DIR}emdat_total_affected_stripplots.png",
    )

    # Make stripplots
    impact_var = "Total Damage, Adjusted ('000 US$)"
    _stripplot(
        data=emdat_df[impact_var].dropna(),
        var_name=impact_var,
        color="blue",
        savepath=f"{OUTPUT_DIR}emdat_damages_stripplots.png",
    )


if __name__ == "__main__":
    main()
