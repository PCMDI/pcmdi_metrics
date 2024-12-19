import faulthandler

import cartopy.crs as ccrs
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import xarray as xr
from cartopy.feature import LAND as cartopy_land
from cartopy.feature import OCEAN as cartopy_ocean
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

from pcmdi_metrics.io import get_latitude, get_longitude, get_time
from pcmdi_metrics.variability_mode.lib import debug_print

faulthandler.enable()

# -----------------------
# Main plotting functions
# -----------------------


def plot_map_multi_panel(
    mode: str,
    model: str,
    syear: int,
    eyear: int,
    season: str,
    obs_eof_pattern: xr.DataArray,
    obs_eof_pattern_global: xr.DataArray,
    obs_pc,
    model_eof_pattern: xr.DataArray,
    model_eof_pattern_global: xr.DataArray,
    model_pc,
    eof_variance_fraction: float,
    output_file_name: str = None,
    gridline=True,
    debug=False,
):
    # Validate input years
    if syear > eyear:
        raise ValueError("Start year must be less than or equal to end year.")

    # Determine projection
    proj = determine_projection(mode)
    projection = configure_projection_obj(proj, obs_eof_pattern, debug)

    proj_teleconnection = determine_projection(f"{mode}_teleconnection")
    projection_tel = configure_projection_obj(proj_teleconnection, debug)

    # Construct plot title
    plot_title = construct_plot_title(
        mode, model, syear, eyear, season, eof_variance_fraction
    )

    debug_print(
        f"plot_map: projections: {proj}, {proj_teleconnection}, plot_title: {plot_title}",
        debug,
    )

    # Set levels and maskout based on mode
    levels, maskout = set_levels_and_maskout(mode)

    # Set central longitude
    central_longitude = 0 if mode in ["AMO", "AMO_teleconnection"] else 180

    # Prepare data array
    obs_eof_pattern_data_array = obs_eof_pattern.where(obs_eof_pattern != 1e20, np.nan)
    obs_eof_pattern_global_data_array = obs_eof_pattern_global.where(
        obs_eof_pattern_global != 1e20, np.nan
    )
    model_eof_pattern_data_array = model_eof_pattern.where(
        model_eof_pattern != 1e20, np.nan
    )
    model_eof_pattern_global_data_array = model_eof_pattern_global.where(
        model_eof_pattern_global != 1e20, np.nan
    )

    # Generate plot
    # Create the figure and gridspec
    fig = plt.figure(figsize=(8, 6))
    gs = fig.add_gridspec(3, 2)

    # Create the subplots
    ax1 = fig.add_subplot(gs[0, 0], projection=projection)
    ax2 = fig.add_subplot(gs[0, 1], projection=projection)
    ax3 = fig.add_subplot(gs[1, 0], projection=projection_tel)
    ax4 = fig.add_subplot(gs[1, 1], projection=projection_tel)
    ax5 = fig.add_subplot(gs[2, :])

    debug_print("fig, ax done", debug)

    # Call the plotting function
    fig, ax1 = plot_map_cartopy(
        obs_eof_pattern_data_array,
        title=plot_title,
        proj=proj,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        central_longitude=central_longitude,
        fig=fig,
        ax=ax1,
        debug=debug,
    )

    fig, ax2 = plot_map_cartopy(
        model_eof_pattern_data_array,
        title=plot_title,
        proj=proj,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        central_longitude=central_longitude,
        fig=fig,
        ax=ax2,
        debug=debug,
    )

    fig, ax3 = plot_map_cartopy(
        obs_eof_pattern_global_data_array,
        title=plot_title,
        proj=proj_teleconnection,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        central_longitude=central_longitude,
        fig=fig,
        ax=ax3,
        debug=debug,
    )

    fig, ax4 = plot_map_cartopy(
        model_eof_pattern_global_data_array,
        title=plot_title,
        proj=proj_teleconnection,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        central_longitude=central_longitude,
        fig=fig,
        ax=ax4,
        debug=debug,
    )

    if debug:
        print("obs_pc:", obs_pc)
        print("model_pc:", model_pc)
    time = get_time(obs_pc)
    plot_time_series_with_variance(ax5, time, obs_pc, model_pc)

    # Done, save figure
    if output_file_name is not None:
        debug_print("plot done, save figure as " + output_file_name, debug)
        fig.savefig(output_file_name)

    plt.close("all")


