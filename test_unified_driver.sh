#!/bin/bash
#
# Test script for unified mean climate driver
#
# This script demonstrates how to test the unified driver with minimal resources

echo "=================================================="
echo "Testing Mean Climate Unified Driver"
echo "=================================================="

# Set up test directories
TEST_DIR="/pscratch/sd/l/lee1043/git/pcmdi_metrics/test_unified_output"
mkdir -p ${TEST_DIR}

# Configuration
REF_CATALOGUE="/global/cfs/projectdirs/m4581/obs4MIPs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_latest.json"
MODEL_CATALOGUE="/pscratch/sd/l/lee1043/git/pcmdi_metrics/sample_setups/pcmdi/data_search/models_path_CMIP6_historical_mon.json"
REF_DATA_HEAD="/global/cfs/projectdirs/m4581/obs4MIPs"

echo ""
echo "Test Configuration:"
echo "  Test directory: ${TEST_DIR}"
echo "  Reference catalogue: ${REF_CATALOGUE}"
echo "  Model catalogue: ${MODEL_CATALOGUE}"
echo ""

# Test 1: Check help
echo "=================================================="
echo "Test 1: Display help message"
echo "=================================================="
python pcmdi_metrics/mean_climate/mean_climate_unified_driver.py --help

echo ""
echo "=================================================="
echo "Test 2: Run unified mode with minimal data"
echo "=================================================="
echo "  Mode: unified"
echo "  Variable: pr (precipitation)"
echo "  Models: 1 model, first member only"
echo "  Time period: 1980-01 to 1984-12 (5 years)"
echo ""

python pcmdi_metrics/mean_climate/mean_climate_unified_driver.py \
    --mode unified \
    --working_dir ${TEST_DIR}/work \
    --output_path ${TEST_DIR}/output \
    --ref_catalogue ${REF_CATALOGUE} \
    --model_catalogue ${MODEL_CATALOGUE} \
    --ref_data_head ${REF_DATA_HEAD} \
    --variables pr \
    --num_models 1 \
    --first_member_only \
    --start 1980-01 \
    --end 1984-12 \
    --target_grid 2.5x2.5 \
    --regions global

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "Test 2: PASSED"
    echo "=================================================="
    echo "Output files:"
    ls -lh ${TEST_DIR}/output/*.json 2>/dev/null || echo "  No JSON files found"
    echo ""
    echo "Annual cycle directories:"
    ls -d ${TEST_DIR}/work/clim_*/ 2>/dev/null || echo "  No climatology directories found"
else
    echo ""
    echo "=================================================="
    echo "Test 2: FAILED"
    echo "=================================================="
    echo "Check error log: ${TEST_DIR}/work/error_log.txt"
    exit 1
fi

echo ""
echo "=================================================="
echo "Test 3: Run annual_cycle mode only"
echo "=================================================="
echo "  Mode: annual_cycle"
echo "  Variable: tas (temperature)"
echo "  Models: 1 model"
echo ""

TEST3_DIR="${TEST_DIR}/test3"
mkdir -p ${TEST3_DIR}

python pcmdi_metrics/mean_climate/mean_climate_unified_driver.py \
    --mode annual_cycle \
    --working_dir ${TEST3_DIR}/work \
    --output_path ${TEST3_DIR}/output \
    --ref_catalogue ${REF_CATALOGUE} \
    --model_catalogue ${MODEL_CATALOGUE} \
    --ref_data_head ${REF_DATA_HEAD} \
    --variables tas \
    --num_models 1 \
    --first_member_only \
    --start 1980-01 \
    --end 1982-12

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "Test 3: PASSED"
    echo "=================================================="
    echo "Annual cycles generated in: ${TEST3_DIR}/work/"
else
    echo ""
    echo "=================================================="
    echo "Test 3: FAILED"
    echo "=================================================="
    exit 1
fi

echo ""
echo "=================================================="
echo "ALL TESTS COMPLETED"
echo "=================================================="
echo ""
echo "To clean up test outputs:"
echo "  rm -rf ${TEST_DIR}"
echo ""
