# Flood Disaster Impacts: EM-DAT and MODIS Analysis

This repository contains the complete codebase for Nicole Keeney's Master of Science thesis in the Department of Civil & Environmental Engineering at Colorado State University (2025). The research develops methods for spatially and temporally disaggregating disaster event records using satellite imagery, constructs a balanced panel dataset of flood events from 2000-2024, and uses panel regression analysis to examine the relationship between climate variables and flood impacts across global administrative regions. It also includes SLURM batch scripts for submitting processing jobs on CSU's HPC cluster, used in various steps in the analysis. 

This work was presented at the American Geophysical Union (AGU) Fall Meeting 2025 (doi: ADD DOI)

## Data

This research combines multiple global datasets to analyze flood disasters from 2000-2024:

- **EM-DAT**: International disaster database providing flood event records and reported impacts
- **MODIS**: Satellite imagery (Terra/Aqua) for flood detection via Google Earth Engine
- **MSWEP/MSWX**: Climate reanalysis data 
- **GPW v4**: Gridded Population of the World for population-weighting
- **GAUL 2015**: Global Administrative Unit Layers (admin level 1 boundaries)

### Data Source Licenses

- **EM-DAT**: Subject to EM-DAT terms of use
- **MODIS**: NASA data, publicly available
- **GPW**: Creative Commons Attribution 4.0
- **GAUL**: FAO terms of use
- **MSWEP/MSWX**: Check respective data provider terms

## Key Methods

1. **Flood Detection**: Adapted Cloud2Street algorithm for MODIS-based flood mapping
2. **Administrative Disaggregation**: Splitting multi-region/multi-month events into admin1-month records
3. **Population-Weighted Impact Allocation**: Distributing reported damages based on satellite-detected affected populations
4. **Climate Integration**: Extracting event-specific climate anomalies using zonal statistics
5. **Panel Construction**: Creating balanced admin1-month panel (2000-2024) for flood impact analysis

## Repository Structure

```
├── dataset_generation/       # Data processing pipeline (18 steps)
│   ├── preprocess_emdat.py
│   ├── detect_flooded_pixels.py
│   ├── extract_flood_metrics.py
│   ├── compute_zonal_stats.py
│   ├── prepare_panel_dataset.py
│   ├── utils/                # Helper modules (flood detection, MODIS toolbox, etc.)
│   ├── README.md             # Detailed pipeline documentation
│   └── ...
│
├── data_analysis/            # Analysis scripts and visualizations
│   ├── panel_analysis.py
│   ├── emdat_modis_regression.py
│   ├── summary_maps.py
│   ├── produce_all_figures.sh
│   ├── README.md
│   └── ...
│
├── hpc/                      # HPC job scripts (SLURM)
│   └── README.md
│
├── data/                     # Data files (not tracked in git, except flags)
│   └── data_processing_flags.csv      # Flag definitions
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
- **Parallel processing**: `dask`, `exactextract` 

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

If you encounter any problems with the code, data, or documentation, please shoot me an email! 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Acknowledgments

- **Cloud2Street** for the MODIS flood detection algorithm
- **EM-DAT** (CRED, UCLouvain) for disaster data
- **NASA** for MODIS imagery and Earth Engine platform