def plot_map(
    mode: str,
    model: str,
    syear: int,
    eyear: int,
    season: str,
    eof_pattern: xr.DataArray,
    eof_variance_fraction: float,
    output_file_name: str = None,
    gridline=True,
    debug=False,
):
    """
    Plot a dive down map and save the output.

    This function generates a plot of the EOF pattern for a specified variability mode
    and saves it as an image file. The plot includes information about the model,
    analysis period, and season.

    Parameters
    ----------
    mode : str
        The mode to plot (e.g., "NAO" or "NAO_teleconnection").
    model : str
        The name of the model or reference dataset to be displayed in the figure title.
    syear : int
        The start year for the analysis.
    eyear : int
        The end year for the analysis.
    season : str
        The season used for analysis, which will be shown in the figure title.
        Options include "DJF", "MAM", "JJA", "SON", "monthly", or "yearly".
    eof_pattern : xr.DataArray
        The EOF pattern of the variability mode, represented as a 2D xarray DataArray
        with latitude and longitude coordinates.
    eof_variance_fraction : float
        The fraction of explained variability (between 0 and 1), which will be displayed
        in the figure as a percentage after multiplying by 100.
    output_file_name : str
        The name of the output image file (e.g., "output_file.png") It is okay to omit '.png'
    gridline : bool, optional
        Whether to include gridlines in the plot. Default is True.
    debug : bool, optional
        A flag to enable debugging output. Default is False.

    Returns
    -------
    None
    """
    # Validate input years
    if syear > eyear:
        raise ValueError("Start year must be less than or equal to end year.")

    # Determine projection
    proj = determine_projection(mode)
    projection = configure_projection_obj(proj, eof_pattern)

    # Construct plot title
    plot_title = construct_plot_title(
        mode, model, syear, eyear, season, eof_variance_fraction
    )

    debug_print(f"plot_map: projection: {projection}, plot_title: {plot_title}", debug)

    # Set levels and maskout based on mode
    levels, maskout = set_levels_and_maskout(mode)

    # Set central longitude
    central_longitude = 0 if mode in ["AMO", "AMO_teleconnection"] else 180

    # Prepare data array
    data_array = eof_pattern.where(eof_pattern != 1e20, np.nan)

    # Generate plot
    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(8, 6))
    debug_print("fig, ax done", debug)

    # Call the plotting function
    fig, ax = plot_map_cartopy(
        data_array,
        title=plot_title,
        proj=proj,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        central_longitude=central_longitude,
        fig=fig,
        ax=ax,
        debug=debug,
    )

    # Done, save figure
    if output_file_name is not None:
        debug_print("plot done, save figure as " + output_file_name, debug)
        fig.savefig(output_file_name)

    plt.close("all")


# --------------------
# Supporting functions
# --------------------


def determine_projection(mode: str) -> str:
    """Determine the projection based on the mode."""
    if "teleconnection" in mode:
        return "Robinson"
    elif mode in ["NAO", "PNA", "NPO", "PDO", "NPGO", "AMO"]:
        return "Lambert"
    elif mode in ["NAM"]:
        return "Stereo_north"
    elif mode in ["SAM", "PSA1", "PSA2"]:
        return "Stereo_south"
    else:
        raise ValueError(f"Unknown mode: {mode}")


