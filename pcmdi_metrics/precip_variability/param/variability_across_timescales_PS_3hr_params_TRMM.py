import datetime
import os

mip = "obs"
dat = "TRMM"
var = "pr"
frq = "3hr"
ver = "v20210123"

# indir = '/work/ahn6/obs/TRMM/TRMM_3B42.7/3hr_rewrite/'
indir = "/work/ahn6/obs/TRMM/TRMM_3B42.7/3hr_2deg/"
infile = "TRMM_3B42.7_*.nc"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmpdir = "/work/ahn6/pr/variability_across_timescales/power_spectrum/"+ver+"_test/"
results_dir = os.path.join(
    pmpdir, '%(output_type)', 'precip_variability', '%(mip)', '%(case_id)')

xmldir = "./xml_obs/"
if not (os.path.isdir(xmldir)):
    os.makedirs(xmldir)
os.system(
    "cdscan -x " + xmldir + var + "." + frq + "." + dat + ".xml " + indir + infile
)

modpath = xmldir
mod = var + "." + frq + "." + dat + ".xml"
prd = [2001, 2019]  # analysis period
fac = 24  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 8  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 8
