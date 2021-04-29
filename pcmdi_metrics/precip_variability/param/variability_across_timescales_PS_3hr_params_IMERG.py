import os

mip = "obs"
dat = "IMERG"
var = "pr"
frq = "3hr"
ver = "v20210123"

# indir = '/work/ahn6/obs/IMERG/IMERG_Final.Run_V06B/3hr/'
# indir = '/work/ahn6/obs/IMERG/IMERG_Final.Run_V06B/3hr.center/'
indir = "/work/ahn6/obs/IMERG/IMERG_Final.Run_V06B/3hr.center_2deg/"
infile = "IMERG_Final.Run.V06B_*.nc"

# outdir = '/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data/'+mip+'/'
outdir = (
    "/work/ahn6/pr/variability_across_timescales/power_spectrum/"+ver+"_test/data/"+mip+"/"
)

xmldir = "./xml_obs/"
if not (os.path.isdir(xmldir)):
    os.makedirs(xmldir)
os.system(
    "cdscan -x " + xmldir + var + "." + frq + "." + dat + ".xml " + indir + infile
)

modpath = xmldir
mod = dat
prd = [2001, 2019]  # analysis period
fac = 24  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 8  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 8
