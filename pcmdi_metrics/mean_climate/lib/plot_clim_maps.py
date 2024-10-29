import os
from typing import Optional

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import matplotlib as mpl
import numpy as np
import xarray as xr
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm

from pcmdi_metrics.stats import cor_xy, mean_xy, rms_xy, seasonal_mean

from .colormap import colormap_WhiteBlueGreenYellowRed
from .load_and_regrid import extract_level


def plot_climatology_diff(
    ds_test: xr.Dataset,
    data_var_test: str,
    ds_ref: xr.Dataset,
    data_var_ref: str,
    level: Optional[int] = None,
    season: str = "AC",
    map_projection: str = "PlateCarree",
    output_dir: str = ".",
    output_filename: Optional[str] = None,
    dataname_test: Optional[str] = None,
    dataname_ref: Optional[str] = None,
    variable_long_name: Optional[str] = None,
    units: Optional[str] = None,
    period: Optional[str] = None,
    figsize: tuple = (5, 10),
    fig_title: Optional[str] = None,
) -> None:
    if dataname_test is None:
        dataname_test = _get_source_id(ds_test, "")

    if dataname_ref is None:
        dataname_ref = _get_source_id(ds_ref, "")

    # Create a deep copy of the dataset and assign it back to the same
    # variable name to avoid original dataset to be modified
    ds_test = ds_test.copy(deep=True)
    ds_ref = ds_ref.copy(deep=True)

    # Extract specified level if provided
    if level is not None:
        level = int(level)
        if "plev" in list(ds_test.sizes):
            ds_test = extract_level(ds_test, level)
        if "plev" in list(ds_ref.sizes):
            ds_ref = extract_level(ds_ref, level)

    # Apply unit conversions for specific variables
    ds_test[data_var_test] = _apply_variable_units_conversion(ds_test, data_var_test)
    ds_ref[data_var_ref] = _apply_variable_units_conversion(ds_ref, data_var_ref)

    ds_test_season = _extract_seasonal_mean(ds_test, data_var_test, season)
    ds_ref_season = _extract_seasonal_mean(ds_ref, data_var_ref, season)

    # Retrieve variable attributes
    long_name, units, period_test = _get_variable_attributes(
        ds_test, data_var_test, variable_long_name, units, period
    )

    long_name, units, period_ref = _get_variable_attributes(
        ds_ref, data_var_ref, variable_long_name, units, period
    )

    # Prepare variable information string
    var_info_str = ""
    separator = ", "
    if long_name:
        var_info_str += f"Variable: {_wrap_text(long_name)}"
    if units:
        var_info_str += f"{separator}Units: {units}"
    if period is not None:
        if len(period) > 0:
            var_info_str += f"{separator}Period: {period}"

    # Set up a figure
    nrow, ncol = 3, 1
    figsize = (5, 10)
    fig = plt.figure(figsize=figsize)

    # Optimize layout
    plt.subplots_adjust(top=0.86)

    contour_levels, cmap, cmap_ext, norm = _prepare_colorbar_settings(
        ds_test, data_var_test, level
    )

    (
        contour_levels_diff,
        cmap_diff,
        cmap_diff_ext,
        norm_diff,
    ) = _prepare_colorbar_settings(ds_test, data_var_test, level, diff=True)

    proj = _prepare_map_projection_settings(map_projection)

    for idx in [1, 2, 3]:
        if idx in [1, 2]:
            if idx == 1:
                da_plot = ds_test_season[data_var_test].copy()
                title = f"(a) {dataname_test.replace('_', ' ')}"
                data_var = data_var_test
            elif idx == 2:
                da_plot = ds_ref_season[data_var_ref].copy()
                title = f"(b) {dataname_ref.replace('_', ' ')}"
                data_var = data_var_ref
            contour_levels_plot = contour_levels
            cmap_plot = cmap
            cmap_ext_plot = cmap_ext
            norm_plot = norm
        else:
            da_plot = (
                ds_test_season[data_var_test] - ds_ref_season[data_var_ref]
            ).copy()
            title = "(c) Difference (a - b)"
            data_var = data_var_test
            contour_levels_plot = contour_levels_diff
            cmap_plot = cmap_diff
            cmap_ext_plot = cmap_diff_ext
            norm_plot = norm_diff

        ax = fig.add_subplot(nrow, ncol, idx, projection=proj)

        # Set the global extent to cover the entire globe regardless of region that data exists
        ax.set_global()

        ax.contourf(
            da_plot.lon,
            da_plot.lat,
            da_plot,
            transform=ccrs.PlateCarree(),
            levels=contour_levels_plot,
            extend=cmap_ext_plot,
            cmap=cmap_plot,
            norm=norm_plot,
        )

        ax.add_feature(cfeature.COASTLINE)

        # Add latitude/longitude grid lines
        _add_gridlines(ax)

        # Calculate and format min, max, and mean values
        min_value = float(da_plot.min())
        max_value = float(da_plot.max())
        mean_value = float(mean_xy(da_plot))
        mean_max_min_info_str = (
            f"Max {max_value:.2f}    Mean {mean_value:.2f}    Min {min_value:.2f}"
        )

        # Add titles and information to the plot
        ax.text(
            0.5,
            1.12,
            title,
            fontsize=11,
            horizontalalignment="center",
            verticalalignment="bottom",
            transform=ax.transAxes,
        )

        ax.text(
            0,
            1.01,
            _wrap_text(mean_max_min_info_str, max_length=60),
            fontsize=9,
            horizontalalignment="left",
            verticalalignment="bottom",
            transform=ax.transAxes,
        )

        # Add colorbar
        _add_colorbar(
            fig,
            ax,
            1,
            contour_levels_plot,
            norm_plot,
            cmap_plot,
            cmap_ext_plot,
            data_var,
            units,
            colorbar_tick_label_fontsize=8,
            colorbar_label_fontsize=10,
        )

        # Add period
        if idx == 1:
            period = period_test
        elif idx == 2:
            period = period_ref

        if period is not None:
            if len(period) > 0:
                ax.text(
                    1,
                    1,
                    f"Period: {period}",
                    fontsize=7,
                    color="grey",
                    horizontalalignment="right",
                    verticalalignment="bottom",
                    transform=ax.transAxes,
                )

        # Add statistics
        if idx == 3:
            info_stats = ""
            # RMSE
            try:
                rmse = rms_xy(
                    ds_test_season[data_var_test], ds_ref_season[data_var_ref]
                )
                info_stats += f"RMSE {rmse:.2f}"
            except Exception as e:
                print(f"Error computing RMSE: {e}")
                rmse = None
            # Pattern correlation
            try:
                corr = cor_xy(
                    ds_test_season[data_var_test], ds_ref_season[data_var_ref]
                )
                info_stats += f"\nCORR {corr:.2f}"
            except Exception as e:
                print(f"Error computing correlation: {e}")
                corr = None
            # Show the numbers
            ax.text(
                0.97,
                -0.04,
                info_stats,
                fontsize=8.5,
                horizontalalignment="left",
                verticalalignment="top",
                transform=ax.transAxes,
            )

    # Title and further text info
    # ---------------------------
    # Optimize layout
    # plt.subplots_adjust(top=0.85)

    # Set title for the entire figure
    if fig_title is None:
        fig_title = f"Climatology ({season}): {data_var_test}"

    if level is not None:
        fig_title += f", {level} hPa"

    plt.suptitle(fig_title, fontsize=14, y=0.95)

    # Add additional detailed information if plotting all seasons
    plt.gcf().text(
        0.5,
        0.905,
        var_info_str,
        fontsize=9,
        color="grey",
        horizontalalignment="center",
        verticalalignment="bottom",
    )

    # Save the plot
    # -------------
    # Define output file name if not provided
    if output_filename is None:
        if level is None:
            output_filename_head = f"{data_var}"
        else:
            output_filename_head = f"{data_var}-{level}"

        output_filename = f"{output_filename_head}_{_split_and_join(dataname_test)}_{period_test}_{season}_vs_{_split_and_join(dataname_ref)}.png"

    # Save and show plot
    plt.savefig(os.path.join(output_dir, output_filename), bbox_inches="tight", dpi=150)


