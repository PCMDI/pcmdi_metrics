# Revision by MFW 08/10/2018: Removed the 4 seasons for speed. Added some comments
# Adapted for numpy/ma/cdms2 by convertcdms.py
# Calculate annual and seasonal extrema from a dataset of daily averages
# suitable for input into a return value calculation.
import  MV2 as MV, cdtime,os, cdms2 as cdms, sys, string
#Note: NCAR Control runs have no leap years. Historical runs do.

#cdms.setNetcdfShuffleFlag(0)
#cdms.setNetcdfDeflateFlag(0)
#cdms.setNetcdfDeflateLevelFlag(0)

# Calculate annual 3 day extrema from a dataset of daily averages
# suitable for input into a return value calculation or comparison between models and observations.
# example execute line:
# python make_extrema_longrun_3day.py var model_scenario_realization var_file lat_name date_range
# Where:
# var is the variable name (for the PMP this is either tasmax or tasmin or the negative of these)
# model_scenario_realization is a descriptor for the output file
# var_file is the input file of daily data. An xml file constructed with cdscan works here.
# lat_name is the name of the latitude dimension
# date_range = first_year last_year
# or
# date_range = "all"
# Note: the main purpose of this routine is to construct the ETCCDI-like extreme index, TX3x, from the daily variable tasmax.
# However, the prefix of the name of the output variable is unchanged from the input variable name.
# The suffix of the name of the output variable reflects the season.

# PMP specific instructions for Peter regarding output file and variable names. Not sure how you want to deal with this
# If var== tasmax, the change the variable name to TX3x
# If var== -tasmax, the change the variable name to TX3n
# If var== tasmin, the change the variable name to TN3x
# If var== -tasmin, the change the variable name to TN3n
# If var== -tasmax or -tasmin, multiply the final answer by -1 to make it positive again.
# And change output file names accordingly


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

output=cdms.open(var+'_max_3day_'+model+'.nc','w')
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

if sys.argv[5]=='all':
 time1=cdtime.reltime(tim[0],u)
 time2=cdtime.reltime(tim[n-1],u)
 y1=int(time1.torel('years since 0000-1-1').value)+1
 y2=int(time2.torel('years since 0000-1-1').value)
else:
 y0=string.atoi(sys.argv[5])+1
 y1=y0
 y2=string.atoi(sys.argv[6])

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
  ii=2
  while ii<ndays:
    s[ii,:,:]=(s1[ii,:,:]+s1[ii-1,:,:]+s1[ii-2,:,:])/3.
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

output.close()
