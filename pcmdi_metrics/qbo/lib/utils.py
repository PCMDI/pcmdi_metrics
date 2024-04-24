import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import xcdat as xc


def generate_target_grid(target_grid):
    """Generate common grid for interpolation

    Parameters
    ----------
    target_grid : str
        For example, "2.5x2.5"

    Returns
    -------
    xcdat grid
        _description_
    """

    # generate target grid
    res = target_grid.split("x")
    lat_res = float(res[0])
    lon_res = float(res[1])
    start_lat = -90.0 + lat_res / 2
    start_lon = 0.0
    end_lat = 90.0 - lat_res / 2
    end_lon = 360.0 - lon_res
    t_grid = xc.create_uniform_grid(
        start_lat, end_lat, lat_res, start_lon, end_lon, lon_res
    )

    return t_grid


def select_time_range(ds, start, end):
    """Subset time range

    Parameters
    ----------
    ds : xarray dataset
        dataset to subset
    start : str
        Starting year and month in format of "yyyy-mm"
    end : str
        Ending year and month in format of "yyyy-mm"

    Returns
    -------
    xarray.Dataset
        subsetted dataset
    """

    # USER DEFINED PERIOD
    start_yr = int(start.split("-")[0])
    start_mo = int(start.split("-")[1])
    start_da = 1
    end_yr = int(end.split("-")[0])
    end_mo = int(end.split("-")[1])

    print("end_yr:", end_yr)
    print("end_mo:", end_mo)

    ds_tmp = ds.time.dt.days_in_month.sel(time=(ds.time.dt.year == end_yr))
    # end_da = int(
    #    ds_tmp.time.dt.days_in_month.sel(time=(ds_tmp.time.dt.month == end_mo))[-1]
    # )
    end_da = int(ds_tmp.time[-1].dt.day)

    start_yr_str = str(start_yr).zfill(4)
    start_mo_str = str(start_mo).zfill(2)
    start_da_str = str(start_da).zfill(2)
    end_yr_str = str(end_yr).zfill(4)
    end_mo_str = str(end_mo).zfill(2)
    end_da_str = str(end_da).zfill(2)

    # Subset given time period
    ds = ds.sel(
        time=slice(
            start_yr_str + "-" + start_mo_str + "-" + start_da_str + " 00:00:00",
            end_yr_str + "-" + end_mo_str + "-" + end_da_str + " 23:59:59",
        )
    )

    print("start_yr_str is ", start_yr_str)
    print("start_mo_str is ", start_mo_str)
    print("start_da is ", start_da)
    print("end_yr_str is ", end_yr_str)
    print("end_mo_str is ", end_mo_str)
    print("end_da is", end_da)

    return ds


def test_plot_time_series(da, output_file, std=None, title=None):
    """Plot time series to visualize interim output

    Parameters
    ----------
    da : DataArray
        DataArray to plot time series
    output_file : str
        file path and name for saving image
    std : float, optional
        standard deviation used for the threshold
    title : str, optional
        optional title, by default None
    """

    fig, ax = plt.subplots()

    da.plot(ax=ax)

    if std is not None:
        ax.axhline(y=0.5 * std, c="k", ls="--")
        ax.axhline(y=-0.5 * std, c="k", ls="--")
        y = da.to_numpy()
        x = da.time.to_numpy()

        ax.fill_between(
            x,
            y,
            0.5 * std,
            where=y > 0.5 * std,
            color="red",
            interpolate=True,
            alpha=0.5,
        )

        ax.fill_between(
            x,
            y,
            -0.5 * std,
            where=y < -0.5 * std,
            color="blue",
            interpolate=True,
            alpha=0.5,
        )

    if title is not None:
        ax.set_title(title)

    fig.savefig(output_file)


def test_plot_maps(std2_map, std2_map_phase, fig_title=None, output_file=None):
    """_summary_

    Parameters
    ----------
    std2_map : xarray DataArray
        _description_
    std2_map_phase : dict
        _description_
    """

    proj_setup = ccrs.PlateCarree(central_longitude=180)
    proj = ccrs.PlateCarree()

    fig, axs = plt.subplots(
        nrows=4, ncols=1, subplot_kw={"projection": proj_setup}, figsize=(13, 12)
    )

    axs = axs.flatten()

    for i, ax in enumerate(axs):
        if i == 0:
            data = std2_map
            title = "All"
            cmap = "viridis"
        elif i == 1:
            data = std2_map_phase["east"]
            title = "QBO East"
            cmap = "viridis"
        elif i == 2:
            data = std2_map_phase["west"]
            title = "QBO West"
            cmap = "viridis"
        elif i == 3:
            data = std2_map_phase["east"] - std2_map_phase["west"]
            title = "Diff: East - West"
            cmap = "coolwarm"

        data.plot(
            ax=ax,
            transform=proj,
            cmap=cmap,
        )

        # Title each subplot
        ax.set_title(title)

        # Draw the coastines for each subplot
        ax.coastlines()

        # Create gridlines
        gl = ax.gridlines(
            crs=proj, linewidth=1, color="grey", alpha=0.2, linestyle="--"
        )
        # Manipulate gridlines number and spaces
        gl.ylocator = mticker.FixedLocator(np.arange(-90, 90, 20))
        gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, 60))
        gl.top_labels = False
        gl.bottom_labels = True
        gl.left_labels = True
        gl.right_labels = False

    if fig_title is not None:
        fig.text(0.5, 0.95, fig_title, ha="center", va="bottom", fontsize=15)
        fig.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.05, hspace=0.15)

    if output_file is not None:
        fig.savefig(output_file)


