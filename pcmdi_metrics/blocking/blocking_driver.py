#!/usr/bin/env python
"""
Driver script for batch processing of atmospheric blocking detection.

Processes multiple CMIP6 models and ensemble members in parallel using xsearch
for data discovery. Adapted from original driver by Elina Valkonen and Jiwoo Lee.

Usage:
    python blocking_driver.py [--param parameter_file.py]

Or use as module:
    from pcmdi_metrics.blocking.blocking_driver import main
    main(param_file='my_params.py')

Created by: Elina Valkonen, Jiwoo Lee (original)
Adapted for PMP by: Claude (November 2026)
"""

import glob
import logging
import multiprocessing
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

# Import new API functions
from pcmdi_metrics.blocking import (
    compute_blocking_metrics,
    detect_blocking,
    metrics_to_csv,
    spatial_means_to_npy,
)


def main(param_file: Optional[str] = None, **kwargs):
    """
    Main driver function for batch blocking detection.

    Parameters
    ----------
    param_file : str, optional
        Path to parameter file. If None, uses default parameters.
    **kwargs : dict
        Override parameters from param file.

    Examples
    --------
    >>> # Run with parameter file
    >>> main(param_file='blocking_params.py')

    >>> # Run with inline parameters
    >>> main(exps=['historical'], models=['CESM2'], parallel=False)
    """
    # Load parameters
    params = load_parameters(param_file, **kwargs)

    # Extract parameters
    exps = params.get("exps", ["historical"])
    var = params.get("var", "zg")
    freq = params.get("freq", "day")
    cmip_table = params.get("cmipTable", "day")
    mip_era = params.get("mip_era", "CMIP6")
    first_member_only = params.get("first_member_only", True)
    parallel = params.get("parallel", False)
    num_processes = params.get("num_processes", 3)
    debug = params.get("debug", False)
    overwrite_output = params.get("overwrite_output", False)
    run_detection = params.get("run_detection", True)
    compute_metrics_flag = params.get("compute_metrics", True)
    result_dir = params.get("result_dir", "output")
    output_filename_template = params.get(
        "output_filename_template",
        "blocking_pval_day_%(model)_%(exp)_%(realization)_%(start)_%(end).nc",
    )
    model_path = params.get("model_path", None)
    threshold = params.get("threshold", 0.34)

    if debug and run_detection:
        result_dir = "output_debug"

    # List to collect parallel tasks
    parallel_tasks = []

    for exp in exps:
        # Set time ranges
        if exp == "historical":
            if debug and run_detection:
                start = "2000-01"
                end = "2010-12"
            else:
                start = "1979-01"
                end = "2010-12"
        else:
            start = "2014-01"
            end = "2100-12"

        # Prepare output directories
        outdir = os.path.join(result_dir, "diagnostics", exp)
        metdir = os.path.join(result_dir, "metrics", exp)
        logdir = os.path.join(result_dir, "log", exp)

        for directory in [outdir, metdir, logdir]:
            os.makedirs(directory, exist_ok=True)

        # Search available models
        print(f"\nSearching for {exp} models...")
        models, models_dict = get_models_dict(
            exp, var, freq, cmip_table, mip_era, first_member_only=first_member_only
        )

        if debug:
            models = models[0:3]

        print(f"Experiment: {exp}")
        print(f"Models found: {len(models)}")
        print(f"Models: {models}")

        # Process each model
        for model in models:
            members = models_dict[model]["members"]

            for member in members:
                ncfiles = models_dict[model][member]["dpaths"]

                # Generate output filenames
                output_filename = (
                    output_filename_template.replace("%(exp)", exp)
                    .replace("%(model)", model)
                    .replace("%(realization)", member)
                    .replace("%(start)", start)
                    .replace("%(end)", end)
                )
                output_file = os.path.join(outdir, output_filename)

                log_filename = output_filename.replace(".nc", ".log")
                log_file = os.path.join(logdir, log_filename)

                # Run detection
                if run_detection:
                    if os.path.isfile(output_file) and not overwrite_output:
                        print(f"Detection: File exists, skipping {model} {member}")
                    else:
                        if parallel:
                            # Queue for parallel processing
                            task = (
                                exp,
                                model,
                                member,
                                ncfiles,
                                output_file,
                                start,
                                end,
                                log_file,
                                model_path,
                                threshold,
                            )
                            parallel_tasks.append(task)
                        else:
                            # Run sequentially
                            print(f"Detection: Processing {model} {member}")
                            try:
                                run_detection_task(
                                    ncfiles,
                                    output_file,
                                    start,
                                    end,
                                    model_path,
                                    threshold,
                                )
                                print(f"Detection: Complete for {model} {member}")
                            except Exception as e:
                                print(f"Detection: FAILED for {model} {member}: {e}")

                # Compute metrics
                if compute_metrics_flag and os.path.isfile(output_file):
                    result_file_csv = os.path.join(
                        metdir, output_filename.replace(".nc", ".csv")
                    )
                    result_file_npy = os.path.join(
                        metdir, output_filename.replace(".nc", ".npy")
                    )

                    if (
                        os.path.isfile(result_file_csv)
                        and os.path.isfile(result_file_npy)
                        and not overwrite_output
                    ):
                        print(f"Metrics: File exists, skipping {model} {member}")
                    else:
                        print(f"Metrics: Computing for {model} {member}")
                        is_historical = exp == "historical"

                        try:
                            run_metrics_task(
                                output_file,
                                result_file_csv,
                                result_file_npy,
                                is_historical,
                            )
                            print(f"Metrics: Complete for {model} {member}")
                        except Exception as e:
                            print(f"Metrics: FAILED for {model} {member}: {e}")

    # Run parallel detection if queued
    if parallel and parallel_tasks:
        num_tasks = len(parallel_tasks)
        print(f"\nRunning {num_tasks} detection tasks in parallel...")

        if num_tasks < num_processes:
            num_processes = num_tasks

        print(f"Using {num_processes} processes")

        pool = multiprocessing.Pool(processes=num_processes)
        pool.starmap(process_detection_parallel, parallel_tasks)
        pool.close()
        pool.join()

        print("Parallel detection complete!")


