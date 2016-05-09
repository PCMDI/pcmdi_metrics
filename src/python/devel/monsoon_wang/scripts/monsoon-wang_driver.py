import cdms2,MV2
import sys, string
import os, vcs
from genutil import statistics
import cdutil
import regrid2
import json

execfile('/export_backup/gleckler1/git/pcmdi_metrics/src/python/devel/monsoon_wang/lib/PMP_rectangular_domains.py')


conv = 1 
mod_clim_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package/'

mip = 'cmip5'
exp = 'historical'

var = 'pr'

lst = os.popen('ls ' + mod_clim_path + '*' + var + '*1985*.nc').readlines()

#lst = lst[0:2]
print lst

#########################################
## obs 
fcobs = '/work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc'
fobs = cdms2.open(fcobs)
dobs_orig = fobs('pr')

obsgrid = dobs_orig.getGrid()

#lat_range = (latitude = (-45.,45))

########################################

def mpd(d):
 mjjas = (d[4] + d[5] + d[6] + d[7] + d[8])/5.
 ndjfm = (d[10] + d[11] + d[0] + d[1] + d[2])/5.
 ann = MV2.average(d,axis=0)

 annrange = MV2.subtract(mjjas,ndjfm)
 annrange0 = annrange*1.

 lats0 = annrange.getAxis(0)

 for l in range(len(lats0)):
   if lats0[l] <0:
    annrange[l,:] = -1*annrange[l,:]

 mpi = MV2.divide(annrange,ann)

 return annrange, mpi 

annrange_obs, mpi_obs = mpd(dobs_orig)

#print obs,' ', annrange_obs,' ', mpi_obs

#########################################

doms = Monsoon_region.keys() 

mpi_stats_dic = {}
for l in lst: 
 try:
  tmp = string.split(l,'/')[5] 
  mod = string.split(tmp,'_')[1]
  mpi_stats_dic[mod] = {}

  f = cdms2.open(l[:-1]) 
  d_orig = f('pr')

  annrange_mod, mpi_mod = mpd(d_orig)
  annrange_mod = annrange_mod.regrid(obsgrid)
  mpi_mod = mpi_mod.regrid(obsgrid)

  for dom in doms:

   llat = Monsoon_region[dom]['llat']
   ulat = Monsoon_region[dom]['ulat']
   llon = Monsoon_region[dom]['llon']
   ulon = Monsoon_region[dom]['ulon']

   mpi_stats_dic[mod][dom] = {}

   reg_sel = cdutil.region.domain(latitude= (llat,ulat),longitude =(llon,ulon))

   mpi_obs_reg = mpi_obs(reg_sel)
   mpi_obs_reg_sd = float(statistics.std(mpi_obs_reg,axis='xy')) 
   mpi_mod_reg = mpi_mod(reg_sel)

   cor = float(statistics.correlation(mpi_mod_reg,mpi_obs_reg,axis='xy'))
   rms = float(statistics.rms(mpi_mod_reg,mpi_obs_reg,axis='xy'))
   rmsn = rms/mpi_obs_reg_sd 

   print mod,' ', dom, ' ', cor 

   mpi_stats_dic[mod][dom] = {'cor':cor, 'rmsn':rmsn}
 except:
  print 'FAILED FOR MODEL ', mod 

json_filename = 'MPI_' + mip + '_' + exp 
json.dump(mpi_stats_dic, open(json_filename + '.json','w'),sort_keys=True, indent=4, separators=(',', ': '))





#v =vcs.init()
#v1 = vcs.init()
#v1.plot(mpi_obs)

#v.plot(cdutil.averager(annrange,axis=1))
#w = sys.stdin.readline()
#v1.plot(cdutil.averager(annrange0,axis=1))






print 'done'
