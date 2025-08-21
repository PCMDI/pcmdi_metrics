#!/bin/bash
#SBATCH --job-name=drcdp_run
#SBATCH --nodes=1
#SBATCH --constraint=cpu
#SBATCH --ntasks-per-node=1
#SBATCH --time=04:00:00
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --partition=regular
#SBATCH --account=m4581

# Load necessary modules
cd ~/pcmdi_metrics/pcmdi_metrics/drcdm/
conda activate pcmdi_metrics
pip install ../../
scp ../mean_climate/lib/colormap.py /global/homes/j/jsgoodni/miniforge3/envs/pcmdi_metrics/lib/python3.10/site-packages/pcmdi_metrics/mean_climate/lib/colormap.py

# Run your Python script with srun (recommended for parallel jobs
srun python drcdm_driver.py -p param/drcdm_param.py
