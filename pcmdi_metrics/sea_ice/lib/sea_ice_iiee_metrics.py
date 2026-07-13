import argparse
import json
import os
import warnings

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import xcdat as xc
from matplotlib.colors import BoundaryNorm, ListedColormap
from scipy.interpolate import griddata

from pcmdi_metrics.io.xcdat_dataset_io import get_calendar

warnings.filterwarnings("ignore", message="invalid value encountered in divide")
warnings.filterwarnings("ignore", category=RuntimeWarning)


"""
Code History
------------
2026-04 Original code written in Matlab was conveted to Python by Younjoo Lee (Naval Postgraduate School (NPS))
2026-05 Developed a Python API based on the conveted code. Jiwoo Lee (Lawrence Livermore National Laboratory (LLNL))
"""


ICE_THRESHOLD_PERCENT = 15.0
OBS_GRID_RESOLUTION_KM = 25.0
OBS_GRID_CELL_AREA_KM2 = OBS_GRID_RESOLUTION_KM * OBS_GRID_RESOLUTION_KM
N_MONTHS = 12

LAT_CANDIDATES = ["lat", "latitude", "Lat", "Latitude", "LAT", "nav_lat"]
LON_CANDIDATES = ["lon", "longitude", "Lon", "Longitude", "LON", "nav_lon"]


def calc_iiee_annual_cycle(
    ds_obs,
    ds_model,
    obs_data_var="ice_conc",
    model_data_var="siconc",
    syear=1988,
    eyear=2014,
    identifier=None,
    save_dir="output",
    debug=False,
):
    """
    Compute the monthly climatological annual cycle of Integrated Ice-Edge Error
    (IIEE) between observational and model sea ice concentration datasets.

    The function subsets the input datasets to the requested time range, computes
    monthly climatologies, evaluates IIEE for each month, and optionally saves
    monthly comparison plots plus a seasonal-cycle summary plot.

    Parameters
    ----------
    ds_obs : xarray.Dataset
        Observational dataset containing sea ice concentration and a
        ``status_flag`` variable used to identify land points on the
        observational grid.
    ds_model : xarray.Dataset
        Model dataset containing sea ice concentration to compare with the
        observations.
    obs_data_var : str, optional
        Name of the observational sea ice concentration variable in ``ds_obs``.
        Default is ``"ice_conc"``.
    model_data_var : str, optional
        Name of the model sea ice concentration variable in ``ds_model``.
        Default is ``"siconc"``.
    syear : int, optional
        Starting year of the analysis period, inclusive. Default is ``1988``.
    eyear : int, optional
        Ending year of the analysis period, inclusive. Default is ``2014``.
    identifier : str, optional
        Text identifier that to be added to diagnostics' headser and as a part of output files
    save_dir : str or None, optional
        Directory where figures are saved. If ``None``, figures are not saved.
        Default is ``"output"``.
    debug : bool, optional
        If ``True``, print additional diagnostic information. Default is ``False``.

    Returns
    -------
    dict
        Dictionary containing metadata and monthly IIEE metrics.

    Examples
    --------
    This function is mainly intended for development testing or command-line
    execution. In package usage, call ``calc_iiee_annual_cycle()`` directly:

    >>> import xcdat as xc
    >>> ds_obs = xc.open_dataset("data/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc")
    >>> ds_model = xc.open_mfdataset("data/siconc_SImon_E3SM-1-0_historical_r1i1p1f1_*_*.nc")
    >>> from pcmdi_metrics.sea_ice import calc_iiee_annual_cycle
    >>> result = calc_iiee_annual_cycle(
    ...     ds_obs=ds_obs,
    ...     ds_model=ds_model,
    ...     obs_data_var="ice_conc",
    ...     model_data_var="siconc",
    ...     syear=2010,
    ...     eyear=2014,
    ...     save_dir="output",
    ... )
    """
    # Quick quality control
    validate_inputs(ds_obs, ds_model, obs_data_var, model_data_var)

    # Get annual cycle for time period (e.g., 1988-2014)
    eday_model = get_eday_model_considering_calendar(ds_model)

    reference_period_obs = (f"{syear}-01-01", f"{eyear}-12-31")
    reference_period_model = (f"{syear}-01-01", f"{eyear}-12-{eday_model}")

    obs_monthly_clim = get_annual_cycle(
        ds_obs, obs_data_var, reference_period=reference_period_obs
    )
    model_monthly_clim = get_annual_cycle(
        ds_model, model_data_var, reference_period=reference_period_model
    )

    # status_flag is needed to find land grid (thus, not time varying)
    obs_monthly_clim["status_flag"] = ds_obs["status_flag"].isel(time=0)

    # Get coordinate info
    obs_lat_name, obs_lon_name = get_coordinate_names(ds_obs)
    model_lat_name, model_lon_name = get_coordinate_names(ds_model)

    # Prepare output dict with metadata
    result = {
        "metadata": {
            "start_year": syear,
            "end_year": eyear,
            "obs_variable": obs_data_var,
            "model_variable": model_data_var,
            "ice_threshold_percent": ICE_THRESHOLD_PERCENT,
            "grid_cell_area_km2": OBS_GRID_CELL_AREA_KM2,
            "obs_lat_name": obs_lat_name,
            "obs_lon_name": obs_lon_name,
            "model_lat_name": model_lat_name,
            "model_lon_name": model_lon_name,
        },
        "metrics": {},
    }

    monthly_diagnostics = {}

    # Calculate metrics per month
    for month_index in range(N_MONTHS):
        month = month_index + 1

        metrics, diagnostics = calc_iiee(
            obs_data=obs_monthly_clim.isel(time=month_index),
            model_data=model_monthly_clim.isel(time=month_index),
            obs_data_var=obs_data_var,
            model_data_var=model_data_var,
            debug=debug,
        )

        result["metrics"][month] = metrics
        monthly_diagnostics[month] = diagnostics

        if save_dir is not None:
            if identifier:
                map_filename = f"sic_iiee_{identifier}_month_{month:02d}.png"
            else:
                map_filename = f"sic_iiee_month_{month:02d}.png"

            plot_ice_comparison(
                diag_dict=diagnostics,
                metrics_dict=metrics,
                time_label=f"Month: {month} ({syear}-{eyear})",
                save_path=os.path.join(save_dir, map_filename),
                identifier=identifier,
            )

    if save_dir is not None:
        if identifier:
            map_all_filename = f"sic_iiee_{identifier}_month_all.png"
            lineplot_filename = f"sic_iiee_{identifier}_line_plot.png"
        else:
            map_all_filename = "sic_iiee_all_months.png"
            lineplot_filename = "sic_iiee_line_plot.png"

        plot_iiee_all_months_grid(
            monthly_diagnostics=monthly_diagnostics,
            monthly_metrics=result["metrics"],
            syear=syear,
            eyear=eyear,
            save_path=os.path.join(save_dir, map_all_filename),
            show_edge_on_diff=False,
            show_diff_colorbar=False,
            identifier=identifier,
        )

        plot_iiee_seasonal_cycle(
            metrics_data=result,
            title="Monthly Integrated Ice-Edge Error (IIEE)",
            save_path=os.path.join(save_dir, lineplot_filename),
            identifier=identifier,
        )

    return result


