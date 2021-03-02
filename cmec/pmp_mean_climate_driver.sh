#!/bin/bash

cd $CMEC_CODE_DIR

tmp_param=$CMEC_WK_DIR/mjo_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "mean_climate"

if [[ $? = 0 ]]; then
    mean_climate_driver.py -p $tmp_param
else
    echo "Failure in PMP/mjo parameter file generation"
fi