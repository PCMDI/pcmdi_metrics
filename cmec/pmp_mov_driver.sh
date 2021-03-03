#!/bin/bash

cd $CMEC_CODE_DIR/cmec

tmp_param=$CMEC_WK_DIR/variability_modes_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "variability_modes"

if [[ $? = 0 ]]; then
    variability_modes_driver.py -p $tmp_param
else
    echo "Failure in PMP/variability_modes"
fi