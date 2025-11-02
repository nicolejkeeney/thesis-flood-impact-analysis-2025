#!/bin/bash -l

# Job Script: gpw_adm1_job.sh
#
# Description:
#   Processes a list of small ADM1 regions in serial using high-resolution GPW data.
#   Each ADM1 code is read from a text file and passed one at a time to the 
#   Python script. This job is not parallelized—ADM1 regions are processed 
#   sequentially within a single SLURM task.
#
# Python Script:
#   process_gpw_adm1_zone.py

#SBATCH --job-name=smol_1                # Job name
#SBATCH --cpus-per-task=64               # Request entire node 
#SBATCH --ntasks=1                       # Number of tasks
#SBATCH --nodes=1                        # Number of nodes
#SBATCH --time=48:00:00                  # Max runtime
#SBATCH --partition=dav_all,coe_all      # Partition/queue
#SBATCH --output=%x_%j_output.txt        # Standard output
#SBATCH --error=%x_%j_error.txt          # Standard error

# Paths
PYSCRIPT="../dataset_generation/process_gpw_adm1.py"
ADM1_FILE="../text_inputs/adm1_codes/smol_adm1_codes_1.txt"
OUTPUT_FILE="${SLURM_JOB_NAME}_${SLURM_JOB_ID}_output.txt"

# Log job settings
{
  echo "====================================="
  echo "Input File: $ADM1_FILE"
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
while IFS= read -r ADM1_CODE; do
  echo "Processing ADM1_CODE: $ADM1_CODE" >> "$OUTPUT_FILE"
  python "$PYSCRIPT" "$ADM1_CODE" >> "$OUTPUT_FILE" 2>&1
done < "$ADM1_FILE"

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
