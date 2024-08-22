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


def create_summary_maps_arctic(ds, var_ice, metrics_output_path, meta, model):
    xvar = lib.find_lon(ds)
    yvar = lib.find_lat(ds)

    # Set up regions
    region_NA = np.array([[-120, 45], [-120, 80], [90, 80], [90, 45]])
    region_NP = np.array([[90, 45], [90, 65], [240, 65], [240, 45]])
    names = ["North_Atlantic", "North_Pacific"]
    abbrevs = ["NA", "NP"]
    arctic_regions = regionmask.Regions(
        [region_NA, region_NP], names=names, abbrevs=abbrevs, name="arctic"
    )

    cmap = colors.LinearSegmentedColormap.from_list(
        "", [[0, 85 / 255, 182 / 255], "white"]
    )

    # Do plotting
    try:
        proj = ccrs.NorthPolarStereo()
        f1, axs = plt.subplots(
            1, 2, figsize=(10, 5), subplot_kw={"projection": proj}, layout="compressed"
        )

        # Model arctic Feb
        ax = axs[0]
        ax.set_global()  # to use cartopy polar proj

        ds[var_ice].isel({"time": 1}).plot(
            ax=ax,
            x=xvar,
            y=yvar,
            levels=[0.15, 0.4, 0.6, 0.8, 1],
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            add_colorbar=False,
        )
        arctic_regions.plot_regions(
            ax=ax,
            add_label=False,
            label="abbrev",
            line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
        )
        ax.set_extent([-180, 180, 43, 90], ccrs.PlateCarree())
        ax.coastlines(color=[0.3, 0.3, 0.3])
        ax.set_facecolor([0.55, 0.55, 0.6])
        ax.set_title("Feb\n" + model.replace("_", " "), fontsize=12)

        # Model Arctic Sept
        ax = axs[1]
        ax.set_global()  # to use cartopy polar proj

        fds = (
            ds[var_ice]
            .isel({"time": 8})
            .plot(
                ax=ax,
                x=xvar,
                y=yvar,
                levels=[0.15, 0.4, 0.6, 0.8, 1],
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                add_colorbar=False,
                # cbar_kwargs={"label": "ice fraction", "fraction": 0.046, "pad": 0.04},
            )
        )
        arctic_regions.plot_regions(
            ax=ax,
            add_label=False,
            label="abbrev",
            line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
        )
        ax.set_extent([-180, 180, 43, 90], ccrs.PlateCarree())
        ax.coastlines(color=[0.3, 0.3, 0.3])
        ax.set_facecolor([0.55, 0.55, 0.6])
        ax.set_title("Sep\n" + model.replace("_", " "), fontsize=12)

        # plt.suptitle("Arctic", fontsize=30)
        fig_path = os.path.join(
            metrics_output_path, model.replace(" ", "_") + "_Feb_Sep_NH.png"
        )
        # plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        plt.colorbar(fds, label="ice fraction", ax=axs)
        plt.savefig(fig_path)
        plt.close()
        meta.update_plots(
            "Summary_NH_" + model.replace(" ", "_"),
            fig_path,
            "Feb_Sep_maps",
            "Summary map of Feb and Sep ice areas for Northern hemispheres",
        )
    except Exception as e:
        print("Could not create summary maps.")
        print(e)
        if plt.get_fignums():
            plt.close()
    return meta


