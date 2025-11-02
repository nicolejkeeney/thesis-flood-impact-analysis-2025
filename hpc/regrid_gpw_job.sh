#!/bin/bash -l

# Job Information:
# Name: regrid_gpw_job.sh
# Description: Run the regrid_gpw.py Python script for 5 years (as a SLURM job array)
# Python Script: regrid_gpw.py

#SBATCH --job-name=regrid_gpw                 # Job name
#SBATCH --array=0-4                           # Array: 5 jobs, index 0 to 4
#SBATCH --cpus-per-task=64                    # CPUs per task
#SBATCH --ntasks=1                            # Number of tasks per job
#SBATCH --nodes=1                             # Number of nodes per task
#SBATCH --time=24:00:00                       # Time limit
#SBATCH --partition=dav_all                   # Partition
#SBATCH --output=regrid_gpw_%A_%a_output.txt  # Stdout (%A=job ID, %a=array index)
#SBATCH --error=regrid_gpw_%A_%a_error.txt    # Stderr

# List of years to match SLURM_ARRAY_TASK_ID
years=(2000 2005 2010 2015 2020)

# Determine the year for this array task
year=${years[$SLURM_ARRAY_TASK_ID]}

# Path to the Python script
PYSCRIPT="../modis_event_damages/regrid_gpw.py"

# Output log file 
output_file="regrid_gpw_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_output.txt"

# Print SLURM job settings to log
{
  echo "====================================="
  echo "Job Name: $SLURM_JOB_NAME"
  echo "Job ID: $SLURM_JOB_ID"
  echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
  echo "Processing Year: $year"
  echo "Partition: $SLURM_JOB_PARTITION"
  echo "Nodes: $SLURM_JOB_NUM_NODES"
  echo "Tasks/Node: $SLURM_NTASKS_PER_NODE"
  echo "Total Tasks: $SLURM_NTASKS"
  echo "CPUs/Task: $SLURM_CPUS_PER_TASK"
  echo "Start Time: $(date)"
  echo "====================================="
} >> "$output_file"

# Check if Python script exists
if [ ! -f "$PYSCRIPT" ]; then
  echo "Error: Python script not found at $PYSCRIPT" >> "$output_file"
  exit 1
fi

# Activate environment
conda activate clim-haz

# Time tracking
start_time=$(date +%s)

# Run the Python script for this year
python "$PYSCRIPT" "$year"

# Record time
end_time=$(date +%s)
elapsed=$((end_time - start_time))

# Print completion message
{
  echo "====================================="
  echo "Finished processing year: $year"
  echo "Elapsed time: ${elapsed} seconds"
  echo "End Time: $(date)"
  echo "====================================="
} >> "$output_file"

# Deactivate environment
conda deactivate