def plot_climatology(
    ds: xr.Dataset,
    data_var: str,
    level: Optional[int] = None,
    season_to_plot: str = "all",
    map_projection: str = "PlateCarree",
    output_dir: str = ".",
    output_filename: Optional[str] = None,
    variable_long_name: Optional[str] = None,
    units: Optional[str] = None,
    period: Optional[str] = None,
) -> None:
    """
    Plot climatology of a specified variable over defined seasons.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset containing the variable to plot.
    data_var : str
        The name of the variable to plot (e.g., 'pr' for precipitation).
    level : Optional[int], optional
        The vertical level to extract from the dataset, if applicable.
    season_to_plot : str, optional
        The season to plot ('all', 'AC', 'DJF', 'MAM', 'JJA', 'SON'). Default is 'all'.
    map_projection : str, optional
        The map projection to use ('PlateCarree', 'Robinson'). Default is 'PlateCarree'.
    output_dir : str, optional
        The directory to save the output plot. Default is the current directory.
    output_filename : Optional[str], optional
        The filename for the output plot. If None, a default filename will be generated.
    variable_long_name : str, optional
        The long name of the variable to use in the plot title. If None, the
        variable name will be extracted from dataset attributes if exist. Default is None.
    units : str, optional
        The units of the variable to use in the plot title. If None, the
        variable units will be extracted from dataset attributes if exist. Default is None.
    period : str, optional
        The period to plot (e.g., '1981-2010'). If None, the
        period will be extracted from dataset attributes if exist. Default is None.

    Raises
    ------
    ValueError
        If `season_to_plot` or `map_projection` is not valid.

    Notes
    -----
    The function calculates seasonal means and generates a contour plot for the specified variable.
    """
    # Create a deep copy of the dataset and assign it back to the same
    # variable name (ds) to avoid original dataset to be modified
    ds = ds.copy(deep=True)

    # Define available seasons
    available_seasons = ["AC", "DJF", "MAM", "JJA", "SON"]

    # Handle seasons input
    seasons = _validate_season_input(season_to_plot, available_seasons)

    # Extract specified level if provided
    if level is not None:
        level = int(level)
        if "plev" in list(ds.sizes):
            ds = extract_level(ds, level)

    # Apply unit conversions for specific variables
    ds[data_var] = _apply_variable_units_conversion(ds, data_var)

    # Precalculate seasonal means
    ds_season_dict = _extract_seasonal_means(ds, data_var)

    # Retrieve variable attributes
    long_name, units, period = _get_variable_attributes(
        ds, data_var, variable_long_name, units, period
    )

    # Prepare variable information string
    var_info_str = ""
    separator1 = "\n\n" if season_to_plot == "all" else ", "
    separator2 = "\n\n" if season_to_plot == "all" else "\n"
    if long_name:
        var_info_str += f"Variable: {_wrap_text(long_name)}{separator1}"
    if units:
        var_info_str += f"Units: {units}{separator1}"
    if period:
        var_info_str += f"Period: {period}{separator2}"

    # Set up a figure
    if season_to_plot.lower() == "all":
        nrow, ncol = 3, 2
        info_x, info_y = 0.57, 0.85
        figsize = (11, 9)
    else:
        nrow, ncol = 1, 1
        idx = 1
        info_x, info_y = 0.1, 0.8
        figsize = (9, 6)

    fig = plt.figure(figsize=figsize)

    contour_levels, cmap, cmap_ext, norm = _prepare_colorbar_settings(
        ds, data_var, level
    )

    proj = _prepare_map_projection_settings(map_projection)

    # Dictionary of seasons for dynamic plotting
    seasons_dict = {
        "AC": {"title": "Annual Mean", "panel_index": 1},
        "DJF": {"title": "DJF", "panel_index": 3},
        "MAM": {"title": "MAM", "panel_index": 4},
        "JJA": {"title": "JJA", "panel_index": 5},
        "SON": {"title": "SON", "panel_index": 6},
    }

    # Loop through subplots
    for season in seasons:
        if season_to_plot.lower() == "all":
            idx = seasons_dict[season]["panel_index"]
        else:
            idx = 1

        title = seasons_dict[season]["title"]
        da_season = ds_season_dict[season][data_var]

        ax = fig.add_subplot(nrow, ncol, idx, projection=proj)

        # Set the global extent to cover the entire globe regardless of region that data exists
        ax.set_global()

        ax.contourf(
            da_season.lon,
            da_season.lat,
            da_season,
            transform=ccrs.PlateCarree(),
            levels=contour_levels,
            extend=cmap_ext,
            cmap=cmap,
            norm=norm,
        )
        ax.add_feature(cfeature.COASTLINE)

        # Add latitude/longitude grid lines
        _add_gridlines(ax)

        # Calculate and format min, max, and mean values
        min_value = float(da_season.min())
        max_value = float(da_season.max())
        mean_value = float(mean_xy(da_season))
        mean_max_min_info_str = (
            f"Max {max_value:.2f}    Mean {mean_value:.2f}    Min {min_value:.2f}"
        )

        # Add titles and information to the plot
        if season_to_plot == "all":
            ax.text(
                0.5,
                1.12,
                title,
                fontsize=15,
                horizontalalignment="center",
                verticalalignment="bottom",
                transform=ax.transAxes,
            )
            ax.text(
                0.5,
                1.01,
                mean_max_min_info_str,
                horizontalalignment="center",
                verticalalignment="bottom",
                transform=ax.transAxes,
            )
        else:
            var_info_str += mean_max_min_info_str
            ax.text(
                0.5,
                1.01,
                var_info_str,
                fontsize=15,
                horizontalalignment="center",
                verticalalignment="bottom",
                transform=ax.transAxes,
            )

    # Add colorbar
    _add_colorbar(
        fig,
        ax,
        len(seasons),
        contour_levels,
        norm,
        cmap,
        cmap_ext,
        data_var,
        units,
    )

    # Title and further text info
    # ---------------------------
    # Set title for the entire figure
    if season_to_plot.lower() != "all":
        title_str = f"{season_to_plot} Climatology: {data_var}"
    else:
        title_str = f"Climatology: {data_var}"

    if level is not None:
        title_str += f", {level} hPa"

    source_id = _get_source_id(ds)
    if source_id:
        title_str += f", {source_id}"

    plt.suptitle(title_str, fontsize=23, y=0.95)

    # Add additional detailed information if plotting all seasons
    if season_to_plot == "all":
        plt.gcf().text(
            info_x,
            info_y,
            var_info_str,
            fontsize=13,
            horizontalalignment="left",
            verticalalignment="top",
        )

    # Save the plot
    # -------------
    # Define output file name if not provided
    if output_filename is None:
        if level is None:
            output_filename = f"{data_var}_{source_id}_{period}_{season_to_plot}.png"
        else:
            output_filename = (
                f"{data_var}-{level}_{source_id}_{period}_{season_to_plot}.png"
            )

    # Save and show plot
    plt.savefig(os.path.join(output_dir, output_filename), bbox_inches="tight", dpi=150)


