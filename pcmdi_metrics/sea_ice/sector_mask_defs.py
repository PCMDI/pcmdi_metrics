def getmask(sector,lats,lons,lons_a,lons_p,land_mask):
 import MV2 as MV
#Arctic Regions
#Central Arctic
 if sector == 'ca':
   lat_bound1=MV.logical_and(MV.greater(lats,80.),MV.less_equal(lats,90.))
   lat_bound2=MV.logical_and(MV.greater(lats,65.),MV.less_equal(lats,90.))
   lon_bound1=MV.logical_and(MV.greater(lons_a,-120.),MV.less_equal(lons_a,90.))
   lon_bound2=MV.logical_and(MV.greater(lons_p,90.),MV.less_equal(lons_p,240.))
   reg1=MV.logical_and(lat_bound1,lon_bound1)
   reg2=MV.logical_and(lat_bound2,lon_bound2)
   mask=MV.where(MV.logical_or(reg1,reg2),1,0)
   mask=MV.where(MV.equal(land_mask,0),0,mask)           # 0 - Land

#NA region
 if sector == 'na':
   lat_bound=MV.logical_and(MV.greater(lats,45.),MV.less_equal(lats,80.))
   lon_bound=MV.logical_and(MV.greater(lons_a,-120.),MV.less_equal(lons_a,90.))
   lat_bound3=MV.logical_and(MV.greater(lats,45.),MV.less_equal(lats,50.))
   lon_bound3=MV.logical_and(MV.greater(lons_a,30.),MV.less_equal(lons_a,60.))
   reg3=MV.logical_and(lat_bound3,lon_bound3)

   mask=MV.where(MV.logical_and(lat_bound,lon_bound),1,0)
   mask=MV.where(MV.equal(reg3,True),0,mask)   # Masking out the Black and Caspian Seas
   mask=MV.where(MV.equal(land_mask,True),0,mask)           # 0 - Land
   mask=MV.where(MV.equal(land_mask,0),0,mask)           # 0 - Land
   
#NP region
 if sector == 'np':
   lat_bound=MV.logical_and(MV.greater(lats,45.),MV.less_equal(lats,65.))
   lon_bound=MV.logical_and(MV.greater(lons_p,90.),MV.less_equal(lons_p,240.))
   mask=MV.where(MV.logical_and(lat_bound,lon_bound),1,0)
   mask=MV.where(MV.equal(land_mask,0),0,mask)           # 0 - Land

#Antarctic Regions

#SA region
 if sector == 'sa':
   lat_bound=MV.logical_and(MV.greater(lats,-90.),MV.less_equal(lats,-55.))
   lon_bound=MV.logical_and(MV.greater(lons_a,-60.),MV.less_equal(lons_a,20.))
   mask=MV.where(MV.logical_and(lat_bound,lon_bound),1,0)
   mask=MV.where(MV.equal(land_mask,0),0,mask)           # 0 - Land

#SP region
 if sector == 'sp':
   lat_bound=MV.logical_and(MV.greater(lats,-90.),MV.less_equal(lats,-55.))
   lon_bound=MV.logical_and(MV.greater(lons_p,90.),MV.less_equal(lons_p,300.))
   mask=MV.where(MV.logical_and(lat_bound,lon_bound),1,0)
   mask=MV.where(MV.equal(land_mask,0),0,mask)           # 0 - Land

#IO region
 if sector == 'io':
   lat_bound=MV.logical_and(MV.greater(lats,-90.),MV.less_equal(lats,-55.))
   lon_bound=MV.logical_and(MV.greater(lons_p,20.),MV.less_equal(lons_p,90.))
   mask=MV.where(MV.logical_and(lat_bound,lon_bound),1,0)
   mask=MV.where(MV.equal(land_mask,0),0,mask)           # 0 - Land

 return mask



