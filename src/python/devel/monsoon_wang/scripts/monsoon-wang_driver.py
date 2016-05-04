import cdms2,MV2
import sys, string
import os, vcs
import genutil
import cdutil
import regrid2

conv = 1 
mod_clim_path = '/work/gleckler1/processed_data/cmip5clims_metrics_package/'

var = 'pr'

lst = os.popen('ls ' + mod_clim_path + '*' + var + '*GFDL*1985*.nc').readlines()

lst = lst[0:2]
print lst

#########################################
## obs 
fcobs = '/work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc'
fobs = cdms2.open(fcobs)
dobs = fobs('pr')

obsgrid = cdms2.getGrid(dobs)

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

annrange_obs, mpi_obs = mpd(dobs)

#print obs,' ', annrange_obs,' ', mpi_obs


#########################################
for l in lst: 
 tmp = string.split(l,'/')[5] 
 mod = string.split(tmp,'_')[1]

 f = cdms2.open(l[:-1]) 
 d = f('pr')

 annrange_mod, mpi_mod = mpd(d) 

#print mod,' ', annrange_mod,' ', mpi_mod


v =vcs.init()
v1 = vcs.init()
v1.plot(mpi_obs)
#v.plot(cdutil.averager(annrange,axis=1))
#w = sys.stdin.readline()
#v1.plot(cdutil.averager(annrange0,axis=1))






print 'done'