# ================
# Helper functions
# ================


def _validate_season_input(season_to_plot, available_seasons):
    if season_to_plot.lower() == "all":
        return available_seasons
    elif season_to_plot.upper() in available_seasons:
        return [season_to_plot.upper()]
    else:
        raise ValueError(
            f"Invalid season_to_plot '{season_to_plot}'. Choose from 'all', {', '.join(available_seasons)}"
        )


def _apply_variable_units_conversion(ds, data_var):
    """Apply unit conversion based on the variable type."""
    units = ds[data_var].attrs.get("units", "")
    conversion_factor = 1

    if data_var == "pr":
        if units not in ["mm/day", "mm d-1"]:
            conversion_factor = 86400  # Convert kg/m²/s to mm/day
            ds[data_var].attrs["units"] = "mm/day"
            ds[data_var].attrs["long_name"] = "Precipitation"
    elif data_var == "psl" and ds[data_var].max() > 100000:
        if units not in ["hPa"]:
            conversion_factor = 0.01  # Convert Pa to hPa
            ds[data_var].attrs["units"] = "hPa"
            ds[data_var].attrs["long_name"] = "Sea Level Pressure"

    # Store original attributes
    original_attrs = ds[data_var].attrs

    # Perform the operation
    ds[data_var] = ds[data_var] * conversion_factor

    # Re-assign the original attributes
    ds[data_var].attrs = original_attrs

    return ds[data_var]


