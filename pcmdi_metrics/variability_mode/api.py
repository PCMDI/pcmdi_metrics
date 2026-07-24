"""
Standard API for computing variability modes.

This module provides simple, standardized functions for computing climate variability modes
such as NAO, NAM, SAM, PNA, NPO, PDO, NPGO, and AMO. Each function takes xarray datasets
as input and returns diagnostics and metrics as Python dictionaries.

Usage
-----
>>> import xarray as xr
>>> from pcmdi_metrics.variability_mode import NAO
>>>
>>> # Load model data
>>> model_ds = xr.open_dataset('model_psl.nc')
>>>
>>> # Compute NAO without reference
>>> results = NAO(model_ds)
>>>
>>> # With reference data for metrics
>>> obs_ds = xr.open_dataset('obs_psl.nc')
>>> results = NAO(model_ds, reference_ds=obs_ds)
"""

from typing import Dict, List, Optional, Union

import xarray as xr

# Import utilities from pcmdi_metrics.io
from pcmdi_metrics.io import get_grid  # Get grid information from dataset
from pcmdi_metrics.io import get_time_key  # Get time coordinate key name
from pcmdi_metrics.io import load_regions_specs  # Load predefined geographic regions
from pcmdi_metrics.io import region_subset  # Subset dataset by region
# Import utilities from pcmdi_metrics.utils
from pcmdi_metrics.utils import regrid  # Regrid dataset to target grid
# Import computation functions from variability_mode.lib
# These functions contain the core EOF/CBF analysis logic
from pcmdi_metrics.variability_mode.lib import (
    adjust_timeseries,  # Remove annual cycle and domain mean
)
from pcmdi_metrics.variability_mode.lib import (
    calc_stats_save_dict,  # Calculate comparison statistics
)
from pcmdi_metrics.variability_mode.lib import calcSTD  # Calculate standard deviation
from pcmdi_metrics.variability_mode.lib import (
    eof_analysis_get_variance_mode,  # Perform EOF analysis
)
from pcmdi_metrics.variability_mode.lib import (
    gain_pcs_fraction,  # Calculate variance fraction for CBF
)
from pcmdi_metrics.variability_mode.lib import (
    gain_pseudo_pcs,  # Project data onto reference EOFs
)
from pcmdi_metrics.variability_mode.lib import (
    linear_regression_on_globe_for_teleconnection,  # Linear regression for teleconnection patterns
)

# Mapping of modes to their properties
_MODE_CONFIG = {
    "NAO": {"eof_number": 1, "variable": "psl"},
    "NAM": {"eof_number": 1, "variable": "psl"},
    "SAM": {"eof_number": 1, "variable": "psl"},
    "PNA": {"eof_number": 1, "variable": "psl"},
    "NPO": {"eof_number": 2, "variable": "psl"},
    "PDO": {"eof_number": 1, "variable": "ts"},
    "NPGO": {"eof_number": 2, "variable": "ts"},
    "AMO": {"eof_number": 1, "variable": "ts"},
    "PSA1": {"eof_number": 2, "variable": "psl"},
    "PSA2": {"eof_number": 3, "variable": "psl"},
}


