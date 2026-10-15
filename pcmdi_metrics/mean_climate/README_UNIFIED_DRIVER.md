# Mean Climate Unified Driver

## Overview

The unified driver (`mean_climate_unified_driver.py`) combines two previously separate workflows:

1. **Annual Cycle Generation**: Compute climatological annual cycles from time series data
2. **Metrics Calculation**: Calculate statistics and metrics comparing models to observations

This unified approach simplifies the workflow while maintaining backward compatibility for users who need to run these steps separately.

## Key Features

- **Three execution modes**:
  - `unified`: Run both annual cycle generation and metrics calculation (default)
  - `annual_cycle`: Generate only annual cycles (backward compatibility)
  - `metrics`: Calculate only metrics from pre-computed annual cycles (backward compatibility)

- **Flexible configuration**: All options available via command-line arguments
- **Backward compatible**: Can reproduce results from separate workflows
- **Comprehensive logging**: Track errors and progress

## Installation

Ensure you have the pcmdi_metrics package installed:

```bash
cd /path/to/pcmdi_metrics
pip install -e .
```

## Usage

### Basic Usage (Unified Mode)

Run both steps together:

```bash
python mean_climate_unified_driver.py \
    --mode unified \
    --working_dir /path/to/working_dir \
    --output_path /path/to/output \
    --ref_catalogue /path/to/ref_catalogue.json \
    --model_catalogue /path/to/model_catalogue.json \
    --variables pr tas psl \
    --start 1980-01 \
    --end 2014-12
```

### Backward Compatibility: Separate Steps

#### Step 1: Generate Annual Cycles Only

```bash
python mean_climate_unified_driver.py \
    --mode annual_cycle \
    --working_dir /path/to/working_dir \
    --output_path /path/to/output \
    --ref_catalogue /path/to/ref_catalogue.json \
    --model_catalogue /path/to/model_catalogue.json \
    --variables pr tas psl \
    --start 1980-01 \
    --end 2014-12
```

This will save annual cycles to the working directory.

#### Step 2: Calculate Metrics from Pre-computed Annual Cycles

```bash
python mean_climate_unified_driver.py \
    --mode metrics \
    --working_dir /path/to/working_dir \
    --output_path /path/to/output \
    --ref_catalogue /path/to/ref_catalogue.json \
    --model_catalogue /path/to/model_catalogue.json \
    --variables pr tas psl \
    --start 1980-01 \
    --end 2014-12
```

This assumes annual cycles have already been computed and saved.

## Command-Line Arguments

### Required Arguments

- `--working_dir`: Working directory for intermediate outputs and logs
- `--output_path`: Output path for metrics JSON files
- `--ref_catalogue`: Path to reference data catalogue JSON file
- `--model_catalogue`: Path to model data catalogue JSON file

### Optional Arguments

#### Mode Selection
- `--mode`: Execution mode (choices: `unified`, `annual_cycle`, `metrics`; default: `unified`)

#### Data Selection
- `--variables`: Space-separated list of variables (e.g., `pr tas psl`)
- `--models`: Space-separated list of models (default: all from catalogue)
- `--first_member_only`: Use only first ensemble member of each model
- `--num_models`: Limit number of models for testing

#### Time Period
- `--start`: Start date in YYYY-MM format (default: `1980-01`)
- `--end`: End date in YYYY-MM format (default: `2014-12`)

#### Grid and Regions
- `--target_grid`: Target grid resolution (default: `2.5x2.5`)
- `--regions`: Space-separated list of regions (default: `global`)

#### Reference Settings
- `--ref_data_head`: Optional head path for reference data
- `--default_ref_only`: Use only the default reference from catalogue
- `--all_ref_variables`: Use all variables from reference catalogue
- `--target_ref`: Use a specific reference dataset

#### Input Data Format
- `--is_ref_input_annual_cycle`: Reference data is already in annual cycle format
- `--is_model_input_annual_cycle`: Model data is already in annual cycle format

#### Paths for Interim Outputs
- `--base_ref_ac_path`: Base path for reference annual cycle outputs
- `--base_model_ac_path`: Base path for model annual cycle outputs

#### Other Options
- `--version`: Version identifier (default: auto-generated from date)
- `--rad_diagnostic_variables`: Radiation diagnostic variables
- `--debug`: Enable debug logging

## Examples

### Example 1: Process a Single Variable for Testing

```bash
python mean_climate_unified_driver.py \
    --mode unified \
    --working_dir ./test_output \
    --output_path ./test_output/json \
    --ref_catalogue /global/cfs/projectdirs/m4581/obs4MIPs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_latest.json \
    --model_catalogue /path/to/models_catalogue.json \
    --variables pr \
    --num_models 2 \
    --first_member_only \
    --start 1980-01 \
    --end 1984-12
```

