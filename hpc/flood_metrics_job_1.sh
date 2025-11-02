#!/bin/bash -l

# Job Script: flood_metrics_job.sh
#
# Description:
#   Computes flood metrics for a list event IDs in serial.
#   Each ID is read from a text file and passed one at a time to the 
#   Python script. This job is not parallelized; IDs are processed 
#   sequentially within a single SLURM task.
#   Takes about 2 hr for ~2500 events 
#
# Python Script:
#   extract_flood_metrics.py

#SBATCH --job-name=metrics_1             # Job name
#SBATCH --cpus-per-task=1                # Just use a single CPU
#SBATCH --ntasks=1                       # Number of tasks
#SBATCH --nodes=1                        # Number of nodes
#SBATCH --time=05:00:00                  # Max runtime
#SBATCH --partition=coe_all              # Partition/queue
#SBATCH --output=%x_%j_output.txt        # Standard output
#SBATCH --error=%x_%j_error.txt          # Standard error

# Paths
PYSCRIPT="../dataset_generation/extract_flood_metrics.py"
ID_INPUT_FILE="../text_inputs/emdat_mon_yr_adm1_id/emdat_mon_yr_adm1_id_1.txt"
OUTPUT_FILE="${SLURM_JOB_NAME}_${SLURM_JOB_ID}_output.txt"

# Log job settings
{
  echo "====================================="
  echo "Input File: $ID_INPUT_FILE"
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

# Loop through ADM1 codes
while IFS= read -r ID; do
  echo "Processing ID: $ID" >> "$OUTPUT_FILE"
  python "$PYSCRIPT" "$ID" >> "$OUTPUT_FILE" 2>&1
done < "$ID_INPUT_FILE"

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
