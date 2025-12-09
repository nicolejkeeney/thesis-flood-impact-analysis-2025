"""
event_duration_violinplot.py

Creates violin plots comparing event duration distributions between flood events
with zero flooded area versus non-zero flooded area.

"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from data_analysis_utils import filter_by_flags

DATA_DIR = "../data/"
FIGS_DIR = "../figures/"
EVENTS_FILEPATH = f"{DATA_DIR}event_level_flood_dataset.csv"
OUTPUT_FILEPATH = f"{FIGS_DIR}event_duration_flooded_pixels_violinplot.png"

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 24
TICK_FONTSIZE = 20
LABEL_FONTSIZE = 23
plt.rcParams["font.family"] = "Georgia"


def create_violin_plot(
    events_no_flooded_pixels, events_yes_flooded_pixels, savepath=None
):
    """
    Create violin plot comparing event duration distributions between flood categories.

    Parameters
    ----------
    events_no_flooded_pixels : pd.DataFrame
        DataFrame containing flood events with zero flooded pixels.
        Must include 'event_duration (days)' column.
    events_yes_flooded_pixels : pd.DataFrame
        DataFrame containing flood events with non-zero flooded pixels.
        Must include 'event_duration (days)' column.
    savepath : str, optional
        Path to save the figure. If None, figure is not saved.
    """
    # Combine the data and add category labels
    no_flooded_data = events_no_flooded_pixels.copy()
    no_flooded_data["category"] = "Zero Flooded Area"

    yes_flooded_data = events_yes_flooded_pixels.copy()
    yes_flooded_data["category"] = "Non-Zero Flooded Area"

    combined_data = pd.concat([no_flooded_data, yes_flooded_data], ignore_index=True)

    # Create the plot
    plt.figure(figsize=(7, 4))
    ax = sns.violinplot(
        data=combined_data,
        x="category",
        y="event_duration (days)",
        color="plum",
        inner="box",
    )

    # Customize the plot
    ax.tick_params(labelsize=TICK_FONTSIZE)
    plt.title("Event Duration Distribution Comparison", fontsize=TITLE_FONTSIZE)
    plt.ylabel("Event Duration (days)", fontsize=LABEL_FONTSIZE)
    plt.xlabel(None)
    plt.grid(True, alpha=0.4)
    plt.ylim(1, 31)
    plt.tight_layout()

    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Figure saved to: {savepath}")


def main():
    # Read in data
    events_df = pd.read_csv(EVENTS_FILEPATH)

    # Get events with no flooded pixels
    events_no_flooded_pixels = filter_by_flags(events_df, flags=[12])

    # Get events with non-zero flooded pixels
    events_yes_flooded_pixels = filter_by_flags(events_df, flags=[12], exclude=True)

    create_violin_plot(
        events_no_flooded_pixels, events_yes_flooded_pixels, savepath=OUTPUT_FILEPATH
    )


if __name__ == "__main__":
    main()
