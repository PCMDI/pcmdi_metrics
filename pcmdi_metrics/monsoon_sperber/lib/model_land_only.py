import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np


def model_land_only(model, model_timeseries, lf, debug=False):
    # -------------------------------------------------
    # Mask out over ocean grid
    # - - - - - - - - - - - - - - - - - - - - - - - - -

    if debug:
        plot_map(model_timeseries[0], "_".join(["test", model, "beforeMask.png"]))
        print("debug: plot for beforeMask done")

    # Check land fraction variable to see if it meet criteria
    # (0 for ocean, 100 for land, no missing value)

    if np.max(lf) == 1.0:
        lf = lf * 100.0

    opt1 = False

    if opt1:  # Masking out partial ocean grids as well
        # Mask out ocean even fractional (leave only pure ocean grid)
        model_timeseries_masked = model_timeseries.where(lf > 0 & lf < 100)

    else:  # Mask out only full ocean grid & use weighting for partial ocean grid
        model_timeseries_masked = model_timeseries.where(lf > 0)

        if model == "EC-EARTH":
            # Mask out over 90% land grids for models those consider river as
            # part of land-sea fraction. So far only 'EC-EARTH' does..
            model_timeseries_masked = model_timeseries.where(lf > 90)

    if debug:
        plot_map(model_timeseries_masked[0], "_".join(["test", model, "afterMask.png"]))
        print("debug: plot for afterMask done")

    return model_timeseries_masked


def plot_map(data, filename):
    lons = data["lon"]
    lats = data["lat"]
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    ax.contourf(lons, lats, data, transform=ccrs.PlateCarree(), cmap="viridis")
    ax.coastlines()
    ax.set_global()
    plt.savefig(filename)