def run_detection_task(
    ncfiles: List[str],
    output_file: str,
    start: str,
    end: str,
    model_path: Optional[str] = None,
    threshold: float = 0.34,
):
    """
    Run blocking detection for a single model/member.

    Parameters
    ----------
    ncfiles : list of str
        Input NetCDF file paths.
    output_file : str
        Output file path.
    start : str
        Start date (yyyy-mm).
    end : str
        End date (yyyy-mm).
    model_path : str, optional
        Path to pre-trained model.
    threshold : float, optional
        Probability threshold. Default 0.34.
    """
    import xarray as xr

    # Load data
    if len(ncfiles) == 1:
        ds = xr.open_dataset(ncfiles[0])
    else:
        ds = xr.open_mfdataset(ncfiles)

    # Run detection (output_file parameter saves to disk)
    detect_blocking(
        ds,
        var="zg",
        start=start,
        end=end,
        model_path=model_path,
        threshold=threshold,
        output_file=output_file,
        verbose=True,
    )


def run_metrics_task(
    input_file: str, output_csv: str, output_npy: str, historical: bool = False
):
    """
    Compute blocking metrics for detected events.

    Parameters
    ----------
    input_file : str
        Input NetCDF with blocking detections.
    output_csv : str
        Output CSV file path.
    output_npy : str
        Output NPY file path.
    historical : bool, optional
        Whether this is historical data. Default False.
    """
    import xarray as xr

    # Load blocking detections
    ds = xr.open_dataset(input_file)

    # Compute metrics
    metrics_df, spatial_means = compute_blocking_metrics(
        ds, var="pval_binary", historical=historical, verbose=True
    )

    # Save outputs
    metrics_to_csv(metrics_df, output_csv)
    spatial_means_to_npy(spatial_means, output_npy)


def process_detection_parallel(
    exp: str,
    model: str,
    member: str,
    ncfiles: List[str],
    output_file: str,
    start: str,
    end: str,
    log_file: str,
    model_path: Optional[str] = None,
    threshold: float = 0.34,
):
    """
    Parallel processing wrapper with logging.

    Parameters
    ----------
    exp : str
        Experiment name.
    model : str
        Model name.
    member : str
        Ensemble member.
    ncfiles : list of str
        Input file paths.
    output_file : str
        Output file path.
    start : str
        Start date.
    end : str
        End date.
    log_file : str
        Log file path.
    model_path : str, optional
        Path to pre-trained model.
    threshold : float, optional
        Probability threshold.
    """
    logger = configure_logger(log_file)
    logger.info(
        f"Starting detection for {exp}, {model}, {member} at "
        f'{time.strftime("%Y-%m-%d %H:%M:%S")}'
    )

    # Redirect stdout to logger
    sys.stdout = LoggerWriter(logger, logging.INFO)

    start_time = time.time()

    try:
        run_detection_task(ncfiles, output_file, start, end, model_path, threshold)
        elapsed_time = time.time() - start_time
        logger.info(f"Completed in {elapsed_time:.1f} seconds")
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise
    finally:
        # Restore stdout
        sys.stdout = sys.__stdout__