def _extract_seasonal_mean(ds: xr.Dataset, data_var: str, season: str) -> xr.Dataset:
    if season.upper() == "AC":
        return ds.mean(dim="time")
    else:
        return seasonal_mean(ds, season, data_var)


def _extract_seasonal_means(ds: xr.Dataset, data_var: str) -> dict:
    """
    Extract seasonal means for the specified variable from the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset containing the variable.
    data_var : str
        The name of the variable to extract seasonal means for.

    Returns
    -------
    dict
        A dictionary containing seasonal means for 'AC', 'DJF', 'MAM', 'JJA', and 'SON'.
    """
    return {
        "AC": ds.mean(dim="time"),
        "DJF": seasonal_mean(ds, "DJF", data_var),
        "MAM": seasonal_mean(ds, "MAM", data_var),
        "JJA": seasonal_mean(ds, "JJA", data_var),
        "SON": seasonal_mean(ds, "SON", data_var),
    }


def _get_variable_attributes(ds, data_var, variable_long_name, units, period):
    """Retrieve or set default variable attributes for the plot."""
    long_name = variable_long_name or ds[data_var].attrs.get("long_name", data_var)
    units = units or ds[data_var].attrs.get("units", "")
    period = period or ds.attrs.get("period", "")
    return long_name, units, period


