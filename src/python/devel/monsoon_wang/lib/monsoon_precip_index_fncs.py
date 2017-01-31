import MV2
#  SEASONAL RANGE - USING ANNUAL CYCLE CLIMATOLGIES 0=Jan, 11=Dec
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

def mpi_skill_scores(annrange_mod_dom,annrange_obs_dom,thr):
   mt = MV2.where(MV2.greater(annrange_mod_dom,thr),1.,0.)
   ot = MV2.where(MV2.greater(annrange_obs_dom,thr),1.,0.)

   both = MV2.add(mt,ot) # HIT WILL MEAN 2, OTHERWISE 0 or 1
   hitmap = MV2.where(MV2.equal(both,2.),1.,0.)
   hit = float(MV2.sum(hitmap))

   mt1 = MV2.where(MV2.greater(annrange_mod_dom,thr),10.,0.)
   both1 = MV2.add(mt1,ot) # 10 for MOD above THRESHOLD, OTHERWISE 0 
   missmap = MV2.where(MV2.equal(both1,1.),1.,0.)
   missed = float(MV2.sum(missmap))

   ot1 = MV2.where(MV2.greater(annrange_obs_dom,thr),10.,0.)
   both2 = MV2.add(mt,ot1) # 10 for OBS above THRESHOLD OTHERWISE 0 
   falarmmap = MV2.where(MV2.equal(both2,1.),1.,0.)
   falarm = float(MV2.sum(falarmmap))

#  print mod,' hit missed falarm ', hit,' ', missed,' ', falarm

   score = hit/(hit+missed+falarm)

   return hit, missed,falarm,score,hitmap,missmap,falarmmap


