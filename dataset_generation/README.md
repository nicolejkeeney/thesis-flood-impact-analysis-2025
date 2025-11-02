# Dataset Generation Pipeline

This directory contains the complete data processing pipeline for combining EM-DAT flood disaster records with MODIS satellite imagery, climate reanalysis data, and population data. The workflow produces two final datasets: an event-level dataset and a balanced panel dataset.

---

## Final Outputs

- **`event_level_flood_dataset.csv`**: Event-level dataset with flood metrics, climate data, and impact measures for each disaggregated flood event
- **`panel_dataset.csv`**: Balanced admin1-month panel (2000-2024) for econometric analysis

---

## Pipeline Overview

The pipeline follows these sequential steps:

### 1. Preprocess EM-DAT Data
**Script:** `preprocess_emdat.py`

Cleans raw EM-DAT flood records by filtering for inland floods (2000-2024), removing events with missing critical date information, and adjusting 2024 damages using CPI.

**Inputs:**
- `data/emdat/emdat-2000-2024.csv` (raw EM-DAT download from [emdat.be](https://www.emdat.be/))

**Outputs:**
- `data/emdat/emdat-2000-2024_preprocessed.csv`

---

### 2. Disaggregate Events by Admin1 and Month
**Script:** `prepare_disagreggated_dataset.py`

Fills missing start/end days, matches EM-DAT location strings to GAUL admin1 codes, and splits multi-month/multi-region events into individual admin1-month records with new IDs.

**Inputs:**
- `data/emdat/emdat-2000-2024_preprocessed.csv` — *output from Step 1*
- GAUL Level 2 shapefile (`data/GAUL_2015/g2015_2014_2`)

**Outputs:**
- `data/emdat/emdat_floods_by_mon_yr_adm1.csv`

**Helper modules:**
- `utils/emdat_toolbox.py`

---

### 3. Generate Input Files for Parallel Processing
**Scripts:** `generate_input_files/*.py`

Creates text files that batch event IDs, admin codes, and year-day combinations for parallel processing on HPC systems.

Run all scripts in `generate_input_files/`:
- `split_emdat_ids_into_batches.py`
- `generate_adm1_code_inputs.py`
- `generate_year_day_file.py`

**Inputs:**
- `data/emdat/emdat_floods_by_mon_yr_adm1.csv` — *output from Step 2*

**Outputs:**
- Text files saved to `text_inputs/` subdirectories

---

### 4. Regrid Population Data
**Script:** `regrid_gpw.py`
**HPC job:** `hpc/regrid_gpw_job.sh`

Regrids [Gridded Population of the World (GPW v4)](https://sedac.ciesin.columbia.edu/data/collection/gpw-v4) population density rasters from 30 arc-second resolution to match the global MODIS grid.

**Inputs:**
- GPW v4 population density GeoTIFF files for years 2000, 2005, 2010, 2015, 2020

**Outputs:**
- Regridded population NetCDF files (5 files, one per GPW year)

---

### 5. Process Population by Admin1
**Script:** `process_gpw_adm1.py`
**HPC jobs:** `hpc/small_adm1_gpw_job_1.sh` (example)

Clips regridded population data to each admin1 zone and calculates grid cell area and population counts.

**Inputs:**
- Regridded GPW NetCDF files — *outputs from Step 4*
- GAUL Level 1 shapefile (`data/GAUL_2015/g2015_2014_1`)
- Text input files from `text_inputs/adm1_codes/` — *outputs from Step 3*

**Outputs:**
- NetCDF files with population density, count, and cell area for each admin1 zone per year
- CSV success reports for each admin1 zone

**Note:** For production runs, multiple batch scripts process different subsets of admin1 codes in parallel. The example script shows the pattern.

---

### 6. Generate Population Summary File
**Script:** `gpw_adm1_summary_file.py`

Aggregates population data by admin1 zone across all years.

**Inputs:**
- Population NetCDF files by admin1 — *outputs from Step 5*

**Outputs:**
- `data/GPW_summary_by_adm1.csv`

---

### 7. Extract GDP by Admin1
**Script:** `extract_gdp_adm1.py`

Extracts subnational GDP data by admin1 region for normalizing economic damages.

**Inputs:**
- GDP raster/tabular data
- GAUL Level 1 shapefile

**Outputs:**
- `data/gdp/gdp_by_adm1.csv`

---

### 8. Detect Flooded Pixels Using Google Earth Engine
**Script:** `detect_flooded_pixels.py`

Uses the Google Earth Engine (GEE) Python API to run the Cloud2Street MODIS flood detection algorithm for each disaggregated flood event. Exports 4-band GeoTIFF images to Google Drive (flooded, duration, clear_views, clear_perc_scaled).

**Requires:** GEE account and authentication (`earthengine authenticate`)

**Inputs:**
- Text input files from `text_inputs/emdat_mon_yr_adm1_id/` — *outputs from Step 3*
- `data/emdat/emdat_floods_by_mon_yr_adm1.csv` — *output from Step 2*
- GAUL Level 1 shapefile

**Outputs:**
- GeoTIFF files exported to Google Drive
- `.log` file recording script execution
- `.csv` file summarizing success/failure for each event

**Helper modules:**
- `utils/flood_detection.py` (Cloud2Street algorithm)
- `utils/modis_toolbox.py`
- `utils/logger.py`

**Example usage:**
```bash
python detect_flooded_pixels.py ../text_inputs/emdat_mon_yr_adm1_id/emdat_mon_yr_adm1_id_1.txt
```

**Note:** Run separately for each batch file in `text_inputs/emdat_mon_yr_adm1_id/` for parallel processing.

---

### 9. Extract Flood Metrics from Images
**Script:** `extract_flood_metrics.py`
**HPC job:** `hpc/flood_metrics_job_1.sh` (example)

Downloads GEE-exported flood images and computes zonal statistics (flooded area, flooded population, cloud cover metrics) for each event.

**Inputs:**
- MODIS flood GeoTIFF images — *outputs from Step 8*
- GPW population NetCDF files — *outputs from Step 5*
- GAUL Level 1 shapefile
- Text input files from `text_inputs/emdat_mon_yr_adm1_id/`

**Outputs:**
- CSV files named `<mon-yr-adm1-id>_metrics.csv` for each event

**Note:** Run separately for each batch file for parallel processing.

---

### 10. Combine Flood Metric CSVs
**Script:** `combine_csvs.py`

Merges individual event metric CSV files into a single consolidated file.

**Inputs:**
- Individual `*_metrics.csv` files — *outputs from Step 9*

**Outputs:**
- `data/event_intermediate_files/event_metrics.csv`

---

### 11. Compute Population-Weighted Damages
**Script:** `compute_pop_weighted_damages.py`
**HPC job:** `hpc/weighted_damages_job.sh`

Calculates population-weighted damage allocation for events spanning multiple admin1 zones.

**Inputs:**
- `data/emdat/emdat_floods_by_mon_yr_adm1.csv` — *output from Step 2*
- `data/event_intermediate_files/event_metrics.csv` — *output from Step 10*

**Outputs:**
- `data/event_intermediate_files/event_metrics_with_pop_weighted_damages.csv`

---

### 12. Add Data Quality Flags
**Script:** `add_data_flags.py`

Adds data quality flags indicating missing data, processing issues, and impact allocation methods. See `data/data_processing_flags.csv` for flag definitions.

**Inputs:**
- `data/event_intermediate_files/event_metrics_with_pop_weighted_damages.csv` — *output from Step 11*
- `data/emdat/emdat_floods_by_mon_yr_adm1.csv` — *output from Step 2*
- CSV logfiles from `detect_flooded_pixels.py` — *outputs from Step 8*

**Outputs:**
- `data/event_intermediate_files/event_metrics_with_pop_weighted_damages_and_flags.csv`

---

### 13. Clean Event Metrics
**Script:** `event_metrics_cleanup.py`

Adds event duration column and reorders indices for clarity.

**Inputs:**
- `data/event_intermediate_files/event_metrics_with_pop_weighted_damages_and_flags.csv` — *output from Step 12*
- `data/emdat/emdat-2000-2024_preprocessed.csv` — *output from Step 1*

**Outputs:**
- `data/event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags.csv`

---

### 14. Compute Climate Zonal Statistics
**Script:** `compute_zonal_stats.py`
**HPC job:** `hpc/zonal_stats_job.sh`

Extracts daily climate data (precipitation, temperature, wind, humidity) from MSWEP/MSWX reanalysis datasets for each admin1 region.

**Inputs:**
- Text input files from `text_inputs/zonal_inputs/` — *outputs from Step 3*
- MSWEP and MSWX meteorological NetCDF files
- GAUL Level 1 shapefile

**Outputs:**
- Daily climate NetCDF files (one per admin1-year-day combination)

**Note:** Uses `exactextract` for efficient zonal statistics. Run separately for each batch file for parallel processing.

---

### 15. Combine Climate Zonal Statistics
**Script:** `combine_zonal_stats.py`
**HPC job:** `hpc/combine_files_job.sh`

Merges individual daily climate NetCDF files into a single consolidated file.

**Inputs:**
- Daily climate NetCDF files — *outputs from Step 14*

**Outputs:**
- `data/zonal_stats_all.nc`

---

### 16. Add Normalized Impact Metrics
**Script:** `add_normalized_impacts.py`

Adds GDP-normalized damages, flooded area normalized by admin1 area, and population-normalized affected counts.

**Inputs:**
- `data/event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags.csv` — *output from Step 13*
- `data/gdp/gdp_by_adm1.csv` — *output from Step 7*
- `data/GPW_summary_by_adm1.csv` — *output from Step 6*
- GAUL Level 1 shapefile

**Outputs:**
- `data/event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags_and_normalized_impacts.csv`

---

### 17. Add Climate Data to Events (FINAL EVENT DATASET)
**Script:** `add_zonal_stats.py`

Merges event-level climate anomalies into the flood dataset.

**Inputs:**
- `data/zonal_stats_all.nc` — *output from Step 15*
- `data/event_intermediate_files/CLEANED_event_metrics_with_pop_weighted_damages_and_flags_and_normalized_impacts.csv` — *output from Step 16*

**Outputs:**
- ⭐ **`data/event_level_flood_dataset.csv`** ⭐ (Final event-level dataset)

---

### 18. Prepare Panel Dataset
**Script:** `prepare_panel_dataset.py`

Creates a balanced admin1-month panel (2000-2024) by merging flood events with climate data and filling missing values using percentile-based imputation.

**Inputs:**
- `data/event_level_flood_dataset.csv` — *output from Step 17*
- `data/zonal_stats_all.nc` — *output from Step 15*
- GAUL Level 1 shapefile

**Outputs:**
- ⭐ **`data/panel_dataset.csv`** ⭐ (Final panel dataset)

---

## Key Helper Modules

Located in `utils/`:

- **`flood_detection.py`**: Cloud2Street MODIS flood detection algorithm (adapted)
- **`modis_toolbox.py`**: MODIS preprocessing (pan-sharpening, QA masking, slope/water masks)
- **`emdat_toolbox.py`**: EM-DAT preprocessing utilities (date parsing, admin unit expansion)
- **`logger.py`**: Logging setup
- **`utils_misc.py`**: General utilities (file checks, year mapping, etc.)

---

## Notes on HPC Jobs

The `hpc/` directory contains SLURM job scripts for parallel processing. For transparency, one example of each job type is included. In practice, multiple numbered variants were run in parallel (e.g., `flood_metrics_job_1.sh`, `flood_metrics_job_2.sh`, etc.) to process different batches concurrently.

See `hpc/README.md` for more details on the HPC workflow.