def create_summary_maps_antarctic(ds, var_ice, metrics_output_path, meta, model):
    xvar = lib.find_lon(ds)
    yvar = lib.find_lat(ds)

    # Set up regions
    region_IO = np.array([[20, -90], [90, -90], [90, -55], [20, -55]])
    region_SA = np.array([[20, -90], [-60, -90], [-60, -55], [20, -55]])
    region_SP = np.array([[90, -90], [300, -90], [300, -55], [90, -55]])

    names = ["Indian Ocean", "South Atlantic", "South Pacific"]
    abbrevs = ["IO", "SA", "SP"]
    antarctic_regions = regionmask.Regions(
        [region_IO, region_SA, region_SP],
        names=names,
        abbrevs=abbrevs,
        name="antarctic",
    )

    cmap = colors.LinearSegmentedColormap.from_list(
        "", [[0, 85 / 255, 182 / 255], "white"]
    )

    # Do plotting
    try:
        # proj = ccrs.NorthPolarStereo()
        f1, axs = plt.subplots(
            1,
            2,
            figsize=(10, 5),
            subplot_kw={"projection": ccrs.SouthPolarStereo()},
            layout="compressed",
        )

        # Model Antarctic September
        ax = axs[0]
        ax.set_global()
        ds[var_ice].isel({"time": 8}).plot(
            ax=ax,
            x=xvar,
            y=yvar,
            levels=[0.15, 0.4, 0.6, 0.8, 1],
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            add_colorbar=False,
        )
        antarctic_regions.plot_regions(
            ax=ax,
            add_label=False,
            label="abbrev",
            line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
        )
        ax.set_extent([-180, 180, -53, -90], ccrs.PlateCarree())
        ax.coastlines(color=[0.3, 0.3, 0.3])
        ax.set_facecolor([0.55, 0.55, 0.6])
        ax.set_title("Sep\n" + model.replace("_", " "), fontsize=12)

        # Model Antarctic Feb
        ax = axs[1]
        ax.set_global()
        fds = (
            ds[var_ice]
            .isel({"time": 1})
            .plot(
                ax=ax,
                x=xvar,
                y=yvar,
                levels=[0.15, 0.4, 0.6, 0.8, 1],
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                add_colorbar=False,
                # cbar_kwargs={"label": "ice fraction", "fraction": 0.046, "pad": 0.04},
            )
        )
        antarctic_regions.plot_regions(
            ax=ax,
            add_label=False,
            label="abbrev",
            line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
        )
        ax.set_extent([-180, 180, -53, -90], ccrs.PlateCarree())
        ax.coastlines(color=[0.3, 0.3, 0.3])
        ax.set_facecolor([0.55, 0.55, 0.6])
        ax.set_title("Feb\n" + model.replace("_", " "), fontsize=12)

        # plt.suptitle("Arctic", fontsize=30)
        fig_path = os.path.join(
            metrics_output_path, model.replace(" ", "_") + "_Feb_Sep_SH.png"
        )
        # plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        plt.colorbar(fds, label="ice fraction", ax=axs)
        plt.savefig(fig_path)
        plt.close()
        meta.update_plots(
            "Summary_SH_" + model.replace(" ", "_"),
            fig_path,
            "Feb_Sep_maps",
            "Summary map of Feb and Sep ice areas for Southern hemispheres",
        )
    except Exception as e:
        print("Could not create summary maps.")
        print(e)
        if plt.get_fignums():
            plt.close()
    return meta


