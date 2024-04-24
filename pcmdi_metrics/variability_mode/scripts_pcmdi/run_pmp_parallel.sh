#!/bin/sh
set -a

# To avoid below error
# OpenBLAS blas_thread_init: pthread_create failed for thread XX of 96: Resource temporarily unavailable
# export OMP_NUM_THREADS=1

# Working conda env in gates: cdat82_20191107_py27

ver=`date +"%Y%m%d-%H%M"`
case_id="v"`date +"%Y%m%d"`
#case_id="v20240401"

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

modes='all'
#modes='NAO NPO PNA'
#modes='NAM NAO PNA NPO'
#modes='SAM PDO NPGO'
#modes="NAO NPO PNA SAM NPGO"
#modes="NAM PDO"
#modes="NPO NPGO"
#modes="SAM"

modnames='all'

realization='all'

num_workers=5

#param_dir='../../../sample_setups/pcmdi_parameter_files/variability_modes'
#param_dir='../../../sample_setups/pcmdi_parameter_files/variability_modes/alternative_obs'
param_dir='../param'

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

            if [ $mode == 'PDO' ] || [ $mode == 'NPGO' ] || [ $mode == 'AMO' ]; then
                mode_o='PDO'
            elif [ $mode == "SAM" ]; then
                mode_o='SAM'
            else
                mode_o='NAM'
            fi

            echo $mip $exp $mode $case_id $mode_o
            ./parallel_driver.py -p ${param_dir}/myParam_pcmdi_${mode_o}.py --param_dir $param_dir --mip $mip --exp $exp --case_id $case_id --modnames $modnames --realization $realization --variability_mode $mode --num_workers $num_workers >& ./log/$mip/$exp/$case_id/log.${mip}.${exp}.${mode}.all.v${ver}.txt &
            disown
            sleep 1
        done
    done
done
