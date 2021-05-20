#!/bin/bash

source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate cmec_pcmdi_metrics

cd $CMEC_CODE_DIR

tmp_param=$CMEC_WK_DIR/monsoon_sperber_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "monsoon_sperber"

if [[ $? = 0 ]]; then
    driver_monsoon_sperber.py -p $tmp_param
else
    echo "Failure in PMP/monsoon_sperber parameter file generation"
fi