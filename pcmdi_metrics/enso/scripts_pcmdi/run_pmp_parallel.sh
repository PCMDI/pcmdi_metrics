#!/bin/sh
set -a

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
export OMP_NUM_THREADS=1

# Working conda env in gates: cdat82_20191107_py27

case_id="v"`date +"%Y%m%d"`
#case_id="v20200224"

#mips='cmip5 cmip6'
#mips='cmip5'
#mips='cmip6'
mips='CLIVAR_LE'
#mips='obs2obs'

#MCs='ENSO_perf ENSO_tel ENSO_proc'
#MCs='ENSO_perf'
MCs='ENSO_tel ENSO_proc'
#MCs='ENSO_tel'
#MCs='ENSO_proc'

modnames='all'
#modnames='IPSL-CM5A-LR'

realization='all'

mkdir -p log/$case_id

for mip in $mips; do
    if [ $mip == 'cmip5' ]; then
        #realization='r1i1p1'
        #modnames="BNU-ESM HadCM3"
        param_file='my_Param_ENSO_PCMDIobs.py'
    elif [ $mip == 'cmip6' ]; then
        #realization='r1i1p1f1'
        #modnames="BCC-ESM1 CESM2 CESM2-FV2 CESM2-WACCM CESM2-WACCM-FV2 GFDL-CM4 GFDL-ESM4 MRI-ESM2-0"
        param_file='my_Param_ENSO_PCMDIobs.py'
    elif [ $mip == 'CLIVAR_LE' ]; then
        param_file='my_Param_ENSO_PCMDIobs_CLIVAR_LE.py'
    elif [ $mip == 'obs2obs' ]; then
        param_file='my_Param_ENSO_obs2obs.py'
    fi

    for MC in $MCs; do
        echo $mip $MC $realization $case_id
        python -u ./parallel_driver.py -p $param_file --mip $mip --case_id=$case_id --modnames $modnames --metricsCollection $MC --realization $realization >& log/$case_id/log_parallel.${mip}.${MC}.all.${case_id}.txt &
        disown
        sleep 1
    done
done
