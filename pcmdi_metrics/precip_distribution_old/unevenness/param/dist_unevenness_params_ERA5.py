import datetime
import os

mip = "obs"
dat = "ERA5"
var = "pr"
frq = "day"
# ver = "v20210717"
# ver = "v20220108"
# ver = "v20220205"
ver = "v20220219"

# prd = [2001, 2019]  # analysis period
prd = [1979, 2018]  # analysis period
# fac = 24  # factor to make unit of [mm/day]
fac = 86400  # factor to make unit of [mm/day]
# res = [0.25, 0.25]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [0.5, 0.5]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [1, 1]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [2, 2]  # target horizontal resolution [degree] for interporation (lon, lat)
res = [4, 4]  # target horizontal resolution [degree] for interporation (lon, lat)

indir = "/p/user_pub/PCMDIobs/obs4MIPs/ECMWF/ERA-5/day/pr/1x1/latest/"
infile = "pr_day_ERA-5_PCMDIFROGS_1x1_19790101-20181231.nc"

# case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
case_id = ver
# pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/unevenness/"+ver+"/"
# results_dir = os.path.join(
#     pmpdir, '%(output_type)', 'precip_distribution', '%(mip)', '%(case_id)')
pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/"
results_dir = os.path.join(
    pmpdir, '%(output_type)', 'unevenness', '%(mip)', '%(case_id)')

xmldir = "./xml_obs/"
if not (os.path.isdir(xmldir)):
    os.makedirs(xmldir)
os.system(
    "cdscan -x " + xmldir + var + "." + frq + "." + dat + ".xml " + indir + infile
)

modpath = xmldir
mod = var + "." + frq + "." + dat + ".xml"