def calc_iiee(
    obs_data,
    model_data,
    obs_data_var="ice_conc",
    model_data_var="siconc",
    debug=False,
):
    """
    Calculate Integrated Ice-Edge Error (IIEE) for a single monthly field.

    Parameters
    ----------
    obs_data : xarray.Dataset
        Observational monthly dataset containing sea ice concentration and
        ``status_flag``.
    model_data : xarray.Dataset
        Model monthly dataset containing sea ice concentration.
    obs_data_var : str, optional
        Name of the observational sea ice concentration variable.
    model_data_var : str, optional
        Name of the model sea ice concentration variable.
    debug : bool, optional
        If ``True``, print scalar diagnostic values.

    Returns
    -------
    tuple[dict, dict]
        Metrics dictionary and diagnostics dictionary.
    """
    # Quick quality control
    validate_monthly_inputs(obs_data, model_data, obs_data_var, model_data_var)

    # CONVERTING coordinates onto OSI SAF grid in meters centered at the North Pole
    # Define the Lambert Azimuthal Equal-Area (laea) projection centered at the North Pole
    # This coordinate is used in OSI SAF data
    projection = get_polar_equal_area_projection()

    # Conversion of satellite coordinates from degrees to meters centered at the North Pole
    obs_x, obs_y = project_grid(obs_data, grid_label="obs", projection=projection)

    # Conversion of model latitude and longitude to meters centered at the North Pole
    model_x, model_y = project_grid(
        model_data, grid_label="model", projection=projection
    )

    obs_sic = obs_data[obs_data_var]
    obs_status_flag = obs_data["status_flag"]
    model_sic = model_data[model_data_var]

    check_sic_units(obs_sic, model_sic)

    # INTERPOLATING model data onto observational data grid (i.e., laea projection)
    model_sic_on_obs_grid = interpolate_model_to_obs_grid(
        model_sic=model_sic,
        model_x=model_x,
        model_y=model_y,
        obs_x=obs_x,
        obs_y=obs_y,
        obs_status_flag=obs_status_flag,
    )

    # IIEE CALCULATION
    metrics, diagnostics = compute_iiee_metrics_and_diagnostics(
        obs_sic=obs_sic,
        model_sic_on_obs_grid=model_sic_on_obs_grid,
        obs_status_flag=obs_status_flag,
        debug=debug,
    )

    return metrics, diagnostics


