#!/bin/bash -l

# Job Script: weighted_damages_job.sh
#
# Description:
#   Computes population weighted damages for each flood 
#
# Python Script:
#   compute_pop_weighted_damages.py

#SBATCH --job-name=weighted_damages      # Job name
#SBATCH --cpus-per-task=1                # Just use a single CPU
#SBATCH --ntasks=1                       # Number of tasks
#SBATCH --nodes=1                        # Number of nodes
#SBATCH --time=05:00:00                  # Max runtime
#SBATCH --partition=dav_all,coe_all      # Partition/queue
#SBATCH --output=%x_%j_output.txt        # Standard output
#SBATCH --error=%x_%j_error.txt          # Standard error

# Paths
PYSCRIPT="../dataset_generation/compute_pop_weighted_damages.py"
OUTPUT_FILE="${SLURM_JOB_NAME}_${SLURM_JOB_ID}_output.txt"

# Log job settings
{
  echo "====================================="
  echo "Job Name: $SLURM_JOB_NAME"
  echo "Job ID: $SLURM_JOB_ID"
  echo "Partition: $SLURM_JOB_PARTITION"
  echo "Nodes: $SLURM_JOB_NUM_NODES"
  echo "Tasks: $SLURM_NTASKS"
  echo "CPUs Per Task: $SLURM_CPUS_PER_TASK"
  echo "Start Time: $(date)"
  echo "====================================="
} >> "$OUTPUT_FILE"

# Check Python script exists
if [ ! -f "$PYSCRIPT" ]; then
  echo "Error: Python script not found!" >> "$OUTPUT_FILE"
  exit 1
fi

# Activate Conda environment
conda activate clim-haz

# Start timer
start_time=$(date +%s)

# Run the Python script
python ${PYSCRIPT}

# End timer
end_time=$(date +%s)
elapsed_time=$((end_time - start_time))

# Log job completion
{
  echo "====================================="
  echo "Job completed in $elapsed_time seconds."
  echo "Job End Time: $(date)"
  echo "====================================="
} >> "$OUTPUT_FILE"

# Deactivate Conda
conda deactivate
