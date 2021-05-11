#!/bin/bash

source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate cmec_pcmdi_metrics

cd $CMEC_CODE_DIR

tmp_param=$CMEC_WK_DIR/variability_modes_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "variability_modes"

if [[ $? = 0 ]]; then
    variability_modes_driver.py -p $tmp_param
else
    echo "Failure in PMP/variability_modes"
fi