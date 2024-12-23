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

from pcmdi_metrics.io import get_latitude, get_longitude
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
    ref_name: str = None,
    output_file_name: str = None,
    gridline=True,
    debug=False,
):
    # Validate input years
    if syear > eyear:
        raise ValueError("Start year must be less than or equal to end year.")

    # Set central longitude
    central_longitude = 0 if mode in ["AMO", "AMO_teleconnection"] else 180

    # Determine projection
    proj = determine_projection(mode)
    projection = configure_projection_obj(
        proj, obs_eof_pattern, central_longitude=central_longitude, debug=debug
    )

    proj_teleconnection = determine_projection(f"{mode}_teleconnection")
    projection_tel = configure_projection_obj(
        proj_teleconnection, central_longitude=central_longitude, debug=debug
    )

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

    # Create the figure and gridspec
    fig = plt.figure(figsize=(10, 8))
    gs = fig.add_gridspec(3, 2)

    # Create the subplots
    ax1 = fig.add_subplot(gs[0, 0], projection=projection)
    ax2 = fig.add_subplot(gs[0, 1], projection=projection)
    ax3 = fig.add_subplot(gs[1, 0], projection=projection_tel)
    ax4 = fig.add_subplot(gs[1, 1], projection=projection_tel)
    ax5 = fig.add_subplot(gs[2, 0])
    ax6 = fig.add_subplot(gs[2, 1])

    debug_print("fig, ax done", debug)

    if "eof_mode" in obs_eof_pattern_data_array.attrs:
        eofn_ref = obs_eof_pattern_data_array.attrs["eof_mode"]
    else:
        eofn_ref = None

    if "eof_mode" in model_eof_pattern_data_array.attrs:
        eofn_model = model_eof_pattern_data_array.attrs["eof_mode"]
    else:
        eofn_model = None

    # Reference mode domain map
    title_ref = f"Reference: {ref_name}" if ref_name is not None else "Reference"
    title_ref += f" (EOF{eofn_ref})" if eofn_ref is not None else ""
    fig, ax1 = plot_map_cartopy(
        obs_eof_pattern_data_array,
        title=title_ref,
        proj=proj,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        fig=fig,
        ax=ax1,
        show_colorbar=False,
        debug=debug,
    )

    # Model mode domain map
    title_model = "Model"
    title_model += f" EOF{eofn_model}" if eofn_model is not None else ""
    fig, ax2 = plot_map_cartopy(
        model_eof_pattern_data_array,
        title=title_model,
        proj=proj,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        fig=fig,
        ax=ax2,
        show_colorbar=True,
        debug=debug,
    )

    # Reference mode teleconnection global map
    fig, ax3 = plot_map_cartopy(
        obs_eof_pattern_global_data_array,
        title="Reference Teleconnection",
        proj=proj_teleconnection,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        fig=fig,
        ax=ax3,
        show_colorbar=False,
        debug=debug,
    )

    # Model mode teleconnection global map
    fig, ax4 = plot_map_cartopy(
        model_eof_pattern_global_data_array,
        title="Model Teleconnection",
        proj=proj_teleconnection,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        fig=fig,
        ax=ax4,
        show_colorbar=False,
        debug=debug,
    )

    # Time series of PCs for reference and model as line plot
    fig, ax5 = plot_time_series(obs_pc, model_pc, fig=fig, ax=ax5)

    # Standard deviation of PCs for reference and model as bar plot
    fig, ax6 = plot_std_bar_graph(obs_pc, model_pc, fig=fig, ax=ax6)

    # Title
    fig.suptitle(plot_title, fontsize=18)

    # Adjust margins
    plt.subplots_adjust(
        left=0.1, right=0.88, top=0.85, bottom=0.08, wspace=0.2, hspace=0.4
    )

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

    # Set central longitude
    central_longitude = 0 if mode in ["AMO", "AMO_teleconnection"] else 180

    # Determine projection
    proj = determine_projection(mode)
    projection = configure_projection_obj(
        proj, eof_pattern, central_longitude=central_longitude, debug=debug
    )

    # Construct plot title
    plot_title = construct_plot_title(
        mode, model, syear, eyear, season, eof_variance_fraction
    )

    debug_print(f"plot_map: projection: {projection}, plot_title: {plot_title}", debug)

    # Set levels and maskout based on mode
    levels, maskout = set_levels_and_maskout(mode)

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
    maskout=None,
    fig=None,
    ax=None,
    show_colorbar=True,
    debug=False,
):
    """
    Plot a map using cartopy.

    Parameters
    ----------
    data_array : data_array
        2D xarray DataArray with lat/lon coordinates attached.
    title : str, optional
        Figure title
    gridline : bool
        Show grid lines (default is True)
    levels : list, optional
        List of numbers for colormap levels
    proj : str, optional
        Map projection: PlateCarree (default), Robinson, Stereo_north, Stereo_south, Lambert
    data_area : str, optional
        Spatial coverage area of data: global (default), regional
    cmap : str, optional
        Matplotlib colormap name. See https://matplotlib.org/stable/gallery/color/colormap_reference.html for available options
    maskout : str (optional)
        Maskout: land, ocean
    fig : matplotlib figure, optional
        If provided, plot on this figure
    ax : matplotlib axes, optional
        If provided, plot on this axes
    show_colorbar : bool, optional
        Show colorbar (default is True)
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
            gl.right_labels = False  # suppress right labels
            gl.bottom_labels = False  # suppress right labels
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
    if title is not None:
        ax.set_title(title, pad=15, fontsize=15)

    # Add a colorbar
    if show_colorbar:
        posn = ax.get_position()
        cbar_ax = fig.add_axes([0, 0, 0.1, 0.1])
        cbar_ax.set_position([posn.x0 + posn.width + 0.03, posn.y0, 0.01, posn.height])
        cbar = plt.colorbar(contourf_plot, cax=cbar_ax)
        cbar.ax.tick_params(labelsize=10)

    return fig, ax


def plot_time_series(
    series1: xr.DataArray, series2: xr.DataArray, labels=None, fig=None, ax=None
):
    """
    Plot two time series.

    Parameters
    ----------
    series1 : xr.DataArray
        The first time series data.
    series2 : xr.DataArray
        The second time series data.
    labels : list of str, optional
        The labels for the time series. If None, default labels, ("Reference", "Model"), will be used.
    fig : matplotlib.figure.Figure, optional
        The figure to plot on. If None, a new figure will be created.
    ax : matplotlib.axes.Axes, optional
        The axes to plot on. If None, a new axes will be created.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The figure object.
    ax : matplotlib.axes.Axes
        The axes object.
    """
    if fig is None and ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    if labels is None:
        labels = ["Reference", "Model"]

    # Plot the time series
    series1.plot.line(ax=ax, label=labels[0], color="black")
    series2.plot.line(ax=ax, label=labels[1], color="blue")

    # Add a horizontal line at y=0
    ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)

    # Set axis labels, title, and legend
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("PC Time Series")
    ax.legend()

    return fig, ax


def plot_std_bar_graph(
    series1: xr.DataArray, series2: xr.DataArray, labels=None, fig=None, ax=None
):
    """
    Plot the standard deviation of two time series as vertical bars.

    Parameters
    ----------
    series1 : xr.DataArray
        The first time series data.
    series2 : xr.DataArray
        The second time series data.
    labels : list of str, optional
        The labels for the time series. If None, default labels, ("Reference", "Model"), will be used.
    fig : matplotlib.figure.Figure, optional
        The figure to plot on. If None, a new figure will be created.
    ax : matplotlib.axes.Axes, optional
        The axes to plot on. If None, a new axes will be created.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The figure object.
    ax : matplotlib.axes.Axes
        The axes object.
    """
    if fig is None and ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    # Calculate std
    var1 = np.std(series1)
    var2 = np.std(series2)

    if labels is None:
        labels = ["Reference", "Model"]

    # Adding std as vertical bars
    bar_positions = [0, 1]  # Positions to the right of the lines
    bar_width = 0.8
    ax.bar(
        bar_positions,
        [var1, var2],
        width=bar_width,
        color=["black", "blue"],
        label=labels,
    )

    # Annotations for variance values
    ax.text(
        bar_positions[0],
        var1 * 0.9,
        f"{var1:.2f}",
        ha="center",
        va="top",
        color="white",
    )
    ax.text(
        bar_positions[1],
        var2 * 0.9,
        f"{var2:.2f}",
        ha="center",
        va="top",
        color="white",
    )

    # Set x-axis tick labels
    ax.set_xticks(bar_positions, labels)

    ax.set_title("Standard deviation of PC Time Series")
    ax.legend()

    return fig, ax
