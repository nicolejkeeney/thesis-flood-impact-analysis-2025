"""
emdat_yearly_barcharts.py

Create bar charts of the yearly aggregated EM-DAT data for the following variables:
- Adjusted Damages
- People Affected
Along with the total event count

"""

import matplotlib.pyplot as plt
import pandas as pd

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 24
TICK_FONTSIZE = 20
LABEL_FONTSIZE = 23
plt.rcParams["font.family"] = "Georgia"

# Filepaths
DATA_DIR = "../data/"
FIGS_DIR = "../figures/"
EMDAT_FILEPATH = f"{DATA_DIR}emdat/emdat-2000-2024_preprocessed.csv"
OUTPUT_FILEPATH = f"{FIGS_DIR}emdat_yearly_barcharts.png"


def main():
    ## SETUP DATA
    emdat_df = pd.read_csv(EMDAT_FILEPATH)

    # Aggregate by start year
    emdat_agg = (
        emdat_df.groupby("Start Year")
        .agg(
            {
                col: "sum"
                for col in ["No. Affected", "Total Damage, Adjusted ('000 US$)"]
            }
            | {"id": "count"}  # add count aggregation for 'id'
        )
        .reset_index()
    )
    emdat_agg.rename(columns={"id": "event_count"}, inplace=True)

    ## MAKE PLOT
    columns = ["No. Affected", "Total Damage, Adjusted ('000 US$)", "event_count"]
    ylabels = ["# People", "'000 US$", "count"]
    titles = [
        "a) Number of People Affected",
        "b) Total Damages ('000 US$)",
        "c) Number of Floods\n",
    ]
    colors = ["#1b9e77", "#d95f02", "#7570b3"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))  # 1 row, 3 columns

    for ax, col, title, ylabel, color in zip(axes, columns, titles, ylabels, colors):
        ax.bar(emdat_agg["Start Year"], emdat_agg[col], color=color)
        ax.set_xlabel("Year", fontsize=LABEL_FONTSIZE)
        ax.set_ylabel(ylabel, fontsize=LABEL_FONTSIZE)
        ax.tick_params(axis="x", labelsize=TICK_FONTSIZE, rotation=45)
        ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)
        ax.set_title(title, fontsize=TITLE_FONTSIZE, pad=20)
        ax.set_xticks(range(2000, 2024 + 1, 4))
        ax.yaxis.get_offset_text().set_fontsize(TICK_FONTSIZE)  # adjust font size

    # plt.suptitle("EM-DAT Annual Aggregated Impacts", fontsize=TITLE_FONTSIZE+2, fontweight="bold")
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.5)  # increase horizontal space between subplots
    plt.savefig(OUTPUT_FILEPATH, dpi=FIG_DPI, bbox_inches="tight")
    print(f"Saved figure to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
