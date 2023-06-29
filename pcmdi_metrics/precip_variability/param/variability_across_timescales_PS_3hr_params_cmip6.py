import datetime
import os

mip = "cmip6"
exp = "historical"
var = "pr"
frq = "3hr"
ver = "v20230407"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
# case_id = ver
pmpdir = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2"
results_dir = os.path.join(pmpdir, "%(output_type)", "precip", "%(mip)", exp, "%(case_id)", "variability_across_timescales")

prd = [1985, 2004]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 8  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 8