### Example 2: Process Multiple Variables with Custom Regions

```bash
python mean_climate_unified_driver.py \
    --mode unified \
    --working_dir /scratch/mean_climate_work \
    --output_path /scratch/mean_climate_output \
    --ref_catalogue /path/to/ref_catalogue.json \
    --model_catalogue /path/to/model_catalogue.json \
    --variables pr tas psl rlut rsut \
    --regions global NHEX SHEX TROPICS NAM SAM EUR \
    --target_grid 2.5x2.5 \
    --first_member_only
```

### Example 3: Use Pre-computed Reference Annual Cycles

If you already have reference annual cycles computed:

```bash
python mean_climate_unified_driver.py \
    --mode unified \
    --working_dir /scratch/mean_climate_work \
    --output_path /scratch/mean_climate_output \
    --ref_catalogue /path/to/precomputed_ac_catalogue.json \
    --model_catalogue /path/to/model_catalogue.json \
    --variables pr tas \
    --is_ref_input_annual_cycle
```

### Example 4: Process Specific Model Against Specific Reference

```bash
python mean_climate_unified_driver.py \
    --mode unified \
    --working_dir ./output \
    --output_path ./output/json \
    --ref_catalogue /path/to/ref_catalogue.json \
    --model_catalogue /path/to/model_catalogue.json \
    --variables pr \
    --models ACCESS-CM2 \
    --target_ref GPCP-2-3 \
    --first_member_only
```

## Output Structure

### Unified Mode Output

```
working_dir/
├── error_log.txt                          # Error log
├── clim_refs_1980-2014/                   # Reference annual cycles
│   ├── pr/
│   │   ├── gn/                            # Native grid
│   │   └── gr/                            # Regridded
│   └── tas/
│       ├── gn/
│       └── gr/
└── clim_models_1980-2014/                 # Model annual cycles
    ├── pr/
    │   ├── gn/
    │   └── gr/
    └── tas/
        ├── gn/
        └── gr/

output_path/
├── pr_*.json                              # Metrics for precipitation
└── tas_*.json                             # Metrics for temperature
```

### Annual Cycle Mode Output

Only generates the `clim_refs_*` and `clim_models_*` directories.

### Metrics Mode Output

Only generates the JSON files in `output_path/`.

## Migration from Original Workflow

If you have been using the original `mean_climate_driver.py` or separate scripts:

### From Original Driver

The original driver is still available and maintained. The unified driver provides:
- More explicit control over the workflow steps
- Better suited for batch processing and automation
- Cleaner separation between annual cycle generation and metrics calculation

### From Separate Scripts

If you have been running annual cycle generation and metrics calculation as separate scripts:

1. **Option 1**: Use unified mode to run both steps together
   ```bash
   python mean_climate_unified_driver.py --mode unified [options]
   ```

2. **Option 2**: Continue running separately with backward compatibility modes
   ```bash
   # Step 1
   python mean_climate_unified_driver.py --mode annual_cycle [options]
   
   # Step 2
   python mean_climate_unified_driver.py --mode metrics [options]
   ```

## Troubleshooting

### Common Issues

1. **Memory errors with many models/variables**
   - Use `--num_models` to limit the number of models
   - Process variables one at a time
   - Use `--first_member_only` to reduce ensemble members

2. **Missing references**
   - Check your reference catalogue file
   - Use `--default_ref_only` or `--target_ref` to limit references
   - Verify `--ref_data_head` path if reference files aren't found

3. **Annual cycles not found in metrics mode**
   - Ensure annual cycles were generated with matching paths
   - Check `--base_ref_ac_path` and `--base_model_ac_path` settings
   - Verify the time period (`--start`, `--end`) matches

### Debug Mode

Enable debug logging for detailed information:

```bash
python mean_climate_unified_driver.py --debug [other options]
```

Check `error_log.txt` in the working directory for detailed error messages.

## Comparison with Original mean_climate_driver.py

| Feature | Original Driver | Unified Driver |
|---------|----------------|----------------|
| Annual cycle + metrics | ✓ (implicit) | ✓ (explicit mode) |
| Separate steps | ✗ | ✓ (via modes) |
| CLI configuration | Limited | Comprehensive |
| Backward compatibility | N/A | ✓ |
| Batch processing | ✓ | ✓ |
| Parameter file support | ✓ | Via CLI args |

Both drivers are maintained and can be used based on your needs.

## Contributing

To contribute or report issues:

1. Repository: https://github.com/PCMDI/pcmdi_metrics
2. Issues: https://github.com/PCMDI/pcmdi_metrics/issues

## Version History

- v1.0 (2026-10-15): Initial unified driver implementation
  - Combines annual cycle generation and metrics calculation
  - Three execution modes (unified, annual_cycle, metrics)
  - Comprehensive CLI argument parsing
  - Backward compatibility maintained