def _prepare_colorbar_settings(ds, data_var, level, diff=False):
    """Set up plot properties such as levels, and colormap."""
    contour_levels, cmap, cmap_ext = _load_variable_setting(
        ds, data_var, level, diff=diff
    )
    norm = BoundaryNorm(boundaries=contour_levels, ncolors=cmap.N)
    return contour_levels, cmap, cmap_ext, norm


def _prepare_map_projection_settings(map_projection, central_longitude=180):
    """Set up plot projection."""
    if map_projection == "PlateCarree":
        proj = ccrs.PlateCarree(central_longitude=central_longitude)
    elif map_projection == "Robinson":
        proj = ccrs.Robinson(central_longitude=central_longitude)
    else:
        raise ValueError(
            f"Invalid map_projection '{map_projection}'. Choose 'PlateCarree' or 'Robinson'."
        )
    return proj


def _get_source_id(ds, unknown_return=None):
    """Get the source ID from the dataset."""
    return ds.attrs.get("source_id", unknown_return)


def _add_gridlines(ax):
    """Add latitude and longitude gridlines."""
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=1,
        color="gray",
        alpha=0.5,
        linestyle=":",
    )
    gl.top_labels = False
    gl.left_labels = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {"size": 9, "color": "gray"}
    gl.ylabel_style = {"size": 9, "color": "gray"}


