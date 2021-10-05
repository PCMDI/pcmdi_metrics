#!/bin/sh
set -a

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
export OMP_NUM_THREADS=1

# Working conda env in gates: cdat82_20191107_py27, cdat82_20200128_py27

case_id="v"`date +"%Y%m%d"`

mips='obs2obs'

MCs='ENSO_perf ENSO_tel ENSO_proc'
modnames='20CR ERA-20C ERA-INT TropFlux-1-0 CMAP-V1902 GPCP-2-3 TRMM-3B43v-7 ERA-5 CERES-EBAF-4-0 CERES-EBAF-4-1 AVISO-1-0'

mkdir -p log/$case_id

for mip in $mips; do
    for MC in $MCs; do
        echo $mip $MC $realization $case_id
        python -u ./parallel_driver.py -p my_Param_ENSO_obs2obs.py --mip $mip --case_id=$case_id --modnames $modnames --metricsCollection $MC >& log/$case_id/log_parallel.${mip}.${MC}.all.${case_id}.txt &
        disown
        sleep 1
    done
done
