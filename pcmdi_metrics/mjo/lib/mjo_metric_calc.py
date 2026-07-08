# pcmdi_metrics/mjo/lib/mjo_metric_calc.py
"""
MJO east-west power ratio calculation.

Public API
----------
compute_mjo_ewr_from_dataset(ds, data_var, start_year, end_year, ...)
    Pure computation — accepts an already-opened xarray Dataset.

mjo_metric_ewr_calculation(...)
    driver-oriented entry point (backward compatible).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

import numpy as np
import xarray as xr

from pcmdi_metrics.io import get_longitude, get_time_key, xcdat_open
from pcmdi_metrics.mjo.lib import (
    calculate_ewr,
    generate_axes_and_decorate,
    get_daily_ano_segment,
    interp2commonGrid,
    output_power_spectra,
    space_time_spectrum,
    subSliceSegment,
    write_netcdf_output,
)
from pcmdi_metrics.utils import adjust_units

from .plot_wavenumber_frequency_power import plot_power

logger = logging.getLogger(__name__)

np_float = np.float64


# ---------------------------------------------------------------------------
# Public API — pure computation, no file I/O, no side effects
# ---------------------------------------------------------------------------


def compute_mjo_ewr_from_dataset(
    ds: xr.Dataset,
    data_var: str,
    start_year: int,
    end_year: int,
    season: str = "NDJFMA",
    cmm_grid: bool = False,
    deg_x: float = 2.5,
    units_adjust: tuple[bool, str, str] | None = None,
    segment_length: int = 180,
) -> dict[str, Any]:
    """Compute the MJO east-west power ratio from an open xarray Dataset.

    This is the pure-computation entry point. It performs no file I/O,
    writes no output files, and produces no plots. Suitable for use in
    Jupyter notebooks, pipelines, and unit tests.

    Parameters
    ----------
    ds : xr.Dataset
        Daily precipitation (or OLR) dataset. Must be CF-compliant with
        latitude, longitude, and a recognised time coordinate.
    data_var : str
        Name of the variable to analyse within *ds* (e.g. ``"pr"``).
    start_year : int
        First year of the analysis window (inclusive).
    end_year : int
        Last year of the analysis window (inclusive).
    season : {"NDJFMA", "MJJASO"}
        Season for segment extraction.
    cmm_grid : bool
        If ``True``, regrid to a common ``deg_x`` × ``deg_x`` grid before
        the spectral analysis.
    deg_x : float
        Grid spacing (degrees) used when *cmm_grid* is ``True``.
    units_adjust : tuple or None
        Passed directly to :func:`pcmdi_metrics.utils.adjust_units`.
        ``None`` skips unit conversion.
    segment_length : int
        Number of time steps per segment (must be even). Defaults to 180.

    Returns
    -------
    dict
        ``east_power``, ``west_power``, ``east_west_power_ratio``,
        ``analysis_time_window_start_year``, ``analysis_time_window_end_year``.

    Raises
    ------
    ValueError
        If *season* is not one of the accepted values, or if the dataset
        does not cover the requested time window.
    """
    if season not in {"NDJFMA", "MJJASO"}:
        raise ValueError(f"season must be 'NDJFMA' or 'MJJASO', got {season!r}")

    ds = ds.bounds.add_missing_bounds()
    lon = get_longitude(ds)
    time_key = get_time_key(ds)

    # Resolve actual start/end years from the dataset
    first_time = datetime(
        ds[time_key][0].item().year,
        ds[time_key][0].item().month,
        ds[time_key][0].item().day,
    )
    last_time = datetime(
        ds[time_key][-1].item().year,
        ds[time_key][-1].item().month,
        ds[time_key][-1].item().day,
    )

    if season == "NDJFMA":
        if first_time > datetime(start_year, 11, 1):
            start_year += 1
        if last_time < datetime(end_year, 4, 30):
            end_year -= 1
        mon, day = 11, 1
        num_year = end_year - start_year
    else:  # MJJASO
        mon, day = 5, 1
        num_year = end_year - start_year + 1

    nt = segment_length
    nl = int(360 / deg_x) if cmm_grid else len(lon.values)

    logger.debug(
        "start_year=%d, end_year=%d, NL=%d, NT=%d", start_year, end_year, nl, nt
    )

    # ------------------------------------------------------------------
    # Build daily seasonal cycle
    # ------------------------------------------------------------------
    n_lat, n_lon = ds[data_var].shape[1], ds[data_var].shape[2]
    sea_cyc_values = np.zeros((nt, n_lat, n_lon), dtype=np_float)
    segments: dict[int, xr.Dataset] = {}

    for year in range(start_year, end_year):
        seg = subSliceSegment(ds, year, mon, day, nt)
        if units_adjust is not None:
            seg[data_var] = adjust_units(seg[data_var], units_adjust)
        segments[year] = seg
        sea_cyc_values += seg[data_var].values / float(num_year)
        logger.debug("Processed seasonal cycle for year %d", year)

    # ------------------------------------------------------------------
    # Remove seasonal cycle → anomalies
    # ------------------------------------------------------------------
    segment_ano: dict[int, xr.Dataset] = {}
    for year in range(start_year, end_year):
        ano = segments[year].copy()
        ano[data_var] = xr.DataArray(
            segments[year][data_var].values - sea_cyc_values,
            dims=segments[year][data_var].dims,
            coords=segments[year][data_var].coords,
        )
        segment_ano[year] = ano

    # ------------------------------------------------------------------
    # Space-time power spectra
    # ------------------------------------------------------------------
    power_arr = np.zeros((num_year, nt + 1, nl + 1), dtype=np_float)

    for n, year in enumerate(range(start_year, end_year)):
        seg = segment_ano[year]
        if cmm_grid:
            seg = interp2commonGrid(seg, data_var, deg_x)
        d_seg_x_ano = get_daily_ano_segment(seg, data_var)
        power_arr[n] = space_time_spectrum(d_seg_x_ano, data_var)
        logger.debug("Computed spectrum for year %d", year)

    power_mean = np.average(power_arr, axis=0)
    power_mean = generate_axes_and_decorate(power_mean, nt, nl)
    oee = output_power_spectra(nl, nt, power_mean)

    ewr, east_power, west_power = calculate_ewr(oee)
    logger.info("EWR=%.4f  east=%.4f  west=%.4f", ewr, east_power, west_power)

    return {
        "east_power": east_power,
        "west_power": west_power,
        "east_west_power_ratio": ewr,
        "analysis_time_window_start_year": start_year,
        "analysis_time_window_end_year": end_year,
        # Expose intermediate arrays so callers can do their own plotting
        "_oee": oee,
    }


# ---------------------------------------------------------------------------
# driver-oriented entry point
# ---------------------------------------------------------------------------


def mjo_metric_ewr_calculation(
    mip: str,
    model: str,
    exp: str,
    run: str,
    debug: bool,
    plot: bool,
    nc_out: bool,
    cmmGrid: bool,
    degX: float,
    UnitsAdjust,
    inputfile: str,
    data_var: str,
    startYear: int,
    endYear: int,
    segmentLength: int,
    dir_paths: dict[str, str],
    season: str = "NDJFMA",
) -> dict[str, Any]:
    """Driver-oriented wrapper — preserves the original CLI call signature.

    Prefer :func:`compute_mjo_ewr_from_dataset` for library use.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    logger.debug("Opening file: %s", inputfile)
    ds = xcdat_open(inputfile)

    result = compute_mjo_ewr_from_dataset(
        ds=ds,
        data_var=data_var,
        start_year=startYear,
        end_year=endYear,
        season=season,
        cmm_grid=cmmGrid,
        deg_x=degX,
        units_adjust=UnitsAdjust,
        segment_length=segmentLength,
    )

    oee = result.pop("_oee")

    # Build output filename (driver concern, not science concern)
    output_stem = f"{mip}_{model}_{exp}_{run}_mjo_{startYear}-{endYear}_{season}"
    if cmmGrid:
        output_stem += "_cmmGrid"

    if nc_out:
        os.makedirs(dir_paths["diagnostic_results"], exist_ok=True)
        fout = os.path.join(dir_paths["diagnostic_results"], output_stem)
        write_netcdf_output(oee, fout)

    if plot:
        os.makedirs(dir_paths["graphics"], exist_ok=True)
        fout = os.path.join(dir_paths["graphics"], output_stem)
        title = (
            f"OBS ({run})\n{data_var.capitalize()}, {season} {startYear}-{endYear}"
            if model == "obs"
            else f"{mip.upper()}: {model} ({run})\n{data_var.capitalize()}, {season} {startYear}-{endYear}"
        )
        if cmmGrid:
            title += ", common grid (2.5x2.5deg)"
        plot_power(oee, title, fout, result["east_west_power_ratio"])

    ds.close()
    return result
