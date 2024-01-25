import cftime
import matplotlib.pyplot as plt
import xarray as xr
import xcdat as xc

ds = xc.open_mfdataset(
    "/p/user_pub/pmp/demo/sea-ice/links_siconc/E3SM-1-0/historical/r1i2p2f1/siconc/siconc_SImon_E3SM-1-0_historical_r1i2p2f1_*_*.nc"
)
area = xc.open_dataset(
    "/p/user_pub/pmp/demo/sea-ice/links_area/E3SM-1-0/areacello_Ofx_E3SM-1-0_historical_r1i1p1f1_gr.nc"
)

arctic = (ds.where(ds.lat > 0) * 1e-2 * area.areacello * 1e-6).sum(("lat", "lon"))

f_os_n = "/p/user_pub/pmp/demo/sea-ice/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc"
obs = xc.open_dataset(f_os_n)
obs_area = 625
obs_arctic = (obs.ice_conc.where(obs.lat > 0) * 1e-2 * obs_area).sum(("xc", "yc"))

# Time series plot
arctic.siconc.sel({"time": slice("1981-01-01", "2010-12-31")}).plot(label="E3SM-1-0")
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
plt.savefig("E3SM_arctic_tseries.png")
plt.close()

# Climatology plot
arctic_ds = xr.Dataset(
    data_vars={"siconc": arctic.siconc, "time_bnds": ds.time_bnds},
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
plt.savefig("E3SM_arctic_clim.png")
plt.close()
