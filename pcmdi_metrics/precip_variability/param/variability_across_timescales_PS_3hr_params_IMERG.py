import datetime
import os

mip = "obs"
dat = "IMERG"
var = "pr"
frq = "3hr"
ver = "v20221111"

modpath = "/p/user_pub/PCMDIobs/obs4MIPs/NASA-GSFC/IMERG-v06B-Final/3hr/pr/2x2/latest/"
mod = "*.nc"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmpdir = "/work/ahn6/pr/variability_across_timescales/power_spectrum/" + ver + "_test/"
results_dir = os.path.join(
    pmpdir, "%(output_type)", "%(mip)", "%(case_id)"
)

prd = [2001, 2019]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 8  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 8
