#!/bin/bash

# =============================================================================
# produce_final_datasets.sh
# 
# USAGE INSTRUCTIONS:
# 1. Make executable: chmod +x produce_final_datasets.sh
# 2. Run the script: ./produce_final_datasets.sh
#
# REQUIREMENTS:
# - Python 3 must be installed
# - Run from directory containing the required Python scripts
# =============================================================================

# Array of Python scripts to run
scripts=("add_data_flags.py" "event_metrics_cleanup.py" "add_normalized_impacts.py" "add_zonal_stats.py" "compute_summary_stats.py" "prepare_panel_dataset.py")

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