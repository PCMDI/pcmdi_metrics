import datetime
import os

mip = "obs"
dat = "TRMM"
var = "pr"
frq = "day"
ver = "v20210717"

indir = "/work/ahn6/obs/TRMM/TRMM_3B42.7/day/"
infile = "TRMM_3B42.7_*.nc"
#indir = "/work/ahn6/obs/TRMM/TRMM_3B42.7/day_download/disc2.gesdisc.eosdis.nasa.gov/data/TRMM_L3/TRMM_3B42_Daily.7/*/*/"
#infile = "3B42_Daily.*.nc4"

# case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
case_id = ver
pmpdir = "/work/ahn6/pr/intensity_frequency_distribution/frequency_amount_peak/"+ver+"/"
results_dir = os.path.join(
    pmpdir, '%(output_type)', 'precip_distribution', '%(mip)', '%(case_id)')

xmldir = "./xml_obs/"
if not (os.path.isdir(xmldir)):
    os.makedirs(xmldir)
#os.system(
#    "cdscan -x " + xmldir + var + "." + frq + "." + dat + ".xml " + indir + infile
#)

modpath = xmldir
mod = var + "." + frq + "." + dat + ".xml"
prd = [2001, 2019]  # analysis period
# prd = [2001, 2002]  # analysis period
fac = 24  # factor to make unit of [mm/day]
# res = [0.5, 0.5]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [1, 1]  # target horizontal resolution [degree] for interporation (lon, lat)
# res = [2, 2]  # target horizontal resolution [degree] for interporation (lon, lat)
res = [4, 4]  # target horizontal resolution [degree] for interporation (lon, lat)
