#!/usr/bin/env python
#######################################################################################
# THIS PROGRAM USES pcmdi_compute_climatologies.py FOR MASS PRODUCTION OF CMORized OBS CLIMATOLOGIES FROM DATA AVAILABLE FROM PCMDI CMIP OBS DATABASE (/work/clim_obs)
# ASPIRATIONAL GOAL IS TO BE THE WORKHORSE FOR PRODUCING ALL OBS CLIMATOLGIES
# IMPORTANT DISTINCTION BETWEEN THIS AND MODEL CODE IS THAT FOR OBS THE PERIOD DEPENDS ON THE DATASET
# TODO:
## LOG FILE SHOULD BE ADDED
## NEED TO ADD OCEAN VARS AND CMOR TABLE
## POSITIVE ATTRIBUTES SHOULD BE STORED EXTERNAL TO THIS PROGRAM 
## CMOR TABLES HARDWIRED - PROBABLY SHOULD BE OPTION ON PARAMETER LIST

#Last modified: PJG 03/05/16
#######################################################################################
import cdms2 as cdms
import os, string
import cdtime, cdutil
import MV2 as MV
import sys
import logging
import time
from subprocess import call,Popen,PIPE

#### PARAMETERS SET BY USER ##########################################################################################
# REALM
realm = 'ocn'
realm = 'atm'

## LIST OF ALL VARIABLES USED FROM EXPERIMENT

if realm == 'atm': 
   table_realm = 'Amon'
   allvars = ['rlut','rsdt','rsut','rsutcs','rlutcs','rsds','rsus','rlus','rlds','rsuscs','rsdscs','rldscs','pr','prw','psl','ts','tas','tauu','tauv','uas','vas','huss', 'ta','ua','va','zg','hus']
if realm =='ocn': 
   table_realm = 'Omon'
   allvars = ['tos','sos','zos']

# OUTPUT TARGET ROOT DIRECTORY
outpath_base = '/work/metricspackage/obs_clims/'

# VARIABLES TO COMPUTE (if not 'all' or list of individual vars)
vars = ['all']
#vars = ['rlut','rsdt','pr','ts','ta']
#vars = ['rlut','rsdt','rsut','rsutcs','rlutcs','rsds','rsus','rlus','rlds','rsuscs','rsdscs','rldscs','pr','prw','psl','ts','tas','tauu','tauv','uas','vas','huss', 'ta','ua','va','zg','hus']
vars = ['rlut']

# CLIMATOLOGY PERIOD 
begyrmo = '1979-12'     # Beginning year and month of period
endyrmo = '1989-12'     # End year and month of period

#### END PARAMETERS SET BY USER #######################################################################################
# INPUT PATHS
if realm == 'atm': pathin = '/clim_obs/obs/atm/mo/'
if realm == 'ocn': pathin = '/clim_obs/obs/ocn/mo/'

outpath = outpath_base + realm    # OUTPUT DIR

## CREATE DIRECTORIES AS NEEDED
for newdir in []:  #[outpath_base + realm,outpath_base +'/' realm + '/ac' ,  outpath_base + realm + '/ac/seas']:
 try:
   os.mkdir(newdir)
 except:
   pass

## TRAP ALL VARS AS NEEDED 
if vars[0] == 'all':
   vars = []
   lst = os.listdir(pathin)
   for l in lst:
     if l not in vars and l in allvars: 
        vars.append(l)
print vars 
#w = sys.stdin.readline()

## LOOP THROUGH VARIABLES
print 'working on ', vars

var_datasets = {}

for var in vars:
 datasets = os.listdir(pathin + '/' + var)
 try:
  datasets.remove('MERRA')
 except:
  pass

 print var,'  ', datasets
 var_datasets[var] = datasets

#w = sys.stdin.readline()

for var in vars:
 for ds in var_datasets[var]:

  positive = "" 
  if var in ['rlut','rsut','rsutcs','rlus','rsus','rsuscs','hfls','hfss']: positive = ' -X ' + "'{" + '"positive"' + ':' + '"up"' + "}'"  
  if var in ['rsdt','rldscs','rsdscs','rlds','rsds','tauu','tauv']: positive = ' -X ' + "'{" + '"positive"' + ':' + '"down"' + "}'"

  fc = os.popen('ls ' + pathin + '/' + var + '/' + ds + '/*.nc').readlines()[0][:-1]

  print fc
  f = cdms.open(fc)
  d = f[var]
  t = d.getTime()
  c = t.asComponentTime()
  yrs = []
  for cc in c:
    if cc.year not in yrs: yrs.append(cc.year)
  mo_beg = c[0].month
  mo_end = c[len(c)-1].month
  yr_beg = c[0].year
  yr_end = c[len(c)-1].year

  print yr_beg,' ', mo_beg,' ', yr_end,' ', mo_end

### NEED TO TRAP DATASET NAME AND VERSION - THIS WILL BE IMPROVED WITH CMOR3
  tmp = string.split(fc,var+'_')[1]
  tmp2 =  string.split(tmp,`yr_beg`)[0]
  ver = string.replace(tmp2,'_','')
  print '####### ', ver

# newname = var + '_pcmdi-metrics_' + table_realm + '_' + ver + '_' + `yr_beg`+`mo_beg` + '-clim.nc' 

  z = ''
  if mo_beg in [1,2,3,4,5,6,7,8,9]: z = '0'
  if mo_end in [1,2,3,4,5,6,7,8,9]: z = '0'

  begyrmo = `yr_beg`+ z + `mo_beg`
  endyrmo = `yr_end`+ z + `mo_end`

# w = sys.stdin.readline()
#tos_pcmdi-metrics_Omon_NOAA-OISST-v2_198202-201201-clim.nc

  cmd1 = fc + ' -v ' + var + positive + ' -s ' + begyrmo + ' -e ' + endyrmo + ' -T CMOR_Amon_pmp_02052016 '  + '-O ' + outpath
  cmd1 = fc + ' -v ' + var + positive + ' -s ' + begyrmo + ' -e ' + endyrmo + ' -T CMOR_Amon_pmp_02052016 '  + '-O ' + ' --forcing ' + 'crap ' + outpath

  cmd = 'pcmdi_compute_climatologies.py -f ' + cmd1
  print cmd
  os.popen(cmd).readlines()
  print 'done with model ', var 
#    time.sleep(1)

  print 'JOB COMPLETE ', fc 

#cmd_mv_seas = 'mv ' + outpath_base + exp + '/*djf.nc ' + outpath_base + exp + '/*mam.nc ' + outpath_base + exp + '/*jja.nc ' + outpath_base + exp + '/*son.nc ' + outpath_base + exp + '/*year.nc ' + outpath_base + exp + '/seas'

#p = Popen(cmd_mv_seas,shell=True)

print 'JOB COMPLETE'

#    w = sys.stdin.readline()