def _validate_dataset(
    ds: xr.Dataset, data_var: str, dataset_name: str = "dataset"
) -> None:
    """
    Validate that dataset contains required variable and dimensions.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to validate.
    data_var : str
        Required variable name.
    dataset_name : str, optional
        Name for error messages. Default is "dataset".

    Raises
    ------
    TypeError
        If ds is not an xarray Dataset.
    ValueError
        If required variable or dimensions are missing.
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError(f"{dataset_name} must be an xarray.Dataset, got {type(ds)}")

    if data_var not in ds.data_vars:
        raise ValueError(
            f"Variable '{data_var}' not found in {dataset_name}. "
            f"Available variables: {list(ds.data_vars.keys())}"
        )

    # Check for time dimension (using get_time_key will raise error if not found)
    try:
        get_time_key(ds)
    except Exception as e:
        raise ValueError(f"{dataset_name} must have a time dimension: {e}")


def _subset_time_range(
    ds: xr.Dataset, start_year: Optional[int], end_year: Optional[int]
) -> xr.Dataset:
    """
    Subset dataset by time range using pcmdi_metrics.io utilities.

    Uses get_time_key() from pcmdi_metrics.io to robustly find the time coordinate.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset.
    start_year : int, optional
        Start year for subsetting.
    end_year : int, optional
        End year for subsetting.

    Returns
    -------
    xr.Dataset
        Subsetted dataset.
    """
    if start_year is None and end_year is None:
        return ds

    # Get time coordinate key using pcmdi_metrics.io utility
    time_key = get_time_key(ds)

    # Convert times to years
    years = ds[time_key].dt.year

    # Build selection criteria
    if start_year is not None and end_year is not None:
        selection = (years >= start_year) & (years <= end_year)
    elif start_year is not None:
        selection = years >= start_year
    else:  # end_year is not None
        selection = years <= end_year

    return ds.sel({time_key: selection})


def _compute_variability_mode(
    mode: str,
    model_ds: xr.Dataset,
    data_var: str,
    seasons: List[str],
    reference_ds: Optional[xr.Dataset],
    method: str,
    start_year: Optional[int],
    end_year: Optional[int],
    EofScaling: bool = False,
    RmDomainMean: bool = True,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Core computation function for variability modes.

    Parameters
    ----------
    mode : str
        Variability mode name (e.g., 'NAO', 'NAM', 'SAM', etc.).
    model_ds : xr.Dataset
        Model dataset containing the variable to analyze.
    data_var : str
        Variable name in the dataset.
    seasons : list of str
        List of seasons to compute (e.g., ['DJF', 'MAM', 'JJA', 'SON']).
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics.
    method : str
        Method to use: 'eof' or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis.
    end_year : int, optional
        End year for analysis.
    EofScaling : bool, optional
        If True, apply EOF scaling (unit variance). Default is False.
    RmDomainMean : bool, optional
        If True, remove domain mean at each time step. Default is True.

    Returns
    -------
    dict
        Results dictionary with structure:
        {
            'SEASON': {
                'diagnostics': {
                    'eof_pattern': xr.DataArray,
                    'pc_timeseries': xr.DataArray,
                    'cbf_pattern': xr.DataArray,  # only if method='cbf'
                },
                'metrics': {  # only if reference_ds provided
                    'frac': float,
                    'stdv_pc': float,
                    'cor': float,
                    'rms': float,
                    ...
                }
            }
        }
    """
    # Validate inputs
    if mode not in _MODE_CONFIG:
        raise ValueError(
            f"Unknown mode: {mode}. Supported modes: {list(_MODE_CONFIG.keys())}"
        )

    if method not in ["eof", "cbf"]:
        raise ValueError(f"Method must be 'eof' or 'cbf', got: {method}")

    if method == "cbf" and reference_ds is None:
        raise ValueError("method='cbf' requires reference_ds to be provided")

    # Get mode configuration
    eofn = _MODE_CONFIG[mode]["eof_number"]
    expected_var = _MODE_CONFIG[mode]["variable"]

    # Validate datasets using helper function
    _validate_dataset(model_ds, data_var, "model_ds")
    if reference_ds is not None:
        _validate_dataset(reference_ds, data_var, "reference_ds")

    # Load region specifications
    regions_specs = load_regions_specs()

    # Subset time range
    model_ds = _subset_time_range(model_ds, start_year, end_year)
    if reference_ds is not None:
        reference_ds = _subset_time_range(reference_ds, start_year, end_year)

    # Initialize results dictionary
    results = {}

    # Process reference data if provided (once, before season loop)
    if reference_ds is not None:
        ref_grid_global = get_grid(reference_ds)
        eof_obs = {}
        pc_obs = {}
        frac_obs = {}
        stdv_pc_obs = {}
        solver_obs = {}
        reverse_sign_obs = {}
        eof_lr_obs = {}
        ref_timeseries_season_dict = {}

        for season in seasons:
            # Adjust reference timeseries
            ref_timeseries_season = adjust_timeseries(
                reference_ds, data_var, mode, season, regions_specs, RmDomainMean
            )

            # Extract subdomain
            ref_timeseries_season_subdomain = region_subset(
                ref_timeseries_season, mode, regions_specs=regions_specs
            )

            # EOF analysis on reference
            (
                eof_obs[season],
                pc_obs[season],
                frac_obs[season],
                reverse_sign_obs[season],
                solver_obs[season],
            ) = eof_analysis_get_variance_mode(
                mode,
                ref_timeseries_season_subdomain,
                data_var,
                eofn=eofn,
                EofScaling=EofScaling,
            )

            # Calculate stdv of pc time series
            stdv_pc_obs[season] = calcSTD(pc_obs[season])

            # Linear regression for teleconnection
            (
                eof_lr_obs[season],
                slope_obs,
                intercept_obs,
            ) = linear_regression_on_globe_for_teleconnection(
                pc_obs[season],
                ref_timeseries_season,
                data_var,
                stdv_pc_obs[season],
                RmDomainMean,
                EofScaling,
            )

            ref_timeseries_season["eof_lr"] = eof_lr_obs[season]
            ref_timeseries_season_dict[season] = ref_timeseries_season

    # Season loop for model data
    for season in seasons:
        # Adjust model timeseries
        model_timeseries_season = adjust_timeseries(
            model_ds, data_var, mode, season, regions_specs, RmDomainMean
        )

        # Extract subdomain
        model_timeseries_season_subdomain = region_subset(
            model_timeseries_season, mode, regions_specs=regions_specs
        )

        # Initialize season results
        season_results = {"diagnostics": {}}

        if method == "eof":
            # EOF analysis on model
            (
                eof_model,
                pc_model,
                frac_model,
                reverse_sign_model,
                solver_model,
            ) = eof_analysis_get_variance_mode(
                mode,
                model_timeseries_season_subdomain,
                data_var,
                eofn=eofn,
                EofScaling=EofScaling,
            )

            # Calculate stdv of pc time series
            stdv_pc_model = calcSTD(pc_model)

            # Linear regression for teleconnection
            (
                eof_lr_model,
                slope_model,
                intercept_model,
            ) = linear_regression_on_globe_for_teleconnection(
                pc_model,
                model_timeseries_season,
                data_var,
                stdv_pc_model,
                RmDomainMean,
                EofScaling,
            )

            model_timeseries_season["eof_lr"] = eof_lr_model

            # Store diagnostics
            season_results["diagnostics"]["eof_pattern"] = eof_lr_model
            season_results["diagnostics"]["pc_timeseries"] = pc_model
            season_results["diagnostics"]["frac"] = float(frac_model)
            season_results["diagnostics"]["stdv_pc"] = float(stdv_pc_model)

            # Compute metrics if reference provided
            if reference_ds is not None:
                model_timeseries_season_subdomain = region_subset(
                    model_timeseries_season, mode, regions_specs=regions_specs
                )

                dict_head = {}
                dict_head, _ = calc_stats_save_dict(
                    mode=mode,
                    dict_head=dict_head,
                    model_ds=model_timeseries_season,
                    model_data_var="eof_lr",
                    eof=model_timeseries_season_subdomain["eof_lr"],
                    eof_lr=eof_lr_model,
                    pc=pc_model,
                    stdv_pc=stdv_pc_model,
                    frac=frac_model,
                    regions_specs=regions_specs,
                    obs_ds=ref_timeseries_season_dict[season],
                    eof_obs=eof_obs[season],
                    eof_lr_obs=eof_lr_obs[season],
                    stdv_pc_obs=stdv_pc_obs[season],
                    obs_compare=True,
                    method="eof",
                )

                season_results["metrics"] = dict_head

        elif method == "cbf":
            # CBF requires reference
            # Regrid model to reference grid
            model_timeseries_season_regrid = regrid(
                model_timeseries_season,
                data_var,
                ref_grid_global,
                regrid_tool="regrid2",
                fill_zero=True,
            )

            # Crop to subdomain
            model_timeseries_season_regrid_subdomain = region_subset(
                model_timeseries_season_regrid, mode, regions_specs=regions_specs
            )

            # Project onto reference EOFs to get CBF PCs
            cbf_pc = gain_pseudo_pcs(
                solver_obs[season],
                model_timeseries_season_regrid_subdomain[data_var],
                eofn,
                reverse_sign_obs[season],
                EofScaling=EofScaling,
            )

            # Calculate stdv of cbf pc
            stdv_cbf_pc = calcSTD(cbf_pc)

            # Linear regression for teleconnection
            (
                eof_lr_cbf,
                slope_cbf,
                intercept_cbf,
            ) = linear_regression_on_globe_for_teleconnection(
                cbf_pc,
                model_timeseries_season,
                data_var,
                stdv_cbf_pc,
                RmDomainMean,
                EofScaling,
            )

            model_timeseries_season["eof_lr_cbf"] = eof_lr_cbf

            # Extract subdomain for statistics
            model_timeseries_season_subdomain = region_subset(
                model_timeseries_season, mode, regions_specs=regions_specs
            )

            # Calculate fraction of variance explained by cbf pc
            frac_cbf = gain_pcs_fraction(
                model_timeseries_season_subdomain,
                data_var,
                model_timeseries_season_subdomain,
                "eof_lr_cbf",
                cbf_pc / stdv_cbf_pc,
            )

            # Store diagnostics
            season_results["diagnostics"]["cbf_pattern"] = eof_lr_cbf
            season_results["diagnostics"]["pc_timeseries"] = cbf_pc
            season_results["diagnostics"]["frac"] = float(frac_cbf)
            season_results["diagnostics"]["stdv_pc"] = float(stdv_cbf_pc)

            # Compute metrics
            dict_head = {}
            dict_head, _ = calc_stats_save_dict(
                mode=mode,
                dict_head=dict_head,
                model_ds=model_timeseries_season,
                model_data_var="eof_lr_cbf",
                eof=model_timeseries_season_subdomain["eof_lr_cbf"],
                eof_lr=eof_lr_cbf,
                pc=cbf_pc,
                stdv_pc=stdv_cbf_pc,
                frac=frac_cbf,
                regions_specs=regions_specs,
                obs_ds=ref_timeseries_season_dict[season],
                eof_obs=eof_obs[season],
                eof_lr_obs=eof_lr_obs[season],
                stdv_pc_obs=stdv_pc_obs[season],
                obs_compare=True,
                method="cbf",
            )

            season_results["metrics"] = dict_head

        results[season] = season_results

    return results