def get_eday_model_considering_calendar(ds):
    calendar = get_calendar(ds)
    if "360" in calendar:
        return 30
    else:
        return 31


def get_annual_cycle(ds, data_var, reference_period=None):
    """
    Compute the monthly climatology of a variable.

    Parameters
    ----------
    ds : xarray.Dataset
        Input dataset.
    data_var : str
        Variable name for climatology calculation.
    reference_period : tuple[str, str] | None, optional
        The climatological reference period, which is a subset of the entire time series.
        This parameter accepts a tuple of strings in the format ‘yyyy-mm-dd’.
        For example, ('1850-01-01', '1899-12-31'). If no value is provided,
        the climatological reference period will be the full period covered by the dataset.
        See https://xcdat.readthedocs.io/en/latest/generated/xarray.Dataset.temporal.climatology.html for details.

    Returns
    -------
    xarray.Dataset
        Monthly climatology dataset with 12 time steps.
    """
    return ds.temporal.climatology(
        data_var, freq="month", reference_period=reference_period
    )


def get_polar_equal_area_projection():
    """
    Return the Lambert Azimuthal Equal-Area projection centered on the North Pole.

    Returns
    -------
    pyproj.Proj
        Projection object used for interpolation onto the observational grid.
    """
    return pyproj.Proj(
        proj="laea",
        lat_0=90,
        lon_0=0,
        x_0=0,
        y_0=0,
        datum="WGS84",
    )


def _find_coordinate_name(ds, candidates, coord_type):
    """
    Find the first matching coordinate or variable name in a dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset to inspect.
    candidates : list[str]
        Candidate names to search for.
    coord_type : str
        Coordinate type for error messages.

    Returns
    -------
    str
        Matched coordinate or variable name.

    Raises
    ------
    ValueError
        If no candidate name is found.
    """
    for name in candidates:
        if name in ds.coords or name in ds.variables:
            return name

    raise ValueError(f"Could not find a {coord_type} coordinate. Tried: {candidates}")


def get_coordinate_names(ds):
    """
    Resolve latitude and longitude coordinate names in a dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing latitude and longitude.

    Returns
    -------
    tuple[str, str]
        Latitude name, longitude name.
    """
    lat_name = _find_coordinate_name(ds, LAT_CANDIDATES, "latitude")
    lon_name = _find_coordinate_name(ds, LON_CANDIDATES, "longitude")
    return lat_name, lon_name


def project_grid(ds, grid_label, projection):
    """
    Project a dataset grid to planar x/y coordinates.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing latitude and longitude coordinates or variables.
    grid_label : str
        Grid label, expected values are ``"obs"`` or ``"model"``.
    projection : pyproj.Proj
        Projection used to convert lon/lat to x/y in meters.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Projected x and y arrays.

    Raises
    ------
    ValueError
        If coordinate dimensionality is unsupported.
    """
    lat_name, lon_name = get_coordinate_names(ds)

    lat_values = ds[lat_name].data
    lon_values = ds[lon_name].data

    if grid_label == "obs":
        if lat_values.ndim != lon_values.ndim:
            raise ValueError(
                f"Observational latitude and longitude dimensions do not match: "
                f"{lat_name}.ndim={lat_values.ndim}, {lon_name}.ndim={lon_values.ndim}"
            )
        return projection(lon_values, lat_values)

    if grid_label == "model":
        if lon_values.ndim == 1 and lat_values.ndim == 1:
            lon_2d, lat_2d = np.meshgrid(lon_values, lat_values)
        elif lon_values.ndim == 2 and lat_values.ndim == 2:
            lon_2d, lat_2d = lon_values, lat_values
        else:
            raise ValueError(
                f"Incompatible model coordinate dimensions: "
                f"{lon_name}.ndim={lon_values.ndim}, {lat_name}.ndim={lat_values.ndim}"
            )
        return projection(lon_2d, lat_2d)

    raise ValueError(f"Unsupported grid_label: {grid_label}")