def create_arctic_map(
    ds, obs, var_ice, var_obs, metrics_output_path, meta, model, title
):
    # Load and process data
    xvar = lib.find_lon(ds)
    yvar = lib.find_lat(ds)

    # Some models have NaN values in coordinates
    # that can't be plotted by pcolormesh
    # ds[xvar] = replace_nan_zero(ds[xvar])
    # ds[yvar] = replace_nan_zero(ds[yvar])

    # Set up regions
    region_NA = np.array([[-120, 45], [-120, 80], [90, 80], [90, 45]])
    region_NP = np.array([[90, 45], [90, 65], [240, 65], [240, 45]])
    names = ["North_Atlantic", "North_Pacific"]
    abbrevs = ["NA", "NP"]
    arctic_regions = regionmask.Regions(
        [region_NA, region_NP], names=names, abbrevs=abbrevs, name="arctic"
    )

    # Do plotting
    try:
        cmap = colors.LinearSegmentedColormap.from_list(
            "", [[0, 85 / 255, 182 / 255], "white"]
        )
        proj = ccrs.NorthPolarStereo()
        f1, axs = plt.subplots(
            4, 6, figsize=(21, 13), subplot_kw={"projection": proj}, layout="compressed"
        )
        pos1 = [1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3]  # row
        pos2 = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]  # col
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        for mo in range(0, 12):
            ax = axs[pos1[mo], pos2[mo]]
            fds = (
                ds[var_ice]
                .isel({"time": mo})
                .plot(
                    ax=ax,
                    x=xvar,
                    y=yvar,
                    levels=[0.15, 0.4, 0.6, 0.8, 1],
                    transform=ccrs.PlateCarree(),
                    cmap=cmap,
                    add_colorbar=False,
                )
            )
            arctic_regions.plot_regions(
                ax=ax,
                add_label=False,
                label="abbrev",
                line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
            )
            if pos2[mo] == 0:
                if len(model) > 12:
                    fsize = 12
                else:
                    fsize = 14
                ax.text(
                    0.03,
                    0.04,
                    model.replace("_", " "),
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    backgroundcolor="white",
                    fontsize=fsize,
                )
            ax.set_extent([-180, 180, 43, 90], ccrs.PlateCarree())
            ax.coastlines(color=[0.3, 0.3, 0.3])
            ax.set_facecolor([0.55, 0.55, 0.6])
            ax.set_title("")
        pos1 = [0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2]  # row
        pos2 = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]  # col
        xvar = lib.find_lon(obs)
        yvar = lib.find_lat(obs)
        for mo in range(0, 12):
            ax = axs[pos1[mo], pos2[mo]]
            obs[var_obs].isel({"time": mo}).plot(
                ax=ax,
                x=xvar,
                y=yvar,
                levels=[0.15, 0.4, 0.6, 0.8, 1],
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                add_colorbar=False,
            )
            arctic_regions.plot_regions(
                ax=ax,
                add_label=False,
                label="abbrev",
                line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
            )
            if pos2[mo] == 0:
                ax.text(
                    0.03,
                    0.04,
                    "Reference",
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    backgroundcolor="white",
                    fontsize=14,
                )
            ax.set_extent([-180, 180, 43, 90], ccrs.PlateCarree())
            ax.coastlines(color=[0.3, 0.3, 0.3])
            ax.set_facecolor([0.55, 0.55, 0.6])
            ax.set_title(months[mo], fontsize=18)

        plt.suptitle(title, fontsize=26)
        fig_path = os.path.join(
            metrics_output_path, model.replace(" ", "_") + "_arctic_regions.png"
        )
        cbar = plt.colorbar(
            fds,
            ax=axs[0:2, :],
            pad=0.02,
            aspect=25,
        )
        cbar.ax.tick_params(labelsize=18)
        cbar.set_label(label="ice fraction", size=18)
        cbar = plt.colorbar(
            fds,
            ax=axs[2:, :],
            pad=0.02,
            aspect=25,
        )
        cbar.ax.tick_params(labelsize=18)
        cbar.set_label(label="ice fraction", size=18)
        plt.savefig(fig_path)
        plt.close()
        meta.update_plots(
            "Arctic" + model.replace(" ", "_"),
            fig_path,
            "Arctic_map",
            "Maps of monthly Antarctic ice fraction",
        )
    except Exception as e:
        print("Could not create Arctic maps.")
        print(e)
        if plt.get_fignums():
            plt.close()
    return meta