def NAO(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute North Atlantic Oscillation (NAO) diagnostics and metrics.

    NAO is the leading EOF of sea level pressure over the North Atlantic (20-80N, 90W-40E).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with structure:
        {
            'SEASON': {
                'diagnostics': {
                    'eof_pattern': xr.DataArray,
                    'pc_timeseries': xr.DataArray,
                    'frac': float,
                    'stdv_pc': float,
                },
                'metrics': {...}  # only if reference_ds provided
            }
        }

    Examples
    --------
    >>> import xarray as xr
    >>> from pcmdi_metrics.variability_mode import NAO
    >>> model_ds = xr.open_dataset('model_psl.nc')
    >>> results = NAO(model_ds)
    >>> print(results['DJF']['diagnostics']['frac'])
    """
    return _compute_variability_mode(
        "NAO", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def NAM(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Northern Annular Mode (NAM) diagnostics and metrics.

    NAM is the leading EOF of sea level pressure over the Northern Hemisphere (20-90N).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import NAM
    >>> results = NAM(model_ds, reference_ds=obs_ds)
    """
    return _compute_variability_mode(
        "NAM", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def SAM(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Southern Annular Mode (SAM) diagnostics and metrics.

    SAM is the leading EOF of sea level pressure over the Southern Hemisphere (90S-20S).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import SAM
    >>> results = SAM(model_ds)
    """
    return _compute_variability_mode(
        "SAM", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def PNA(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Pacific North American Pattern (PNA) diagnostics and metrics.

    PNA is the leading EOF of sea level pressure over the North Pacific (20-85N, 120-240E).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import PNA
    >>> results = PNA(model_ds)
    """
    return _compute_variability_mode(
        "PNA", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def NPO(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute North Pacific Oscillation (NPO) diagnostics and metrics.

    NPO is the second EOF of sea level pressure over the North Pacific (20-85N, 120-240E).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import NPO
    >>> results = NPO(model_ds)
    """
    return _compute_variability_mode(
        "NPO", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def PDO(
    model_ds: xr.Dataset,
    data_var: str = "ts",
    seasons: List[str] = ["monthly"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Pacific Decadal Oscillation (PDO) diagnostics and metrics.

    PDO is the leading EOF of sea surface temperature over the North Pacific (20-70N, 110-260E).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea surface temperature data.
    data_var : str, optional
        Variable name in the dataset. Default is 'ts'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['monthly'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import PDO
    >>> results = PDO(model_ds, data_var='ts')
    >>> # PDO defaults to monthly analysis
    >>> print(results['monthly']['diagnostics']['frac'])
    """
    return _compute_variability_mode(
        "PDO", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def NPGO(
    model_ds: xr.Dataset,
    data_var: str = "ts",
    seasons: List[str] = ["monthly"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute North Pacific Gyre Oscillation (NPGO) diagnostics and metrics.

    NPGO is the second EOF of sea surface temperature over the North Pacific (20-70N, 110-260E).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea surface temperature data.
    data_var : str, optional
        Variable name in the dataset. Default is 'ts'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['monthly'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import NPGO
    >>> results = NPGO(model_ds, data_var='ts')
    >>> # NPGO defaults to monthly analysis
    >>> print(results['monthly']['diagnostics']['frac'])
    """
    return _compute_variability_mode(
        "NPGO", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def AMO(
    model_ds: xr.Dataset,
    data_var: str = "ts",
    seasons: List[str] = ["yearly"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Atlantic Multidecadal Oscillation (AMO) diagnostics and metrics.

    AMO is the leading EOF of sea surface temperature over the North Atlantic (0-70N, 80W-0E).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea surface temperature data.
    data_var : str, optional
        Variable name in the dataset. Default is 'ts'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['yearly'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import AMO
    >>> results = AMO(model_ds, data_var='ts')
    >>> # AMO defaults to yearly analysis
    >>> print(results['yearly']['diagnostics']['frac'])
    """
    return _compute_variability_mode(
        "AMO", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def PSA1(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Pacific-South American Pattern 1 (PSA1) diagnostics and metrics.

    PSA1 is the second EOF of sea level pressure over the Southern Hemisphere (90S-20S).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import PSA1
    >>> results = PSA1(model_ds)
    >>> print(results['DJF']['diagnostics']['frac'])
    """
    return _compute_variability_mode(
        "PSA1", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )


def PSA2(
    model_ds: xr.Dataset,
    data_var: str = "psl",
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],
    reference_ds: Optional[xr.Dataset] = None,
    method: str = "eof",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Dict[str, Union[xr.DataArray, float, Dict]]]:
    """
    Compute Pacific-South American Pattern 2 (PSA2) diagnostics and metrics.

    PSA2 is the third EOF of sea level pressure over the Southern Hemisphere (90S-20S).

    Parameters
    ----------
    model_ds : xr.Dataset
        Model dataset containing sea level pressure data.
    data_var : str, optional
        Variable name in the dataset. Default is 'psl'.
    seasons : list of str, optional
        List of seasons to compute. Default is ['DJF', 'MAM', 'JJA', 'SON'].
    reference_ds : xr.Dataset, optional
        Reference/observational dataset for computing metrics. Default is None.
    method : str, optional
        Method to use: 'eof' (default) or 'cbf' (requires reference_ds).
    start_year : int, optional
        Start year for analysis. Default is None (use all data).
    end_year : int, optional
        End year for analysis. Default is None (use all data).

    Returns
    -------
    dict
        Results dictionary with diagnostics and metrics (if reference provided).

    Examples
    --------
    >>> from pcmdi_metrics.variability_mode import PSA2
    >>> results = PSA2(model_ds)
    >>> print(results['DJF']['diagnostics']['frac'])
    """
    return _compute_variability_mode(
        "PSA2", model_ds, data_var, seasons, reference_ds, method, start_year, end_year
    )
