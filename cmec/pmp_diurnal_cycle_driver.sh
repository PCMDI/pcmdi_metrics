#!/bin/bash

source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate cmec_pcmdi_metrics_test_install

cd $CMEC_WK_DIR

tmp_param=$CMEC_WK_DIR/diurnal_param.py

python $CMEC_CODE_DIR/pmp_param_generator.py \
$CMEC_CONFIG_DIR/cmec.json $tmp_param "diurnal_cycle"

if [[ $? = 0 ]]; then
    cmec_json=$CMEC_CONFIG_DIR/cmec.json

    printf "\ncomputeStdOfDailyMeans\n"

    computeStdOfDailyMeans.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/nc

    printf "\nstd_of_dailymeans\n"
    std_of_dailymeans.py \
    -p $tmp_param \
    -t 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_std_of_dailymeans.nc' \
    --results_dir $CMEC_WK_DIR/json \
    --modpath $CMEC_WK_DIR/nc

    printf "\ncompositeDiurnalStatistics\n"
    compositeDiurnalStatistics.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/nc

    printf "\nfourierDiurnalGridpoints\n"
    fourierDiurnalGridpoints.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/ascii \
    --modpath $CMEC_WK_DIR/nc \
    -t 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_avg.nc' \
    --filename_template_std 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_std.nc'

    printf "\nstd_of_hourlyvalues\n"
    std_of_hourlyvalues.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/json \
    --modpath $CMEC_WK_DIR/nc \
    --filename_template 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_std.nc'

    printf "\nstd_of_meandiurnalcycle\n"
    std_of_meandiurnalcycle.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/json \
    --modpath $CMEC_WK_DIR/nc \
    --filename_template 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_avg.nc'

    printf "\nfourierDiurnalAllGrid\n"
    fourierDiurnalAllGrid.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/nc \
    --modpath $CMEC_WK_DIR/nc \
    -t 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_avg.nc'

    printf "\nsavg_fourier.py\n"
    savg_fourier.py \
    -p $tmp_param \
    --results_dir $CMEC_WK_DIR/json \
    --modpath $CMEC_WK_DIR/nc \
    -t 'pr_%(model)_%(month)_%(firstyear)-%(lastyear)_S.nc'

else
    printf "Failure in PMP/diurnal_cycle parameter file generation"
fi