def interpolate_model_to_obs_grid(
    model_sic,
    model_x,
    model_y,
    obs_x,
    obs_y,
    obs_status_flag,
):
    """
    Interpolate model sea ice concentration onto the observational grid.

    Parameters
    ----------
    model_sic : xarray.DataArray
        Model sea ice concentration field.
    model_x, model_y : np.ndarray
        Projected model grid coordinates.
    obs_x, obs_y : np.ndarray
        Projected observational grid coordinates.
    obs_status_flag : xarray.DataArray
        Observational status flag used to mask land points.

    Returns
    -------
    np.ndarray
        Model sea ice concentration on the observational grid.
    """
    model_points_xy = np.column_stack((model_x.ravel(), model_y.ravel()))
    model_sic_1d = model_sic.values.ravel()
    model_ocean_mask = ~np.isnan(model_sic_1d)

    obs_points_xy = np.column_stack((obs_x.ravel(), obs_y.ravel()))
    obs_status_flag_1d = obs_status_flag.values.ravel()

    # the model input data are interpolated onto the observational data grid
    model_sic_interpolated_1d = griddata(
        model_points_xy[model_ocean_mask],
        model_sic_1d[model_ocean_mask],
        obs_points_xy,
        method="nearest",
    )

    model_sic_interpolated_1d[obs_status_flag_1d == 1] = np.nan
    return model_sic_interpolated_1d.reshape(obs_x.shape)


def compute_iiee_metrics_and_diagnostics(
    obs_sic,
    model_sic_on_obs_grid,
    obs_status_flag,
    debug=False,
):
    """
    Compute scalar IIEE metrics and diagnostic arrays.

    Parameters
    ----------
    obs_sic : xarray.DataArray
        Observed sea ice concentration on the observational grid.
    model_sic_on_obs_grid : np.ndarray
        Interpolated model sea ice concentration on the observational grid.
    obs_status_flag : xarray.DataArray
        Observational land or status mask.
    debug : bool, optional
        If ``True``, print scalar metric values.

    Returns
    -------
    tuple[dict, dict]
        Metrics dictionary and diagnostics dictionary.
    """
    obs_sic_1d = obs_sic.values.ravel()
    model_sic_1d = model_sic_on_obs_grid.ravel()
    obs_status_flag_1d = obs_status_flag.values.ravel()
    grid_shape = model_sic_on_obs_grid.shape

    # Define ice edge threshold (i.e., 15%)
    ice_model = model_sic_1d > ICE_THRESHOLD_PERCENT
    ice_obs = obs_sic_1d > ICE_THRESHOLD_PERCENT

    # Finding areas where they disagree: Overestiamted vs. Underestimated
    # overestimated: False positive (model says ice, obs says water)
    iiee_false_positive = ice_model & ~ice_obs
    # underestimated: False negative (model says water, obs says ice)
    iiee_false_negative = ~ice_model & ice_obs
    # Integrating over the total area
    iiee_total_mask = iiee_false_positive | iiee_false_negative

    # Area size: sum of pixels where there is disagreement * area of those pixels
    iiee_overestimated_km2 = OBS_GRID_CELL_AREA_KM2 * iiee_false_positive.sum()
    iiee_underestimated_km2 = OBS_GRID_CELL_AREA_KM2 * iiee_false_negative.sum()
    iiee_total_area_km2 = OBS_GRID_CELL_AREA_KM2 * iiee_total_mask.sum()

    # KEY VARIABLES: iiee_total_area_km2, iiee_overestimated_km2, and iiee_underestimated_km2
    # NOTE: lakes are NOT completeley removed yet and sub-Arctic regions are included
    # FOR FUTURE: applying a Arctic mask with several sub-regions as well as excluding lakes.

    if debug:
        print("iiee_overestimated_km2:", iiee_overestimated_km2)
        print("iiee_underestimated_km2:", iiee_underestimated_km2)
        print("iiee_total_area_km2:", iiee_total_area_km2)

    metrics = {
        "iiee_overestimated_km2": float(iiee_overestimated_km2),
        "iiee_underestimated_km2": float(iiee_underestimated_km2),
        "iiee_total_area_km2": float(iiee_total_area_km2),
    }

    # Save difference for plotting overestimated and underestimated area
    ice_diff = ice_model.astype(float) - ice_obs.astype(float)
    ice_diff[obs_status_flag_1d == 1] = np.nan

    diagnostics = {
        "model_sic": model_sic_on_obs_grid,
        "obs_sic": obs_sic,
        "ice_model": ice_model.reshape(grid_shape),
        "ice_obs": ice_obs.reshape(grid_shape),
        "ice_diff": ice_diff.reshape(grid_shape),
    }

    return metrics, diagnostics


