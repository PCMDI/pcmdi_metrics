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
import logging
import os
import sys

from pcmdi_metrics.mean_climate.lib_unified import (
    calculate_metrics_for_models,
    generate_annual_cycles_for_references,
    get_model_catalogue,
    get_ref_catalogue,
    multi_level_dict,
    setup_interim_paths,
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
        help="Base path for reference annual cycle outputs (use %%(var) for variable)",
    )

    parser.add_argument(
        "--base_model_ac_path",
        type=str,
        default=None,
        help="Base path for model annual cycle outputs (use %%(var) for variable)",
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


def main():
    """Main execution function."""
    parser = create_unified_parser()
    args = parser.parse_args()

    # Setup
    setup_logging(args.working_dir, args.debug)

    print("=" * 80)
    print("MEAN CLIMATE UNIFIED DRIVER")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print(f"Working directory: {args.working_dir}")
    print(f"Output path: {args.output_path}")
    print(f"Reference catalogue: {args.ref_catalogue}")
    print(f"Model catalogue: {args.model_catalogue}")
    print("=" * 80 + "\n")

    # Create output directories
    os.makedirs(args.working_dir, exist_ok=True)
    os.makedirs(args.output_path, exist_ok=True)

    # Set version
    version = (
        args.version
        if args.version
        else datetime.datetime.now().strftime("v%Y%m%d")
    )
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
    models = args.models if args.models else sorted(list(models_dict.keys()))

    if args.num_models is not None:
        models = models[: args.num_models]
        print(f"Limiting to {args.num_models} models for testing")

    print(f"Models to process ({len(models)}): {models}\n")

    # Setup grid
    print("Setting up target grid...")
    common_grid = create_target_grid(target_grid_resolution=args.target_grid)
    sft = create_land_sea_mask(common_grid)
    common_grid = common_grid.merge(sft.rename("sftlf"))
    print(f"Target grid: {args.target_grid}\n")

    # Setup interim output paths
    interim_output_path_dict, syear, eyear = setup_interim_paths(
        args.working_dir,
        args.start,
        args.end,
        args.base_ref_ac_path,
        args.base_model_ac_path,
    )

    # Initialize dictionaries
    anncyc_ref_dict = multi_level_dict()
    encountered_variables = set()

    # Execute based on mode
    if args.mode in ["unified", "annual_cycle"]:
        # Generate annual cycles for references
        print("\n" + "=" * 80)
        print("STEP 1: GENERATING ANNUAL CYCLES FOR REFERENCES")
        print("=" * 80 + "\n")

        anncyc_ref_dict, encountered_variables = generate_annual_cycles_for_references(
            variables=variables,
            refs_dict=refs_dict,
            common_grid=common_grid,
            start=args.start,
            end=args.end,
            version=version,
            interim_output_path_dict=interim_output_path_dict,
            rad_diagnostic_variables=args.rad_diagnostic_variables,
            is_ref_input_annual_cycle=args.is_ref_input_annual_cycle,
            default_ref_only=args.default_ref_only,
            target_ref=args.target_ref,
        )

        print("\n" + "=" * 80)
        print("ANNUAL CYCLE GENERATION COMPLETED")
        print("=" * 80)
        print(f"Annual cycles saved to: {args.working_dir}/clim_*_{syear}-{eyear}/")

        if args.mode == "annual_cycle":
            # Stop here if only generating annual cycles
            print("\nTo calculate metrics, run with --mode metrics")
            return

    # Calculate metrics (for unified and metrics modes)
    if args.mode in ["unified", "metrics"]:
        print("\n" + "=" * 80)
        print("STEP 2: CALCULATING METRICS")
        print("=" * 80 + "\n")

        # Initialize model dict
        anncyc_model_run_dict = multi_level_dict()

        metrics_dict = calculate_metrics_for_models(
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
            is_model_input_annual_cycle=(
                args.is_model_input_annual_cycle or args.mode == "metrics"
            ),
            default_ref_only=args.default_ref_only,
            target_ref=args.target_ref,
        )

    # Final summary
    print("\n" + "=" * 80)
    print("EXECUTION COMPLETED")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print(f"Variables processed: {len(variables)}")
    print(f"Models processed: {len(models)}")
    print(f"Output location: {args.output_path}")

    if args.mode in ["unified", "metrics"]:
        # Count JSON files and check if they're empty
        import glob
        json_files = glob.glob(os.path.join(args.output_path, "*.json"))
        if json_files:
            print(f"\nMetrics output:")
            for jf in json_files:
                size = os.path.getsize(jf)
                status = "✓ Contains data" if size > 10 else "⚠ Empty (no successful metrics)"
                print(f"  {os.path.basename(jf)}: {size} bytes - {status}")
        else:
            print(f"\n⚠ No metrics JSON files created")

    if args.mode in ["unified", "annual_cycle"]:
        print(f"\nAnnual cycles: {args.working_dir}/clim_*_{syear}-{eyear}/")

    # Check error log
    error_log = os.path.join(args.working_dir, "error_log.txt")
    if os.path.exists(error_log) and os.path.getsize(error_log) > 0:
        print(f"\n⚠ Errors occurred during processing. Check: {error_log}")
        print("  Common issues:")
        print("    - Reference data calendar conflicts")
        print("    - Missing or incompatible data files")
        print("    - Grid interpolation failures")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
