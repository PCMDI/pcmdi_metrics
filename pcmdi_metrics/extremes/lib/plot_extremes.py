#!/usr/bin/env python
import json
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

from pcmdi_metrics.graphics import TaylorDiagram


def make_maps(data, model, run, region_name, index, yrs, plot_dir, desc, meta):
    # Consolidating some plotting code here to streamline main function
    output_template = os.path.join(
        plot_dir, "_".join([model, run, region_name, index, "season"])
    )
    plot_extremes(data, index, model, run, yrs, output_template)
    meta.update_plots(
        os.path.basename(output_template), output_template + ".png", index, desc
    )
    return meta


def plot_extremes(data, metric, model, run, yrs, output_template):
    if yrs == [None, None]:
        start_year = int(data.time[0].dt.year)
        end_year = int(data.time[-1].dt.year)
    else:
        start_year = yrs[0]
        end_year = yrs[1]
    yrs_str = "({0}-{1})".format(start_year, end_year)

    if metric in ["TXx", "TXn", "TNx", "TNn"]:
        colors = "YlOrRd"
    elif metric in ["Rx1day", "Rx5day"]:
        colors = "PuBu"

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        ds = data[season].mean("time")
        outfile = output_template.replace("season", season)
        title = " ".join([model, run, season, "mean", metric, yrs_str])
        min_lev = math.floor(ds.min() / 10) * 10
        max_lev = math.floor(ds.max() / 10) * 10
        levels = np.arange(min_lev, max_lev + 10, 10)
        try:
            plot_map_cartopy(
                ds, outfile, title=title, proj="Robinson", cmap=colors, levels=levels
            )
        except Exception as e:
            print("Error. Could not create figure", outfile, ":")
            print("    ", e)
    return


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
    debug=False,
):
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

    return


def taylor_diag(fname, outfile_template):
    with open(fname, "r") as metrics_file:
        metrics = json.load(metrics_file)

    models = metrics["DIMENSIONS"]["model"]
    realizations = metrics["DIMENSIONS"]["realization"]
    region = metrics["DIMENSIONS"]["region"]
    indices = metrics["DIMENSIONS"]["index"]

    # For legend
    models_label = models.copy()
    if "Reference" in models_label:
        models_label.remove("Reference")

    nc = 1
    fsize = (8, 5)
    if len(models_label) > 10:
        nc = 2
        fsize = (12, 5)

    for s in ["ANN", "DJF", "MAM", "SON", "JJA"]:
        for r in realizations:
            # Possible for a realization to be not found for every model
            if r not in metrics["RESULTS"][models[1]]:
                continue
            for idx in indices:
                if idx not in metrics["RESULTS"][models[1]][r]:
                    continue
                for rg in region:
                    stat_dict = {}
                    for stat in ["std_xy", "std-obs_xy", "cor_xy"]:
                        tmp = []
                        for m in models:
                            if m == "Reference":
                                continue
                            else:
                                tmp.append(metrics["RESULTS"][m][r][idx][rg][stat][s])
                        stat_dict[stat] = np.array(tmp)

                    stddev = stat_dict["std_xy"]
                    corrcoeff = stat_dict["cor_xy"]
                    refstd = stat_dict["std-obs_xy"]

                    plottitle = " ".join([r, s, idx, rg])
                    outfile = (
                        outfile_template.replace("realization", r)
                        .replace("region", rg)
                        .replace("index", idx)
                        .replace("season", s)
                    )

                    fig = plt.figure(figsize=fsize)
                    fig, ax = TaylorDiagram(
                        stddev,
                        corrcoeff,
                        refstd,
                        fig=fig,
                        labels=models_label,
                        ref_label="Reference",
                    )

                    ax.legend(bbox_to_anchor=(1.05, 0), loc="lower left", ncol=nc)
                    fig.suptitle(plottitle, fontsize=20)
                    plt.savefig(outfile)
    return
