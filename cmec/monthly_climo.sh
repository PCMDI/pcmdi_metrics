#!/bin/bash

cd $CMEC_CODE_DIR/cmec

tmp_param=$CMEC_WK_DIR/climatology_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "climatology"

pcmdi_compute_climatologies.py -p $tmp_param

mv $CMEC_WK_DIR/*.AC.nc $CMEC_MODEL_DATA/

