import xarray
import pandas as pd
from pcmdi_metrics.drought.lib import spi
from pcmdi_metrics.drought.lib import cdd
import matplotlib as mpl

# driver to call SPI and CDD

# PMP PARSER READIN

# LOOP FOR OBS or MODELS
    # LOOP FOR RUNS
        # CALL SPI -- calculated for each grid --> output to nc file
            # Input: monthly precipitation over land (OBS: CPC over CONUS)
        # CALL CDD -- calculated for each grid --> output to nc file
            # Input: daily precipitation over land

# OUTPUT TO JSON (which output to JSON??)


# The input data should be monthly mean precipitaion. The data used here can be downloaded at https://psl.noaa.gov/data/gridded/data.unified.daily.conus.html
observe_path = "/Users/lee1043/Documents/Research/DATA/CPC/precip.V1.0.mon.mean.nc"
observe = xarray.open_dataset(observe_path)
observe_df = observe.to_dataframe().reset_index()
observe_regional_mean = observe_df.groupby('time').mean().reset_index()
date = observe_regional_mean.time

# Build a dataframe to save the SPI3, SPI6, SPI12 and SPI36 of the regional mean monthly precipitation
observe_regional_spi = pd.DataFrame(columns=['SPI3','SPI6','SPI12','SPI36'], index=date)
for scale, col in zip([3,6,12,36], observe_regional_spi.columns):
    observe_regional_spi[col] = spi(observe_regional_mean.precip,observe_regional_mean.precip, scale)    
observe_regional_spi = observe_regional_spi.reset_index()

# Here I plot the regional mean SPI6 over the total period
fig, (ax) = plt.subplots(nrows=1, ncols=1, sharex=True,sharey=True,figsize=(20,8))
ax.fill_between(observe_regional_spi.time, 0, observe_regional_spi.SPI6, where=observe_regional_spi.SPI6 >= 0, facecolor='blue', interpolate=True)
ax.fill_between(observe_regional_spi.time, 0, observe_regional_spi.SPI6, where=observe_regional_spi.SPI6 < 0, facecolor='red', interpolate=True)
ax.set_ylabel('Regional Mean SPI6 over CONUS',fontsize=22)
ax.set_xlabel("Date",fontsize=22)
