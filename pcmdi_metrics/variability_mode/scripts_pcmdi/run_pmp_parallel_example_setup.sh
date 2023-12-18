#!/bin/sh
set -a

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
export OMP_NUM_THREADS=1

# Working conda env in gates: cdat82_20191107_py27

ver=`date +"%Y%m%d-%H%M"`
case_id="v"`date +"%Y%m%d"`

#mips='cmip3 cmip5 cmip6'
#mips='cmip5 cmip6'
#mips='cmip5'
mips='cmip6'
#mips='cmip3'

#exps='20c3m amip'
#exps='20c3m'
#exps='historical amip'
exps='historical'
#exps='amip'

#modes='all'
modes='NAO NPO PNA'

modnames='all'

realization='all'

param_dir='../../../sample_setups/pcmdi_parameter_files/variability_modes'
#param_dir='../../../sample_setups/pcmdi_parameter_files/variability_modes/alternative_obs'

for mip in $mips; do
    echo $mip
    for exp in $exps; do
        if [ $modes == 'all' ]; then
            if [ $exp == 'historical' ] || [ $exp == '20c3m' ]; then
                modes_list='NAM NAO PNA SAM PDO NPO NPGO'
            elif [ $exp == 'amip' ]; then
                modes_list='NAM NAO PNA SAM NPO'
            fi
        else
            modes_list=$modes
        fi
        # Log dir
        mkdir -p ./log/$mip/$exp/$case_id
        # Run
        for mode in $modes_list; do
            echo $mip $exp $mode $case_id
            python ./parallel_driver.py -p ${param_dir}/myParam_${mode}_${mip}.py --param_dir $param_dir --mip $mip --exp $exp --case_id $case_id --modnames $modnames --realization $realization --variability_mode $mode >& ./log/$mip/$exp/$case_id/log.${mip}.${exp}.${mode}.all.v${ver}.txt &
            disown
            sleep 1
        done
    done
done
