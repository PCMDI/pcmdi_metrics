#!/bin/sh
set -a

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
export OMP_NUM_THREADS=1

# Working conda env in gates: cdat82_20191107_py27

case_id="v"`date +"%Y%m%d"`
#case_id="v20210608"
#case_id="v20210620"

#mips='cmip5 cmip6'
#mips='cmip5'
mips='cmip6'
#mips='CLIVAR_LE'
#mips='obs2obs'

MCs='ENSO_perf ENSO_tel ENSO_proc'
#MCs='ENSO_perf'
#MCs='ENSO_tel ENSO_proc'
MCs='ENSO_tel'
#MCs='ENSO_proc'

param_dir='../param'

modnames='all'

realization='all'

mkdir -p log/$case_id

for mip in $mips; do
    if [ $mip == 'cmip5' ]; then
        #realization='r1i1p1'
        #modnames="BNU-ESM HadCM3"
        #modnames='IPSL-CM5A-LR'
        param_file='my_Param_ENSO_PCMDIobs.py'
    elif [ $mip == 'cmip6' ]; then
        #realization='r1i1p1f1'
        #modnames="BCC-ESM1 CESM2 CESM2-FV2 CESM2-WACCM CESM2-WACCM-FV2 GFDL-CM4 GFDL-ESM4 MRI-ESM2-0"
        #modnames="MIROC6 MPI-ESM-1-2-HAM MPI-ESM1-2-HR MPI-ESM1-2-LR MRI-ESM2-0 NESM3 NorCPM1 NorESM2-LM NorESM2-MM SAM0-UNICON TaiESM1 UKESM1-0-LL"
        #modnames="CNRM-CM6-1-HR CNRM-CM6-1 CNRM-ESM2-1 E3SM-1-0 E3SM-1-1-ECA E3SM-1-1 EC-Earth3-AerChem EC-Earth3-CC EC-Earth3 EC-Earth3-Veg-LR EC-Earth3-Veg FGOALS-f3-L FGOALS-g3 FIO-ESM-2-0 GFDL-CM4 GFDL-ESM4 GISS-E2-1-G-CC GISS-E2-1-G GISS-E2-1-H HadGEM3-GC31-LL HadGEM3-GC31-MM INM-CM4-8 INM-CM5-0 IPSL-CM5A2-INCA IPSL-CM6A-LR-INCA IPSL-CM6A-LR KACE-1-0-G KIOST-ESM MCM-UA-1-0 MIROC6 MIROC-ES2H MIROC-ES2L MPI-ESM-1-2-HAM MPI-ESM1-2-HR MPI-ESM1-2-LR MRI-ESM2-0 NESM3 NorCPM1 NorESM2-LM NorESM2-MM SAM0-UNICON TaiESM1 UKESM1-0-LL"
        #modnames="UKESM1-0-LL"
        #modnames="ACCESS-ESM1-5"
        param_file='my_Param_ENSO_PCMDIobs.py'
    elif [ $mip == 'CLIVAR_LE' ]; then
        param_file='my_Param_ENSO_PCMDIobs_CLIVAR_LE.py'
    elif [ $mip == 'obs2obs' ]; then
        param_file='my_Param_ENSO_obs2obs.py'
    fi

    for MC in $MCs; do
        echo $mip $MC $realization $case_id
        python -u ./parallel_driver.py -p $param_dir/$param_file --mip $mip --case_id=$case_id --modnames $modnames --metricsCollection $MC --realization $realization >& log/${case_id}/log_parallel.${mip}.${MC}.all.${case_id}.txt &
        disown
        sleep 1
    done
done
