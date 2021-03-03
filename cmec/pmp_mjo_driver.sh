#!/bin/bash

cd $CMEC_CODE_DIR/cmec

tmp_param=$CMEC_WK_DIR/mjo_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "mjo"

if [[ $? = 0 ]]; then
    mjo_metrics_driver.py -p $tmp_param
else
    echo "Failure in PMP/mjo parameter file generation"
fi