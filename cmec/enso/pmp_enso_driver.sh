#!/bin/bash

source $CONDA_SOURCE
conda activate $CONDA_ENV_ROOT/_CMEC_pcmdi_metrics

cd $CMEC_WK_DIR

tmp_param=$CMEC_WK_DIR/enso_param.py

python $CMEC_CODE_DIR/../scripts/pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "enso"

if [[ $? = 0 ]]; then
    enso_driver.py -p $tmp_param

    # write output.json
    # Not implemented yet
    #python $CMEC_CODE_DIR/enso_output.py
else
    echo "Failure in PMP/enso parameter file generation"
fi
