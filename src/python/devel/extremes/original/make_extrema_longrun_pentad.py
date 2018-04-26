# Adapted for numpy/ma/cdms2 by convertcdms.py
# Calculate annual and seasonal pentadal extrema from a dataset of daily averages
# suitable for input into a return value calculation or comparison between models and observations.
# example execute line:
# python make_extrema_longrun_pentad.py var model_scenario_realization var_file lat_name
# Where:
# var is the variable name
# model_scenario_realization is a descriptor for the output file
# var_file is the input file of daily data. An xml file constructed with cdscan works here.
# lat_name is the name of the latitude dimension
# Note: the main purpose of this routine is to construct the ETCCDI extreme index called "rx5day" from the daily variable called "pr"
# but it would work for any variable.
# However, the prefix of the name of the output variable is unchanged from the input variable name.
# The suffix of the name of the output variable reflects the season.

import  MV2 as MV, cdtime,os, cdms2 as cdms, sys, string
#NCAR Control runs have no leap years. Historical runs do.

#cdms.setNetcdfShuffleFlag(0)
#cdms.setNetcdfDeflateFlag(0)
#cdms.setNetcdfDeflateLevelFlag(0)

var=sys.argv[1]
f=cdms.open(sys.argv[3])

model=sys.argv[2]
tim=f.dimensionarray('time')
u=f.getdimensionunits('time')
n=len(tim)

cdtime.DefaultCalendar=cdtime.NoLeapCalendar
tt=f.dimensionobject('time')
if hasattr(tt, 'calendar'):
 if tt.calendar=='360_day':cdtime.DefaultCalendar=cdtime.Calendar360
 if tt.calendar=='gregorian':cdtime.DefaultCalendar=cdtime.MixedCalendar
 if tt.calendar=='365_day':cdtime.DefaultCalendar=cdtime.NoLeapCalendar
 if tt.calendar=='noleap':cdtime.DefaultCalendar=cdtime.NoLeapCalendar
 if tt.calendar=='proleptic_gregorian':cdtime.DefaultCalendar=cdtime.GregorianCalendar
 if tt.calendar=='standard':cdtime.DefaultCalendar=cdtime.StandardCalendar

output=cdms.open(var+'_max_pentad_'+model+'.nc','w')
output.execute_line="python "+ " ".join(sys.argv)
for a in f.listglobal():
  setattr(output,a,getattr(f,a))


lat_name='latitude'
lon_name='longitude'

lat=sys.argv[4]
if lat=='lat': lat_name='lat'
if lat=='lat': lon_name='lon'
latitude=f.dimensionarray(lat_name)
longitude=f.dimensionarray(lon_name)
latitude=latitude.astype(MV.float64)
longitude=longitude.astype(MV.float64)
nlat=latitude.shape[0]
nlon=longitude.shape[0]

#y0=string.atoi(sys.argv[4])+1
#y1=y0
#y2=string.atoi(sys.argv[5])
time1=cdtime.reltime(tim[0],u)
time2=cdtime.reltime(tim[n-1],u)
y1=int(time1.torel('years since 0000-1-1').value)+1
y2=int(time2.torel('years since 0000-1-1').value)
y0=y1

daily_max=MV.zeros((y2-y1+1,nlat,nlon),MV.float)

time=MV.zeros((y2-y0+1),MV.float)

# Calculate annual extrema
print("starting annual")
y1=y0
m1=1 # January
d1=1
m2=12 # december
d2=31
y=0
while y1<y2+1:
  beg=cdtime.comptime(y1,m1,d1).torel(u).value
  end=cdtime.comptime(y1,m2,d2).torel(u).value
  if hasattr(tt, 'calendar'):
    if tt.calendar=='360_day':end=end-1.0
  time[y]=float(y1)
  b=0
  e=-1
  for i in range(n-1):
    t1=cdtime.reltime(tim[i]  ,u).value
    t2=cdtime.reltime(tim[i+1],u).value
    if t1<=beg and t2>beg : b=i
    if t1<end and t2>=end : e=i+1
# Compute the extrema of the daily average values for year=Y
  s1=f.getslab(var,tim[b],tim[e])
  if var=='pr' or var=='precip' or var=='PRECT':s1.missing_value=0.0
