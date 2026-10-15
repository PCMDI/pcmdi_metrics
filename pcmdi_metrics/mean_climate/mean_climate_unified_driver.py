#!/usr/bin/env python
"""
Unified Mean Climate Driver

This driver unifies the two separate workflows:
1. Annual cycle generation
2. Metrics calculation

It can run both steps together (unified mode) or separately (backward compatibility mode).

Usage:
    # Unified mode (both steps):
    python mean_climate_unified_driver.py --mode unified [options]

    # Separate modes (backward compatibility):
    python mean_climate_unified_driver.py --mode annual_cycle [options]
    python mean_climate_unified_driver.py --mode metrics [options]
"""

import argparse
import datetime
import json
import logging
import os
import sys
from typing import Dict, List, Optional

from pcmdi_metrics.io import xcdat_open
from pcmdi_metrics.mean_climate.lib_unified import (
    calculate_and_save_metrics,
    get_model_catalogue,
    get_ref_catalogue,
    get_ref_data_path,
    get_unique_bases,
    multi_level_dict,
    print_dict,
    process_models,
    process_references,
)
from pcmdi_metrics.utils import create_land_sea_mask, create_target_grid


def create_unified_parser():
    """Create argument parser for unified driver."""
    parser = argparse.ArgumentParser(
        description="Unified Mean Climate Metrics Driver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["unified", "annual_cycle", "metrics"],
        default="unified",
        help="Execution mode: unified (both steps), annual_cycle (only AC generation), "
        "metrics (only metrics calculation)",
    )

    # Input/Output paths
    parser.add_argument(
        "--working_dir",
        type=str,
        required=True,
        help="Working directory for intermediate outputs and logs",
    )

    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Output path for metrics JSON files",
    )

    # Data catalogues
    parser.add_argument(
        "--ref_catalogue",
        type=str,
        required=True,
        help="Path to reference data catalogue JSON file",
    )

    parser.add_argument(
        "--model_catalogue",
        type=str,
        required=True,
        help="Path to model data catalogue JSON file",
    )

    parser.add_argument(
        "--ref_data_head",
        type=str,
        default=None,
        help="Optional head path for reference data (if not in catalogue)",
    )

    # Variables and models
    parser.add_argument(
        "--variables",
        type=str,
        nargs="+",
        default=None,
        help="List of variables to process (e.g., pr tas). If not provided, uses all "
        "variables from reference catalogue",
    )

    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=None,
        help="List of models to process. If not provided, uses all models from catalogue",
    )

    parser.add_argument(
        "--first_member_only",
        action="store_true",
        help="Use only the first ensemble member of each model",
    )

    # Time period
    parser.add_argument(
        "--start",
        type=str,
        default="1980-01",
        help="Start date in YYYY-MM format (default: 1980-01)",
    )

    parser.add_argument(
        "--end",
        type=str,
        default="2014-12",
        help="End date in YYYY-MM format (default: 2014-12)",
    )

    # Grid settings
    parser.add_argument(
        "--target_grid",
        type=str,
        default="2.5x2.5",
        help="Target grid resolution (default: 2.5x2.5)",
    )

    # Regions
    parser.add_argument(
        "--regions",
        type=str,
        nargs="+",
        default=["global"],
        help="Regions for metrics calculation (default: global)",
    )

    # Reference settings
    parser.add_argument(
        "--default_ref_only",
        action="store_true",
        help="Use only the default reference from catalogue",
    )

    parser.add_argument(
        "--all_ref_variables",
        action="store_true",
        help="Use all variables from reference catalogue",
    )

    parser.add_argument(
        "--target_ref",
        type=str,
        default=None,
        help="Specific reference to use (overrides default_ref_only)",
    )

    # Input data format
    parser.add_argument(
        "--is_ref_input_annual_cycle",
        action="store_true",
        help="Reference input is already in annual cycle format",
    )

    parser.add_argument(
        "--is_model_input_annual_cycle",
        action="store_true",
        help="Model input is already in annual cycle format",
    )

    # Interim output paths
    parser.add_argument(
        "--base_ref_ac_path",
        type=str,
        default=None,
        help="Base path for reference annual cycle outputs (use %(var) for variable)",
    )

    parser.add_argument(
        "--base_model_ac_path",
        type=str,
        default=None,
        help="Base path for model annual cycle outputs (use %(var) for variable)",
    )

    # Version and metadata
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Version identifier (default: auto-generated from current date)",
    )

    # Diagnostic variables
    parser.add_argument(
        "--rad_diagnostic_variables",
        type=str,
        nargs="+",
        default=["rt", "rst", "rstcre", "rltcre"],
        help="Radiation diagnostic variables",
    )

    # Testing and debugging
    parser.add_argument(
        "--num_models",
        type=int,
        default=None,
        help="Limit number of models for testing (default: all)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    return parser


def setup_logging(working_dir: str, debug: bool = False) -> None:
    """Setup logging configuration."""
    log_file = os.path.join(working_dir, "error_log.txt")
    os.makedirs(working_dir, exist_ok=True)

    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG if debug else logging.ERROR,
        filemode="w",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def remove_nested_key(data, target_key):
    """Remove specific keys from nested dictionary structure."""
    if isinstance(data, dict):
        for key in list(data.keys()):
            if key == target_key:
                del data[key]
            else:
                remove_nested_key(data[key], target_key)
    elif isinstance(data, list):
        for item in data:
            remove_nested_key(item, target_key)


def generate_annual_cycles(
    variables: List[str],
    refs_dict: Dict,
    models_dict: Dict,
    models: List[str],
    common_grid,
    start: str,
    end: str,
    version: str,
    interim_output_path_dict: Dict,
    rad_diagnostic_variables: List[str],
    is_ref_input_annual_cycle: bool,
    is_model_input_annual_cycle: bool,
    default_ref_only: bool,
    target_ref: Optional[str],
    first_member_only: bool,
    regions: List[str],
) -> tuple:
    """
    Generate annual cycles for references and models.

    Returns:
        tuple: (anncyc_ref_dict, anncyc_model_run_dict, encountered_variables)
    """
    print("\n" + "="*80)
    print("STEP 1: GENERATING ANNUAL CYCLES")
    print("="*80 + "\n")

    variables_level_dict = get_unique_bases(variables)
    variables_unique = list(variables_level_dict.keys())

    print(f"Processing {len(variables_unique)} unique variables: {variables_unique}")

    encountered_variables = set()
    anncyc_ref_dict = multi_level_dict()
    anncyc_model_run_dict = multi_level_dict()

    for var in variables_unique:
        try:
            print(f"\n--- Processing variable: {var} ---")
            encountered_variables.add(var)
            levels = variables_level_dict[var]
            print(f"Levels: {levels}")

            if var in refs_dict:
                refs = list(refs_dict[var].keys())
                print(f"Available references: {refs}")

                # Handle default reference selection
                if "default" in refs:
                    print(f"Default reference: {refs_dict[var]['default']}")
                    if default_ref_only:
                        refs = [refs_dict[var]["default"]]
                    else:
                        refs.remove("default")

                # Handle target reference selection
                if target_ref is not None:
                    if target_ref in refs:
                        refs = [target_ref]
                    else:
                        refs = []

                if is_ref_input_annual_cycle:
                    print(f"Loading pre-computed annual cycles for {var}")
                    for ref in refs:
                        ref_data_path = get_ref_data_path(refs_dict, var, ref)
                        print(f"  {ref}: {ref_data_path}")
                        anncyc_ref_dict[var][ref] = xcdat_open(ref_data_path)
                else:
                    print(f"Generating annual cycles for references: {refs}")
                    anncyc_ref_dict = process_references(
                        var,
                        refs,
                        rad_diagnostic_variables,
                        levels,
                        common_grid,
                        start,
                        end,
                        version,
                        interim_output_path_dict,
                        refs_dict,
                        anncyc_ref_dict,
                        encountered_variables,
                    )

                print(f"Completed reference processing for {var}")

        except Exception as e:
            print(f"Error processing variable {var}: {e}")
            logging.error(f"Error processing variable {var}: {str(e)}")

    return anncyc_ref_dict, anncyc_model_run_dict, encountered_variables


def calculate_metrics(
    variables: List[str],
    refs_dict: Dict,
    models_dict: Dict,
    models: List[str],
    common_grid,
    start: str,
    end: str,
    version: str,
    interim_output_path_dict: Dict,
    rad_diagnostic_variables: List[str],
    anncyc_ref_dict: Dict,
    anncyc_model_run_dict: Dict,
    encountered_variables: set,
    regions: List[str],
    output_path: str,
    first_member_only: bool,
    is_model_input_annual_cycle: bool,
    default_ref_only: bool,
    target_ref: Optional[str],
) -> Dict:
    """
    Calculate metrics by comparing models to references.

    Returns:
        Dict: metrics_dict containing computed metrics
    """
    print("\n" + "="*80)
    print("STEP 2: CALCULATING METRICS")
    print("="*80 + "\n")

    variables_level_dict = get_unique_bases(variables)
    variables_unique = list(variables_level_dict.keys())

    metrics_dict = multi_level_dict()

    for var in variables_unique:
        try:
            print(f"\n--- Calculating metrics for variable: {var} ---")
            levels = variables_level_dict[var]

            if var in refs_dict:
                refs = list(refs_dict[var].keys())

                # Apply same reference selection logic as in annual cycle generation
                if "default" in refs:
                    if default_ref_only:
                        refs = [refs_dict[var]["default"]]
                    else:
                        refs.remove("default")

                if target_ref is not None:
                    if target_ref in refs:
                        refs = [target_ref]
                    else:
                        refs = []

                print(f"Processing {len(models)} models against {len(refs)} references")

                process_models(
                    var,
                    models,
                    models_dict,
                    rad_diagnostic_variables,
                    levels,
                    common_grid,
                    refs,
                    start,
                    end,
                    version,
                    interim_output_path_dict,
                    anncyc_model_run_dict,
                    encountered_variables,
                    regions,
                    anncyc_ref_dict,
                    refs_dict,
                    output_path,
                    metrics_dict,
                    first_member_only=first_member_only,
                    is_model_input_annual_cycle=is_model_input_annual_cycle,
                )

                print(f"Completed metrics calculation for {var}")

        except Exception as e:
            print(f"Error calculating metrics for {var}: {e}")
            logging.error(f"Error calculating metrics for {var}: {str(e)}")

    return metrics_dict


def main():
    """Main execution function."""
    parser = create_unified_parser()
    args = parser.parse_args()

    # Setup
    setup_logging(args.working_dir, args.debug)

    print("="*80)
    print("MEAN CLIMATE UNIFIED DRIVER")
    print("="*80)
    print(f"Mode: {args.mode}")
    print(f"Working directory: {args.working_dir}")
    print(f"Output path: {args.output_path}")
    print(f"Reference catalogue: {args.ref_catalogue}")
    print(f"Model catalogue: {args.model_catalogue}")
    print("="*80 + "\n")

    # Create output directories
    os.makedirs(args.working_dir, exist_ok=True)
    os.makedirs(args.output_path, exist_ok=True)

    # Set version
    if args.version is None:
        version = datetime.datetime.now().strftime("v%Y%m%d")
    else:
        version = args.version
    print(f"Version: {version}\n")

    # Load catalogues
    print("Loading catalogues...")
    refs_dict = get_ref_catalogue(args.ref_catalogue, args.ref_data_head)
    models_dict = get_model_catalogue(args.model_catalogue)
    print(f"Reference catalogue loaded: {len(refs_dict)} variables")
    print(f"Model catalogue loaded: {len(models_dict)} models\n")

    # Determine variables to process
    if args.variables is None:
        if args.all_ref_variables:
            variables = sorted(list(refs_dict.keys()))
        else:
            print("ERROR: --variables must be specified unless --all_ref_variables is used")
            sys.exit(1)
    else:
        variables = args.variables

    print(f"Variables to process: {variables}")

    # Determine models to process
    if args.models is None:
        models = sorted(list(models_dict.keys()))
    else:
        models = args.models

    if args.num_models is not None:
        models = models[:args.num_models]
        print(f"Limiting to {args.num_models} models for testing")

    print(f"Models to process ({len(models)}): {models}\n")

    # Setup grid
    print("Setting up target grid...")
    common_grid = create_target_grid(target_grid_resolution=args.target_grid)
    sft = create_land_sea_mask(common_grid)
    common_grid = common_grid.merge(sft.rename("sftlf"))
    print(f"Target grid: {args.target_grid}\n")

    # Setup interim output paths
    syear = args.start.split("-")[0]
    eyear = args.end.split("-")[0]

    if args.base_ref_ac_path is None:
        base_ref_ac_path = os.path.join(
            args.working_dir, f"clim_refs_{syear}-{eyear}", "%(var)"
        )
    else:
        base_ref_ac_path = args.base_ref_ac_path

    if args.base_model_ac_path is None:
        base_model_ac_path = os.path.join(
            args.working_dir, f"clim_models_{syear}-{eyear}", "%(var)"
        )
    else:
        base_model_ac_path = args.base_model_ac_path

    interim_output_path_dict = {
        "ref": {
            "path_ac": f"{base_ref_ac_path}/gn",
            "path_ac_interp": f"{base_ref_ac_path}/gr",
        },
        "model": {
            "path_ac": f"{base_model_ac_path}/gn",
            "path_ac_interp": f"{base_model_ac_path}/gr",
        },
    }

    # Optional: Remove problematic datasets (can be made configurable)
    # remove_nested_key(refs_dict, "MSWEP-V280-Past")
    # remove_nested_key(refs_dict, "MSWEP-V280-Past-nogauge")
    # remove_nested_key(refs_dict, "PRISM-M3")

    # Execute based on mode
    if args.mode == "unified":
        # Run both steps
        print("\n" + "="*80)
        print("RUNNING UNIFIED MODE (Annual Cycles + Metrics)")
        print("="*80 + "\n")

        anncyc_ref_dict, anncyc_model_run_dict, encountered_variables = generate_annual_cycles(
            variables=variables,
            refs_dict=refs_dict,
            models_dict=models_dict,
            models=models,
            common_grid=common_grid,
            start=args.start,
            end=args.end,
            version=version,
            interim_output_path_dict=interim_output_path_dict,
            rad_diagnostic_variables=args.rad_diagnostic_variables,
            is_ref_input_annual_cycle=args.is_ref_input_annual_cycle,
            is_model_input_annual_cycle=args.is_model_input_annual_cycle,
            default_ref_only=args.default_ref_only,
            target_ref=args.target_ref,
            first_member_only=args.first_member_only,
            regions=args.regions,
        )

        metrics_dict = calculate_metrics(
            variables=variables,
            refs_dict=refs_dict,
            models_dict=models_dict,
            models=models,
            common_grid=common_grid,
            start=args.start,
            end=args.end,
            version=version,
            interim_output_path_dict=interim_output_path_dict,
            rad_diagnostic_variables=args.rad_diagnostic_variables,
            anncyc_ref_dict=anncyc_ref_dict,
            anncyc_model_run_dict=anncyc_model_run_dict,
            encountered_variables=encountered_variables,
            regions=args.regions,
            output_path=args.output_path,
            first_member_only=args.first_member_only,
            is_model_input_annual_cycle=args.is_model_input_annual_cycle,
            default_ref_only=args.default_ref_only,
            target_ref=args.target_ref,
        )

    elif args.mode == "annual_cycle":
        # Run only annual cycle generation
        print("\n" + "="*80)
        print("RUNNING ANNUAL CYCLE MODE ONLY")
        print("="*80 + "\n")

        anncyc_ref_dict, anncyc_model_run_dict, encountered_variables = generate_annual_cycles(
            variables=variables,
            refs_dict=refs_dict,
            models_dict=models_dict,
            models=models,
            common_grid=common_grid,
            start=args.start,
            end=args.end,
            version=version,
            interim_output_path_dict=interim_output_path_dict,
            rad_diagnostic_variables=args.rad_diagnostic_variables,
            is_ref_input_annual_cycle=args.is_ref_input_annual_cycle,
            is_model_input_annual_cycle=args.is_model_input_annual_cycle,
            default_ref_only=args.default_ref_only,
            target_ref=args.target_ref,
            first_member_only=args.first_member_only,
            regions=args.regions,
        )

        print("\n" + "="*80)
        print("ANNUAL CYCLE GENERATION COMPLETED")
        print("="*80)
        print(f"Annual cycles saved to: {args.working_dir}")
        print("To run metrics calculation, use --mode metrics")

    elif args.mode == "metrics":
        # Run only metrics calculation (requires pre-computed annual cycles)
        print("\n" + "="*80)
        print("RUNNING METRICS MODE ONLY")
        print("="*80)
        print("NOTE: This assumes annual cycles have been pre-computed")
        print("="*80 + "\n")

        # Initialize empty dictionaries and load from interim outputs
        anncyc_ref_dict = multi_level_dict()
        anncyc_model_run_dict = multi_level_dict()
        encountered_variables = set()

        metrics_dict = calculate_metrics(
            variables=variables,
            refs_dict=refs_dict,
            models_dict=models_dict,
            models=models,
            common_grid=common_grid,
            start=args.start,
            end=args.end,
            version=version,
            interim_output_path_dict=interim_output_path_dict,
            rad_diagnostic_variables=args.rad_diagnostic_variables,
            anncyc_ref_dict=anncyc_ref_dict,
            anncyc_model_run_dict=anncyc_model_run_dict,
            encountered_variables=encountered_variables,
            regions=args.regions,
            output_path=args.output_path,
            first_member_only=args.first_member_only,
            is_model_input_annual_cycle=True,  # Assume ACs are pre-computed
            default_ref_only=args.default_ref_only,
            target_ref=args.target_ref,
        )

    # Final summary
    print("\n" + "="*80)
    print("EXECUTION COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Mode: {args.mode}")
    print(f"Variables processed: {len(variables)}")
    print(f"Models processed: {len(models)}")
    print(f"Output location: {args.output_path}")
    if args.mode in ["unified", "metrics"]:
        print(f"Metrics JSON files: {args.output_path}/*.json")
    if args.mode in ["unified", "annual_cycle"]:
        print(f"Annual cycles: {args.working_dir}/clim_*_{syear}-{eyear}/")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