def configure_projection_obj(
    proj: str, data_array=None, central_longitude=180, debug=False
):
    """
    Configures and returns a map projection object based on the specified projection type and data array.

    Parameters
    ----------
    proj : str
        The type of map projection to use. Supported options include:
        - "PlateCarree"
        - "Robinson"
        - "Stereo_north"
        - "Stereo_south"
        - "Lambert"
    data_array : array-like, optional
        The input data array from which latitude and longitude information will be extracted.
        It is expected to contain geographical coordinates.
    central_longitude : int, optional
        The central longitude for the projection. Default is 180 degrees.
    debug : bool, optional
        If True, enables debug output for tracing the configuration process. Default is False.

    Returns
    -------
    projection : cartopy.crs.Projection
        A Cartopy projection object configured according to the specified parameters.

    Raises
    ------
    ValueError
        If the specified projection type is not supported or defined.

    Notes
    -----
    The function extracts the minimum and maximum latitude and longitude from the provided
    data array to determine the extent of the projection. For the Lambert projection, it
    also calculates the central latitude based on the data's latitude range.
    """

    debug_print("Central longitude setup starts", debug)
    debug_print("proj: " + proj, debug)

    # map types example:
    # https://github.com/SciTools/cartopy-tutorial/blob/master/tutorial/projections_crs_and_terms.ipynb

    # Initialize projection variable
    projection = None

    if proj == "PlateCarree":
        projection = ccrs.PlateCarree(central_longitude=central_longitude)
    elif proj == "Robinson":
        projection = ccrs.Robinson(central_longitude=central_longitude)
    elif proj == "Stereo_north":
        projection = ccrs.NorthPolarStereo()
    elif proj == "Stereo_south":
        projection = ccrs.SouthPolarStereo()
    elif proj == "Lambert":
        if data_array is None:
            raise ValueError("Data array is required for Lambert projection")
        else:
            lon = get_longitude(data_array)
            lat = get_latitude(data_array)

            # Determine the extent based on the longitude range where data exists
            lon_min = lon.min().item()
            lon_max = lon.max().item()
            lat_min = lat.min().item()
            lat_max = lat.max().item()

            # Adjust lat range
            lat_min = max(lat_min, -80)
            lat_max = min(lat_max, 80)
            if debug:
                print("revised maxlat:", lat_max)
            central_longitude = (lon_min + lon_max) / 2.0
            central_latitude = (lat_min + lat_max) / 2.0
            projection = ccrs.AlbersEqualArea(
                central_longitude=central_longitude,
                central_latitude=central_latitude,
                standard_parallels=(20, lat_max),
            )
    else:
        raise ValueError(f"Error: projection not defined for {proj}")

    return projection


def construct_plot_title(
    mode: str,
    model: str,
    syear: int,
    eyear: int,
    season: str,
    eof_variance_fraction: float,
) -> str:
    """Construct the plot title."""
    percentage = (
        f"{round(float(eof_variance_fraction * 100.0), 1)}%"
        if eof_variance_fraction != -999
        else ""
    )
    return f"{mode}: {model}\n{syear}-{eyear} {season} {percentage}"


def set_levels_and_maskout(mode: str):
    """Set levels and maskout based on the mode."""
    if mode in [
        "PDO",
        "NPGO",
        "AMO",
        "PDO_teleconnection",
        "NPGO_teleconnection",
        "AMO_teleconnection",
    ]:
        return [r / 10 for r in range(-5, 6)], "land"
    else:
        return list(range(-5, 6)), None


