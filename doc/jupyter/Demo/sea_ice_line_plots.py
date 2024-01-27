import cftime
import matplotlib.pyplot as plt
import xarray as xr
import xcdat as xc

# Load data -- model

ds = xc.open_mfdataset(
    "/p/user_pub/pmp/demo/sea-ice/links_siconc/E3SM-1-0/historical/r1i2p2f1/siconc/siconc_SImon_E3SM-1-0_historical_r1i2p2f1_*_*.nc"
)
area = xc.open_dataset(
    "/p/user_pub/pmp/demo/sea-ice/links_area/E3SM-1-0/areacello_Ofx_E3SM-1-0_historical_r1i1p1f1_gr.nc"
)

arctic = (
    (ds.siconc.where(ds.lat > 0) * 1e-2 * area.areacello * 1e-6)
    .where(ds.siconc > 0.15)
    .sum(("lat", "lon"))
)
"""
Note for the above line
- where siconc > 0.15: to consider sea ice extent instead of total sea ice area
- multiply 1e-2: to convert percentage (%) to fraction
"""

# Load data -- observation

obs_file = "/p/user_pub/pmp/demo/sea-ice/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc"
obs = xc.open_dataset(obs_file)
obs_area = 625
obs_arctic = (
    obs.ice_conc.where(obs.lat > 0).where(obs.ice_conc > 0.15) * 1e-2 * obs_area
).sum(("xc", "yc"))
"""
Note for the above lines
- obs_area = 625  # area size represented by each grid (625 km^2 = 25 km x 25 km resolution)
- where siconc > 0.15: to consider sea ice extent instead of total sea ice area
- multiply 1e-2: to convert percentage (%) to fraction
"""


# Time series plot
arctic.sel({"time": slice("1981-01-01", "2010-12-31")}).plot(label="E3SM-1-0")
obs_arctic.plot(label="OSI-SAF")
plt.title("Arctic monthly sea ice extent")
plt.ylabel("Extent (km${^2}$)")
plt.xlabel("time")
plt.xlim(
    [
        cftime.DatetimeNoLeap(1981, 1, 16, 12, 0, 0, 0, has_year_zero=True),
        cftime.DatetimeNoLeap(2010, 12, 16, 12, 0, 0, 0, has_year_zero=True),
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
arctic_clim = arctic_ds.sel(
    {"time": slice("1981-01-01", "2010-12-31")}
).temporal.climatology("siconc", freq="month")
arctic_clim["time"] = [x for x in range(1, 13)]

obs_arc_ds = xr.Dataset(
    data_vars={"ice_conc": obs_arctic, "time_bnds": obs.time_bnds},
    coords={"time": obs.time},
)
obs_clim = obs_arc_ds.temporal.climatology("ice_conc", freq="month")
obs_clim["time"] = [x for x in range(1, 13)]

arctic_clim.siconc.plot(label="E3SM-1-0")
obs_clim.ice_conc.plot(label="OSI-SAF")
plt.title("Arctic climatological sea ice extent\n1981-2010")
plt.xlabel("month")
plt.ylabel("Extent (km${^2}$)")
plt.xlim([1, 12])
plt.legend(loc="upper right", fontsize=9)
plt.savefig("Arctic_clim.png")
plt.close()