#  mask_s=s.mask
#  MV.putmask(s,mask_s,0)
  ndays=s1.shape[0]
  s=0.*s1
  ii=4
  while ii<ndays:
    s[ii,:,:]=0.2*(s1[ii,:,:]+s1[ii-1,:,:]+s1[ii-2,:,:]+s1[ii-3,:,:]+s1[ii-4,:,:])
    ii=ii+1
  sorted=MV.sort(s,0)
  daily_max[y,:,:]=sorted[e-b,:,:]
  print y
  y=y+1
  y1=y1+1

# output Daily extrema

daily_max.setdimattribute(0,'values',time)
daily_max.setdimattribute(1,'values',latitude)
daily_max.setdimattribute(2,'values',longitude)
daily_max.setdimattribute(0,'name','time')
daily_max.setdimattribute(1,'name','latitude')
daily_max.setdimattribute(2,'name','longitude')
daily_max.setattribute('name',var+'_annual_daily_max')
daily_max.setdimattribute(0,'units','years since 00-01-01 00:00:00')
daily_max.id=var+'_annual_daily_max'
output.write(daily_max)

# Calculate DJF extrema
print("starting DJF")
y1=y0
m1=11 # December
d1=27
m2=2 # February
d2=28
y=0
while y1<y2+1:
  beg=cdtime.comptime(y1-1,m1,d1).torel(u).value
  end=cdtime.comptime(y1,m2,d2).torel(u).value
  time[y]=float(y1)
  b=0
  e=-1
  for i in range(n-1):
    t1=cdtime.reltime(tim[i]  ,u).value
    t2=cdtime.reltime(tim[i+1],u).value
    if t1<=beg and t2>beg : b=i
    if t1<end and t2>=end : e=i+1
  s1=f.getslab(var,tim[b+1],tim[e+1])
  if var=='pr' or var=='precip' or var=='PRECT':s1.missing_value=0.0
  ndays=s1.shape[0]
  s=0.*s1
  ii=4
  while ii<ndays:
    s[ii,:,:]=0.2*(s1[ii,:,:]+s1[ii-1,:,:]+s1[ii-2,:,:]+s1[ii-3,:,:]+s1[ii-4,:,:])
    ii=ii+1
#  mask_s=s.mask
#  MV.putmask(s,mask_s,0)
  sorted=MV.sort(s,0)
  daily_max[y,:,:]=sorted[e-b,:,:]
  y=y+1
  y1=y1+1

# output DJF Daily extrema
daily_max.setdimattribute(0,'values',time)
daily_max.setdimattribute(1,'values',latitude)
daily_max.setdimattribute(2,'values',longitude)
daily_max.setdimattribute(0,'name','time')
daily_max.setdimattribute(1,'name','latitude')
daily_max.setdimattribute(2,'name','longitude')
daily_max.setattribute('name',var+'_DJF_daily_max')
daily_max.setdimattribute(0,'units','years since 00-01-01 00:00:00')
daily_max.id=var+'_DJF_daily_max'
output.write(daily_max)

# Calculate MAM extrema
print("starting MAM")
y1=y0
m1=2# March
d1=24
m2=5 # May
d2=31
y=0
while y1<y2+1:
  beg=cdtime.comptime(y1,m1,d1).torel(u).value
  end=cdtime.comptime(y1,m2,d2).torel(u).value
  time[y]=float(y1)
  b=0
  e=-1
  for i in range(n-1):
    t1=cdtime.reltime(tim[i]  ,u).value
    t2=cdtime.reltime(tim[i+1],u).value
    if t1<=beg and t2>beg : b=i
    if t1<end and t2>=end : e=i+1
# Compute the extrema of the daily average values for year=Y
  s1=f.getslab(var,tim[b+1],tim[e+1])
  ndays=s1.shape[0]
  s=0.*s1
  ii=4
  while ii<ndays:
    s[ii,:,:]=0.2*(s1[ii,:,:]+s1[ii-1,:,:]+s1[ii-2,:,:]+s1[ii-3,:,:]+s1[ii-4,:,:])
    ii=ii+1
#  mask_s=s.mask
#  MV.putmask(s,mask_s,0)
  sorted=MV.sort(s,0)
  daily_max[y,:,:]=sorted[e-b,:,:]
  y=y+1
  y1=y1+1

