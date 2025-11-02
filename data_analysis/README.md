# Data Analysis Scripts

This directory contains analysis scripts for generating summary statistics, visualizations, and econometric models used in the publication. The scripts operate on the final datasets produced by the data generation pipeline.

## Prerequisites

These scripts expect the following data files to be available in `../data/`:
- `event_level_flood_dataset.csv` - Final event-level dataset
- `panel_dataset.csv` - Panel dataset for regression analysis
- `emdat/emdat-2000-2024_preprocessed.csv` - Preprocessed EM-DAT data
- `data_processing_flags.csv` - Flag definitions

Figures are saved to `../figures/` subdirectories.

## Running Multiple Scripts

Use `produce_all_figures.sh` to run multiple visualization scripts sequentially:

```bash
chmod +x produce_all_figures.sh
./produce_all_figures.sh
```

This script runs the main visualization scripts and will stop if any script fails.

## Analysis Scripts

### Summary Statistics

**`print_event_stats.py`**
- Prints event counts, durations, and impact statistics to console
- Useful for quick data overview

**`emdat_yearly_barchart.py`**
- Creates bar charts of yearly aggregated damages, affected populations, and event counts
- Output: `figures/emdat_yearly_barcharts.png`

**`event_count_distribution.py`**
- Visualizes distribution of events across countries and regions
- Output: `figures/event_count_distribution.png`

**`event_duration_violinplot.py`**
- Violin plots showing distribution of event durations
- Output: `figures/event_duration_violinplot.png`

**`emdat_impact_distribution_stripplots.py`**
- Strip plots showing distribution of damages and affected populations
- Output: `figures/emdat_impact_distribution/`

**`top_regions_hist.py`**
- Histograms of events for the most affected regions
- Output: `figures/top_regions_hist.png`

**`flag_summary_plots.py`**
- Visualizes data quality flag distributions
- Output: `figures/flag_summary/`

**`precip_distribution.py`**
- Multi-panel histograms of precipitation anomalies, damages, and flood probabilities
- Output: `figures/panel_model/precip_distr_all.png`

### Maps

**`summary_maps.py`**
- Choropleth maps showing event counts and impacts by admin1 region
- Output: `figures/summary_maps/`

**`create_flood_map.py`**
- Creates detailed map for a specific flood event
- Usage: `python create_flood_map.py <event_id>`
- Example: `python create_flood_map.py 04-2011-0131-CAN-825`
- Output: `figures/flood_maps/`

### Regression Analysis

**`emdat_modis_regression.py`**
- Compares EM-DAT reported impacts vs. MODIS-derived affected populations
- Tests correlation between satellite-detected floods and reported impacts
- Output: `figures/emdat_modis_regression/`

**`panel_analysis.py`**
- Panel regression models analyzing precipitation anomalies → damages/affected populations
- Estimates linear and quadratic effects with fixed effects
- Standard errors clustered by country
- Output: `figures/panel_model/`

**`state_damages_modis_regression.ipynb`**
- Jupyter notebook with additional regression analysis
- Exploratory analysis of state-level damages vs. MODIS flood metrics

### Impact Allocation Methods

**`plot_impact_allocation_approaches.py`**
- Compares different methods for allocating impacts across admin regions
- Visualizes population-weighted vs. equal allocation approaches
- Output: `figures/impact_allocation/`

## Utility Module

**`data_analysis_utils.py`**
- Helper functions used across analysis scripts
- Includes: `filter_by_flags()`, data loading utilities, plotting helpers
- Import with: `from data_analysis_utils import filter_by_flags`

## Notes

- All scripts use relative paths (`../data/`, `../figures/`)
- Run scripts from this directory: `python script_name.py`
- Most scripts have configurable parameters at the top (figure DPI, font sizes, etc.)
- Data quality filtering is handled via the `filter_by_flags()` function
