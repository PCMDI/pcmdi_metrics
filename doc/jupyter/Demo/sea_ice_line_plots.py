import logging

import cftime
import matplotlib.pyplot as plt
import xarray as xr
import xcdat as xc

logging.getLogger("xcdat").setLevel(logging.ERROR)

# Input files and configurations ======================

MODEL_DATA = "demo_data/CMIP5_demo_timeseries/historical/ice/mon/siconc_SImon_E3SM-1-0_historical_r1i1p1f1_gr_201001-201412.nc"
MODEL_AREA = (
    "demo_data/misc_demo_data/fx/areacello_Ofx_E3SM-1-0_historical_r1i1p1f1_gr.nc"
)
MODEL_NAME = "E3SM-1-0"

OBS_DATA = (
    "demo_data/misc_demo_data/ocn/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc"
)
OBS_NAME = "OSI-SAF"

START_YEAR = 2010
END_YEAR = 2014

# =======================================================

# Load data -- model
ds = xc.open_mfdataset(MODEL_DATA)
area = xc.open_dataset(MODEL_AREA)

arctic = (
    (ds.siconc.where(ds.lat > 0) * 1e-2 * area.areacello * 1e-6)
    .where(ds.siconc > 15)
    .sum(("lat", "lon"))
)
"""
Note for the above line
- where siconc > 15: to consider sea ice extent instead of total sea ice area (criteria: 15%)
- multiply 1e-2: to convert percentage (%) to fraction
"""

# Load data -- observation
obs_file = OBS_DATA
obs = xc.open_dataset(obs_file)
obs_area = 625
obs_arctic = (
    obs.ice_conc.where(obs.lat > 0).where(obs.ice_conc > 15) * 1e-2 * obs_area
).sum(("xc", "yc"))
"""
Note for the above lines
- obs_area = 625  # area size represented by each grid (625 km^2 = 25 km x 25 km resolution)
- where siconc > 15: to consider sea ice extent instead of total sea ice area (criteria: 15%)
- multiply 1e-2: to convert percentage (%) to fraction
"""


# Time series plot
arctic.sel({"time": slice(f"{START_YEAR}-01-01", f"{END_YEAR}-12-31")}).plot(
    label=MODEL_NAME
)
obs_arctic.plot(label=OBS_NAME)
plt.title("Arctic monthly sea ice extent")
plt.ylabel("Extent (km${^2}$)")
plt.xlabel("time")
plt.xlim(
    [
        cftime.DatetimeNoLeap(START_YEAR, 1, 16, 12, 0, 0, 0, has_year_zero=True),
        cftime.DatetimeNoLeap(END_YEAR, 12, 16, 12, 0, 0, 0, has_year_zero=True),
    ]
)
plt.legend(loc="upper right", fontsize=9)
plt.savefig("Arctic_tseries.png")
plt.close()

# Climatology plot
arctic_ds = xr.Dataset(
    data_vars={"siconc": arctic, "time_bnds": ds.time_bnds},
    coords={"time": ds.time},
)
# Calculate climatology for model
arctic_clim = arctic_ds.sel(
    {"time": slice(f"{START_YEAR}-01-01", f"{END_YEAR}-12-31")}
).temporal.climatology("siconc", freq="month")
arctic_clim["time"] = [x for x in range(1, 13)]

obs_arc_ds = xr.Dataset(
    data_vars={"ice_conc": obs_arctic, "time_bnds": obs.time_bnds},
    coords={"time": obs.time},
)
# Calculate climatology for obs
obs_clim = obs_arc_ds.temporal.climatology("ice_conc", freq="month")
obs_clim["time"] = [x for x in range(1, 13)]

arctic_clim.siconc.plot(label=MODEL_NAME)
obs_clim.ice_conc.plot(label=OBS_NAME)
plt.title(f"Arctic climatological sea ice extent\n{START_YEAR}-{END_YEAR}")
plt.xlabel("month")
plt.ylabel("Extent (km${^2}$)")
plt.xlim([1, 12])
plt.legend(loc="upper right", fontsize=9)
plt.savefig("Arctic_clim.png")
plt.close()