def configure_logger(filename: str) -> logging.Logger:
    """
    Configure logger for a processing task.

    Parameters
    ----------
    filename : str
        Log file path.

    Returns
    -------
    logging.Logger
        Configured logger.
    """
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


class LoggerWriter:
    """Redirect stdout to logger."""

    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip() != "":
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass


def get_models_dict(
    exp: str,
    var: str,
    freq: str,
    cmip_table: str,
    mip_era: str,
    first_member_only: bool = False,
) -> Tuple[List[str], Dict]:
    """
    Search available models using xsearch.

    Parameters
    ----------
    exp : str
        Experiment name.
    var : str
        Variable name.
    freq : str
        Time frequency.
    cmip_table : str
        CMIP table.
    mip_era : str
        CMIP era.
    first_member_only : bool, optional
        Use only first ensemble member. Default False.

    Returns
    -------
    models : list of str
        List of model names.
    models_dict : dict
        Dictionary with model/member/path information.

    Notes
    -----
    Requires xsearch package for CMIP6 data discovery.
    """
    try:
        import xsearch as xs
    except ImportError:
        raise ImportError(
            "xsearch package required for CMIP6 data discovery.\n"
            "Install with: pip install xsearch\n"
            "Or provide data paths directly in parameter file."
        )

    dpaths = xs.findPaths(exp, var, freq, cmipTable=cmip_table, mip_era=mip_era)
    models = xs.natural_sort(xs.getGroupValues(dpaths, "model"))

    models_dict = {}
    for model in models:
        models_dict[model] = {}
        dpaths_model = xs.retainDataByFacetValue(dpaths, "model", model)
        members = xs.natural_sort(xs.getGroupValues(dpaths_model, "member"))

        if first_member_only:
            members = members[0:1]

        models_dict[model]["members"] = members

        for member in members:
            dpaths_model_member_list = xs.getValuesForFacet(
                dpaths_model, "member", member
            )
            models_dict[model][member] = {}

            # Sanity check
            if len(dpaths_model_member_list) > 1:
                print(
                    f"Warning: multiple paths for {model} {member}: "
                    f"{dpaths_model_member_list}"
                )

            dpath = dpaths_model_member_list[0]
            ncfiles = xs.natural_sort(glob.glob(os.path.join(dpath, "*.nc")))
            models_dict[model][member]["dpaths"] = ncfiles

    return models, models_dict


def load_parameters(param_file: Optional[str] = None, **kwargs) -> Dict:
    """
    Load parameters from file or use defaults.

    Parameters
    ----------
    param_file : str, optional
        Path to parameter file.
    **kwargs : dict
        Override parameters.

    Returns
    -------
    dict
        Parameter dictionary.
    """
    params = {
        "exps": ["historical"],
        "var": "zg",
        "freq": "day",
        "cmipTable": "day",
        "mip_era": "CMIP6",
        "first_member_only": True,
        "parallel": False,
        "num_processes": 3,
        "debug": False,
        "overwrite_output": False,
        "run_detection": True,
        "compute_metrics": True,
        "result_dir": "output",
        "output_filename_template": "blocking_pval_day_%(model)_%(exp)_%(realization)_%(start)_%(end).nc",
        "model_path": None,
        "threshold": 0.34,
    }

    # Load from file if provided
    if param_file:
        import importlib.util

        spec = importlib.util.spec_from_file_location("params", param_file)
        param_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(param_module)

        # Update with parameters from file
        for key in params.keys():
            if hasattr(param_module, key):
                params[key] = getattr(param_module, key)

    # Override with kwargs
    params.update(kwargs)

    return params


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch atmospheric blocking detection driver"
    )
    parser.add_argument(
        "--param",
        help="Parameter file path",
        default=None,
    )

    args = parser.parse_args()

    main(param_file=args.param)