def plot_ice_comparison(
    diag_dict,
    metrics_dict=None,
    time_label="",
    save_path=None,
    show_edge_on_diff=False,
    show_diff_colorbar=False,
    identifier=None,
):
    """
    Plot model SIC, observed SIC, and their spatial difference.

    Parameters
    ----------
    diag_dict : dict
        Diagnostic fields returned by ``calc_iiee``.
    metrics_dict : dict, optional
        Scalar IIEE metrics in km².
    time_label : str, optional
        Label shown in the figure title.
    save_path : str, optional
        If provided, save the figure to this path.
    show_edge_on_diff : bool, optional
        If ``True``, overlay model and observed ice edges on the difference panel.
    show_diff_colorbar : bool, optional
        If ``True``, add a colorbar to the difference panel.
    identifier : str, optional
        If provided, it will be shown in the header
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    sic_cmap = plt.get_cmap("Blues_r").copy()
    sic_cmap.set_bad(color="#FFF9C4")

    # Define Proxy Artists for the legends
    model_line = mlines.Line2D([], [], color="red", linewidth=1, label="Model Edge")
    obs_line = mlines.Line2D([], [], color="limegreen", linewidth=1, label="OBS Edge")

    # New Proxy Artists for filled areas
    over_patch = mpatches.Patch(color="#C00707", label="Overestimated Area")
    under_patch = mpatches.Patch(color="#000080", label="Underestimated Area")

    # --- PANEL 1 & 2 (Model & OBS) ---
    for i, (field_key, edge_key, edge_color, title, line_handle) in enumerate(
        [
            ("model_sic", "ice_model", "red", "Model SIC & Edge", model_line),
            ("obs_sic", "ice_obs", "limegreen", "OBS SIC & Edge", obs_line),
        ]
    ):
        im = axes[i].imshow(
            diag_dict[field_key],
            cmap=sic_cmap,
            origin="upper",
            vmin=0,
            vmax=100,
        )
        axes[i].contour(
            diag_dict[edge_key], levels=[0.5], colors=edge_color, linewidths=1
        )
        axes[i].set_title(title)
        axes[i].legend(handles=[line_handle], loc="lower left", fontsize=9)
        axes[i].set_facecolor("#ADD8E6")
        axes[i].set_xticks([])
        axes[i].set_yticks([])
        axes[i].tick_params(
            axis="both", bottom=False, left=False, labelbottom=False, labelleft=False
        )

    fig.colorbar(
        im,
        ax=[axes[0], axes[1]],
        label="Sea Ice Concentration (%)",
        orientation="vertical",
        shrink=0.65,
        pad=0.02,
    )

    # --- PANEL 3: Difference ---
    diff_data = diag_dict["ice_diff"]

    # FILL AREAS: Positive (1) in Red, Negative (-1) in Blue
    # levels=[0.5, 1.5] catches the +1 values; levels=[-1.5, -0.5] catches -1 values
    diff_cmap = ListedColormap(["#000080", "#ADD8E6", "#C00707"])
    diff_cmap.set_bad(color="#FFF9C4")
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], diff_cmap.N)

    diff_im = axes[2].imshow(
        diff_data,
        cmap=diff_cmap,
        norm=norm,
        origin="upper",
        interpolation="none",
    )

    if show_diff_colorbar:
        fig.colorbar(
            diff_im, ax=axes[2], label="Under <-- diff --> Over", shrink=0.7, pad=0.05
        )

    legend_handles = [over_patch, under_patch]
    if show_edge_on_diff:
        axes[2].contour(
            diag_dict["ice_model"], levels=[0.5], colors="red", linewidths=1
        )
        axes[2].contour(
            diag_dict["ice_obs"], levels=[0.5], colors="limegreen", linewidths=1
        )
        legend_handles = [model_line, obs_line] + legend_handles

    axes[2].legend(handles=legend_handles, loc="lower left", fontsize=10)
    axes[2].set_title("Spatial Difference")
    axes[2].set_facecolor("#F1F5F7")

    # Turn off ticks and ticklabels
    axes[2].set_xticks([])
    axes[2].set_yticks([])
    axes[2].tick_params(
        axis="both", bottom=False, left=False, labelbottom=False, labelleft=False
    )

    box_ref = axes[1].get_position()
    box_diff = axes[2].get_position()
    axes[2].set_position([box_diff.x0, box_ref.y0, box_ref.width, box_ref.height])

    # --- METRICS TEXT BOX ---
    if metrics_dict is not None:
        metrics_text = (
            f"IIEE Total Area: {metrics_dict['iiee_total_area_km2'] / 1e6:.2f} M km²\n"
            f"Overestimated: {metrics_dict['iiee_overestimated_km2'] / 1e6:.2f} M km²\n"
            f"Underestimated: {metrics_dict['iiee_underestimated_km2'] / 1e6:.2f} M km²"
        )
        fig.text(
            0.85,
            0.97,
            metrics_text,
            fontsize=12,
            va="top",
            ha="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="gray"),
        )

    title = f"Sea Ice Evaluation: {time_label}"
    if identifier:
        title += f"\n{identifier.replace('_', ', ')}"
    plt.suptitle(title, fontsize=16, y=0.98)

    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, bbox_inches="tight", dpi=150)
        plt.close()
    else:
        plt.show()


def plot_iiee_seasonal_cycle(
    metrics_data,
    title="Monthly IIEE",
    save_path=None,
    identifier=None,
):
    """
    Plot the seasonal cycle of monthly IIEE metrics.

    Parameters
    ----------
    metrics_data : dict
        Either the full result dictionary returned by
        ``calc_iiee_annual_cycle`` or the nested monthly metrics dictionary.
    title : str, optional
        Title of the plot.
    save_path : str, optional
        If provided, save the figure to this path.
    identifier : str, optional
        If provided, it will be shown in the header
    """
    data_to_plot = (
        metrics_data["metrics"] if "metrics" in metrics_data else metrics_data
    )

    # Convert to DataFrame and scale units to Million km^2
    df = pd.DataFrame.from_dict(data_to_plot, orient="index") / 1e6

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        df.index,
        df["iiee_total_area_km2"],
        marker="o",
        label="Total IIEE",
        color="black",
        linewidth=2,
    )
    ax.plot(
        df.index,
        df["iiee_overestimated_km2"],
        marker="s",
        label="Overestimated",
        color="red",
        linestyle="--",
        alpha=0.8,
    )
    ax.plot(
        df.index,
        df["iiee_underestimated_km2"],
        marker="^",
        label="Underestimated",
        color="blue",
        linestyle="--",
        alpha=0.8,
    )

    if title:
        if identifier:
            title += f"\n{identifier.replace('_', ', ')}"
        ax.set_title(title, fontsize=14, fontweight="bold")

    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Area (Million km²)", fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(frameon=True, loc="upper right")
    ax.axhline(0, color="gray", linewidth=0.8, alpha=0.5)

    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, bbox_inches="tight", dpi=150)
        plt.close()
    else:
        plt.show()


def plot_iiee_all_months_grid(
    monthly_diagnostics,
    monthly_metrics=None,
    syear=None,
    eyear=None,
    save_path=None,
    show_edge_on_diff=False,
    show_diff_colorbar=False,
    identifier=None,
):
    """
    Plot all 12 climatological months in a single multi-panel figure.

    Parameters
    ----------
    monthly_diagnostics : dict
        Dictionary keyed by month number (1..12), where each value is the
        diagnostics dictionary returned by ``calc_iiee()``.
    monthly_metrics : dict, optional
        Dictionary keyed by month number (1..12), where each value is the
        metrics dictionary returned by ``calc_iiee()``.
    syear, eyear : int, optional
        Year range for title annotation.
    save_path : str, optional
        If provided, save the figure to this path.
    show_edge_on_diff : bool, optional
        If True, overlay model and obs ice edges on the difference panels.
    show_diff_colorbar : bool, optional
        If True, add a colorbar for the difference column.
    identifier : str, optional
        If provided, it will be shown in the header
    """
    fig, axes = plt.subplots(nrows=12, ncols=3, figsize=(12, 42))

    sic_cmap = plt.get_cmap("Blues_r").copy()
    sic_cmap.set_bad(color="#FFF9C4")

    diff_cmap = ListedColormap(["#000080", "#ADD8E6", "#C00707"])
    diff_cmap.set_bad(color="#FFF9C4")
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], diff_cmap.N)

    model_line = mlines.Line2D([], [], color="red", linewidth=1, label="Model Edge")
    obs_line = mlines.Line2D([], [], color="limegreen", linewidth=1, label="OBS Edge")
    over_patch = mpatches.Patch(color="#C00707", label="Overestimated Area")
    under_patch = mpatches.Patch(color="#000080", label="Underestimated Area")

    sic_im = None
    diff_im = None

    for month in range(1, 13):
        diag_dict = monthly_diagnostics[month]
        metrics_dict = (
            monthly_metrics.get(month) if monthly_metrics is not None else None
        )
        row = month - 1

        ax = axes[row, 0]
        sic_im = ax.imshow(
            diag_dict["model_sic"], cmap=sic_cmap, origin="upper", vmin=0, vmax=100
        )
        ax.contour(diag_dict["ice_model"], levels=[0.5], colors="red", linewidths=1)
        ax.set_facecolor("#ADD8E6")
        ax.set_xticks([])
        ax.set_yticks([])
        if row == 0:
            ax.set_title("Model SIC & Edge")
        ax.set_ylabel(f"Month {month}", fontsize=11)

        ax = axes[row, 1]
        ax.imshow(diag_dict["obs_sic"], cmap=sic_cmap, origin="upper", vmin=0, vmax=100)
        ax.contour(diag_dict["ice_obs"], levels=[0.5], colors="limegreen", linewidths=1)
        ax.set_facecolor("#ADD8E6")
        ax.set_xticks([])
        ax.set_yticks([])
        if row == 0:
            ax.set_title("OBS SIC & Edge")

        ax = axes[row, 2]
        diff_im = ax.imshow(
            diag_dict["ice_diff"],
            cmap=diff_cmap,
            norm=norm,
            origin="upper",
            interpolation="none",
        )
        if show_edge_on_diff:
            ax.contour(diag_dict["ice_model"], levels=[0.5], colors="red", linewidths=1)
            ax.contour(
                diag_dict["ice_obs"], levels=[0.5], colors="limegreen", linewidths=1
            )
        ax.set_facecolor("#F1F5F7")
        ax.set_xticks([])
        ax.set_yticks([])
        if row == 0:
            ax.set_title("Spatial Difference")

        if metrics_dict is not None:
            metrics_text = (
                f"Total: {metrics_dict['iiee_total_area_km2'] / 1e6:.2f}\n"
                f"Over: {metrics_dict['iiee_overestimated_km2'] / 1e6:.2f}\n"
                f"Under: {metrics_dict['iiee_underestimated_km2'] / 1e6:.2f}"
            )
            ax.text(
                0.98,
                0.98,
                metrics_text,
                transform=ax.transAxes,
                fontsize=8,
                va="top",
                ha="right",
                bbox=dict(
                    boxstyle="round",
                    facecolor="white",
                    alpha=0.75,
                    edgecolor="gray",
                ),
            )

    if syear is not None and eyear is not None:
        title = f"Sea Ice Evaluation for Monthly Climatology, {syear}-{eyear}"
    else:
        title = "Sea Ice Evaluation for Monthly Climatology"

    if identifier:
        title += f"\n{identifier.replace('_', ', ')}"

    fig.suptitle(title, fontsize=18, y=0.975)

    fig.legend(
        handles=[model_line, obs_line, over_patch, under_patch],
        loc="upper center",
        ncol=4,
        frameon=True,
        bbox_to_anchor=(0.5, 0.961),
    )

    # Reserve explicit top and bottom space
    plt.tight_layout(rect=[0, 0.06, 1, 0.965], w_pad=0.05)

    # Force draw so axes positions are finalized
    fig.canvas.draw()

    # Dedicated horizontal colorbar axis under columns 1 and 2
    left = axes[-1, 0].get_position().x0
    right = axes[-1, 1].get_position().x1
    cbar_bottom = 0.045
    cbar_height = 0.012
    cax = fig.add_axes([left, cbar_bottom, right - left, cbar_height])

    if sic_im is not None:
        cbar = fig.colorbar(sic_im, cax=cax, orientation="horizontal")
        cbar.set_label("Sea Ice Concentration (%)")

    if show_diff_colorbar and diff_im is not None:
        fig.colorbar(
            diff_im,
            ax=axes[:, 2],
            orientation="vertical",
            shrink=0.98,
            pad=0.01,
            label="Under <-- diff --> Over",
        )

    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, bbox_inches="tight", dpi=150)
        plt.close()
    else:
        plt.show()


def validate_inputs(ds_obs, ds_model, obs_data_var, model_data_var):
    """
    Validate the input datasets for annual-cycle processing.

    Parameters
    ----------
    ds_obs : xarray.Dataset
        Observational dataset.
    ds_model : xarray.Dataset
        Model dataset.
    obs_data_var : str
        Observational SIC variable name.
    model_data_var : str
        Model SIC variable name.

    Raises
    ------
    ValueError
        If required variables or coordinates are missing.
    """
    if obs_data_var not in ds_obs.data_vars:
        raise ValueError(
            f"Required observational data variable '{obs_data_var}' not found."
        )
    if "status_flag" not in ds_obs.data_vars:
        raise ValueError(
            "Required observational data variable 'status_flag' not found."
        )
    if model_data_var not in ds_model.data_vars:
        raise ValueError(f"Required model data variable '{model_data_var}' not found.")

    if "time" not in ds_obs.coords and "time" not in ds_obs.variables:
        raise ValueError("Required observational coordinate 'time' not found.")
    if "time" not in ds_model.coords and "time" not in ds_model.variables:
        raise ValueError("Required model coordinate 'time' not found.")

    get_coordinate_names(ds_obs)
    get_coordinate_names(ds_model)


def validate_monthly_inputs(obs_data, model_data, obs_data_var, model_data_var):
    """
    Validate monthly input datasets for single-field IIEE calculation.

    Parameters
    ----------
    obs_data : xarray.Dataset
        Monthly observational dataset.
    model_data : xarray.Dataset
        Monthly model dataset.
    obs_data_var : str
        Observational SIC variable name.
    model_data_var : str
        Model SIC variable name.

    Raises
    ------
    ValueError
        If required fields are missing.
    """
    for name in [obs_data_var, "status_flag"]:
        if name not in obs_data.data_vars and name not in obs_data.variables:
            raise ValueError(f"Required observational field '{name}' not found.")

    if (
        model_data_var not in model_data.data_vars
        and model_data_var not in model_data.variables
    ):
        raise ValueError(f"Required model field '{model_data_var}' not found.")

    get_coordinate_names(obs_data)
    get_coordinate_names(model_data)


def check_sic_units(obs_sic, model_sic):
    """
    Warn if sea ice concentration values appear to be fractional instead of percent.

    Parameters
    ----------
    obs_sic : xarray.DataArray
        Observational sea ice concentration.
    model_sic : xarray.DataArray
        Model sea ice concentration.
    """
    try:
        obs_max = float(np.nanmax(obs_sic.values))
        model_max = float(np.nanmax(model_sic.values))

        if obs_max <= 1.0:
            warnings.warn(
                "Observed SIC appears to be in fractional units rather than percent."
            )
        if model_max <= 1.0:
            warnings.warn(
                "Model SIC appears to be in fractional units rather than percent."
            )
    except Exception:
        pass


def parse_args():
    """
    Parse command-line arguments for development or standalone execution.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Compute monthly climatological IIEE from observed and model sea ice concentration datasets."
    )
    parser.add_argument(
        "--obs-file", required=True, help="Path to observational dataset."
    )
    parser.add_argument(
        "--model-files", required=True, help="Glob pattern or path for model files."
    )
    parser.add_argument(
        "--obs-data-var",
        default="ice_conc",
        help="Observational sea ice concentration variable name.",
    )
    parser.add_argument(
        "--model-data-var",
        default="siconc",
        help="Model sea ice concentration variable name.",
    )
    parser.add_argument(
        "--syear", type=int, default=1988, help="Start year, inclusive."
    )
    parser.add_argument("--eyear", type=int, default=2014, help="End year, inclusive.")
    parser.add_argument(
        "--save-dir",
        default="output",
        help="Directory for output figures and JSON metrics.",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print extra diagnostic output."
    )
    return parser.parse_args()