def plot_map_cartopy(
    data_array,
    title=None,
    gridline=True,
    levels=None,
    proj="PlateCarree",
    data_area="global",
    cmap="RdBu_r",
    central_longitude=180,
    maskout=None,
    fig=None,
    ax=None,
    debug=False,
):
    """
    Plot a map using cartopy.

    Parameters
    ----------
    data : data_array
        2D xarray DataArray with lat/lon coordinates attached.
    filename : str
        Output file name (it is okay to omit '.png')
    title : str, optional
        Figure title
    gridline : bool
        Show grid lines (default is True)
    levels : list
        List of numbers for colormap levels (optional)
    proj : str
        Map projection: PlateCarree (default), Robinson, Stereo_north, Stereo_south, Lambert
    data_area : str
        Spatial coverage area of data: global (default), regional
    cmap : str
        Matplotlib colormap name. See https://matplotlib.org/stable/gallery/color/colormap_reference.html for available options
    maskout : str (optional)
        Maskout: land, ocean
    debug: bool
        Switch for debugging print statements (default is False)
    """

    debug_print("plot_map_cartopy starts", debug)

    lon = get_longitude(data_array)
    lat = get_latitude(data_array)

    # Determine the extent based on the longitude range where data exists
    lon_min = lon.min().item()
    lon_max = lon.max().item()
    lat_min = lat.min().item()
    lat_max = lat.max().item()

    debug_print("Central longitude setup starts", debug)
    debug_print("proj: " + proj, debug)

    # Generate plot
    if fig is None and ax is None:
        projection = configure_projection_obj(proj, data_array, debug)

        if debug:
            debug_print("Central longitude setup completes", debug)
            print("projection:", projection)

        fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(8, 6))
        debug_print("fig, ax done", debug)

    # Add coastlines
    ax.coastlines()
    debug_print("Generate plot completed", debug)

    # Grid Lines and tick labels
    debug_print("projection starts", debug)
    if proj == "PlateCarree":
        if data_area == "global":
            if gridline:
                gl = ax.gridlines(alpha=0.5, linestyle="--")
            ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
            ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
            lon_formatter = LongitudeFormatter(zero_direction_label=True)
            lat_formatter = LatitudeFormatter()
            ax.xaxis.set_major_formatter(lon_formatter)
            ax.yaxis.set_major_formatter(lat_formatter)
        else:
            if gridline:
                gl = ax.gridlines(draw_labels=True, alpha=0.5, linestyle="--")
    elif proj == "Robinson":
        if gridline:
            gl = ax.gridlines(alpha=0.5, linestyle="--")
    elif "Stereo" in proj:
        debug_print(proj + " start", debug)
        if gridline:
            gl = ax.gridlines(draw_labels=True, alpha=0.5, linestyle="--")
            gl.xlocator = mticker.FixedLocator(
                np.concatenate([np.arange(-180, -89, 30), np.arange(-90, 181, 30)])
            )
            gl.xformatter = LONGITUDE_FORMATTER
            gl.xlabel_style = {"size": 12, "color": "k", "rotation": 0}
            gl.yformatter = LATITUDE_FORMATTER
            if "north" in proj:
                ax.set_extent([-180, 180, 0, 90], crs=ccrs.PlateCarree())
                gl.ylocator = mticker.FixedLocator(np.arange(20, 90, 20), 200)
            elif "south" in proj:
                ax.set_extent([-180, 180, -90, 0], crs=ccrs.PlateCarree())
                gl.ylocator = mticker.FixedLocator(np.arange(-90, -20, 20), 200)
        # Compute a circle in axes coordinates, which we can use as a boundary
        # for the map. We can pan/zoom as much as we like - the boundary will be
        # permanently circular.
        # https://scitools.org.uk/cartopy/docs/v0.15/examples/always_circular_stereo.html
        theta = np.linspace(0, 2 * np.pi, 100)
        center, radius = [0.5, 0.5], 0.4
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax.set_boundary(circle, transform=ax.transAxes)
        debug_print(proj + " plotted", debug)
    elif proj == "Lambert":
        lat_max = min(lat_max, 80)
        # Make a boundary path in PlateCarree projection, I choose to start in
        # the bottom left and go round anticlockwise, creating a boundary point
        # every 1 degree so that the result is smooth:
        # https://stackoverflow.com/questions/43463643/cartopy-albersequalarea-limit-region-using-lon-and-lat
        vertices = [
            (lon - 180, lat_min) for lon in range(int(lon_min), int(lon_max + 1), 1)
        ] + [(lon - 180, lat_max) for lon in range(int(lon_max), int(lon_min - 1), -1)]
        boundary = mpath.Path(vertices)
        ax.set_boundary(
            boundary, transform=ccrs.PlateCarree(central_longitude=180)
        )  # Here, 180 should be hardcoded, otherwise AMO map will be at out of figure box
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
        if gridline:
            gl = ax.gridlines(
                draw_labels=True,
                alpha=0.8,
                linestyle="--",
                crs=ccrs.PlateCarree(),
            )
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            gl.ylocator = mticker.FixedLocator([30, 60])
            gl.xlocator = mticker.FixedLocator([120, 160, 200 - 360, 240 - 360])
            gl.top_labels = False  # suppress top labels
            # suppress right labels
            gl.right_labels = False
            for ea in gl.ylabel_artists:
                right_label = ea.get_position()[0] > 0
                if right_label:
                    ea.set_visible(False)
    else:
        raise ValueError(f"Projection '{proj}' is not defined.")

    debug_print("projection completed", debug)

    # Plot contours from the data
    contourf_plot = ax.contourf(
        lon,
        lat,
        data_array,
        levels=levels,
        cmap=cmap,
        extend="both",
        transform=ccrs.PlateCarree(),
    )
    debug_print("contourf done", debug)

    # Maskout
    if maskout is not None:
        if maskout == "land":
            ax.add_feature(
                cartopy_land, zorder=100, edgecolor="k", facecolor="lightgrey"
            )
        if maskout == "ocean":
            ax.add_feature(
                cartopy_ocean, zorder=100, edgecolor="k", facecolor="lightgrey"
            )
    if proj == "PlateCarree":
        ax.set_aspect("auto", adjustable=None)

    # Add title
    ax.set_title(title, pad=15, fontsize=15)

    # Add a colorbar
    posn = ax.get_position()
    cbar_ax = fig.add_axes([0, 0, 0.1, 0.1])
    cbar_ax.set_position([posn.x0 + posn.width + 0.03, posn.y0, 0.01, posn.height])
    cbar = plt.colorbar(contourf_plot, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=10)

    return fig, ax


