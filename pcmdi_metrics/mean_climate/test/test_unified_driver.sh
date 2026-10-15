#!/bin/bash
#
# Test script for unified mean climate driver
#
# This script demonstrates how to test the unified driver with minimal resources
#
# IMPORTANT: You must have your pcmdi_metrics conda environment activated before running this script!
#   conda activate pmp_devel_20260714  # or your environment name

echo "=================================================="
echo "Testing Mean Climate Unified Driver"
echo "=================================================="

# Check if we have the required Python packages
python -c "import xarray" 2>/dev/null || {
    echo "ERROR: Required Python packages not found!"
    echo "Please activate your pcmdi_metrics conda environment first:"
    echo "  conda activate pmp_devel_20260714  # or your environment name"
    exit 1
}

# Get paths relative to this script
# test is in: pcmdi_metrics/mean_climate/test
# driver is in: pcmdi_metrics/mean_climate
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRIVER_SCRIPT="${SCRIPT_DIR}/../mean_climate_unified_driver.py"
REPO_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Set PYTHONPATH so the driver can import pcmdi_metrics
export PYTHONPATH="${REPO_DIR}:${PYTHONPATH}"

echo "Repository: ${REPO_DIR}"
echo "Driver script: ${DRIVER_SCRIPT}"
echo "PYTHONPATH: ${PYTHONPATH}"
echo ""

# Set up test directories
TEST_DIR="${REPO_DIR}/pcmdi_metrics/mean_climate/test/test_unified_output"
mkdir -p ${TEST_DIR}

# Configuration
REF_CATALOGUE="/global/cfs/projectdirs/m4581/obs4MIPs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_latest.json"
MODEL_CATALOGUE="${REPO_DIR}/sample_setups/pcmdi/data_search/models_path_CMIP6_historical_mon_test.json"
REF_DATA_HEAD="/global/cfs/projectdirs/m4581/obs4MIPs"

# Check if catalogues exist
if [ ! -f "${REF_CATALOGUE}" ]; then
    echo "ERROR: Reference catalogue not found: ${REF_CATALOGUE}"
    echo "Please update the path in this script or create the catalogue file."
    exit 1
fi

if [ ! -f "${MODEL_CATALOGUE}" ]; then
    echo "ERROR: Model catalogue not found: ${MODEL_CATALOGUE}"
    echo "Please create a model catalogue file or run the catalogue generation script."
    echo "See: ${REPO_DIR}/sample_setups/pcmdi/data_search/generate_model_catalogue_xsearch.py"
    exit 1
fi

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
python "${DRIVER_SCRIPT}" --help

echo ""
echo "=================================================="
echo "Test 2: Run unified mode with minimal data"
echo "=================================================="
echo "  Mode: unified"
echo "  Variable: pr (precipitation)"
echo "  Models: 1 model, first member only"
echo "  Time period: 1980-01 to 1984-12 (5 years)"
echo ""

python "${DRIVER_SCRIPT}" \
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

python "${DRIVER_SCRIPT}" \
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
