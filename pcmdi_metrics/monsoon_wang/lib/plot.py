import cartopy.crs as ccrs
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter


def map_plotter(domain, title, ds, save_path=None):
    """
    Plot a map of the domain with a given title and data from a dataset.

    Parameters
    ----------
    domain : str
        Domain name of monsoon domain for the map
    title : str
        Title for the figure
    ds : xarray.Dataset
        Dataset containing the following variables:
        - 'obsmap': observation map
        - 'modmap': model map
        - 'obsmask': observation mask (optional)
        - 'modmask': model mask (optional)
        - 'hitmap': hit map (optional)
        - 'missmap': miss map (optional)
        - 'falarmmap': false alarm map (optional)
    save_path : str, optional
        Path to save the figure, by default None

    Returns
    -------
    None
    """
    if domain in ["ASM"]:
        central_longitude = 180
    else:
        central_longitude = 0

    if domain in ["ASM", "AllMW", "NAFM", "NAMM", "AllM"]:
        legend_loc = "upper left"
    else:
        legend_loc = "lower left"

    if domain in ["AllMW", "AllM"]:
        hit_size = 1
        miss_size = 2
        falarm_size = 1
    else:
        hit_size = 4
        miss_size = 6
        falarm_size = 5

    plot_monsoon_wang_maps(
        ds,
        central_longitude=central_longitude,
        title=title,
        colorbar_label="Monsoon Annual Range (mm/day)",
        colormap="Spectral_r",
        legend_loc=legend_loc,
        hit_size=hit_size,
        miss_size=miss_size,
        falarm_size=falarm_size,
        save_path=save_path,
    )


def plot_monsoon_wang_maps(
    ds: xr.Dataset,
    central_longitude: float = 180,
    title: str = None,
    fig_size: tuple = (8, 6),
    colormap: str = "viridis",
    colorbar_label: str = None,
    num_levels: int = 21,
    legend_loc: str = "lower left",
    projection: ccrs.Projection = None,
    hit_color: str = "blue",
    miss_color: str = "red",
    falarm_color: str = "green",
    hit_size: int = 4,
    miss_size: int = 6,
    falarm_size: int = 6,
    save_path: str = None,
    plot_hit: bool = True,
    plot_miss: bool = True,
    plot_falarm: bool = True,
) -> None:
    """
    Plot observation and model maps with optional hit, miss, and false alarm overlays.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing the following variables:
        - 'obsmap': observation map
        - 'modmap': model map
        - 'hitmap': hit map (optional)
        - 'missmap': miss map (optional)
        - 'falarmmap': false alarm map (optional)
    central_longitude : int, optional
        Central longitude for the map projection, by default 180
    title : str, optional
        Title for the figure, by default None
    fig_size : tuple, optional
        Figure size (width, height) in inches, by default (8, 6)
    colormap : str, optional
        Colormap name for the maps from matplotlib, by default 'viridis'
    colorbar_label : str, optional
        Label for the colorbar, by default None
    num_levels : int, optional
        Number of discrete color levels for the maps, by default 21
    legend_loc : str, optional
        Location of the legend for the markers, by default 'lower left'
    projection : cartopy.crs.Projection, optional
        Custom map projection, by default None (uses PlateCarree)
    hit_color : str, optional
        Color for hit markers, by default 'blue'
    miss_color : str, optional
        Color for miss markers, by default 'red'
    falarm_color : str, optional
        Color for false alarm markers, by default 'green'
    hit_size : int, optional
        Size for hit markers, by default 4
    miss_size : int, optional
        Size for miss markers, by default 6
    falarm_size : int, optional
        Size for false alarm markers, by default 6
    save_path : str, optional
        Path to save the figure, by default None
    plot_hit : bool, optional
        Whether to plot hit map, by default True
    plot_miss : bool, optional
        Whether to plot miss map, by default True
    plot_falarm : bool, optional
        Whether to plot false alarm map, by default True
    """
    ds = ds.copy(deep=True)
    ds["obsmap"] = ds["obsmap"] * 86400  # Convert from kg m-2 s-1 to mm/day
    ds["modmap"] = ds["modmap"] * 86400  # Convert from kg m-2 s-1 to mm/day

    # Check if required variables exist in the dataset
    required_vars = ["obsmap", "modmap"]
    if not all(var in ds for var in required_vars):
        raise ValueError(
            f"Dataset is missing one or more required variables: {required_vars}"
        )

    # Determine shared color range
    vmin = min(ds["obsmap"].min().item(), ds["modmap"].min().item())
    vmax = max(ds["obsmap"].max().item(), ds["modmap"].max().item())

    # Round vmin and vmax to the nearest nice value (e.g., nearest integer)
    vmin = np.floor(vmin)  # Round down
    vmax = np.ceil(vmax)  # Round up

    # Create discrete color levels
    levels = np.linspace(vmin, vmax, num_levels)
    cmap = plt.get_cmap(colormap, len(levels) - 1)
    norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

    # Set up the projection
    if projection is None:
        projection = ccrs.PlateCarree(central_longitude=central_longitude)

    # Create a figure with a GridSpec layout
    fig = plt.figure(figsize=fig_size, constrained_layout=True)
    grid = fig.add_gridspec(
        nrows=2,
        ncols=2,
        width_ratios=[1, 0.05],
        height_ratios=[1, 1],
        wspace=0.1,
        hspace=0.1,
    )

    # Create axes for the maps
    ax1 = fig.add_subplot(grid[0, 0], projection=projection)
    ax2 = fig.add_subplot(grid[1, 0], projection=projection)

    # Plot obsmap
    plot_map(ds, "obsmap", ax1, cmap, norm, title="Observation Map")
    add_monsoon_domain(ds, "obsmask", ax1)

    # Plot modmap
    plot_map(ds, "modmap", ax2, cmap, norm, title="Model Map")
    add_monsoon_domain(ds, "modmask", ax2)

    # Plot overlaying markers
    plot_overlay(ds, ax2, "hitmap", plot_hit, "o", hit_color, hit_size, "Hit")
    plot_overlay(ds, ax2, "missmap", plot_miss, "x", miss_color, miss_size, "Miss")
    plot_overlay(
        ds, ax2, "falarmmap", plot_falarm, "^", falarm_color, falarm_size, "False Alarm"
    )

    # Add a legend for the markers if any overlay is plotted
    if plot_hit or plot_miss or plot_falarm:
        ax2.legend(loc=legend_loc, fontsize=8)

    # Add a shared discrete colorbar to the right
    cbar_ax = fig.add_subplot(grid[:, 1])
    cbar = fig.colorbar(
        cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, orientation="vertical"
    )
    cbar.set_ticks(levels)
    cbar.ax.tick_params(labelsize=10)
    if colorbar_label is not None:
        cbar.set_label(colorbar_label, fontsize=15)

    # Add a title
    if title is not None:
        fig.suptitle(title, fontsize=16)

    # Save the figure if a save path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


