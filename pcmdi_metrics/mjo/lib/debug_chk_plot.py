import os

import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import matplotlib.pyplot as plt


def debug_chk_plot(
        d_seg_x_ano, Power, OEE, segment_year,
        daSeaCyc, segment_ano_year):

    if not os.path.exists('debug'):
        os.makedirs('debug')

    """
    x = vcs.init()
    x.plot(d_seg_x_ano)
    x.png('debug/d_seg_x_ano.png')

    x.clear()
    x.plot(Power)
    x.png('debug/power.png')

    x.clear()
    x.plot(OEE)
    x.png('debug/OEE.png')

    x.clear()
    x.plot(segment_year)
    x.png('debug/segment.png')
    """

    print('type(daSeaCyc)', type(daSeaCyc))
    print('daSeaCyc.shape:', daSeaCyc.shape)
    print(daSeaCyc.getAxis(0))
    print(daSeaCyc.getAxis(1))
    print(daSeaCyc.getAxis(2))
    plot_map(daSeaCyc[0], 'debug/daSeaCyc.png')

    print('type(segment_ano_year)', type(segment_ano_year))
    print('segment_ano_year.shape:', segment_ano_year.shape)
    print(segment_ano_year.getAxis(0))
    print(segment_ano_year.getAxis(1))
    print(segment_ano_year.getAxis(2))
    plot_map(segment_ano_year[0], 'debug/segment_ano.png')


def plot_map(data, filename):
    fig = plt.figure()
    lons = data.getLongitude()
    lats = data.getLatitude()
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    ax.contourf(lons, lats, data,
                transform=ccrs.PlateCarree(),
                cmap='viridis')
    ax.coastlines()
    ax.set_global()
    ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
    ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    fig.savefig(filename)
