"""
create_flood_map.py

This script generates a flood extent map for a specified flood event using a preprocessed
MODIS-based flood image for a specific event stored as a GeoTIFF.

It performs the following steps:
1. Loads a binary flood mask (`.tif`) for a specified event ID.
2. Masks out zero values (non-flooded pixels) for cleaner visualization.
3. Reprojects the data to Web Mercator (EPSG:3857).
4. Overlays the data on a basemap and adds a legend.
5. Saves the resulting map as a PNG to the specified output directory.

Example Usage:
python create_flood_map.py 04-2011-0131-CAN-825

"""

import rioxarray as rio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import contextily as ctx
import os
import argparse

from utils.utils_misc import check_dir_exists, check_file_exists

# Directories
DATA_DIR = "../../data/"
FLOODED_PIXEL_DIR = f"{DATA_DIR}EE_flooded_pixels/"
OUTPUT_DIR = "../../figures/flood_maps/"


def parse_args():
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Compute people affected and total flooded area from flooded image"
    )
    parser.add_argument("mon_yr_adm1_id", type=str, help="ID")
    return parser.parse_args()


def plot_flooded_pixels(da, id, title="", save_fig=False, figures_dir=""):
    """
    Plot flooded pixels from a DataArray, reprojected to Web Mercator, with optional figure saving.

    Parameters
    ----------
    da : xarray.DataArray
        Flood mask to plot. Should be spatially referenced and contain binary (0/1) values.
    id : str
        Unique identifier used in the plot title and output filename.
    title : str, optional
        Title for the plot. If empty, `id` is used instead. Default is "".
    save_fig : bool, optional
        Whether to save the figure to disk. Default is False.
    figures_dir : str, optional
        Directory where the figure should be saved if `save_fig=True`. Default is "".
    """

    flooded_color = "#08306b"  # Dark blue
    # flooded_color = '#FFD700' # Bright yellow
    fig, ax = plt.subplots(figsize=(10, 8))

    # Reproject to Web Mercator
    da_reprojected = da.rio.reproject("EPSG:3857")

    # Plot
    cmap = mcolors.ListedColormap([flooded_color])
    da_reprojected.plot(ax=ax, add_colorbar=False, cmap=cmap, vmax=1)

    # Add basemap
    # ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    # ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    # Legend
    flood_patch = mpatches.Patch(color=flooded_color, label="Flooded pixel")
    ax.legend(handles=[flood_patch], loc="upper right")

    # Set figure title
    if title == "":
        title = id
    plt.title(title, size=15)

    # Save figure to local drive
    if save_fig:
        output_filename = f"{id}_flood_map.png"
        output_filepath = f"{figures_dir}{output_filename}"
        plt.savefig(output_filepath, dpi=300)
        print(f"Figure saved to {output_filepath}")


def main():
    print("Starting script create_flood_map.py")

    args = parse_args()
    mon_yr_adm1_id = args.mon_yr_adm1_id

    print(f"Flood id: {mon_yr_adm1_id}")

    # Ensure all the directories are good to go
    check_dir_exists(FLOODED_PIXEL_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read in the data
    tif_filepath = f"{FLOODED_PIXEL_DIR}{mon_yr_adm1_id}.tif"
    print(f"Reading in data from {tif_filepath}...")
    check_file_exists(tif_filepath)
    flooded_im = rio.open_rasterio(tif_filepath, masked=True)

    print("Masking zeroes...")
    flooded_pixels = flooded_im.sel(band=1)  # Get flood band
    flooded_pixels_zeroes_masked = flooded_pixels.where(
        flooded_pixels != 0
    )  # Set zeroes (non-flooded pixels) to nan to improve plot

    print("Creating figure...")
    plot_flooded_pixels(
        flooded_pixels_zeroes_masked,
        id=mon_yr_adm1_id,
        title=f"{mon_yr_adm1_id}: Flooded pixels",
        save_fig=True,
        figures_dir=OUTPUT_DIR,
    )

    print("Script complete.")


if __name__ == "__main__":
    main()
