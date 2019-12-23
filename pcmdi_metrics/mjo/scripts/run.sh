#!/bin/sh
set -a

# grim: pmp_nightly_20190628
# gates: cdat82_20191107_py37

python mjo_metric_driver.py -p ../doc/myParam_cmip5.py >& log.cmip5.txt &
disown
python mjo_metric_driver.py -p ../doc/myParam_cmip6.py >& log.cmip6.txt &
disown