# ----------
# Antarctic
# ----------
def create_antarctic_map(
    ds, obs, var_ice, var_obs, metrics_output_path, meta, model, title
):
    # Load and process data
    xvar = lib.find_lon(ds)
    yvar = lib.find_lat(ds)

    # Some models have NaN values in coordinates
    # that can't be plotted by pcolormesh
    # ds[xvar] = replace_nan_zero(ds[xvar])
    # ds[yvar] = replace_nan_zero(ds[yvar])

    # Set up regions
    region_IO = np.array([[20, -90], [90, -90], [90, -55], [20, -55]])
    region_SA = np.array([[20, -90], [-60, -90], [-60, -55], [20, -55]])
    region_SP = np.array([[90, -90], [300, -90], [300, -55], [90, -55]])

    names = ["Indian Ocean", "South Atlantic", "South Pacific"]
    abbrevs = ["IO", "SA", "SP"]
    antarctic_regions = regionmask.Regions(
        [region_IO, region_SA, region_SP],
        names=names,
        abbrevs=abbrevs,
        name="antarctic",
    )

    # Do plotting
    try:
        cmap = colors.LinearSegmentedColormap.from_list(
            "", [[0, 85 / 255, 182 / 255], "white"]
        )
        proj = ccrs.SouthPolarStereo()
        f1, axs = plt.subplots(
            4, 6, figsize=(21, 13), subplot_kw={"projection": proj}, layout="compressed"
        )
        pos1 = [1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3]  # row
        pos2 = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]  # col
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        for mo in range(0, 12):
            ax = axs[pos1[mo], pos2[mo]]
            fds = (
                ds[var_ice]
                .isel({"time": mo})
                .plot(
                    ax=ax,
                    x=xvar,
                    y=yvar,
                    levels=[0.15, 0.4, 0.6, 0.8, 1],
                    transform=ccrs.PlateCarree(),
                    cmap=cmap,
                    add_colorbar=False,
                )
            )
            antarctic_regions.plot_regions(
                ax=ax,
                add_label=False,
                label="abbrev",
                line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
            )
            if pos2[mo] == 0:
                if len(model) > 12:
                    fsize = 12
                else:
                    fsize = 14
                ax.text(
                    0.03,
                    0.04,
                    model.replace("_", " "),
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    backgroundcolor="white",
                    fontsize=fsize,
                )
            ax.set_extent([-180, 180, -53, -90], ccrs.PlateCarree())
            ax.coastlines(color=[0.3, 0.3, 0.3])
            ax.set_facecolor([0.55, 0.55, 0.6])
            ax.set_title("")
        pos1 = [0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2]  # row
        pos2 = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]  # col
        xvar = lib.find_lon(obs)
        yvar = lib.find_lat(obs)
        for mo in range(0, 12):
            ax = axs[pos1[mo], pos2[mo]]
            obs[var_obs].isel({"time": mo}).plot(
                ax=ax,
                x=xvar,
                y=yvar,
                levels=[0.15, 0.4, 0.6, 0.8, 1],
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                add_colorbar=False,
            )
            antarctic_regions.plot_regions(
                ax=ax,
                add_label=False,
                label="abbrev",
                line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
            )
            if pos2[mo] == 0:
                ax.text(
                    0.03,
                    0.04,
                    "Reference",
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    backgroundcolor="white",
                    fontsize=14,
                )
            ax.set_extent([-180, 180, -53, -90], ccrs.PlateCarree())
            ax.coastlines(color=[0.3, 0.3, 0.3])
            ax.set_facecolor([0.55, 0.55, 0.6])
            ax.set_title(months[mo], fontsize=18)
        plt.suptitle(title, fontsize=26)
        cbar = plt.colorbar(
            fds,
            ax=axs[0:2, :],
            pad=0.02,
            aspect=25,
        )
        cbar.ax.tick_params(labelsize=18)
        cbar.set_label(label="ice fraction", size=18)
        cbar = plt.colorbar(
            fds,
            ax=axs[2:, :],
            pad=0.02,
            aspect=25,
        )
        cbar.ax.tick_params(labelsize=18)
        cbar.set_label(label="ice fraction", size=18)
        fig_path = os.path.join(
            metrics_output_path, model.replace(" ", "_") + "_antarctic_regions.png"
        )
        plt.savefig(fig_path)
        plt.close()
        meta.update_plots(
            "Antarctic" + model.replace(" ", "_"),
            fig_path,
            "Antarctic_map",
            "Maps of monthly Antarctic ice fraction",
        )
    except Exception as e:
        print("Could not create Antarctic maps.")
        print(e)
        if plt.get_fignums():
            plt.close()
    return meta


