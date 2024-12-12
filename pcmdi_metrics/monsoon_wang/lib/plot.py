import cartopy.crs as ccrs
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


def plot_monsoon_wang_maps(
    ds: xr.Dataset,
    central_longitude: float = 180,
    title: str = None,
    fig_size: tuple = (12, 10),
    colormap: str = "viridis",
    colorbar_label: str = None,
    levels: int = 21,
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
        Figure size (width, height) in inches, by default (12, 10)
    colormap : str, optional
        Colormap name for the maps from matplotlib, by default 'viridis'
    colorbar_label : str, optional
        Label for the colorbar, by default None
    levels : int, optional
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
    # Check if required variables exist in the dataset
    required_vars = ["obsmap", "modmap"]
    if not all(var in ds for var in required_vars):
        raise ValueError(
            f"Dataset is missing one or more required variables: {required_vars}"
        )

    # Determine shared color range
    vmin = min(ds["obsmap"].min().item(), ds["modmap"].min().item())
    vmax = max(ds["obsmap"].max().item(), ds["modmap"].max().item())

    # Create discrete color levels
    levels = np.linspace(vmin, vmax, levels)
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
    ds["obsmap"].plot(
        ax=ax1, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, add_colorbar=False
    )
    ax1.coastlines()
    ax1.set_title("Observation Map")

    # Plot modmap
    ds["modmap"].plot(
        ax=ax2, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, add_colorbar=False
    )
    ax2.coastlines()
    ax2.set_title("Model Map")

    # Function to plot overlay if available and requested
    def plot_overlay(map_name, plot_flag, marker, color, size, label):
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
            ax2.plot(
                mask_lons,
                mask_lats,
                marker,
                color=color,
                markersize=size,
                transform=ccrs.PlateCarree(),
                label=label,
            )

    # Plot overlays
    plot_overlay("hitmap", plot_hit, "o", hit_color, hit_size, "Hit")
    plot_overlay("missmap", plot_miss, "x", miss_color, miss_size, "Miss")
    plot_overlay(
        "falarmmap", plot_falarm, "^", falarm_color, falarm_size, "False Alarm"
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
    cbar.ax.tick_params(labelsize=8)
    if colorbar_label is not None:
        cbar.set_label(colorbar_label)

    # Add a title
    if title is not None:
        fig.suptitle(title, fontsize=16)

    # Save the figure if a save path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()
