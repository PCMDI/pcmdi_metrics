import os
from typing import Optional

import cartopy
import colorcet as cc
import matplotlib as mpl
import numpy as np
import xarray as xr
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm

from pcmdi_metrics.stats import seasonal_mean

from .colormap import colormap_WhiteBlueGreenYellowRed
from .load_and_regrid import extract_level


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
        ds = extract_level(ds, level)

    # Apply unit conversions for specific variables
    ds[data_var] = _apply_variable_units_conversion(ds, data_var)

    # Precalculate seasonal means
    data_season = _extract_seasonal_means(ds, data_var)

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

    fig, proj, levels, cmap, cmap_ext, norm = _prepare_plotting_settings(
        ds, data_var, map_projection, level, figsize
    )

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
        data = data_season[season][data_var]

        ax = fig.add_subplot(nrow, ncol, idx, projection=proj)
        ax.contourf(
            ds.lon,
            ds.lat,
            data,
            transform=cartopy.crs.PlateCarree(),
            levels=levels,
            extend=cmap_ext,
            cmap=cmap,
            norm=norm,
        )
        ax.add_feature(cartopy.feature.COASTLINE)

        # Add latitude/longitude grid lines
        _add_gridlines(ax)

        # Calculate and format min, max, and mean values
        min_value = float(data.min())
        max_value = float(data.max())
        mean_value = float(data_season[season].spatial.average(data_var)[data_var])
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
                0,
                1.01,
                mean_max_min_info_str,
                horizontalalignment="left",
                verticalalignment="bottom",
                transform=ax.transAxes,
            )
        else:
            var_info_str += mean_max_min_info_str
            ax.text(
                0,
                1.01,
                var_info_str,
                fontsize=15,
                horizontalalignment="left",
                verticalalignment="bottom",
                transform=ax.transAxes,
            )

    # Optimize layout
    if season_to_plot == "all":
        plt.subplots_adjust(right=0.9, top=0.85, hspace=0.4)

    # Add colorbar
    _add_colorbar(fig, ax, len(seasons), levels, norm, cmap, cmap_ext, data_var, units)

    # Title and further text info
    # ===========================
    # Set title for the entire figure
    if season_to_plot.lower() != "all":
        title_str = f"{season_to_plot} Climatology: {data_var}"
    else:
        title_str = f"Climatology: {data_var}"

    if level is not None:
        title_str += f", {level} hPa"

    if "source_id" in ds.attrs:
        source_id = ds.attrs["source_id"]
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
    # =============
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
    print("_apply_variable_units_conversion applied 123")


# Helper functions
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
    if data_var == "pr":
        conversion_factor = 86400  # Convert kg/m²/s to mm/day
        ds[data_var].attrs["units"] = "mm/day"
        ds[data_var].attrs["long_name"] = "Precipitation"
    elif data_var == "psl" and ds[data_var].max() > 100000:
        conversion_factor = 0.01  # Convert Pa to hPa
        ds[data_var].attrs["units"] = "hPa"
        ds[data_var].attrs["long_name"] = "Sea Level Pressure"
    else:
        conversion_factor = 1

    # Store original attributes
    original_attrs = ds[data_var].attrs

    # Perform the operation
    ds[data_var] = ds[data_var] * conversion_factor

    # Re-assign the original attributes
    ds[data_var].attrs = original_attrs

    return ds[data_var]


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


def _prepare_plotting_settings(ds, data_var, map_projection, level, figsize):
    """Set up plot properties such as levels, colormap, and projection."""
    fig = plt.figure(figsize=figsize)
    levels, cmap, cmap_ext = _load_variable_setting(ds, data_var, level)
    norm = BoundaryNorm(boundaries=levels, ncolors=cmap.N)

    if map_projection == "PlateCarree":
        proj = cartopy.crs.PlateCarree(central_longitude=180)
    elif map_projection == "Robinson":
        proj = cartopy.crs.Robinson(central_longitude=180)
    else:
        raise ValueError(
            f"Invalid map_projection '{map_projection}'. Choose 'PlateCarree' or 'Robinson'."
        )

    return fig, proj, levels, cmap, cmap_ext, norm


def _add_gridlines(ax):
    """Add latitude and longitude gridlines."""
    gl = ax.gridlines(
        crs=cartopy.crs.PlateCarree(),
        draw_labels=True,
        linewidth=2,
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


def _add_colorbar(fig, ax, num_panels, levels, norm, cmap, cmap_ext, data_var, units):
    """Add a colorbar to the figure."""
    if num_panels > 1:
        cbar_ax = fig.add_axes(
            [0.92, 0.15, 0.02, 0.7]
        )  # if multi-panel figure, make a space for colorbar
        ax = None
    else:
        # if single panel figure, attach colorbar to the subplot.
        cbar_ax = fig.add_axes([ax.get_position().x1+0.01,ax.get_position().y0,0.02,ax.get_position().height])

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
    )

    # Label the colorbar
    cbar.set_label(f"{data_var} ({units})", fontsize=12)


def _get_colormap(colormap):
    if isinstance(colormap, str):
        if colormap == "WhiteBlueGreenYellowRed":
            cmap = colormap_WhiteBlueGreenYellowRed()
        else:
            cmap = plt.get_cmap(colormap)
    else:
        cmap = colormap

    return cmap


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
                "levels": np.linspace(5000, 5800, 11),
                "levels_diff": np.linspace(-70, 70, 11),
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
