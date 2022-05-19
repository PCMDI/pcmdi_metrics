#!/bin/bash

source $CONDA_SOURCE
conda activate $CONDA_ENV_ROOT/_CMEC_pcmdi_metrics

cd $CMEC_WK_DIR

tmp_param=$CMEC_WK_DIR/monsoon_wang_param.py

python $CMEC_CODE_DIR/../scripts/pmp_param_generator.py \
$CMEC_CONFIG_DIR/cmec.json $tmp_param "monsoon_wang"

if [[ $? = 0 ]]; then
    mpindex_compute.py -p $tmp_param

    # write output.json
    python $CMEC_CODE_DIR/monsoon_wang_output.py
else
    echo "Failure in PMP/monsoon_wang parameter file generation"
fi
