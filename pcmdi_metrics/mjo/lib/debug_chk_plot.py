import os

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter


def debug_chk_plot(d_seg_x_ano, Power, OEE, segment_year, daSeaCyc, segment_ano_year):

    os.makedirs("debug", exist_ok=True)

    """ FIX ME ---
    x = vcs.init()
    x.plot(d_seg_x_ano)
    x.png('debug/d_seg_x_ano.png')

    x.clear()
    x.plot(Power)
    x.png('debug/power.png')

    x.clear()
    x.plot(OEE)
    x.png('debug/OEE.png')
    """

    print("type(segment_year)", type(segment_year))
    print("segment_year.shape:", segment_year.shape)
    print(segment_year.getAxis(0))
    print(segment_year.getAxis(1))
    print(segment_year.getAxis(2))
    plot_map(segment_year[0], "debug/segment.png")

    print("type(daSeaCyc)", type(daSeaCyc))
    print("daSeaCyc.shape:", daSeaCyc.shape)
    plot_map(daSeaCyc[0], "debug/daSeaCyc.png")

    print("type(segment_ano_year)", type(segment_ano_year))
    print("segment_ano_year.shape:", segment_ano_year.shape)
    print(segment_ano_year.getAxis(0))
    print(segment_ano_year.getAxis(1))
    print(segment_ano_year.getAxis(2))
    plot_map(segment_ano_year[0], "debug/segment_ano.png")


def plot_map(data, filename):
    fig = plt.figure(figsize=(10, 6))
    lons = data.getLongitude()
    lats = data.getLatitude()
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    im = ax.contourf(lons, lats, data, transform=ccrs.PlateCarree(), cmap="viridis")
    ax.coastlines()
    ax.set_global()
    ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
    ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    plt.colorbar(im)
    ax.set_aspect("auto", adjustable=None)
    fig.savefig(filename)
