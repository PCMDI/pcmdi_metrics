mip = 'cmip6'
exp = 'historical'
mod = 'ACCESS-CM2.r1i1p1f1'
var = 'pr'
frq = '3hr'
ver = 'v20210123'
modpath = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/'+ver+'/'+mip+'/'+exp+'/atmos/'+frq+'/'+var+'/'
#outdir = '/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'/data/'+mip+'/'
outdir = '/work/ahn6/pr/variability_across_timescales/power_spectrum/'+ver+'_test/data/'+mip+'/'
prd = [1985, 2004] # analysis period
fac = 86400 # factor to make unit of [mm/day]
nperseg = 10*365*8 # length of segment in power spectra (~10yrs)
noverlap = 5*365*8 # length of overlap between segments in power spectra (~5yrs)

