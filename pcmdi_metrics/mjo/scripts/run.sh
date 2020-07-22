#!/bin/sh
set -a

# grim: pmp_nightly_20190628
# gates: cdat82_20191107_py37, pmp_nightly_20190912

#parallel=no
parallel=yes

num_workers=20

mips="cmip5 cmip6"
#mips="cmip5"

mkdir -p log

if [ $parallel == no ]; then
    echo 'parallel no'
    for mip in $mips; do
        python -u mjo_metrics_driver.py -p ../doc/myParam_mjo.py --mip ${mip} >& log/log.${mip}.txt &
        disown
    done
elif [ $parallel == yes ]; then
    echo 'parallel yes'
    modnames="all"
    realization="all"
    for mip in $mips; do
        python -u ./parallel_driver.py -p ../doc/myParam_mjo.py --mip ${mip} --num_workers $num_workers --modnames $modnames --realization $realization  >& log/log.parallel.${mip}.txt &
        disown
    done
fi
