import os

import cartopy.crs as ccrs
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

    #x.clear()
    #x.plot(daSeaCyc)
    #x.png('debug/daSeaCyc.png')
    plot_map(daSeaCyc, 'debug/daSeaCyc.png')

    #x.clear()
    #x.plot(segment_ano_year)
    #x.png('debug/segment_ano.png')
    plot_map(segment_ano_year, 'debug/daSeaCyc.png')


def plot_map(data, filename):
    lons = data.getLongitude()
    lats = data.getLatitude()
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    ax.contourf(lons, lats, data,
                transform=ccrs.PlateCarree(),
                cmap='viridis')
    ax.coastlines()
    ax.set_global()
    plt.savefig(filename)
