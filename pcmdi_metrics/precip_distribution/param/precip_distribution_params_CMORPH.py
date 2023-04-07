import datetime
import os

mip = "obs"
dat = "CMORPH"
var = "pr"
frq = "day"
ver = "v20220827"

# prd = [2001, 2019]  # analysis period
prd = [1998, 2012]  # analysis period
# fac = 24  # factor to make unit of [mm/day]
fac = 86400  # factor to make unit of [mm/day]
# res = [0.25, 0.25]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [0.5, 0.5]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [1, 1]  # target horizontal resolution [degree] for interporation (lon, lat)
res = [2, 2]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [4, 4]  # target horizontal resolution [degree] for interporation (lon, lat)

modpath = "/p/user_pub/PCMDIobs/obs4MIPs/NOAA/CMORPH-1-0-CRT/day/pr/1x1/latest/"
mod = "pr_day_CMORPH-1-0-CRT_PCMDIFROGS_1x1_19980101-20121231.nc"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmpdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"
results_dir = os.path.join(pmpdir, "%(output_type)", "precip", "intensity.frequency_distribution", "%(mip)", "%(case_id)")

ref = "IMERG"  # For Perkins socre, P10, and P90
ref_dir = os.path.join(pmpdir, "%(output_type)", "precip", "intensity.frequency_distribution", "obs", "%(case_id)")