def annual_cycle_plots(df, fig_dir, reference_data_set, meta):
    # Annual cycle line figure
    # Model mean climatology
    labels = {
        "antarctic": "Antarctic",
        "arctic": "Arctic",
        "ca": "Central Arctic",
        "na": "North Atlantic",
        "np": "North Pacific",
        "io": "Indian Ocean",
        "sa": "South Atlantic",
        "sp": "South Pacific",
    }
    pos = {
        "antarctic": (0, 1),
        "arctic": (0, 0),
        "ca": (1, 0),
        "na": (2, 0),
        "np": (3, 0),
        "io": (1, 1),
        "sa": (2, 1),
        "sp": (3, 1),
    }
    wts = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) / 365
    for mod in df:
        try:
            f1, axs = plt.subplots(4, 2, figsize=(8, 8))
            if mod != "Reference":
                for rgn in ["arctic", "antarctic", "ca", "sa", "np", "sp", "na", "io"]:
                    # Get realization spread
                    climr = []
                    for real in df[mod][rgn]:
                        if real != "model_mean":
                            tmp = df[mod][rgn][real]["monthly_climatology"]
                            tmp = [float(x) for x in tmp]
                            climr = climr + tmp
                    climr = np.array(climr)
                    climr = np.reshape(climr, (int(len(climr) / 12), 12))
                    mins = np.min(climr, axis=0)
                    maxs = np.max(climr, axis=0)

                    # Get means
                    clim = df[mod][rgn]["model_mean"]["monthly_climatology"]
                    climobs = df["Reference"][rgn][reference_data_set][
                        "monthly_climatology"
                    ]
                    clim = np.array([float(x) for x in clim])
                    climobs = np.array([float(x) for x in climobs])
                    time = np.array([x for x in range(1, 13)])
                    climmean = np.ones(12) * np.average(clim, weights=wts)
                    climmeanobs = np.ones(12) * np.average(climobs, weights=wts)

                    # Make figure
                    ind1 = pos[rgn][0]
                    ind2 = pos[rgn][1]
                    axs[ind1, ind2].plot(
                        time,
                        climmean,
                        color="darkorange",
                        linewidth=1.5,
                        linestyle="dashed",
                        zorder=1,
                    )
                    axs[ind1, ind2].plot(
                        time,
                        climmeanobs,
                        color=[0.2, 0.2, 0.2],
                        linewidth=1.5,
                        linestyle="dashed",
                        zorder=1,
                    )
                    axs[ind1, ind2].fill_between(
                        time, mins, maxs, color="darkorange", alpha=0.3, zorder=1
                    )
                    axs[ind1, ind2].plot(time, clim, color="darkorange", label=mod)
                    axs[ind1, ind2].plot(
                        time, climobs, color=[0.2, 0.2, 0.2], label=reference_data_set
                    )
                    axs[ind1, ind2].set_title(labels[rgn], fontsize=10)
                    axs[ind1, ind2].xaxis.set_tick_params(which="minor", bottom=False)
                    axs[ind1, ind2].set_xlim([1, 12])
                    axs[ind1, ind2].set_xticks([])
                    axs[ind1, ind2].minorticks_on()
                    if ind2 == 0:
                        axs[ind1, ind2].set_ylabel("$10^6$ $km^2$")
                axs[3, 0].set_xticks(time)
                axs[3, 1].set_xticks(time)
                axs[3, 0].set_xlabel("month")
                axs[3, 1].set_xlabel("month")
                axs[0, 0].legend(loc="upper right", fontsize=9)
                plt.suptitle(mod)
                figfile = os.path.join(fig_dir, mod + "_annual_cycle.png")
                plt.savefig(figfile)
                plt.close()
                meta.update_plots(
                    "ann_cycle_" + mod,
                    figfile,
                    "annual_cycle_plot",
                    "Plot of model mean regional annual cycles in sea ice area",
                )
        except Exception as e:
            print("Could not create annual cycle plots for model", mod)
            print(e)
            if plt.get_fignums():
                plt.close()
    return meta


