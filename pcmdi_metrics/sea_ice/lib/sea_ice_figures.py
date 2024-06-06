import os

import cartopy.crs as ccrs
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import regionmask
import xarray as xr

from pcmdi_metrics.sea_ice.lib import sea_ice_lib as lib


def replace_nan_zero(da):
    da_new = xr.where(np.isnan(da), 0, da)
    return da_new


def replace_fill_zero(da, val):
    da_new = xr.where(da > val, 0, da)
    return da_new


def create_arctic_map(ds, metrics_output_path, varname="siconc", title=None):
    print("Creating Arctic map")
    # Load and process data
    xvar = lib.find_lon(ds)
    yvar = lib.find_lat(ds)

    # Some models have NaN values in coordinates
    # that can't be plotted by pcolormesh
    ds[xvar] = replace_nan_zero(ds[xvar])
    ds[yvar] = replace_nan_zero(ds[yvar])

    # Set up regions
    region_NA = np.array([[-120, 45], [-120, 80], [90, 80], [90, 45]])
    region_NP = np.array([[90, 45], [90, 65], [240, 65], [240, 45]])
    names = ["North_Atlantic", "North_Pacific"]
    abbrevs = ["NA", "NP"]
    arctic_regions = regionmask.Regions(
        [region_NA, region_NP], names=names, abbrevs=abbrevs, name="arctic"
    )

    # Do plotting
    cmap = colors.LinearSegmentedColormap.from_list(
        "", [[0, 85 / 255, 182 / 255], "white"]
    )
    proj = ccrs.NorthPolarStereo()
    ax = plt.subplot(111, projection=proj)
    ax.set_global()
    # TODO: get xvar and yvar
    ds[varname].plot.pcolormesh(
        ax=ax,
        x=xvar,
        y=yvar,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        cbar_kwargs={"label": "ice fraction"},
    )
    arctic_regions.plot_regions(
        ax=ax,
        add_label=False,
        label="abbrev",
        line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
    )
    ax.set_extent([-180, 180, 43, 90], ccrs.PlateCarree())
    ax.coastlines(color=[0.3, 0.3, 0.3])
    plt.annotate(
        "North Atlantic",
        (0.5, 0.2),
        xycoords="axes fraction",
        horizontalalignment="right",
        verticalalignment="bottom",
        color="white",
    )
    plt.annotate(
        "North Pacific",
        (0.65, 0.88),
        xycoords="axes fraction",
        horizontalalignment="right",
        verticalalignment="bottom",
        color="white",
    )
    plt.annotate(
        "Central\nArctic ",
        (0.56, 0.56),
        xycoords="axes fraction",
        horizontalalignment="right",
        verticalalignment="bottom",
    )
    ax.set_facecolor([0.55, 0.55, 0.6])
    if title is not None:
        plt.title(title)
        fig_path = os.path.join(
            metrics_output_path, title.replace(" ", "_") + "_arctic_regions.png"
        )
    else:
        fig_path = os.path.join(metrics_output_path, "arctic_regions.png")
    plt.savefig(fig_path)
    plt.close()


# ----------
# Antarctic
# ----------
def create_antarctic_map(ds, metrics_output_path, varname="siconc", title=None):
    print("Creating Antarctic map")
    # Load and process data
    xvar = lib.find_lon(ds)
    yvar = lib.find_lat(ds)

    # Some models have NaN values in coordinates
    # that can't be plotted by pcolormesh
    ds[xvar] = replace_nan_zero(ds[xvar])
    ds[yvar] = replace_nan_zero(ds[yvar])

    # Set up regions
    region_IO = np.array([[20, -90], [90, -90], [90, -55], [20, -55]])
    region_SA = np.array([[20, -90], [-60, -90], [-60, -55], [20, -55]])
    region_SP = np.array([[90, -90], [300, -90], [300, -55], [90, -55]])

    names = ["Indian Ocean", "South Atlantic", "South Pacific"]
    abbrevs = ["IO", "SA", "SP"]
    arctic_regions = regionmask.Regions(
        [region_IO, region_SA, region_SP],
        names=names,
        abbrevs=abbrevs,
        name="antarctic",
    )

    # Do plotting
    cmap = colors.LinearSegmentedColormap.from_list(
        "", [[0, 85 / 255, 182 / 255], "white"]
    )
    proj = ccrs.SouthPolarStereo()
    ax = plt.subplot(111, projection=proj)
    ax.set_global()
    ds[varname].plot.pcolormesh(
        ax=ax,
        x=xvar,
        y=yvar,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        cbar_kwargs={"label": "ice fraction"},
    )
    arctic_regions.plot_regions(
        ax=ax,
        add_label=False,
        label="abbrev",
        line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
    )
    ax.set_extent([-180, 180, -53, -90], ccrs.PlateCarree())
    ax.coastlines(color=[0.3, 0.3, 0.3])
    plt.annotate(
        "South Pacific",
        (0.50, 0.2),
        xycoords="axes fraction",
        horizontalalignment="right",
        verticalalignment="bottom",
        color="black",
    )
    plt.annotate(
        "Indian\nOcean",
        (0.89, 0.66),
        xycoords="axes fraction",
        horizontalalignment="right",
        verticalalignment="bottom",
        color="black",
    )
    plt.annotate(
        "South Atlantic",
        (0.54, 0.82),
        xycoords="axes fraction",
        horizontalalignment="right",
        verticalalignment="bottom",
        color="black",
    )
    ax.set_facecolor([0.55, 0.55, 0.6])
    if title is not None:
        plt.title(title)
        fig_path = os.path.join(
            metrics_output_path, title.replace(" ", "_") + "_antarctic_regions.png"
        )
    else:
        fig_path = os.path.join(metrics_output_path, "antarctic_regions.png")
    plt.savefig(fig_path)
    plt.close()
