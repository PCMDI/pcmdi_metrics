#!/bin/bash

cd $CMEC_CODE_DIR

tmp_param=$CMEC_WK_DIR/variability_modes_param.py

python pmp_param_generator.py $CMEC_CONFIG_DIR/cmec.json $tmp_param "variability_modes"

python variability_modes_driver.py -p $tmp_param \
--results_dir $CMEC_WK_DIR \
--reference_data_path $CMEC_OBS_DATA/psl_mon_20CR_BE_gn_v20200707_187101-201212.nc \
--modpath $CMEC_MODEL_DATA/psl_Amon_%(model)_historical_r1i1p1_185001-200512.nc