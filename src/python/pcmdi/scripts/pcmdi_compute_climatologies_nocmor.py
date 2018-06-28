#!/usr/local/uvcdat/latest/bin/python

import cdms2 as cdms
import os, string
import cdtime, cdutil
import MV2 as MV
import sys
import logging
import time, datetime
import glob
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser

cdms.setAutoBounds('on')

cdms.setNetcdfShuffleFlag(0)
cdms.setNetcdfDeflateFlag(0)
cdms.setNetcdfDeflateLevelFlag(0)

P = PMPParser()

P.use("--modpath")
P.use("--modnames")
P.use("--results_dir")
P.use("--reference_data_path")

P.add_argument("-e", "--experiment",
               type=str,
               dest='experiment',
               default='historical',
               help="AMIP, historical or picontrol")
P.add_argument("--filename_template",
               type=str,
               dest='filename_template',
               help="PCMDIs CMIP.xml filename template")
P.add_argument("-c", "--MIP",
               type=str,
               dest='mip',
               default='CMIP5',
               help="put options here")
P.add_argument("--climout",
               type=str,
               dest='climout',
               help="A subdir name which describes CMIPx-EXP")
P.add_argument("--climatological_season",
               dest="seasons",
               nargs="*",
               choices = ['ANN']) 
## NOT YET IMPLEMENTED
#              choices=["djf", "DJF", "ann", "ANN", "all", "ALL",
#                       "mam", "MAM", "jja", "JJA", "son", "SON", "year",
#                       "YEAR"],
#              help="Which season you wish to produce") 

P.add_argument("--ovar",
               dest='obsvar',
               default='pr',
               help="Name of variable in obs file")
P.add_argument("-v", "--var",
               dest='vars',
               default='pr',
               help="Name of variable in model files")
P.add_argument("-r", "--realm",
               dest='realm',
               default='atm',
               help="Name of realm CMIP variables are in")
P.add_argument("--start_month",
               dest='sm',
               help="Calendar month to begin clim")
P.add_argument("--start_year",
               dest='sy',
               help="Calendar year to begin clim")
P.add_argument("--end_month",
               dest='em',
               help="Calendar month to end clim")
P.add_argument("--end_year",
               dest='ey',
               help="Calendar year to end clim")

args = P.get_parameter()
modpath = args.modpath
filename_template = args.filename_template
results_dir = args.results_dir
vars = args.vars
exp = args.experiment
realm = args.realm
sm = args.start_month
by = args.start_year
em = args.end_month
ey = args.end_year
climout = args.climout

print 'modpath is ', modpath,' ', vars
print 'filename template is ', filename_template
print 'exp is ', exp

pi = '/work/durack1/Shared/cmip5/$EXPERIMENT/' + realm + '/mo/$VAR/'     #*.xml
pi = '/work/cmip5/$EXPERIMENT/' + realm + '/mo/$VAR/'
piv = '/work/cmip5/historical/' + realm + '/mo/' 
#vars = os.listdir(piv)

print vars

#vars = ['pr','rlut', 'rsut','rsutcs','rlutcs','tas','prw','tauu','tauv','uas','vas','psl','hus','ta','ua','va', 'zg']
#vars = ['rlut']
#exps = ['historical']

onerun = 'y'   # one realization only
#onerun = 'n'

"""
ext_vars = sys.argv[1:len(sys.argv)]
print 'ext_vars is ', ext_vars

if len(ext_vars) != 0: 
   vars = ext_vars  
#vars = ['ts']

#w = sys.stdin.readline()
"""

## GENERATE LOG
time_is = datetime.datetime.now()
time_format = time_is.strftime("%y%m%d_%H%M%S")
logfile = 'create_cmip5_clims-' + time_format + '.log'

logging.basicConfig(filename=logfile,level=logging.DEBUG)

t1 = time.time()

try:
   os.mkdir(results_dir)
except:
   pass

#for exp in exps:
for var in vars:
  t2 = time.time()

  try:
   os.mkdir(results_dir + '/' + var)
  except:
   pass
# pit = string.replace(pi,'$EXPERIMENT',exp)
  pit = modpath + var + '/'

# lst = os.listdir(pit)
  lstt = os.popen('ls ' + pit + '*.xml').readlines()


  print 'lenght of full list ', len(lstt)

# w = sys.stdin.readline()

####
## REMOVE \n
  lst0 = []
  for l in lstt:
    tmp = string.replace(l[:-1],pit,'')
    lst0.append(tmp) 
## ONLY ONE RUN
  lst = []
  if onerun == 'y':
   for l in lst0:
    if string.find(l,'r1i1p1.') != -1: lst.append(l)
  if onerun !='y': lst = lst0

  print 'length of list with only one run/model ', len(lst)

######
# w = sys.stdin.readline()

  if onerun != 'y': lst = lstt  

# lst = lst[0:2]

  for l in lst:
# for l in [lst[0]]:
   try:
    var = string.split(l,'.')[7]
    mod = string.split(l,'.')[1]
    run = string.split(l,'.')[3]

    fc = cdms.open(pit + '/' +l)
    realm = fc.directory
    if string.find(realm,'Amon')==-1 and var == 'pr': var = 'crap'  # SKIP IF WRONG REALM (PR) - WILL FAIL TRY BELOW 
#  w = sys.stdin.readline()
#  print pit + l
   except:
    print 'not making if for ', l 


