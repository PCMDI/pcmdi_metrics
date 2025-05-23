#!/bin/bash

source $CONDA_SOURCE
conda activate $CONDA_ENV_ROOT/_CMEC_pcmdi_metrics

cd $CMEC_WK_DIR

tmp_param=$CMEC_WK_DIR/extremes_param.py

python $CMEC_CODE_DIR/../scripts/pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "extremes"

if [[ $? = 0 ]]; then
    extremes_driver.py -p $tmp_param

else
    echo "Failure in PMP/extremes parameter file generation"
fi
