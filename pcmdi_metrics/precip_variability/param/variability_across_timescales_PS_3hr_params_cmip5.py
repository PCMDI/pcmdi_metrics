import datetime
import os

mip = "cmip5"
exp = "historical"
var = "pr"
frq = "3hr"
ver = "v20221111"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmpdir = "/work/ahn6/pr/variability_across_timescales/power_spectrum/" + ver + "_test/"
results_dir = os.path.join(
    pmpdir, "%(output_type)", "%(mip)", exp, "%(case_id)"
)

prd = [1985, 2004]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 8  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 8