def _add_colorbar(
    fig,
    ax,
    num_panels,
    levels,
    norm,
    cmap,
    cmap_ext,
    data_var,
    units,
    colorbar_tick_label_fontsize=10,
    colorbar_label_fontsize=12,
):
    """Add a colorbar to the figure."""
    if num_panels > 1:
        # Optimize layout
        plt.subplots_adjust(right=0.9, top=0.85, hspace=0.4)
        # Add colorbar space
        cbar_ax = fig.add_axes(
            [0.92, 0.15, 0.02, 0.7]
        )  # if multi-panel figure, make a space for colorbar
        ax = None
    else:
        # if single panel figure, attach colorbar to the subplot.
        cbar_ax = fig.add_axes(
            [
                ax.get_position().x1 + 0.01,
                ax.get_position().y0,
                0.02,
                ax.get_position().height,
            ]
        )

    # When colorbar is extended, the extended part has the same color as its inner next.
    # Therefore, remove the outermost tick(s) in such cases.
    if cmap_ext == "max":
        ticks = levels[0:-1]
    elif cmap_ext == "both":
        ticks = levels[1:-1]
    else:
        ticks = levels

    cbar = fig.colorbar(
        mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
        ticks=ticks,
        cax=cbar_ax,
        extend=cmap_ext,
    )

    cbar.ax.tick_params(
        length=0,  # Length of the tick lines
        width=0,  # Width of the tick lines
        color="black",  # Color of the tick lines
        direction="out",  # Direction of the tick lines (in, out, or inout)
        labelsize=colorbar_tick_label_fontsize,
    )

    # Label the colorbar
    cbar.set_label(f"{data_var} ({units})", fontsize=colorbar_label_fontsize)


def _load_variable_setting(ds: xr.Dataset, data_var: str, level: int, diff=False):
    var_setting_dict = {
        "pr": {
            None: {
                "levels": [0, 0.5] + list(np.arange(1, 18, 1)),
                "levels_diff": [-5, -2, -1, -0.5, -0.2, 0, 0.2, 0.5, 1, 2, 5],
                "colormap": "WhiteBlueGreenYellowRed",
                "colormap_diff": "BrBG",
                "colormap_ext": "max",
            }
        },
        "prw": {
            None: {
                "levels": np.arange(0, 22, 1),
                "levels_diff": [-10, -5, -2, -1, -0.5, -0.2, 0, 0.2, 0.5, 1, 2, 5, 10],
                "colormap": "WhiteBlueGreenYellowRed",
                "colormap_diff": "BrBG",
                "colormap_ext": "max",
            }
        },
        "psl": {
            None: {
                "levels": np.arange(980, 1040, 5),
                "levels_diff": [-10, -5, -2, -1, -0.5, -0.2, 0, 0.2, 0.5, 1, 2, 5, 10],
                "colormap": cc.cm.rainbow,
                "colormap_diff": "BrBG",
            }
        },
        "rltcre": {
            None: {
                "levels": np.linspace(0, 50, 21),
                "levels_diff": np.linspace(-30, 30, 13),
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            }
        },
        "rlut": {
            None: {
                "levels": [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320],
                "levels_diff": [-50, -40, -30, -20, -10, -5, 5, 10, 20, 30, 40, 50],
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            }
        },
        "rstscre": {
            None: {
                "levels": np.linspace(-50, 50, 21),
                "levels_diff": np.linspace(-30, 30, 13),
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            }
        },
        "rsut": {
            None: {
                "levels": np.linspace(0, 300, 16),
                "levels_diff": np.linspace(-60, 60, 13),
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
                "colormap_ext": "max",
            }
        },
        "ta": {
            200: {
                "levels": np.arange(-70, -40, 2),
                "levels_diff": np.linspace(-20, 20, 21),
                "colormap": cc.cm.rainbow,
                "colormap_diff": "jet",
            },
            850: {
                "levels": np.arange(-35, 40, 5),
                "levels_diff": [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15],
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            },
        },
        "tauu": {
            None: {
                "levels": np.linspace(-0.1, 0.1, 11),
                "levels_diff": np.linspace(-0.1, 0.1, 11),
                "colormap": "PiYG_r",
                "colormap_diff": "RdBu_r",
            }
        },
        "tas": {
            None: {
                "levels": np.arange(-40, 45, 5),
                "levels_diff": [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15],
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            }
        },
        "ts": {
            None: {
                "levels": np.arange(-40, 45, 5),
                "levels_diff": [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15],
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            }
        },
        "ua": {
            200: {
                "levels": np.arange(-70, 80, 10),
                "levels_diff": np.linspace(-20, 20, 21),
                "colormap": "PiYG_r",
                "colormap_diff": "RdBu_r",
            },
            850: {
                "levels": [
                    -25,
                    -20,
                    -15,
                    -10,
                    -8,
                    -5,
                    -3,
                    -1,
                    1,
                    3,
                    5,
                    8,
                    10,
                    15,
                    20,
                    25,
                ],
                "levels_diff": [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15],
                "colormap": "PiYG_r",
                "colormap_diff": "RdBu_r",
            },
        },
        "va": {
            200: {
                "levels": np.linspace(-10, 10, 11),
                "levels_diff": np.linspace(-5, 5, 6),
                "colormap": "PiYG_r",
                "colormap_diff": "RdBu_r",
            },
            850: {
                "levels": np.linspace(-10, 10, 11),
                "levels_diff": np.linspace(-5, 5, 6),
                "colormap": "PiYG_r",
                "colormap_diff": "RdBu_r",
            },
        },
        "zg": {
            500: {
                "levels": np.arange(4800, 6000, 100),
                "levels_diff": np.linspace(-120, 120, 13),
                "colormap": cc.cm.rainbow,
                "colormap_diff": "RdBu_r",
            },
        },
    }

    # Check if the variable and level exist in the settings

    in_dict = False

    if data_var in var_setting_dict:
        if level in var_setting_dict[data_var]:
            settings = var_setting_dict[data_var][level]
            levels = settings["levels"]
            levels_diff = settings["levels_diff"]
            cmap = _get_colormap(settings["colormap"])
            cmap_diff = _get_colormap(settings["colormap_diff"])
            cmap_ext = settings.get("colormap_ext", "both")
            cmap_ext_diff = "both"
            in_dict = True

    # Use default settings if not found
    if not in_dict:
        vmin = float(ds[data_var].min())
        vmax = float(ds[data_var].max())
        levels = np.linspace(vmin, vmax, 21)
        levels_diff = np.linspace(vmin / 2.0, vmax / 2.0, 21)
        cmap = plt.get_cmap("jet")
        cmap_diff = plt.get_cmap("RdBu_r")
        cmap_ext = "both"
        cmap_ext_diff = "both"

    if diff:
        return levels_diff, cmap_diff, cmap_ext_diff

    return levels, cmap, cmap_ext


