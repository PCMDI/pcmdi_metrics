#!/bin/sh
set -ax

# Working conda env
# - Crunchy: pmp_nightly_20181128
# - Grim: pmp_nightly_20190522

ver=`date +"%Y%m%d"`
mips='cmip5 cmip6'
modes='NAM NAO PNA SAM PDO PDO NPGO'

for mip in $mips; do
    for mode in $modes; do
        python ../scripts/variability_modes_driver.py -p ../doc/param_special_cases/myParam_${mode}_${mip}_obs2.py >& log.${mip}.${mode}.all.v${ver}.obs2.txt &
        disown
    done
done