def main():
    """
    Development and CLI entry point.

    This wrapper parses command-line arguments, opens the observational and
    model datasets, calls ``calc_iiee_annual_cycle()``, appends file path
    metadata to the returned results, and writes the metrics to JSON.

    Example package usage
    ---------------------
    This function is mainly intended for development testing or command-line
    execution. In package usage, call ``calc_iiee_annual_cycle()`` directly:

    >>> import xcdat as xc
    >>> ds_obs = xc.open_dataset("data/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc")
    >>> ds_model = xc.open_mfdataset("data/siconc_SImon_E3SM-1-0_historical_r1i1p1f1_*_*.nc")
    >>> from pcmdi_metrics.sea_ice import calc_iiee_annual_cycle
    >>> result = calc_iiee_annual_cycle(
    ...     ds_obs=ds_obs,
    ...     ds_model=ds_model,
    ...     obs_data_var="ice_conc",
    ...     model_data_var="siconc",
    ...     syear=2010,
    ...     eyear=2014,
    ...     save_dir="output",
    ... )

    Example CLI usage
    -----------------
    Run this module as a script and provide input arguments from the command line:

    >>> python sea_ice_iiee.py \\
    ...   --obs-file data/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc \\
    ...   --model-files "data/siconc_SImon_E3SM-1-0_historical_r1i1p1f1_*_*.nc" \\
    ...   --obs-data-var ice_conc \\
    ...   --model-data-var siconc \\
    ...   --syear 2010 \\
    ...   --eyear 2014 \\
    ...   --save-dir output
    """
    args = parse_args()

    ds_obs = xc.open_dataset(args.obs_file)
    ds_model = xc.open_mfdataset(args.model_files)

    result = calc_iiee_annual_cycle(
        ds_obs=ds_obs,
        ds_model=ds_model,
        obs_data_var=args.obs_data_var,
        model_data_var=args.model_data_var,
        syear=args.syear,
        eyear=args.eyear,
        save_dir=args.save_dir,
        debug=args.debug,
    )

    result["metadata"].update(
        {
            "obs_file": args.obs_file,
            "model_files": args.model_files,
        }
    )

    os.makedirs(args.save_dir, exist_ok=True)
    with open(os.path.join(args.save_dir, "metrics.json"), "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
