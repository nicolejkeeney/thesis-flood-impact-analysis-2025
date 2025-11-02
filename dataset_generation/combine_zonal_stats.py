"""combine_zonal_stats.py

Combine zonal stats netcdf files for individual months into a single netcdf file for easier analysis

"""

import xarray as xr
from glob import glob

DATA_DIR = "../data/"
ZONAL_STATS_DIR = f"{DATA_DIR}zonal_stats/"
EXPORT_FILEPATH = f"{DATA_DIR}zonal_stats_all.nc"  # Store in main directory


def main():
    # Use glob to get filenames
    zonal_filepaths_all = glob(f"{ZONAL_STATS_DIR}*zonal_stats.nc")
    print(f"{len(zonal_filepaths_all)} files found")

    if len(zonal_filepaths_all) == 0:
        raise ValueError(f"No files found in folder {ZONAL_STATS_DIR}")

    # Read in the data using xarray
    print("Reading in data and combining along time dimension...")
    ds = xr.open_mfdataset(zonal_filepaths_all)
    print("Data successfully loaded into xarray Dataset object")

    # Clean and export data
    ds = ds.sortby("time").rename({"ADM1_CODE": "adm1_code"})
    ds.to_netcdf(EXPORT_FILEPATH)
    print(f"File exported to {EXPORT_FILEPATH}")


if __name__ == "__main__":
    print("Starting script combine_zonal_stats.py")

    main()

    print("Script complete")
