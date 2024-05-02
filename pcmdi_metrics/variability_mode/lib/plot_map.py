import faulthandler
import sys

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


def plot_map(
    mode: str,
    model: str,
    syear: int,
    eyear: int,
    season: str,
    eof_pattern: xr.DataArray,
    eof_variance_fraction: float,
    output_file_name: str,
    debug=False,
):
    """Plot dive down map and save

    Parameters
    ----------
    mode : str
        Mode to plot (e.g., "NAO" or "NAO_teleconnection")
    model : str
        Name of model or reference dataset that will be shown in figure title
    syear : int
        Start year from analysis
    eyear : int
        End year from analysis
    season : str
        season ("DJF", "MAM", "JJA", "SON", "monthly", or "yearly") that was used for analysis and will be shown in figure title
    eof_pattern : cdms2.TransientVariable
        EOF pattern to plot, 2D cdms2 TransientVariable with lat/lon coordinates attached
    eof_variance_fraction : float
        Fraction of explained variability (0 to 1), which will be shown in the figure as percentage after multiplying 100
    output_file_name : str
        Name of output image file (e.g., "output_file.png")
    """
    # Map Projection
    if "teleconnection" in mode:
        projection = "Robinson"
    elif mode in ["NAO", "PNA", "NPO", "PDO", "NPGO", "AMO"]:
        projection = "Lambert"
    elif mode in ["NAM"]:
        projection = "Stereo_north"
    elif mode in ["SAM"]:
        projection = "Stereo_south"
    else:
        sys.exit("Projection for " + mode + "is not defined.")

    # title
    if eof_variance_fraction != -999:
        percentage = (
            str(round(float(eof_variance_fraction * 100.0), 1)) + "%"
        )  # % with one floating number
    else:
        percentage = ""

    plot_title = f"{mode}: {model}\n{syear}-{eyear} {season} {percentage}"

    debug_print(
        "plot_map: projection, plot_title:" + projection + ", " + plot_title, debug
    )

    gridline = True

    if mode in [
        "PDO",
        "NPGO",
        "AMO",
        "PDO_teleconnection",
        "NPGO_teleconnection",
        "AMO_teleconnection",
    ]:
        levels = [r / 10 for r in list(range(-5, 6, 1))]
        maskout = "land"
    else:
        levels = list(range(-5, 6, 1))
        maskout = None

    if mode in ["AMO", "AMO_teleconnection"]:
        central_longitude = 0
    else:
        central_longitude = 180

    # Convert cdms variable to xarray
    data_array = eof_pattern
    data_array = data_array.where(data_array != 1e20, np.nan)

    plot_map_cartopy(
        data_array,
        output_file_name,
        title=plot_title,
        proj=projection,
        gridline=gridline,
        levels=levels,
        maskout=maskout,
        central_longitude=central_longitude,
        debug=debug,
    )


def plot_map_cartopy(
    data_array,
    filename=None,
    title=None,
    gridline=True,
    levels=None,
    proj="PlateCarree",
    data_area="global",
    cmap="RdBu_r",
    central_longitude=180,
    maskout=None,
    debug=False,
):
    """
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

    # map types example:
    # https://github.com/SciTools/cartopy-tutorial/blob/master/tutorial/projections_crs_and_terms.ipynb

    if proj == "PlateCarree":
        projection = ccrs.PlateCarree(central_longitude=central_longitude)
    elif proj == "Robinson":
        projection = ccrs.Robinson(central_longitude=central_longitude)
    elif proj == "Stereo_north":
        projection = ccrs.NorthPolarStereo()
    elif proj == "Stereo_south":
        projection = ccrs.SouthPolarStereo()
    elif proj == "Lambert":
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
        print("Error: projection not defined!")

    if debug:
        debug_print("Central longitude setup completes", debug)
        print("projection:", projection)

    # Generate plot
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
        sys.exit("Projection, " + proj + ", is not defined.")

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

    # Done, save figure
    if filename is not None:
        debug_print("plot done, save figure as " + filename, debug)
        fig.savefig(filename)

    plt.close("all")
