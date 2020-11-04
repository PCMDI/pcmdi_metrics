#!/bin/sh
set -ax

# Working conda env
# - Crunchy: pmp_nightly_20181128, pmp_nightly_20190617
# - Grim: pmp_nightly_20190522

ver=`date +"%Y%m%d"`
mips='cmip3 cmip5 cmip6'
mips='cmip6'
modes='NAM NAO PNA SAM PDO NPO NPGO'

for mip in $mips; do
    for mode in $modes; do
        python ../scriptsvariability_modes_driver.py -p ../doc/myParam_${mode}_${mip}.py --modnames all >& log.${mip}.${mode}.all.v${ver}.txt &
        #python ../scriptsvariability_modes_driver.py -p ../doc/param_special_cases/myParam_${mode}_${mip}_obs2.py >& log.${mip}.${mode}.all.v${ver}.obs2.txt &
        disown
    done
done
