import os

import cartopy
import matplotlib as mpl
import numpy as np
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap

from pcmdi_metrics.stats import seasonal_mean


def load_variable_setting(ds, data_var):
    var_setting_dict = {
        "pr": {
            "vmin": 0,
            "vmax": 20,
            "levels": np.linspace(0, 20, 21),
            "colormap": colormap_WhiteBlueGreenYellowRed(),
        },
    }
    if data_var in var_setting_dict:
        vmin = var_setting_dict[data_var]["vmin"]
        vmax = var_setting_dict[data_var]["vmax"]
        levels = var_setting_dict[data_var]["levels"]
        cmap = var_setting_dict[data_var]["colormap"]
    else:
        vmin = float(ds[data_var].min())
        vmax = float(ds[data_var].max())
        levels = np.linspace(vmin, vmax, 20)
        cmap = plt.get_cmap("viridis")

    return levels, cmap


def colormap_WhiteBlueGreenYellowRed():
    """
    Example
    -------
    # Create the colormap using LinearSegmentedColormap
    cmap = colormap_WhiteBlueGreenYellowRed()

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


def plot_climatology_driver(
    ds, data_var, map_projection="PlateCarree", output_dir=".", output_filename=None
):
    season_to_plot = ["all", "AC", "DJF", "MAM", "JJA", "SON"]
    for season in season_to_plot:
        plot_climatology(
            ds,
            data_var,
            season,
            map_projection=map_projection,
            output_dir=output_dir,
            output_filename=output_filename,
        )


def plot_climatology(
    ds,
    data_var,
    season_to_plot="all",
    map_projection="PlateCarree",
    output_dir=".",
    output_filename=None,
):
    # Define seasons
    if season_to_plot.lower() == "all":
        seasons = ["AC", "DJF", "MAM", "JJA", "SON"]
    elif season_to_plot.upper() in ["AC", "DJF", "MAM", "JJA", "SON"]:
        seasons = [season_to_plot.upper()]
    else:
        raise ValueError(
            f"season_to_plot {season_to_plot} is not valid. Available options are 'all', 'AC', 'DJF', 'MAM', 'JJA', 'SON"
        )

    # Precalculate seasonal means
    data_season = {
        "AC": ds.mean(dim="time"),
        "DJF": seasonal_mean(ds, "DJF", data_var),
        "MAM": seasonal_mean(ds, "MAM", data_var),
        "JJA": seasonal_mean(ds, "JJA", data_var),
        "SON": seasonal_mean(ds, "SON", data_var),
    }

    if "long_name" in ds[data_var].attrs:
        long_name = ds[data_var].attrs["long_name"]
    else:
        long_name = None

    if "units" in ds[data_var].attrs:
        units = ds[data_var].attrs["units"]
    else:
        units = None

    if "period" in ds.attrs:
        period = ds.attrs["period"]
    else:
        period = None

    if data_var == "pr":

        def convert_units(da):
            return da * 86400

        long_name = "Precipitation"
        units = "mm/day"
    else:

        def convert_units(da):
            return da

    var_info_str = ""

    if long_name is not None:
        var_info_str += f"Variable: {wrap_text(long_name)}\n"

    if units is not None:
        var_info_str += f"Units: {units}\n"

    if period is not None:
        var_info_str += f"Period: {period}\n"

    # Set up figure
    fig = plt.figure(figsize=(11, 9))

    levels, cmap = load_variable_setting(ds, data_var)

    # Use BoundaryNorm for discrete color boundaries
    norm = BoundaryNorm(boundaries=levels, ncolors=cmap.N)
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
            nrow = 3
            ncol = 2
            idx = seasons_dict[season]["panel_index"]
            info_x = 0.55
            info_y = 0.75
        else:
            nrow = 1
            ncol = 1
            idx = 1
            info_x = 0.1
            info_y = 0.8

        title = seasons_dict[season]["title"]

        data = convert_units(data_season[season][data_var])

        ax = fig.add_subplot(nrow, ncol, idx, projection=proj)
        ax.contourf(
            ds.lon,
            ds.lat,
            data,
            transform=cartopy.crs.PlateCarree(),
            levels=levels,
            extend="both",
            cmap=cmap,
            norm=norm,
        )
        ax.add_feature(cartopy.feature.COASTLINE)

        # lat/lon grid lines
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

        min_value = float(data.min())
        max_value = float(data.max())
        mean_value = convert_units(
            float(data_season[season].spatial.average(data_var)[data_var])
        )
        mean_max_min_info_str = (
            f"Mean {mean_value:.3f}    Max {max_value:.3f}    Min {min_value:.3f}"
        )

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

    # Use constrained layout to optimize space
    plt.subplots_adjust(right=0.9, top=0.85, hspace=0.4)  # , wspace=-0.1)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(
        mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, extend="max"
    )

    # Label the colorbar
    cbar.set_label(f"{data_var} ({units})", fontsize=12)

    # Title
    if season_to_plot.lower() == "all":
        title_str = f"Climatology: {data_var}"
    else:
        title_str = f"{season_to_plot} Climatology: {data_var}"

    # Add source and period to title if available
    if "source_id" in ds.attrs:
        source_id = ds.attrs["source_id"]
        title_str += f", {source_id}"

    plt.suptitle(title_str, fontsize=23, y=0.95)

    # Add additional detailed information
    if season_to_plot == "all":
        plt.gcf().text(info_x, info_y, var_info_str, fontsize=13)

    # Define output file name if not given
    if output_filename is None:
        output_filename = f"{data_var}_{source_id}_{period}_{season_to_plot}.png"

    # Save and show plot
    plt.savefig(os.path.join(output_dir, output_filename), bbox_inches="tight", dpi=150)


def wrap_text(text, max_length=20):
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
    >>> wrap_text(text)
    'This is a long string\nthat needs to be wrappe\nd because it exceeds 20\ncharacters.'
    """
    lines = []

    # Break the string into chunks of max_length
    for i in range(0, len(text), max_length):
        lines.append(text[i : i + max_length])

    # Join lines with newline characters
    return "\n".join(lines)
