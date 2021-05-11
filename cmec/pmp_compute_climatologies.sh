#!/bin/bash

source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate cmec_pcmdi_metrics

cd $CMEC_WK_DIR

tmp_param=$CMEC_WK_DIR/compute_climatologies_param.py

python $CMEC_CODE_DIR/pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "climatology"

if [[ $? = 0 ]]; then
    pcmdi_compute_climatologies.py -p $tmp_param
else
    echo "Failure in PMP/compute_climo parameter file generation"
fi