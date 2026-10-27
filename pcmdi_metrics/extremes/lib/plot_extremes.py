#!/usr/bin/env python
import json
import os

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

from pcmdi_metrics.graphics import TaylorDiagram


def mask_return_values(ds, metric, run):
    if "return_value" not in run:
        return ds

    if "Rx" in metric:
        ds = ds.where(np.abs(ds) < 400)

    elif "TX" in metric:
        ds = ds.where((ds > -70) & (ds < 70))

    elif "TN" in metric:
        ds = ds.where((ds > -90) & (ds < 50))

    return ds


def make_maps(
    data, model, run, region_name, index, yrs, plot_dir, desc, meta, ref_data=None
):
    # Consolidating some plotting code here to streamline main function
    output_template = os.path.join(
        plot_dir, "_".join([model, run, region_name, index, "season"])
    )
    plot_extremes(data, index, model, run, yrs, output_template, ref_data=ref_data)
    meta.update_plots(
        os.path.basename(output_template), output_template + ".png", index, desc
    )
    return meta


def plot_extremes(data, metric, model, run, yrs, output_template, ref_data=None):
    vrange_dict = {
        "Rx1day": {"raw": 69.48, "rv": 188.69},
        "Rx5day": {"raw": 19.09, "rv": 76.57},
        "TXx": {"raw": 18.09, "rv": 20.87},
        "TNx": {"raw": 11.70, "rv": 13.21},
        "TXn": {"raw": 14.78, "rv": 16.45},
        "TNn": {"raw": 16.32, "rv": 19.81},
    }

    if yrs == [None, None]:
        if "time" in data.coords and data.sizes.get("time", 0) > 0:
            start_year = int(data.time[0].dt.year)
            end_year = int(data.time[-1].dt.year)
        else:
            start_year = "unknown"
            end_year = "unknown"
    else:
        start_year = yrs[0]
        end_year = yrs[1]

    yrs_str = f"({start_year}-{end_year})"

    if metric in ["TXx", "TXn", "TNx", "TNn"]:
        colors = "YlOrRd"
    elif metric in ["Rx1day", "Rx5day"]:
        colors = "PuBu"

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        ds = mask_return_values(data[season], metric, run)

        if "time" in ds.dims:
            ds = ds.mean("time")

        outfile = output_template.replace("season", season)

        if "return_value" in run:
            title = f"{model} {run}\n{season} {metric} {yrs_str}"
        else:
            title = f"{model} {run}\n{season} mean {metric} {yrs_str}"

        min_val = float(ds.min(skipna=True))
        max_val = float(ds.max(skipna=True))

        levels = np.linspace(min_val, max_val, 21)

        try:
            plot_map_cartopy(
                ds, outfile, title=title, proj="Robinson", cmap=colors, levels=levels
            )
        except Exception as e:
            print("Error. Could not create figure", outfile, ":")
            print("    ", e)

        # Difference from reference
        if ref_data is not None:
            ref_ds = mask_return_values(ref_data[season], metric, run)

            if "time" in ref_ds.dims:
                ref_ds = ref_ds.mean(dim="time")

            ref_ds = ref_ds.interp(
                lat=ds.lat,
                lon=ds.lon,
            )

            diff = ds - ref_ds

            if "return_value" in run:
                max_abs = vrange_dict[metric]["rv"]
            else:
                max_abs = vrange_dict[metric]["raw"]

            levels_diff = np.linspace(-max_abs, max_abs, 21)

            diff_outfile = f"{outfile}_diff"
            diff_title = (
                f"{model} {run} {season} {metric}\n"
                f"Difference from reference {yrs_str}"
            )

            plot_map_cartopy(
                diff,
                diff_outfile,
                title=diff_title,
                proj="Robinson",
                cmap="RdBu_r",
                levels=levels_diff,
            )
    return


def get_data_extent(data, padding=0.05):
    """Determine map extent from non-NaN cells on a rectilinear grid."""
    valid = data.notnull()

    # Identify latitude and longitude coordinates containing data
    valid_lat = valid.any(dim="lon")
    valid_lon = valid.any(dim="lat")

    if not bool(valid.any()):
        return None

    lats = data.lat.values[valid_lat.values]
    lons = data.lon.values[valid_lon.values]

    # Convert longitudes to -180..180
    lons = (lons + 180) % 360 - 180

    lat_min = float(np.min(lats))
    lat_max = float(np.max(lats))
    lon_min = float(np.min(lons))
    lon_max = float(np.max(lons))

    # Add padding
    lat_pad = max((lat_max - lat_min) * padding, 2)
    lon_pad = max((lon_max - lon_min) * padding, 2)

    return [
        max(-180, lon_min - lon_pad),
        min(180, lon_max + lon_pad),
        max(-90, lat_min - lat_pad),
        min(90, lat_max + lat_pad),
    ]


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

    # Determine geographic coverage
    extent = get_data_extent(data)

    # Detect global or near-global longitude coverage
    is_global = (
        extent is not None
        and extent[1] - extent[0] >= 350
        and extent[3] - extent[2] >= 170
    )

    # Use PlateCarree for regional maps
    if not is_global:
        projection = ccrs.PlateCarree()
    else:
        projection = ccrs.Robinson(central_longitude=center_lon_global)

    fig = plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=projection)

    if is_global or extent is None:
        ax.set_global()
    else:
        ax.set_extent(extent, crs=ccrs.PlateCarree())

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
                ax.gridlines(alpha=0.5, linestyle="--")
            ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
            ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
            lon_formatter = LongitudeFormatter(zero_direction_label=True)
            lat_formatter = LatitudeFormatter()
            ax.xaxis.set_major_formatter(lon_formatter)
            ax.yaxis.set_major_formatter(lat_formatter)
        else:
            if gridline:
                ax.gridlines(draw_labels=True, alpha=0.5, linestyle="--")
    elif proj == "Robinson":
        if gridline:
            ax.gridlines(
                draw_labels=not is_global,
                alpha=0.5,
                linestyle="--",
            )

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

                    # stddev = stat_dict["std_xy"]
                    # corrcoeff = stat_dict["cor_xy"]
                    # refstd = stat_dict["std-obs_xy"]

                    obs_std = stat_dict["std-obs_xy"].astype(float)
                    stddev = stat_dict["std_xy"].astype(float) / obs_std
                    corrcoeff = stat_dict["cor_xy"].astype(float)
                    refstd = 1.0

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
                        normalize=True,
                    )

                    ax.legend(bbox_to_anchor=(1.05, 0), loc="lower left", ncol=nc)
                    fig.suptitle(plottitle, fontsize=20)
                    plt.savefig(outfile)
    return
