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
            plot_map_cartopy(ds, outfile, title=title, cmap=colors, levels=levels)
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
                cmap="RdBu_r",
                levels=levels_diff,
            )

            three_panel_outfile = f"{outfile}_3panel.png"

            plot_three_panel(
                model_data=ds,
                obs_data=ref_ds,
                diff=diff,
                filename=three_panel_outfile,
                title=f"{model} {run} {season} {metric} {yrs_str}",
                cmap=colors,
                diff_max=max_abs,
                extent=get_data_extent(ds),
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

    # Generate plot
    extent = get_data_extent(data)
    is_global = (
        extent is not None
        and extent[1] - extent[0] >= 350
        and extent[3] - extent[2] >= 170
    )

    if is_global or extent is None:
        projection = ccrs.Robinson(central_longitude=center_lon_global)
        projection_name = "PlateCarree"
    else:
        projection = ccrs.PlateCarree()
        projection_name = "PlateCarree"

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
    if projection_name == "PlateCarree":
        if is_global:
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
                gl = ax.gridlines(
                    draw_labels=True,
                    alpha=0.5,
                    linestyle="--",
                )

                gl.top_labels = False
                gl.right_labels = False
                gl.bottom_labels = True
                gl.left_labels = True
    elif projection_name == "Robinson":
        if gridline:
            gl = ax.gridlines(
                draw_labels=True,
                alpha=0.5,
                linestyle="--",
            )

            gl.top_labels = False
            gl.right_labels = False
            gl.bottom_labels = True
            gl.left_labels = True

            gl.x_inline = False
            gl.y_inline = False

    # Add title
    plt.title(title, pad=15, fontsize=15)

    # Add colorbar
    posn = ax.get_position()
    cbar_ax = fig.add_axes([0, 0, 0.1, 0.1])
    cbar_ax.set_position([posn.x0 + posn.width + 0.01, posn.y0, 0.01, posn.height])
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=10)

    if projection_name == "PlateCarree":
        ax.set_aspect("auto", adjustable=None)

    # Done, save figure
    fig.savefig(filename)
    plt.close("all")

    return


def plot_three_panel(
    model_data,
    obs_data,
    diff,
    filename,
    title,
    cmap="PuBu",
    diff_cmap="RdBu_r",
    diff_max=None,
    extent=None,
):
    """Plot model, observations, and model-minus-observation."""

    projection = ccrs.PlateCarree()

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(10, 13),
        subplot_kw={"projection": projection},
        constrained_layout=True,
    )

    # Shared color scale for model and observations
    vmin = float(min(model_data.min(skipna=True), obs_data.min(skipna=True)))
    vmax = float(max(model_data.max(skipna=True), obs_data.max(skipna=True)))

    if np.isclose(vmin, vmax):
        vmax = vmin + 1e-6

    levels = np.linspace(vmin, vmax, 21)

    if diff_max is None:
        diff_max = float(np.abs(diff).max(skipna=True))

    diff_max = max(diff_max, 1e-6)
    diff_levels = np.linspace(-diff_max, diff_max, 21)

    fields = [model_data, obs_data, diff]
    labels = ["Model", "Observations", "Model - Observations"]

    for i, (ax, field, label) in enumerate(zip(axes, fields, labels)):
        if extent is not None:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
        else:
            ax.set_global()

        ax.coastlines(linewidth=0.7)
        ax.gridlines(alpha=0.3, linestyle="--")

        if i < 2:
            im = ax.contourf(
                field.lon,
                field.lat,
                field,
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                levels=levels,
                extend="both",
            )
        else:
            im = ax.contourf(
                field.lon,
                field.lat,
                field,
                transform=ccrs.PlateCarree(),
                cmap=diff_cmap,
                levels=diff_levels,
                extend="both",
            )

        ax.set_title(label, fontsize=13)
        fig.colorbar(
            im,
            ax=ax,
            orientation="vertical",
            shrink=0.85,
            pad=0.02,
        )

    fig.suptitle(title, fontsize=16)
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def taylor_diag(fname, outfile_template):
    with open(fname, "r") as metrics_file:
        metrics = json.load(metrics_file)

    dimensions = metrics["DIMENSIONS"]
    results = metrics["RESULTS"]

    models = [m for m in dimensions["model"] if m != "Reference"]
    realizations = dimensions["realization"]
    regions = dimensions["region"]
    indices = dimensions["index"]

    seasons = ["ANN", "DJF", "MAM", "JJA", "SON"]

    for run in realizations:
        for index in indices:
            for region in regions:
                for season in seasons:

                    valid_models = []
                    stddev = []
                    corrcoeff = []

                    for model in models:
                        try:
                            stats = results[model][run][index][region]

                            model_std = float(stats["std_xy"][season])
                            obs_std = float(stats["std-obs_xy"][season])
                            corr = float(stats["cor_xy"][season])

                        except (KeyError, TypeError, ValueError):
                            continue

                        if (
                            not np.isfinite(model_std)
                            or not np.isfinite(obs_std)
                            or not np.isfinite(corr)
                            or obs_std <= 0
                        ):
                            continue

                        valid_models.append(model)
                        stddev.append(model_std / obs_std)
                        corrcoeff.append(np.clip(corr, -1.0, 1.0))

                    if not valid_models:
                        print(
                            f"Skipping Taylor diagram: "
                            f"{run}, {index}, {region}, {season}"
                        )
                        continue

                    outfile = (
                        outfile_template.replace("realization", run)
                        .replace("region", region)
                        .replace("index", index)
                        .replace("season", season)
                    )

                    os.makedirs(
                        os.path.dirname(outfile) or ".",
                        exist_ok=True,
                    )

                    fig = plt.figure(
                        figsize=(12, 5) if len(valid_models) > 10 else (8, 5)
                    )

                    try:
                        fig, ax = TaylorDiagram(
                            np.asarray(stddev),
                            np.asarray(corrcoeff),
                            1.0,
                            fig=fig,
                            labels=valid_models,
                            ref_label="Reference",
                            normalize=True,
                        )

                        ax.legend(
                            bbox_to_anchor=(1.05, 0),
                            loc="lower left",
                            ncol=2 if len(valid_models) > 10 else 1,
                        )

                        fig.suptitle(
                            f"{run} {season} {index} {region}",
                            fontsize=16,
                        )

                        fig.savefig(
                            outfile + ".png",
                            dpi=150,
                            bbox_inches="tight",
                        )

                    finally:
                        plt.close(fig)
