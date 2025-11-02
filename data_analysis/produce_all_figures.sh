#!/bin/bash

# =============================================================================
# produce_all_figures.sh
# 
# USAGE INSTRUCTIONS:
# 1. Make executable: chmod +x produce_all_figures.sh
# 2. Run the script: ./produce_all_figures.sh
#
# REQUIREMENTS:
# - Python 3 must be installed
# - Run from directory containing the required Python scripts
# =============================================================================

# Array of Python scripts to run
scripts=("emdat_modis_regression.py" "flag_summary_plots.py" "plot_impact_allocation_approaches.py" "emdat_impact_distribution_stripplots.py" "top_regions_hist.py" "event_count_distribution.py" "event_duration_violinplot.py" "emdat_yearly_barchart.py" "precip_distribution.py" "summary_maps.py")

echo "Starting Python script execution..."

# Loop through and run each script
for script in "${scripts[@]}"; do
    echo "Running $script..."
    
    if python3 "$script"; then
        echo "✓ $script completed successfully"
    else
        echo "✗ $script failed with exit code $?"
        exit 1  # Stop execution if a script fails
    fi
done

echo "All scripts completed successfully!"