def plot_time_series_with_variance(ax, time, series1, series2):
    """
    Plot two time series and display their variances as vertical bars.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object on which to draw the plot.
    time : array-like
        The time values corresponding to the x-axis.
    series1 : array-like
        The first time series data.
    series2 : array-like
        The second time series data.

    Notes
    -----
    The function plots two time series as lines and adds vertical bars
    to the right of the plot, representing the variance of each series.
    The bars are annotated with their respective variance values.

    Examples
    --------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> time = np.arange(0, 10, 1)
    >>> series1 = np.sin(time) + np.random.normal(0, 0.1, len(time))
    >>> series2 = np.cos(time) + np.random.normal(0, 0.1, len(time))
    >>> fig, ax = plt.subplots(figsize=(8, 5))
    >>> plot_time_series_with_variance(ax, time, series1, series2)
    >>> plt.show()
    """
    # Calculate variance
    var1 = np.var(series1)
    var2 = np.var(series2)

    # Plot the time series
    ax.plot(time, series1, label="Series 1", color="blue")
    ax.plot(time, series2, label="Series 2", color="green")

    # Adding variance as vertical bars
    bar_positions = [time[-1] + 1, time[-1] + 2]  # Positions to the right of the lines
    bar_width = 0.5
    ax.bar(
        bar_positions, [var1, var2], width=bar_width, color=["blue", "green"], alpha=0.6
    )

    # Annotations for variance values
    ax.text(
        bar_positions[0],
        var1 + 0.1,
        f"{var1:.2f}",
        ha="center",
        va="bottom",
        color="blue",
    )
    ax.text(
        bar_positions[1],
        var2 + 0.1,
        f"{var2:.2f}",
        ha="center",
        va="bottom",
        color="green",
    )

    # Add a horizontal line at y=0
    ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)

    # Set axis labels, title, and legend
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("Time Series with Variance Bars")
    ax.legend(loc="upper right")

    # Adjust x-axis limits to make space for bars
    ax.set_xlim(time[0], time[-1] + 3)
