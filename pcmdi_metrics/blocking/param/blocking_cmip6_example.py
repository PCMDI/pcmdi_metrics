"""
Example parameter file for blocking detection driver.

Usage:
    python blocking_driver.py --param blocking_cmip6_example.py

Or modify parameters and run:
    from pcmdi_metrics.blocking.blocking_driver import main
    main(param_file='blocking_cmip6_example.py')
"""

# ==============================================================================
# Experiment Configuration
# ==============================================================================

# CMIP6 experiments to process
# Examples: ["historical"], ["ssp126"], ["ssp245"], ["ssp370"], ["ssp585"]
exps = ["historical"]

# Variable and frequency
var = "zg"  # Geopotential height
freq = "day"  # Daily data required
cmipTable = "day"
mip_era = "CMIP6"

# ==============================================================================
# Model Selection
# ==============================================================================

# Use only first ensemble member of each model
# Set to False to process all available ensemble members
first_member_only = True

# Optionally specify specific models (leave commented to use all available)
# models = ["CESM2", "ACCESS-CM2", "MPI-ESM1-2-LR"]

# ==============================================================================
# Processing Options
# ==============================================================================

# Parallel processing
parallel = False  # Set to True for parallel processing
num_processes = 3  # Number of parallel processes

# Debug mode (processes only first 3 models, shorter time period)
debug = False

# Overwrite existing output files
overwrite_output = False

# Processing steps
run_detection = True  # Run blocking detection
compute_metrics = True  # Compute regional/seasonal metrics

# ==============================================================================
# Model Configuration
# ==============================================================================

# Path to pre-trained model (None = use default location)
model_path = None

# Probability threshold for blocking detection
threshold = 0.34  # Default optimized value

# ==============================================================================
# Output Configuration
# ==============================================================================

# Base output directory
result_dir = "output"

# Output filename template
# Available placeholders: %(model), %(exp), %(realization), %(start), %(end)
output_filename_template = (
    "blocking_pval_day_%(model)_%(exp)_%(realization)_%(start)_%(end).nc"
)

# ==============================================================================
# Notes
# ==============================================================================
"""
Time Periods (automatically set based on experiment):
- historical: 1979-01 to 2010-12 (debug: 2000-01 to 2010-12)
- scenarios: 2014-01 to 2100-12

Output Structure:
- {result_dir}/diagnostics/{exp}/  - NetCDF files with pval and pval_binary
- {result_dir}/metrics/{exp}/      - CSV and NPY files with metrics
- {result_dir}/log/{exp}/          - Log files for each model/member

Metrics Files:
- CSV: Year, Season, Region, Number, Size
- NPY: Spatial mean blocking frequency (4 seasons × lat × lon)

For Historical (first_member_only=True), expect:
- ~34 CMIP6 models available (as of 2023)
- Processing time: ~30 sec/year/model on CPU, ~5 sec/year/model on GPU
- Total time: ~3-4 hours for full historical period (32 years × 34 models)

Examples:
  # Quick test (3 models, 2000-2010)
  debug = True
  parallel = False

  # Full historical run (all models, 1979-2010)
  debug = False
  parallel = True
  num_processes = 10

  # Scenario run (SSP5-8.5, 2014-2100)
  exps = ["ssp585"]
  parallel = True
  num_processes = 10
"""
