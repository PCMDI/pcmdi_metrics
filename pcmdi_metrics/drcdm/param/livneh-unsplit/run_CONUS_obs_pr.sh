#!/bin/bash
#SBATCH -A m2637
#SBATCH --job-name=livnehpr
#SBATCH --nodes=1
#SBATCH --time=3:00:00
#SBATCH --qos=regular
#SBATCH --constraint=cpu


source /global/homes/a/aordonez/miniconda3/etc/profile.d/conda.sh
conda activate pmp_drcdm

srun time drcdm_driver.py -p /global/homes/a/aordonez/pmp_param/drcdm/obs/livneh-unsplit/drcdm_livneh-unsplit_pr.py

