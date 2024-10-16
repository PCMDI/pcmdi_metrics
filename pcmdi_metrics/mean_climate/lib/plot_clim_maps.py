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

from .colormap import _colormap_WhiteBlueGreenYellowRed
from .load_and_regrid import extract_level


def plot_climatology_driver(
    ds: xr.Dataset,
    data_var: str,
    level: Optional[int] = None,
    map_projection: str = "PlateCarree",
    output_dir: str = ".",
    output_filename: Optional[str] = None,
) -> None:
    """
    Generate climatology plots for a specified variable over different seasons.

    This function iterates over a predefined list of seasons and calls the
    `plot_climatology` function to create and save climatology plots for
    the specified data variable from the provided dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The xarray dataset containing the data variable to be plotted.

    data_var : str
        The name of the variable in the dataset to plot.

    level : int, optional
        The vertical level to plot. If None, the function will plot data
        at all available levels. Default is None.

    map_projection : str, optional
        The map projection to use for the plots. Default is "PlateCarree".

    output_dir : str, optional
        The directory where the output plots will be saved. Default is the
        current directory ("./").

    output_filename : str, optional
        The base filename for the output plots. If None, a default naming
        convention will be used based on the variable and season. Default is None.

    Returns
    -------
    None
        This function does not return any value. It generates and saves
        plots to the specified output directory.

    Notes
    -----
    The function supports plotting for the following seasons:
    - "all" (This will generate 6 image files)
    - "AC" (Annual Cycle)
    - "DJF" (December, January, February)
    - "MAM" (March, April, May)
    - "JJA" (June, July, August)
    - "SON" (September, October, November)
    """
    season_to_plot = ["all", "AC", "DJF", "MAM", "JJA", "SON"]
    for season in season_to_plot:
        plot_climatology(
            ds,
            data_var,
            level=level,
            season_to_plot=season,
            map_projection=map_projection,
            output_dir=output_dir,
            output_filename=output_filename,
        )


def plot_climatology(
    ds: xr.Dataset,
    data_var: str,
    level: Optional[int] = None,
    season_to_plot: str = "all",
    map_projection: str = "PlateCarree",
    output_dir: str = ".",
    output_filename: Optional[str] = None,
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

    Raises
    ------
    ValueError
        If `season_to_plot` or `map_projection` is not valid.

    Notes
    -----
    The function calculates seasonal means and generates a contour plot for the specified variable.
    """

    # Define available seasons
    available_seasons = ["AC", "DJF", "MAM", "JJA", "SON"]

    # Determine seasons to plot
    if season_to_plot.lower() == "all":
        seasons = available_seasons
    elif season_to_plot.upper() in available_seasons:
        seasons = [season_to_plot.upper()]
    else:
        raise ValueError(
            f"season_to_plot {season_to_plot} is not valid. Available options are 'all', {', '.join(available_seasons)}"
        )

    # Extract specified level if provided
    if level is not None:
        ds = extract_level(ds, level)

    # Precalculate seasonal means
    data_season = _extract_seasonal_means(ds, data_var)

    # Retrieve variable attributes
    long_name = ds[data_var].attrs.get("long_name", None)
    units = ds[data_var].attrs.get("units", None)
    period = ds.attrs.get("period", None)

    # Adjust units for precipitation variable
    if data_var == "pr":

        def convert_units(da):
            return da * 86400  # Convert to mm/day

        long_name = "Precipitation"
        units = "mm/day"
    elif data_var == "psl":
        if ds[data_var].max() > 100000:

            def convert_units(da):
                return da / 100  # Convert to hPa

            long_name = "Sea Level Pressure"
            units = "hPa"
    else:

        def convert_units(da):
            return da

    # Prepare variable information string
    var_info_str = ""
    if long_name:
        var_info_str += f"Variable: {_wrap_text(long_name)}\n"
    if units:
        var_info_str += f"Units: {units}\n"
    if period:
        var_info_str += f"Period: {period}\n"

    # Set up figure
    fig = plt.figure(figsize=(11, 9))
    levels, cmap, cmap_ext = _load_variable_setting(ds, data_var, level)

    # Use BoundaryNorm for discrete color boundaries
    norm = BoundaryNorm(boundaries=levels, ncolors=cmap.N)

    # Set map projection
    if map_projection == "PlateCarree":
        proj = cartopy.crs.PlateCarree(central_longitude=180)
    elif map_projection == "Robinson":
        proj = cartopy.crs.Robinson(central_longitude=180)
    else:
        raise ValueError(
            f"map_projection {map_projection} is not valid. Available options: 'PlateCarree', 'Robinson'"
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
            nrow, ncol = 3, 2
            idx = seasons_dict[season]["panel_index"]
            info_x, info_y = 0.55, 0.75
        else:
            nrow, ncol = 1, 1
            idx = 1
            info_x, info_y = 0.1, 0.8

        title = seasons_dict[season]["title"]
        data = convert_units(data_season[season][data_var])

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

        # Calculate and format min, max, and mean values
        min_value = float(data.min())
        max_value = float(data.max())
        mean_value = convert_units(
            float(data_season[season].spatial.average(data_var)[data_var])
        )
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

    # Color bar
    # =========
    # Optimize layout and add colorbar
    plt.subplots_adjust(right=0.9, top=0.85, hspace=0.4)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])

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

    # Title and text info
    # ===================
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
        plt.gcf().text(info_x, info_y, var_info_str, fontsize=13)

    # Save
    # ====
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


def _get_colormap(colormap):
    if isinstance(colormap, str):
        if colormap == "WhiteBlueGreenYellowRed":
            cmap = _colormap_WhiteBlueGreenYellowRed()
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
                "colormap": "nipy_spectral",
                "colormap_diff": "RdBu_r",
            }
        },
        "rlut": {
            None: {
                "levels": np.linspace(100, 300, 21),
                "levels_diff": np.linspace(-30, 30, 13),
                "colormap": "nipy_spectral",
                "colormap_diff": "RdBu_r",
            }
        },
        "rstscre": {
            None: {
                "levels": np.linspace(-50, 50, 21),
                "levels_diff": np.linspace(-30, 30, 13),
                "colormap": "nipy_spectral",
                "colormap_diff": "RdBu_r",
            }
        },
        "rsut": {
            None: {
                "levels": np.linspace(0, 300, 16),
                "levels_diff": np.linspace(-60, 60, 13),
                "colormap": "nipy_spectral",
                "colormap_diff": "RdBu_r",
                "colormap_ext": "max",
            }
        },
        "ta": {
            200: {
                "levels": np.arange(-70, -40, 2),
                "levels_diff": np.linspace(-20, 20, 21),
                "colormap": "nipy_spectral",
                "colormap_diff": "jet",
            },
            850: {
                "levels": np.arange(-35, 40, 5),
                "levels_diff": [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15],
                "colormap": "nipy_spectral",
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
                "colormap": "nipy_spectral",
                "colormap_diff": "RdBu_r",
            }
        },
        "ts": {
            None: {
                "levels": np.arange(-40, 45, 5),
                "levels_diff": [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15],
                "colormap": "nipy_spectral",
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
                "colormap": "nipy_spectral",
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