########
   try:
#  if mod != 'BNU-ESM':

### Trap last 5 years if picontrol
   
     if exp == 'piControl':
       t2 = time.time(1)
       dc = fc[var]
       tc = dc.getTime()
       cc = tc.asComponentTime()
       yrs = []
       for c in cc:
         yr = c.year
         if yr not in yrs: yrs.append(yr)

       by = len(yrs)- 26
#      ey = by + 3    # TESTING 4D THETAO CLIMS WITH 3 years
       ey = by + 25 

       print 'picontrol','  ', mod,' ',  by,'  ', ey,'  ', ey-by
#    w = sys.stdin.readline()


##############################

#    d = fc(var,time = (cdtime.comptime(1980,0),cdtime.comptime(2005,0)))
#    if exp in ['amip','historical']:  d = fc(var,time = (cdtime.comptime(by,0),cdtime.comptime(ey,0)))
     d = fc(var,time = (cdtime.comptime(by,0),cdtime.comptime(ey+1,0)))
     t = d.getTime()
     c = t.asComponentTime()
     nt = len(t)

     t2 = time.time()
#    print exp,' ', mod,' ',run,' ', var,' ',d.shape,'  ', c[0].year,' ', c[0].month,' --> ', c[nt-1].year,' ',c[nt-1].month,' --- ', c[0],'   ', c[nt-1],' ', d.shape[0]/12.,'  ', t2-t1  
     da = cdutil.times.ANNUALCYCLE.climatology(d)
#     ds = cdutil.times.SEASONALCYCLE.climatology(d)   

### DATA CORRECTIONS #####
### THESE SHOULD BE REMOVED FROM CLIM CODE AND BE A SECOND STEP OR AT LEAST READ FROM AN EXTERNAL MODULE

     if mod == 'GFDL-CM2p1' and var == 'tos': 
        da = da + 273.15
        ds = ds + 273.15

     if mod in ['FIO-ESM','BNU-ESM'] and var in ['tauu','tauv']:
        un = d.units
        da = MV.multiply(da,-1.)
        ds = MV.multiply(ds,-1.)
        da.units = un
        ds.units = un

##################
### TIME MODEL REPAIR

     timel = [15.5, 45.5, 75.5, 106, 136.5, 167, 197.5, 228.5, 259, 289.5, 320, 350.5]
     timelbds =  [(0, 31), (31, 60), (60, 91), (91, 121), (121, 152), (152, 182,), (182, 213), (213, 244), (244, 274), (274, 305), (305, 335), (335, 366)]  
     ta = cdms.createAxis(timel,id='time')
     tb = MV.array(timelbds)
     tb = tb.astype('float64')
     ta.setBounds(tb)
     ta.climatology = "climatology_bnds"
     ta.units = "days since 0"
     ta.calendar = 'gregorian'  
     ta.axis = 'T'
     ta.long_name = 'time'
     ta.standard_name = 'time'
    
     dau = d.units
     da.setAxis(0,ta)

### TIME AXIS FOR SEASONAL DATA - CURRENTLY NOT IMPLEMENTED
#    ts = ds.getAxis(0)
#    ts = ts - ts[0]  + 45
#    ts_nax = cdms.createAxis(ts,id='Time')
#    ts_nax.units = 'days since 0-0-0'
#    ts_nax.calendar = 'gregorian'
#    ts_nax.axis = 'T'
#    ds.setAxis(0,ts_nax)
##################

     gc = string.replace(l,'.xml','.' + `by` + '-' + `ey` + '.AC.nc')   #1980-2005_AC.nc')
     gc = string.replace(gc,'.latestX','')
#    print 'after dc write'
     fo = results_dir + '/' + var + '/' + gc
     g  = cdms.open(fo,'w+') 
     da.id = var  #+ '_ac' 
     da.units = dau
#    print 'before da write ', da.shape
     g.write(da)
     att_keys = fc.attributes.keys()
# THIS IS FOR SEASONAL... CURRENTLY TURNED OFF
#    fs = string.replace(fo,'AC.nc','SC.nc')
#    gs = cdms.open(fs,'w+')
#    ds.id = var  #+ '_sc'  
#    ds.units = dau
#    gs.write(ds)

#    att_keys = fc.attributes.keys()
     att_dic = {}
     for i in range(len(att_keys)):
#         print '----------------------'
          att_dic[i]=att_keys[i],fc.attributes[att_keys[i]]
          to_out = att_dic[i]
          setattr(g,to_out[0],to_out[1])
#         setattr(gs,to_out[0],to_out[1])  # NEEDED FOR SEASONAL (SC)
     fc.close()
     g.close()
#    gs.close() # NEEDED FOR SEASONAL (SC)


     outlog = l,' --> ',d.shape,'  ', c[0].year,' ', c[0].month,' to ', c[nt-1].year,' ',c[nt-1].month,' --- ', c[0],'   ', c[nt-1],' ', d.shape[0]/12.,'  ', t2-t1
     print outlog 
#    print l,' --> ',d.shape,'  ', c[0].year,' ', c[0].month,' to ', c[nt-1].year,' ',c[nt-1].month,' --- ', c[0],'   ', c[nt-1],' ', d.shape[0]/12.,'  ', t2-t1
     logging.debug(outlog)
     t1 = t2
#    w = sys.stdin.readline()

   except:
     logging.debug('FAILED with ' + pit + l)   
