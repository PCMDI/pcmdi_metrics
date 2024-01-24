import cartopy.crs as ccrs
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import regionmask
import xcdat as xc

from pcmdi_metrics.utils import create_land_sea_mask

# ----------
# Arctic
# ----------
print("Creating Arctic map")
# Load and process data
f_os_n = "/p/user_pub/pmp/demo/sea-ice/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/ice_conc_nh_ease2-250_cdr-v3p0_198801-202012.nc"
obs = xc.open_dataset(f_os_n)
obs = obs.sel({"time": slice("1988-01-01", "2020-12-31")}).mean("time")
mask = create_land_sea_mask(obs, lon_key="lon", lat_key="lat")
obs["ice_conc"] = obs["ice_conc"].where(mask < 1)
ds = obs.assign_coords(
    xc=obs["lon"], yc=obs["lat"]
)  # Assign these variables to Coordinates, which were originally data variables

# Set up regions
region_NA = np.array([[-120, 45], [-120, 80], [90, 80], [90, 45]])
region_NP = np.array([[90, 45], [90, 65], [240, 65], [240, 45]])
names = ["North_Atlantic", "North_Pacific"]
abbrevs = ["NA", "NP"]
arctic_regions = regionmask.Regions(
    [region_NA, region_NP], names=names, abbrevs=abbrevs, name="arctic"
)

# Do plotting
cmap = colors.LinearSegmentedColormap.from_list("", [[0, 85 / 255, 182 / 255], "white"])
proj = ccrs.NorthPolarStereo()
ax = plt.subplot(111, projection=proj)
ax.set_global()
ds.ice_conc.plot.pcolormesh(
    ax=ax,
    x="xc",
    y="yc",
    transform=ccrs.PlateCarree(),
    cmap=cmap,
    cbar_kwargs={"label": "ice concentration (%)"},
)
arctic_regions.plot_regions(
    ax=ax,
    add_label=False,
    label="abbrev",
    line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
)
ax.set_extent([-180, 180, 43, 90], ccrs.PlateCarree())
ax.coastlines(color=[0.3, 0.3, 0.3])
plt.annotate(
    "North Atlantic",
    (0.5, 0.2),
    xycoords="axes fraction",
    horizontalalignment="right",
    verticalalignment="bottom",
    color="white",
)
plt.annotate(
    "North Pacific",
    (0.65, 0.88),
    xycoords="axes fraction",
    horizontalalignment="right",
    verticalalignment="bottom",
    color="white",
)
plt.annotate(
    "Central\nArctic ",
    (0.56, 0.56),
    xycoords="axes fraction",
    horizontalalignment="right",
    verticalalignment="bottom",
)
ax.set_facecolor([0.55, 0.55, 0.6])
plt.title("Arctic regions with mean\nOSI-SAF ice concentration\n1988-2020")
plt.savefig("Arctic_regions.png")
plt.close()
obs.close()

# ----------
# Antarctic
# ----------
print("Creating Antarctic map")
# Load and process data
f_os_s = "/p/user_pub/pmp/demo/sea-ice/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/ice_conc_sh_ease2-250_cdr-v3p0_198801-202012.nc"
obs = xc.open_dataset(f_os_s)
obs = obs.sel({"time": slice("1988-01-01", "2020-12-31")}).mean("time")
mask = create_land_sea_mask(obs, lon_key="lon", lat_key="lat")
obs["ice_conc"] = obs["ice_conc"].where(mask < 1)
ds = obs.assign_coords(
    xc=obs["lon"], yc=obs["lat"]
)  # Assign these variables to Coordinates, which were originally data variables

# Set up regions
region_IO = np.array([[20, -90], [90, -90], [90, -55], [20, -55]])
region_SA = np.array([[20, -90], [-60, -90], [-60, -55], [20, -55]])
region_SP = np.array([[90, -90], [300, -90], [300, -55], [90, -55]])
names = ["Indian Ocean", "South Atlantic", "South Pacific"]
abbrevs = ["IO", "SA", "SP"]
arctic_regions = regionmask.Regions(
    [region_IO, region_SA, region_SP], names=names, abbrevs=abbrevs, name="antarctic"
)

# Do plotting
cmap = colors.LinearSegmentedColormap.from_list("", [[0, 85 / 255, 182 / 255], "white"])
proj = ccrs.SouthPolarStereo()
ax = plt.subplot(111, projection=proj)
ax.set_global()
ds.ice_conc.plot.pcolormesh(
    ax=ax,
    x="xc",
    y="yc",
    transform=ccrs.PlateCarree(),
    cmap=cmap,
    cbar_kwargs={"label": "ice concentration (%)"},
)
arctic_regions.plot_regions(
    ax=ax,
    add_label=False,
    label="abbrev",
    line_kws={"color": [0.2, 0.2, 0.25], "linewidth": 3},
)
ax.set_extent([-180, 180, -53, -90], ccrs.PlateCarree())
ax.coastlines(color=[0.3, 0.3, 0.3])
plt.annotate(
    "South Pacific",
    (0.50, 0.2),
    xycoords="axes fraction",
    horizontalalignment="right",
    verticalalignment="bottom",
    color="black",
)
plt.annotate(
    "Indian\nOcean",
    (0.89, 0.66),
    xycoords="axes fraction",
    horizontalalignment="right",
    verticalalignment="bottom",
    color="black",
)
plt.annotate(
    "South Atlantic",
    (0.54, 0.82),
    xycoords="axes fraction",
    horizontalalignment="right",
    verticalalignment="bottom",
    color="black",
)
ax.set_facecolor([0.55, 0.55, 0.6])
plt.title("Antarctic regions with mean\nOSI-SAF ice concentration\n1988-2020")
plt.savefig("Antarctic_regions.png")
plt.close()
obs.close()
