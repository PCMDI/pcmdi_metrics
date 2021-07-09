import xarray 
import numpy as np
import scipy.stats
import pandas as pd
from mpl_toolkits.basemap import Basemap

#cdd is the function to calculate the CDD, the output is a dataframe grouped by lat lon and time_period.

# data_df should be the input daily precipitation dataframe consists of lat, lon, time_period and daily precipitation.
# pr_name is the variable name of precipitation
# period_name is the variable name of period used. like 'year' or 'month'.

def cdd(data_df,pr_name,period_name):
    data_df['Dryness']=np.where(data_df[pr_name]>=1,'non-dry','dry')
    dry_duration = pd.DataFrame(data_df.groupby(['lat','lon',period_name,data_df['Dryness'],(data_df['Dryness']!=data_df['Dryness'].shift()).cumsum()]).size().reset_index(level=4,drop=True).rename('duration'))
    dry_duration_reset_index = dry_duration.reset_index()
    dry_duration_reset_index = dry_duration_reset_index[dry_duration_reset_index.Dryness=='dry']
    CDD_each_grid = pd.DataFrame(dry_duration_reset_index.groupby(['lat','lon',period_name]).duration.max())
    CDD_each_grid = CDD_each_grid.rename(columns={'duration':"CDD"})
    return CDD_each_grid.reset_index()

#score_map is a function to plot a variable on map

# data should be the input dataframe.
# variable_name is varable name of the vairable used like CDD.

def score_map(data,variable_name):

    val_pivot_df = data.pivot(index='lat', columns='lon', values=variable_name)
    lons = val_pivot_df.columns.values
    lats = val_pivot_df.index.values
    fig, ax = plt.subplots(1, figsize=(8,8))
    m = Basemap(projection='merc',
            llcrnrlat=data.dropna().min().lat-2
            , urcrnrlat=data.dropna().max().lat+2
            , llcrnrlon=data.dropna().min().lon-2
            , urcrnrlon=data.dropna().max().lon+2
            , resolution='i', area_thresh=10000
            )
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    x, y = np.meshgrid(lons,lats) 
    px,py = m(x,y) 
    data_values = val_pivot_df.values
    masked_data = np.ma.masked_invalid(data_values)
    cmap = plt.cm.viridis
    m.pcolormesh(px, py, masked_data, cmap=cmap,  shading='flat')
    m.colorbar(label=variable_name)