# Support functions for plot_monsoon_wang_maps


def plot_map(ds, var, ax, cmap, norm, title=None):
    da = ds[var]
    da.plot(
        ax=ax, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, add_colorbar=False
    )
    ax.coastlines()
    if title is not None:
        ax.set_title(title)

    # draw parallels and meridians by adding grid lines
    gl = ax.gridlines(
        draw_labels=True, crs=ccrs.PlateCarree(), linestyle="--", color="k"
    )
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 12}
    gl.ylabel_style = {"size": 12}


def add_monsoon_domain(ds, mask_var_name, ax):
    has_nan = np.isnan(ds[mask_var_name]).any()

    if has_nan:
        # Create a binary mask: 1 for NaN, 0 for non-NaN
        binary_mask = np.isnan(ds[mask_var_name])

        # Draw a contour along the boundary between NaN and non-NaN
        ax.contour(
            ds[mask_var_name].lon,  # Replace with your longitude coordinates
            ds[mask_var_name].lat,  # Replace with your latitude coordinates
            binary_mask,
            levels=[0.5],  # This draws the contour along the transition from 0 to 1
            transform=ccrs.PlateCarree(),
            colors="grey",
            linewidths=1,
        )


# Function to plot overlay if available and requested
def plot_overlay(ds, ax, map_name, plot_flag, marker, color, size, label):
    if plot_flag and map_name in ds:
        # Extract coordinates and boolean arrays for overlays
        mask = ds[map_name]  # Boolean array for hitmap
        # Extract lat, lon values where hitmap and missmap are True
        mask_coords = mask == 1  # Mask of where hitmap is True
        mask_lons, mask_lats = np.meshgrid(
            ds["lon"], ds["lat"]
        )  # Create meshgrid for coordinates
        # Filter coordinates where the hitmap and missmap are True
        mask_lons = mask_lons[mask_coords]
        mask_lats = mask_lats[mask_coords]
        # Overlay hitmap (circles) on modmap
        ax.plot(
            mask_lons,
            mask_lats,
            marker,
            color=color,
            markersize=size,
            transform=ccrs.PlateCarree(),
            label=label,
        )
