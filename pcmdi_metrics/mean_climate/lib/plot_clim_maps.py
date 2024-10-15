import os
from typing import Optional

import cartopy
import matplotlib as mpl
import numpy as np
import xarray as xr
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap

from pcmdi_metrics.stats import seasonal_mean

from .load_and_regrid import extract_level  # noqa


def plot_climatology_driver(
    ds: xr.Dataset,
    data_var: str,
    level: Optional[int] = None,
    map_projection: str = "PlateCarree",
    output_dir: str = ".",
    output_filename: Optional[str] = None,
) -> None:
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
        gl.xlabel_style = {"size": 10, "color": "gray"}
        gl.ylabel_style = {"size": 10, "color": "gray"}

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

    # Optimize layout and add colorbar
    plt.subplots_adjust(right=0.9, top=0.85, hspace=0.4)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(
        mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, extend=cmap_ext
    )

    # Label the colorbar
    cbar.set_label(f"{data_var} ({units})", fontsize=12)

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

    # Define output file name if not provided
    if output_filename is None:
        output_filename = f"{data_var}_{source_id}_{period}_{season_to_plot}.png"

    # Save and show plot
    plt.savefig(os.path.join(output_dir, output_filename), bbox_inches="tight", dpi=150)


def _colormap_WhiteBlueGreenYellowRed():
    """
    Example
    -------
    # Create the colormap using LinearSegmentedColormap
    cmap = _colormap_WhiteBlueGreenYellowRed()

    # Display the colormap
    plt.figure(figsize=(6, 1))
    plt.imshow([[0, 1]], cmap=cmap)
    plt.gca().set_visible(False)
    plt.colorbar(orientation="horizontal")
    plt.show()
    """
    # Define the colors for the colormap
    colors = ["white", "steelblue", "green", "yellow", "orange", "red", "darkred"]
    # Create the colormap using LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("WhiteBlueGreenYellowRed", colors)
    return cmap


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


def _load_variable_setting(ds, data_var, level):
    var_setting_dict = {
        "pr": {
            None: {
                "vmin": 0,
                "vmax": 20,
                "levels": np.linspace(0, 20, 21),
                "colormap": _colormap_WhiteBlueGreenYellowRed(),
                "colormap_ext": "max",
            }
        },
        "ua": {
            850: {
                "vmin": -20,
                "vmax": 20,
                "levels": np.linspace(-20, 20, 21),
                "colormap": plt.get_cmap("PiYG_r"),
            }
        },
    }

    in_dict = False

    # Check if the variable and level exist in the settings
    if data_var in var_setting_dict:
        if level in var_setting_dict[data_var]:
            settings = var_setting_dict[data_var][level]
            levels = settings["levels"]
            cmap = settings["colormap"]
            cmap_ext = settings.get("colormap_ext", "both")
            in_dict = True

    # Use default settings if not found
    if not in_dict:
        vmin = float(ds[data_var].min())
        vmax = float(ds[data_var].max())
        levels = np.linspace(vmin, vmax, 20)
        cmap = plt.get_cmap("jet")
        cmap_ext = "both"

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
