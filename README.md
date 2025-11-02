# Flood Disaster Impacts: EM-DAT and MODIS Analysis

This repository contains the complete data processing pipeline and analysis code for combining EM-DAT disaster records with MODIS satellite imagery, climate reanalysis data, and population data to study flood disaster impacts.

## Overview

This research combines multiple global datasets to analyze flood disasters from 2000-2024:

- **EM-DAT**: International disaster database providing flood event records and reported impacts
- **MODIS**: Satellite imagery (Terra/Aqua) for flood detection via Google Earth Engine
- **MSWEP/MSWX**: Climate reanalysis data (precipitation, temperature, wind, humidity)
- **GPW v4**: Gridded Population of the World for population-weighting
- **GAUL 2015**: Global Administrative Unit Layers (admin level 1 boundaries)

### Key Methods

1. **Flood Detection**: Adapted Cloud2Street algorithm for MODIS-based flood mapping
2. **Administrative Disaggregation**: Splitting multi-region/multi-month events into admin1-month records
3. **Population-Weighted Impact Allocation**: Distributing reported damages based on satellite-detected affected populations
4. **Climate Integration**: Extracting event-specific climate anomalies using zonal statistics
5. **Panel Construction**: Creating balanced admin1-month panel (2000-2024) for econometric analysis

## Repository Structure

```
├── dataset_generation/       # Data processing pipeline (18 steps)
│   ├── preprocess_emdat.py   # (key scripts shown)
│   ├── detect_flooded_pixels.py
│   ├── extract_flood_metrics.py
│   ├── compute_zonal_stats.py
│   ├── prepare_panel_dataset.py
│   ├── utils/                # Helper modules (flood detection, MODIS toolbox, etc.)
│   └── README.md             # Detailed pipeline documentation
│
├── data_analysis/            # Analysis scripts and visualizations
│   ├── panel_analysis.py     # (key scripts shown)
│   ├── emdat_modis_regression.py
│   ├── summary_maps.py
│   ├── produce_all_figures.sh
│   └── README.md
│
├── hpc/                      # HPC job scripts (SLURM)
│   └── README.md
│
├── data/                     # Data files (not tracked in git)
│   ├── event_level_flood_dataset.csv  # Final event-level dataset
│   ├── panel_dataset.csv              # Panel dataset
│   └── ...
│
├── figures/                  # Generated figures (not tracked in git)
│
├── text_inputs/              # Input files for parallel processing
│
├── environment.yml           # Conda environment specification
└── LICENSE                   # MIT License
```

## Installation

### Environment Setup

This project uses conda for dependency management:

```bash
conda env create -f environment.yml
conda activate flood-impacts
```

### Key Dependencies

- **Geospatial**: `geopandas`, `rasterio`, `xarray`, `cartopy`, `contextily`
- **Earth Engine**: `earthengine-api` (requires GEE account for flood detection step)
- **Analysis**: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`
- **Econometrics**: `pyfixest` (panel regression)
- **Parallel processing**: `dask`, `exactextract`, `tqdm`

See `environment.yml` for complete dependency list with version specifications.

## Usage

The repository is organized into two main components:

**Data Generation Pipeline** (`dataset_generation/`): The complete workflow for processing raw data sources into analysis-ready datasets. The pipeline consists of 18 sequential steps, from preprocessing EM-DAT records through satellite-based flood detection to creating the final event-level and panel datasets. Detailed documentation is available in `dataset_generation/README.md`.

**Analysis Scripts** (`data_analysis/`): Scripts for generating summary statistics, visualizations, and econometric models. Includes panel regression analysis, comparison of EM-DAT vs. MODIS-derived impacts, and various plotting utilities. See `data_analysis/README.md` for descriptions of individual scripts.

**Note:** The full pipeline includes computationally intensive steps (flood detection via Google Earth Engine, zonal statistics extraction) that require significant resources and processing time. Some steps are designed for HPC environments with SLURM job submission.

## Data Quality Flags

The dataset includes quality flags (1-15) indicating:
- Missing or estimated data (dates, locations, impacts)
- Processing issues (no MODIS data, cloud cover problems)
- Impact allocation methods (population-weighted vs. reported)

See `data/data_processing_flags.csv` for complete flag definitions.

## Issues and Support

If you encounter any problems with the code, data, or documentation, please [open an issue](https://github.com/njkeeney/modis-event-damages/issues) on GitHub. When reporting an issue, please include:

- A clear description of the problem
- Steps to reproduce the issue
- Your environment details (OS, Python version, etc.)
- Any relevant error messages or output

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Data Source Licenses

- **EM-DAT**: Subject to EM-DAT terms of use
- **MODIS**: NASA data, publicly available
- **GPW**: Creative Commons Attribution 4.0
- **GAUL**: FAO terms of use
- **MSWEP/MSWX**: Check respective data provider terms

## Acknowledgments

- **Cloud2Street** for the MODIS flood detection algorithm
- **EM-DAT** (CRED, UCLouvain) for disaster data
- **NASA** for MODIS imagery and Earth Engine platform
