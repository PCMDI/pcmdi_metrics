import datetime
import os

mip = "obs"
dat = "TRMM"
var = "pr"
frq = "day"
ver = "v20230407"

modpath = "/p/user_pub/PCMDIobs/obs4MIPs/NASA-GSFC/TRMM-3B42v-7/day/pr/1x1/latest"
mod = "*.nc"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
# case_id = ver
pmpdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"
results_dir = os.path.join(pmpdir, "%(output_type)", "precip", "%(mip)", "%(case_id)", "variability_across_timescales")

prd = [2001, 2019]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 1  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 1
