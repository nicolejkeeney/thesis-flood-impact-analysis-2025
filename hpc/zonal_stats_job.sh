#!/bin/bash -l

# Job Information:
# Name: zonal_stats_job.sh 
# Description: compute climate stats by admin1 region and output a netcdf for each year-day in zonal-stats-input.dat
# Note: Cashew is limited to input files with 1000 rows due to scheduler limitations 
# Python Script: compute_zonal_stats.py

#SBATCH --job-name=zonal_stats           # Name of the job
#SBATCH --array=1-1000                   # Array of {year} {day} (adjust according to the number of rows in zonal-stats-input.dat)
#SBATCH --cpus-per-task=1                # CPUs per task
#SBATCH --ntasks=1                       # Number of tasks per job
#SBATCH --nodes=1                        # Number of nodes to use
#SBATCH --time=05:00:00                  # Maximum runtime
#SBATCH --partition=dav_all              # Queue/partition
#SBATCH --output=%x_%A_%a_output.txt     # Standard output file with job name and job ID
#SBATCH --error=%x_%A_%a_error.txt       # Standard error file with job name and job ID

# Path to the python script
PYSCRIPT="../dataset_generation/compute_zonal_stats.py"

# Path to input text file 
INPUT_FILE="../text_inputs/zonal_inputs/zonal_stats_input_001.txt"

# Get the year and day for this array task
read YEAR DAY <<< $(awk "NR==$SLURM_ARRAY_TASK_ID" $INPUT_FILE)

# Create a log file based on job name and ID
output_file="${SLURM_JOB_NAME}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_output.txt"

# Print SBATCH job settings for debugging to the log file
{
  echo "====================================="
  echo "Year: $YEAR"
  echo "Job Name: $SLURM_JOB_NAME"
  echo "Job ID: $SLURM_ARRAY_JOB_ID"
  echo "Task ID: $SLURM_ARRAY_TASK_ID"
  echo "Partition: $SLURM_JOB_PARTITION"
  echo "Number of Nodes: $SLURM_JOB_NUM_NODES"
  echo "Tasks Per Node: $SLURM_NTASKS_PER_NODE"
  echo "Total Tasks: $SLURM_NTASKS"
  echo "CPUs Per Task: $SLURM_CPUS_PER_TASK"
  echo "Job Start Time: $(date)"
  echo "====================================="
} >> "$output_file"

# Check if the Python script exists
if [ ! -f "$PYSCRIPT" ]; then
  echo "Error: Python script not found!" >> "$output_file"
  exit 1
fi

# Activate the Conda environment
conda activate clim-haz

# Start time tracking
start_time=$(date +%s)

# Run the Python script
python ${PYSCRIPT} --year=$YEAR --day=$DAY

# End time tracking
end_time=$(date +%s)

# Calculate and print elapsed time to the output file
elapsed_time=$((end_time - start_time))
{
  echo "====================================="
  echo "Job completed in $elapsed_time seconds."
  echo "Job End Time: $(date)"
  echo "====================================="
} >> "$output_file"

# Deactivate Conda environment after job completion
conda deactivate
