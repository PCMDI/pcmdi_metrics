"""
Helper functions for the unified mean climate driver.

These functions support the driver's workflow orchestration,
reference selection, and setup tasks.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

from pcmdi_metrics.io import xcdat_open

from .lib_unified import (
    get_ref_data_path,
    get_unique_bases,
    multi_level_dict,
    process_models,
    process_references,
)


def select_references(
    refs_dict: Dict,
    var: str,
    default_ref_only: bool = False,
    target_ref: Optional[str] = None,
) -> List[str]:
    """
    Select which references to use for a given variable.

    Args:
        refs_dict: Reference catalogue dictionary
        var: Variable name
        default_ref_only: If True, use only the default reference
        target_ref: If provided, use only this specific reference

    Returns:
        List of reference names to process
    """
    if var not in refs_dict:
        return []

    refs = list(refs_dict[var].keys())

    # Handle default reference selection
    if "default" in refs:
        if default_ref_only:
            # Use only the reference marked as default
            return [refs_dict[var]["default"]]
        else:
            # Remove "default" label from list but keep all refs
            refs.remove("default")

    # Handle target reference selection (overrides default_ref_only)
    if target_ref is not None:
        if target_ref in refs:
            return [target_ref]
        else:
            return []

    return refs


def setup_interim_paths(
    working_dir: str,
    start: str,
    end: str,
    base_ref_ac_path: Optional[str] = None,
    base_model_ac_path: Optional[str] = None,
) -> Tuple[Dict, str, str]:
    """
    Setup interim output paths for annual cycles.

    Args:
        working_dir: Working directory path
        start: Start date (YYYY-MM)
        end: End date (YYYY-MM)
        base_ref_ac_path: Optional base path for reference ACs
        base_model_ac_path: Optional base path for model ACs

    Returns:
        Tuple of (interim_output_path_dict, syear, eyear)
    """
    syear = start.split("-")[0]
    eyear = end.split("-")[0]

    if base_ref_ac_path is None:
        base_ref_ac_path = os.path.join(
            working_dir, f"clim_refs_{syear}-{eyear}", "%(var)"
        )

    if base_model_ac_path is None:
        base_model_ac_path = os.path.join(
            working_dir, f"clim_models_{syear}-{eyear}", "%(var)"
        )

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

    return interim_output_path_dict, syear, eyear


def remove_nested_key(data, target_key):
    """
    Remove specific keys from nested dictionary structure.

    This is useful for excluding problematic datasets from processing.

    Args:
        data: Dictionary or list to process
        target_key: Key name to remove
    """
    if isinstance(data, dict):
        for key in list(data.keys()):
            if key == target_key:
                del data[key]
            else:
                remove_nested_key(data[key], target_key)
    elif isinstance(data, list):
        for item in data:
            remove_nested_key(item, target_key)


def generate_annual_cycles_for_references(
    variables: List[str],
    refs_dict: Dict,
    common_grid,
    start: str,
    end: str,
    version: str,
    interim_output_path_dict: Dict,
    rad_diagnostic_variables: List[str],
    is_ref_input_annual_cycle: bool,
    default_ref_only: bool,
    target_ref: Optional[str],
) -> Tuple[Dict, set]:
    """
    Generate annual cycles for reference datasets.

    Args:
        variables: List of variables to process
        refs_dict: Reference catalogue dictionary
        common_grid: Target grid for interpolation
        start: Start date
        end: End date
        version: Version identifier
        interim_output_path_dict: Paths for interim outputs
        rad_diagnostic_variables: List of radiation diagnostic variables
        is_ref_input_annual_cycle: If True, references are already in AC format
        default_ref_only: Use only default reference
        target_ref: Use only this specific reference

    Returns:
        Tuple of (anncyc_ref_dict, encountered_variables)
    """
    variables_level_dict = get_unique_bases(variables)
    variables_unique = list(variables_level_dict.keys())

    print(f"\nProcessing {len(variables_unique)} unique variables: {variables_unique}")

    encountered_variables = set()
    anncyc_ref_dict = multi_level_dict()

    for var in variables_unique:
        try:
            print(f"\n--- Processing reference data for variable: {var} ---")
            encountered_variables.add(var)
            levels = variables_level_dict[var]
            print(f"Levels: {levels}")

            refs = select_references(refs_dict, var, default_ref_only, target_ref)

            if not refs:
                print(f"No references selected for {var}")
                continue

            print(f"Selected references: {refs}")

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

            # Report processing results
            if var in anncyc_ref_dict and anncyc_ref_dict[var]:
                successful_refs = list(anncyc_ref_dict[var].keys())
                print(f"  Successfully processed: {len(successful_refs)}/{len(refs)} references")
                if len(successful_refs) < len(refs):
                    failed_refs = set(refs) - set(successful_refs)
                    print(f"  Failed references: {', '.join(failed_refs)}")
            else:
                print(f"  WARNING: All {len(refs)} references failed for {var}")

        except Exception as e:
            print(f"Error processing variable {var}: {e}")
            logging.error(f"Error processing variable {var}: {str(e)}")

    return anncyc_ref_dict, encountered_variables


def calculate_metrics_for_models(
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

    Args:
        variables: List of variables to process
        refs_dict: Reference catalogue dictionary
        models_dict: Model catalogue dictionary
        models: List of models to process
        common_grid: Target grid
        start: Start date
        end: End date
        version: Version identifier
        interim_output_path_dict: Paths for interim outputs
        rad_diagnostic_variables: List of radiation diagnostic variables
        anncyc_ref_dict: Dictionary of reference annual cycles
        anncyc_model_run_dict: Dictionary of model annual cycles
        encountered_variables: Set of variables already encountered
        regions: List of regions to process
        output_path: Path for output JSON files
        first_member_only: Use only first ensemble member
        is_model_input_annual_cycle: If True, models are already in AC format
        default_ref_only: Use only default reference
        target_ref: Use only this specific reference

    Returns:
        Dict: metrics_dict containing computed metrics
    """
    variables_level_dict = get_unique_bases(variables)
    variables_unique = list(variables_level_dict.keys())

    metrics_dict = multi_level_dict()

    for var in variables_unique:
        try:
            print(f"\n--- Calculating metrics for variable: {var} ---")
            levels = variables_level_dict[var]

            refs = select_references(refs_dict, var, default_ref_only, target_ref)

            if not refs:
                print(f"No references selected for {var}")
                continue

            # Check if we have any successfully processed references
            if var not in anncyc_ref_dict or not anncyc_ref_dict[var]:
                print(f"WARNING: No successfully processed references for {var}")
                print(f"  All {len(refs)} reference(s) failed during processing")
                print(f"  Cannot calculate metrics without valid reference data")
                print(f"  Skipping model processing for {var}")
                continue

            successful_refs = list(anncyc_ref_dict[var].keys())
            print(f"Processing {len(models)} models against {len(successful_refs)} successfully processed references")
            if len(successful_refs) < len(refs):
                failed_count = len(refs) - len(successful_refs)
                print(f"  Note: {failed_count} reference(s) failed during processing")

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
