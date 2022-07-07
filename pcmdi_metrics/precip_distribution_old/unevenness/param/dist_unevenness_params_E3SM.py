import datetime
import os

mip = "cmip6"
exp = "historical"
dat = "E3SM-1-0"
var = "pr"
frq = "day"
# ver = "v20210717"
ver = "v20220108"

prd = [1985, 2004]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
# res = [0.5, 0.5]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [1, 1]  # target horizontal resolution [degree] for interporation (lon, lat)
res = [2, 2]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [4, 4]  # target horizontal resolution [degree] for interporation (lon, lat)

indir = "/home/zhang40/CMIP6/CMIP/E3SM-Project/E3SM-1-0/historical/r1i1p1f1/day/pr/gr/v20210908/"
infile = "pr_day_E3SM-1-0_historical_r1i1p1f1_gr_*.nc"

# case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
case_id = ver
# pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/unevenness/"+ver+"/"
# results_dir = os.path.join(
#     pmpdir, '%(output_type)', 'precip_distribution', '%(mip)', exp, '%(case_id)')
pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/"
results_dir = os.path.join(
    pmpdir, '%(output_type)', 'unevenness', '%(mip)', exp, '%(case_id)')

# xmldir = "./xml_obs/"
xmldir = "./xml_e3sm/"
if not (os.path.isdir(xmldir)):
    os.makedirs(xmldir)
os.system(
    "cdscan -x " + xmldir + var + "." + frq + "." + dat + ".xml " + indir + infile
)

modpath = xmldir
mod = var + "." + frq + "." + dat + ".xml"
