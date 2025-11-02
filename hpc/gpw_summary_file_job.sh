#!/bin/bash -l

# Job Information:
# Name: gpw_adm1_summary_job.sh 
# Description: Summarize GPW population and area metrics by GAUL ADM1 units
# Python Script: gpw_adm1_summary_file.py

#SBATCH --job-name=gpw_adm1_summary       # Name of the job
#SBATCH --cpus-per-task=64               # CPUs per task
#SBATCH --ntasks=1                       # Number of tasks per job
#SBATCH --nodes=1                        # Number of nodes to use
#SBATCH --time=05:00:00                  # Maximum runtime
#SBATCH --partition=dav_all,coe_all      # Queue/partition
#SBATCH --output=%x_%A_output.txt        # Standard output file with job name and job ID
#SBATCH --error=%x_%A_error.txt          # Standard error file with job name and job ID

# Path to the python script
PYSCRIPT="../dataset_generation/gpw_adm1_summary_file.py"

# Print SBATCH job settings for debugging to the log file

echo "====================================="
echo "Job Name: $SLURM_JOB_NAME"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Number of Nodes: $SLURM_JOB_NUM_NODES"
echo "Tasks Per Node: $SLURM_NTASKS_PER_NODE"
echo "Total Tasks: $SLURM_NTASKS"
echo "CPUs Per Task: $SLURM_CPUS_PER_TASK"
echo "Job Start Time: $(date)"
echo "====================================="

# Check if the Python script exists
if [ ! -f "$PYSCRIPT" ]; then
  echo "Error: Python script not found!"
  exit 1
fi

# Activate the Conda environment
conda activate clim-haz

# Start time tracking
start_time=$(date +%s)

# Run the Python script
python ${PYSCRIPT}

# End time tracking
end_time=$(date +%s)

# Calculate and print elapsed time to the output file
elapsed_time=$((end_time - start_time))
echo "====================================="
echo "Job completed in $elapsed_time seconds."
echo "Job End Time: $(date)"
echo "====================================="

# Deactivate Conda environment after job completion
conda deactivate
