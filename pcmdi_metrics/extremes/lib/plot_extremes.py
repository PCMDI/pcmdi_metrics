#!/usr/bin/env python
import math
import os
import sys

import cartopy
import cartopy.crs as ccrs
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

def plot_extremes(data,metric,model,run,metrics_output_path):

    if metric in ["TXx","TXn","TNx","TNn"]:
        colors="YlOrRd"
    elif metric in ["Rx1day","Rx5day"]:
        colors="PuBu"

    for season in ["ANN","DJF","MAM","JJA","SON"]:
        ds = data[season].mean("time")
        outfile = os.path.join(metrics_output_path,"_".join([model,run,metric,season]))
        print(outfile)
        title = " ".join([model,run,season,"mean",metric])
        min_lev = math.floor(ds.min()/10) * 10
        max_lev = math.floor(ds.max()/10) * 10
        levels = np.arange(min_lev,max_lev+10,10)
        plot_map_cartopy(
            ds,
            outfile,
            title=title,
            proj="Robinson",
            cmap=colors,
            levels=levels)                  

def plot_map_cartopy(    
    data,
    filename,
    title=None,
    gridline=True,
    levels=None,
    proj="PlateCarree",
    data_area="global",
    cmap="RdBu_r",
    center_lon_global=180,
    maskout=None,
    debug=False,):
    # Taken from similar function in variability_mode.lib.plot_map

    lons = data.lon
    lats = data.lat

    min_lon = min(lons)
    max_lon = max(lons)
    min_lat = min(lats)
    max_lat = max(lats)
    if debug:
        print(min_lon, max_lon, min_lat, max_lat)

    """ map types:
    https://github.com/SciTools/cartopy-tutorial/blob/master/tutorial/projections_crs_and_terms.ipynb
    """
    if proj == "PlateCarree":
        projection = ccrs.PlateCarree(central_longitude=center_lon_global)
    elif proj == "Robinson":
        projection = ccrs.Robinson(central_longitude=center_lon_global)

    # Generate plot
    fig = plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=projection)
    im = ax.contourf(
        lons,
        lats,
        data,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        levels=levels,
        extend="both",
    )
    ax.coastlines()

    # Grid Lines and tick labels
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

    # Add title
    plt.title(title, pad=15, fontsize=15)

    # Add colorbar
    posn = ax.get_position()
    cbar_ax = fig.add_axes([0, 0, 0.1, 0.1])
    cbar_ax.set_position([posn.x0 + posn.width + 0.01, posn.y0, 0.01, posn.height])
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=10)

    if proj == "PlateCarree":
        ax.set_aspect("auto", adjustable=None)

    # Done, save figure
    fig.savefig(filename)
    plt.close("all")