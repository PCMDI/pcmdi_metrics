from pcmdi_metrics.utils import create_land_sea_mask
import xarray as xr
import xcdat as xc
import os

demo_dir = "/Users/lee1043/Documents/Research/git/pcmdi_metrics_20230620_pcmdi/pcmdi_metrics/doc/jupyter/Demo/demo_data/"
demo_file = "CMIP5_demo_data/ts_Amon_ACCESS1-0_historical_r1i1p1_185001-200512.nc"

dummy_input = os.path.join(demo_dir, demo_file)
ds = xc.open_dataset(dummy_input)
mask = create_land_sea_mask(ds)
mask2 = create_land_sea_mask(ds, method="pcmdi")

mask.plot()
mask2.plot()
(mask2 - mask).plot()

from pcmdi_metrics import resources
import os

egg_pth = resources.resource_path()
source_path = os.path.join(egg_pth, "navy_land.nc")

ds_navy = xc.open_dataset(source_path)

ds_navy["sftlf"].plot()

import cdms2, cdutil

f = cdms2.open(dummy_input)

dc = f('ts')

mask_cdms = cdutil.generateLandSeaMask(dc)

lat = dc.getLatitude()
lon = dc.getLongitude()


mask_cdms_da = xr.DataArray(
    mask_cdms, 
    coords=[list(lat), list(lon)], 
    dims=["lat", "lon"], 
    name=dc.id)


mask_cdms_da.plot()


(mask2 - mask_cdms_da).plot()


(mask2 - mask_cdms_da).sum()

#
#%%time
#a = mask.to_numpy()
#
#
#%%time
#b = mask.data

