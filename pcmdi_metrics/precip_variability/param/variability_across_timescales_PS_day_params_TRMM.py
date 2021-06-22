import os

mip = "obs"
dat = "TRMM"
var = "pr"
frq = "day"
ver = "v20210123"

# indir = '/work/ahn6/obs/TRMM/TRMM_3B42.7/3hr_rewrite/'
# indir = "/work/ahn6/obs/TRMM/TRMM_3B42.7/3hr_2deg/"
# indir = "/work/ahn6/obs/TRMM/TRMM_3B42.7/day/"
indir = "/p/user_pub/hoang1-backups/work_backup/ahn6/obs/TRMM/TRMM_3B42.7/day/"
infile = "TRMM_3B42.7_*.nc"

# outdir = '/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data/'+mip+'/'
outdir = (
#    "/work/ahn6/pr/variability_across_timescales/power_spectrum/"+ver+"_test/data/"+mip+"/"
#    "/work/ahn6/pr/variability_across_timescales/power_spectrum/"+ver+"_test/data/"+mip
    "/home/ahn6/PCMDI/pcmdi_metrics/pcmdi_metrics/precip_variability/scripts_pcmdi/output/"+ver+"_test/data/"+mip
)

xmldir = "./xml_obs/"
if not (os.path.isdir(xmldir)):
    os.makedirs(xmldir)
#os.system(
#    "cdscan -x " + xmldir + var + "." + frq + "." + dat + ".xml " + indir + infile
#)

modpath = xmldir
mod = dat
prd = [2001, 2019]  # analysis period
#prd = [2001, 2002]  # analysis period
fac = 24  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 1  # length of segment in power spectra (~10yrs)
#nperseg = 2 * 365 * 1  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 1
#noverlap = 1 * 365 * 1
