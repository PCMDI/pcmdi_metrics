import datetime
import os

mip = "obs"
dat = "MERRA2"
var = "pr"
frq = "day"
ver = "v20220827"

# prd = [2001, 2019]  # analysis period
# prd = [1979, 2018]  # analysis period
prd = [1980, 2018]  # analysis period
# fac = 24  # factor to make unit of [mm/day]
fac = 86400  # factor to make unit of [mm/day]
# res = [0.25, 0.25]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [0.5, 0.5]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [1, 1]  # target horizontal resolution [degree] for interporation (lon, lat)
res = [2, 2]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [4, 4]  # target horizontal resolution [degree] for interporation (lon, lat)

modpath = "/work/ahn6/obs/MERRA2/pr/"
mod = "*.nc"

# case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
case_id = ver
# pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/"
pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/"+var+"/"
results_dir = os.path.join(
    pmpdir, '%(output_type)', '%(mip)', '%(case_id)')


ref = "IMERG" # For Perkins socre, P10, and P90
ref_dir = os.path.join(
    pmpdir, '%(output_type)', "obs", '%(case_id)')
