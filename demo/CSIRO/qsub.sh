#!/bin/bash
#PBS -P p66
#PBS -q express
#PBS -l walltime=1:00:00
#PBS -l ncpus=1
#PBS -l mem=5GB
#PBS -l wd
#PBS -M me@pauldurack.com
/short/p66/pjd599/PCMDI_METRICS/v1p0/bin/pcmdi_metrics_driver.py -p /short/p66/pjd599/test/csiro_input_parameters_test.py


# qstat -u pjd599 # ; User queued (brief)
# nqstat -u pjd599 # ; User detailed queue info
# > qsub -P v66 qsub.sh # ; Run command line
