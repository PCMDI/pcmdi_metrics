#!/bin/bash

source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate cmec_pcmdi_metrics

cd $CMEC_CODE_DIR

tmp_param=$CMEC_WK_DIR/monsoon_wang_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "monsoon_wang"

if [[ $? = 0 ]]; then
    mpindex_compute.py -p $tmp_param
else
    echo "Failure in PMP/monsoon_wang parameter file generation"
fi