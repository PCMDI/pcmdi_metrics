#!/bin/sh
set -a

# grim: pmp_nightly_20190628
# gates: cdat82_20191107_py37

#parallel=no
parallel=yes

num_workers=20

mips="cmip5 cmip6"
#mips="cmip5"

if [ $parallel == no ]; then
    echo 'parallel no'
    for mip in $mips; do
        python -u mjo_metrics_driver.py -p ../doc/myParam_${mip}.py >& log.${mip}.txt &
        #python -u mjo_metrics_driver.py -p ../doc/myParam_${mip}.py --modnames ACCESS1-0 --realization r1i1p1 >& log.${mip}.txt &
        disown
    done
elif [ $parallel == yes ]; then
    echo 'parallel yes'
    for mip in $mips; do
        ./parallel_driver.py -p ../doc/myParam_${mip}.py --num_workers $num_workers >& log.parallel.${mip}.txt &
        disown
    done
fi