def standardize_lat_lon_name_in_dataset(ds):
    for coord in ("lat", "lon"):
        coord_key_in_file = find_coord_key(ds, coord)

        if coord == coord_key_in_file:
            pass
        else:
            ds = ds.rename({coord_key_in_file: coord})

        # convert coord in descending order to ascending
        if float(ds[coord][0].values) > float(ds[coord][-1].values):
            if coord == "lat":
                ds = ds.reindex(lat=list(ds.lat[::-1]))
            elif coord == "lon":
                ds = ds.reindex(lon=list(ds.lon[::-1]))

    return ds


def find_coord_key(ds, coord):
    for coord_key in list(ds.coords.keys()):
        if coord in coord_key.lower():
            return coord_key


def diag_plot(
    std2_map, std2_map_diff, fig_title=None, output_file=None, sub_region=None
):
    """_summary_

    Parameters
    ----------
    std2_map : xarray DataArray
        _description_
    std2_map_diff : xarray DataArray
        _description_
    """

    proj_setup = ccrs.PlateCarree(central_longitude=180)
    proj = ccrs.PlateCarree()

    fig, ax = plt.subplots(subplot_kw={"projection": proj_setup}, figsize=(8, 3))

    lon1 = 0
    lon2 = 360
    lat1 = -30
    lat2 = 30
    ax.set_extent([lon1, lon2, lat1, lat2], crs=ccrs.PlateCarree())

    data = std2_map.sel(lon=slice(lon1, lon2)).sel(
        lat=slice(lat1, lat2)
    )  # "All" --- contour
    data2 = std2_map_diff.sel(lon=slice(lon1, lon2)).sel(
        lat=slice(lat1, lat2)
    )  # "Diff: East - West" --- color,

    # Adjust colormap
    cmap = mycolormap()

    levels_shade = [-6, -4, -2, -1, 1, 2, 4, 6]
    levels_contour = range(8, 30, 2)

    data.plot.contour(
        ax=ax,
        transform=proj,
        levels=levels_contour,
        colors="grey",
        linewidths=1,
    )

    data2.plot(
        ax=ax,
        transform=proj,
        cmap=cmap,
        cbar_kwargs={"orientation": "horizontal", "ticks": levels_shade, "aspect": 40},
        levels=levels_shade,
        extend="both",
    )

    # Title each subplot
    if fig_title is not None:
        ax.set_title(fig_title)

    # Add coastlines and other features if desired
    ax.coastlines(resolution="50m", color="black", linewidth=1)
    # ax.add_feature(cfeature.LAND, edgecolor='black')

    # plot land area in grey
    land_50m = cfeature.NaturalEarthFeature(
        "physical", "land", "50m", edgecolor=None, facecolor="lightgrey"
    )
    ax.add_feature(land_50m)

    # Create gridlines
    gl = ax.gridlines(crs=proj, linewidth=1, color="grey", alpha=0.2, linestyle="--")
    # Manipulate gridlines number and spaces
    gl.ylocator = mticker.FixedLocator(np.arange(-80, 80, 20))
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, 60))
    gl.top_labels = False
    gl.bottom_labels = True
    gl.left_labels = True
    gl.right_labels = False

    # Draw a rectangle to highlight the sub-region
    if sub_region is not None:
        lon_min, lon_max, lat_min, lat_max = sub_region
        ax.plot(
            [lon_min, lon_max, lon_max, lon_min, lon_min],
            [lat_min, lat_min, lat_max, lat_max, lat_min],
            color="lightgreen",
            linestyle="--",
            transform=ccrs.PlateCarree(),
        )

    if output_file is not None:
        fig.tight_layout()
        fig.savefig(output_file)


def mycolormap():
    """Combine two colormap to generate a new colormap for blue-white(middle)-yellow-red

    Returns
    -------
    matplotlib colormap
    """
    # Adjust colormap

    # sample the colormaps that you want to use. Use 128 from each so we get 256
    # colors in total
    colors1 = plt.cm.Blues_r(np.linspace(0.0, 1, 127))
    colors2 = plt.cm.YlOrBr(np.linspace(0, 1, 127))

    # add white in the middle
    colors1 = np.append(colors1, [[0, 0, 0, 0]], axis=0)
    colors2 = np.vstack((np.array([0, 0, 0, 0]), colors2))

    # combine them and build a new colormap
    colors = np.vstack((colors1, colors2))
    mymap = mcolors.LinearSegmentedColormap.from_list("my_colormap", colors)

    return mymap