# output MAM Daily extrema
daily_max.setdimattribute(0,'values',time)
daily_max.setdimattribute(1,'values',latitude)
daily_max.setdimattribute(2,'values',longitude)
daily_max.setdimattribute(0,'name','time')
daily_max.setdimattribute(1,'name','latitude')
daily_max.setdimattribute(2,'name','longitude')
daily_max.setattribute('name',var+'_MAM_daily_max')
daily_max.setdimattribute(0,'units','years since 00-01-01 00:00:00')
daily_max.id=var+'_MAM_daily_max'
output.write(daily_max)


# Calculate SON extrema
print("starting SON")
y1=y0
m1=8 # September
d1=28
m2=11 # November
d2=30
y=0
while y1<y2+1:
  beg=cdtime.comptime(y1,m1,d1).torel(u).value
  end=cdtime.comptime(y1,m2,d2).torel(u).value
  time[y]=float(y1)
  b=0
  e=-1
  for i in range(n-1):
    t1=cdtime.reltime(tim[i]  ,u).value
    t2=cdtime.reltime(tim[i+1],u).value
    if t1<=beg and t2>beg : b=i
    if t1<end and t2>=end : e=i+1
# Compute the extrema of the daily average values for year=Y
  s1=f.getslab(var,tim[b+1],tim[e+1])
  ndays=s1.shape[0]
  s=0.*s1
  ii=4
  while ii<ndays:
    s[ii,:,:]=0.2*(s1[ii,:,:]+s1[ii-1,:,:]+s1[ii-2,:,:]+s1[ii-3,:,:]+s1[ii-4,:,:])
    ii=ii+1
#  mask_s=s.mask
#  MV.putmask(s,mask_s,0)
  sorted=MV.sort(s,0)
  daily_max[y,:,:]=sorted[e-b,:,:]
  y=y+1
  y1=y1+1

# output SON Daily extrema
daily_max.setdimattribute(0,'values',time)
daily_max.setdimattribute(1,'values',latitude)
daily_max.setdimattribute(2,'values',longitude)
daily_max.setdimattribute(0,'name','time')
daily_max.setdimattribute(1,'name','latitude')
daily_max.setdimattribute(2,'name','longitude')
daily_max.setattribute('name',var+'_SON_daily_max')
daily_max.setdimattribute(0,'units','years since 00-01-01 00:00:00')
daily_max.id=var+'_SON_daily_max'
output.write(daily_max)


# Calculate JJA extrema
print("starting JJA")
y1=y0
m1=5 # June
d1=27
m2=8 # August
d2=31
y=0
while y1<y2+1:
  beg=cdtime.comptime(y1,m1,d1).torel(u).value
  end=cdtime.comptime(y1,m2,d2).torel(u).value
  time[y]=float(y1)
  b=0
  e=-1
  for i in range(n-1):
    t1=cdtime.reltime(tim[i]  ,u).value
    t2=cdtime.reltime(tim[i+1],u).value
    if t1<=beg and t2>beg : b=i
    if t1<end and t2>=end : e=i+1
# Compute the extrema of the daily average values for year=Y
  s1=f.getslab(var,tim[b+1],tim[e+1])
  ndays=s1.shape[0]
  s=0.*s1
  ii=4
  while ii<ndays:
    s[ii,:,:]=0.2*(s1[ii,:,:]+s1[ii-1,:,:]+s1[ii-2,:,:]+s1[ii-3,:,:]+s1[ii-4,:,:])
    ii=ii+1
#  mask_s=s.mask
#  MV.putmask(s,mask_s,0)
  sorted=MV.sort(s,0)
  daily_max[y,:,:]=sorted[e-b,:,:]  
  y=y+1
  y1=y1+1

# output JJA Daily extrema:
daily_max.setdimattribute(0,'values',time)
daily_max.setdimattribute(1,'values',latitude)
daily_max.setdimattribute(2,'values',longitude)
daily_max.setdimattribute(0,'name','time')
daily_max.setdimattribute(1,'name','latitude')
daily_max.setdimattribute(2,'name','longitude')
daily_max.setattribute('name',var+'_JJA_daily_max')
daily_max.setdimattribute(0,'units','years since 00-01-01 00:00:00')
daily_max.id=var+'_JJA_daily_max'
output.write(daily_max)

output.close()