def metrics_bar_chart(model_list, metrics, reference_data_set, fig_dir, meta):
    try:
        sector_list = [
            "Central Arctic Sector",
            "North Atlantic Sector",
            "North Pacific Sector",
            "Indian Ocean Sector",
            "South Atlantic Sector",
            "South Pacific Sector",
        ]
        sector_short = ["ca", "na", "np", "io", "sa", "sp"]
        fig7, ax7 = plt.subplots(6, 1, figsize=(5, 9))
        mlabels = model_list
        ind = np.arange(len(mlabels))  # the x locations for the groups
        width = 0.3
        for inds, sector in enumerate(sector_list):
            # Assemble data
            mse_clim = []
            mse_ext = []
            clim_err_x = []
            clim_err_y = []
            ext_err_y = []
            rgn = sector_short[inds]
            for nmod, model in enumerate(model_list):
                mse_clim.append(
                    float(
                        metrics["RESULTS"][model][rgn]["model_mean"][
                            reference_data_set
                        ]["monthly_clim"]["mse"]
                    )
                )
                mse_ext.append(
                    float(
                        metrics["RESULTS"][model][rgn]["model_mean"][
                            reference_data_set
                        ]["total_extent"]["mse"]
                    )
                )
                # Get spread, only if there are multiple realizations
                if len(metrics["RESULTS"][model][rgn].keys()) > 2:
                    for r in metrics["RESULTS"][model][rgn]:
                        if r != "model_mean":
                            clim_err_x.append(ind[nmod])
                            clim_err_y.append(
                                float(
                                    metrics["RESULTS"][model][rgn][r][
                                        reference_data_set
                                    ]["monthly_clim"]["mse"]
                                )
                            )
                            ext_err_y.append(
                                float(
                                    metrics["RESULTS"][model][rgn][r][
                                        reference_data_set
                                    ]["total_extent"]["mse"]
                                )
                            )

            # plot data
            if len(model_list) < 4:
                mark_size = 9
            elif len(model_list) < 12:
                mark_size = 3
            else:
                mark_size = 1
            ax7[inds].bar(
                ind - width / 2.0, mse_clim, width, color="b", label="Ann. Cycle"
            )
            ax7[inds].bar(ind, mse_ext, width, color="r", label="Ann. Mean")
            if len(clim_err_x) > 0:
                ax7[inds].scatter(
                    [x - width / 2.0 for x in clim_err_x],
                    clim_err_y,
                    marker="D",
                    s=mark_size,
                    color="k",
                )
                ax7[inds].scatter(
                    clim_err_x, ext_err_y, marker="D", s=mark_size, color="k"
                )
            # xticks
            if inds == len(sector_list) - 1:
                ax7[inds].set_xticks(ind + width / 2.0, mlabels, rotation=90, size=7)
            else:
                ax7[inds].set_xticks(ind + width / 2.0, labels="")
            # yticks
            if len(clim_err_y) > 0:
                datamax = np.max(
                    np.concatenate((np.array(clim_err_y), np.array(ext_err_y)))
                )
            else:
                datamax = np.max(
                    np.concatenate((np.array(mse_clim), np.array(mse_ext)))
                )
            ymax = (datamax) * 1.3
            ax7[inds].set_ylim(0.0, ymax)
            if ymax < 0.1:
                ticks = np.linspace(0, 0.1, 6)
                labels = [str(round(x, 3)) for x in ticks]
            elif ymax < 1:
                ticks = np.linspace(0, 1, 5)
                labels = [str(round(x, 1)) for x in ticks]
            elif ymax < 4:
                ticks = np.linspace(0, round(ymax), num=round(ymax / 2) * 2 + 1)
                labels = [str(round(x, 1)) for x in ticks]
            elif ymax > 10:
                ticks = range(0, round(ymax), 5)
                labels = [str(round(x, 0)) for x in ticks]
            else:
                ticks = range(0, round(ymax))
                labels = [str(round(x, 0)) for x in ticks]

            ax7[inds].set_yticks(ticks, labels, fontsize=8)
            # labels etc
            ax7[inds].set_ylabel("10${^1}{^2}$km${^4}$", size=8)
            ax7[inds].grid(True, linestyle=":")
            ax7[inds].annotate(
                sector,
                (0.35, 0.8),
                xycoords="axes fraction",
                size=9,
            )
        # Add legend, save figure
        ax7[0].legend(loc="upper right", fontsize=6)
        plt.suptitle("Mean Square Error relative to " + reference_data_set, y=0.91)
        figfile = os.path.join(fig_dir, "MSE_bar_chart.png")
        plt.savefig(figfile)
        plt.close()
        meta.update_plots(
            "bar_chart", figfile, "regional_bar_chart", "Bar chart of regional MSE"
        )
    except Exception as e:
        print("Could not create metrics plot.")
        print(e)
        if plt.get_fignums():
            plt.close()
    return meta