def _get_colormap(colormap):
    if isinstance(colormap, str):
        if colormap == "WhiteBlueGreenYellowRed":
            cmap = colormap_WhiteBlueGreenYellowRed()
        else:
            cmap = plt.get_cmap(colormap)
    else:
        cmap = colormap

    return cmap


def _wrap_text(text, max_length=20):
    """
    Wraps the input text to ensure each line does not exceed the specified max length.

    Parameters
    ----------
    text : str
        The input text string to be wrapped.
    max_length : int, optional
        The maximum length of each line (default is 20).

    Returns
    -------
    str
        The text string with line breaks after each segment of the specified length.

    Example
    -------
    >>> text = "This is a long string that needs to be wrapped because it exceeds 20 characters."
    >>> _wrap_text(text)
    'This is a long string\nthat needs to be wrappe\nd because it exceeds 20\ncharacters.'
    """
    lines = []

    # Break the string into chunks of max_length
    for i in range(0, len(text), max_length):
        lines.append(text[i : i + max_length])

    # Join lines with newline characters
    return "\n".join(lines)


def _split_and_join(dataname: str) -> str:
    """
    Splits the input string by commas, periods, and spaces, then joins the result with underscores.

    Parameters
    ----------
    dataname : str
        The input string to be split and joined.

    Returns
    -------
    str
        The modified string with parts joined by underscores.

    Example
    -------
    >>> _split_and_join("A,b c.d")
    'A_b_c_d'
    """
    # Split by comma, period, and space using regex
    import re

    parts = re.split(r"[ ,\.]+", dataname)

    # Join with underscore
    return "_".join(parts)
