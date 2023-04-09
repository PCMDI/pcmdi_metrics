import datetime
import os

mip = "cmip5"
# exp = "historical"
exp = "amip"
var = "pr"
frq = "day"
ver = "v20230407"

prd = [1985, 2004]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
# res = [0.5, 0.5]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [1, 1]  # target horizontal resolution [degree] for interporation (lon, lat)
res = [2, 2]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [4, 4]  # target horizontal resolution [degree] for interporation (lon, lat)

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
# case_id = ver
pmpdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"
results_dir = os.path.join(pmpdir, "%(output_type)", "precip", "%(mip)", exp, "%(case_id)", "intensity.frequency_distribution")

ref = "IMERG"  # For Perkins socre, P10, and P90
ref_dir = os.path.join(pmpdir, "%(output_type)", "precip", "obs", "%(case_id)", "intensity.frequency_distribution")
