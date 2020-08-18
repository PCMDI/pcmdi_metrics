#!/bin/sh
set -a

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
export OMP_NUM_THREADS=1

# Working conda env in gates: cdat82_20191107_py27

ver=`date +"%Y%m%d-%H%M"`
case_id="v"`date +"%Y%m%d"`
#case_id="v20191115"

#mips='cmip3 cmip5 cmip6'
#mips='cmip5 cmip6'
#mips='cmip5'
mips='cmip6'
#mips='cmip3'

#exps='20c3m amip'
#exps='20c3m'
exps='historical amip'
#exps='historical'

modes='all'

modnames='all'

realization='all'

for mip in $mips; do
    #if [ $mip == 'cmip5' ]; then
    #    realization='r1i1p1'
    #    #modnames="BNU-ESM CESM1-FASTCHEM CMCC-CM FGOALS-g2 HadCM3 HadGEM2-CC IPSL-CM5A-LR IPSL-CM5A-MR MIROC4h MIROC5 MPI-ESM-LR MPI-ESM-MR"
    #    #modnames="HadGEM2-CC HadGEM2-ES INMCM4 IPSL-CM5A-LR IPSL-CM5A-MR IPSL-CM5B-LR MIROC-ESM MIROC-ESM-CHEM MIROC4h MIROC5 MPI-ESM-LR MPI-ESM-MR MPI-ESM-P MRI-CGCM3 MRI-ESM1 NorESM1-M NorESM1-ME"
    #elif [ $mip == 'cmip6' ]; then
    #    realization='r1i1p1f1'
    #    #modnames="EC-Earth3 EC-Earth3-Veg"
    #fi
    for exp in $exps; do
        if [ $modes == 'all' ]; then
            if [ $exp == 'historical' ]; then
                modes_list='NAM NAO PNA SAM PDO NPO NPGO'
            elif [ $exp == 'amip' ]; then
                modes_list='NAM NAO PNA SAM NPO'
            fi
        else
            modes_list=$modes
        fi
        for mode in $modes_list; do
            echo $mip $exp $mode $case_id
            ./parallel_driver.py -p ../doc/myParam_${mode}_${mip}.py --mip $mip --exp $exp --case_id $case_id --modnames $modnames --realization $realization --variability_mode $mode >& ./log/log.${mip}.${exp}.${mode}.all.v${ver}.txt &
            disown
            sleep 1
        done
    done
done
