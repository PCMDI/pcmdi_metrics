#!/usr/bin/env python

#######################################################################################
# THIS PROGRAM USES pcmdi_compute_climatologies.py FOR MASS PRODUCTION OF CMORized MODEL CLIMATOLOGIES FROM DATA AVAILABEL FROM PCMDIS CMIP DATABASE

#######################################################################################

import pcmdi_metrics
import cdms2 as cdms
import os, string
import cdtime, cdutil
import MV2 as MV
import sys
import logging
import time
from subprocess import call,Popen,PIPE


#ClimCodePath = os.path.join( pcmdi_metrics.__path__[0], "..", "..", "..", "..", "share", "pcmdi", "scripts", "pcmdi_compute_climatologies.py")
ClimCodePath = 'pcmdi_compute_climatologies.py'
ClimCodePath = ClimCodePath + ' -f'


#ClimCodePath = '/export/gleckler1/git/pcmdi_metrics/src/python/pcmdi/scripts/pcmdi_compute_climatologies.py -f'


#### PARAMETERS SET BY USER #######################################################################################################
#EXPERIMENT
exp = 'cmip5-historical'
exp = 'cmip5-amip'

# OUTPUT TARGET ROOT DIRECTORY
#pathout_basedir = '/work/gleckler1/processed_data/'
outpath_base = '/work/metricspackage/mod_clims/'

# VARIABLES TO COMPUTE
#vars = ['rlut','rsdt','pr','ts','ta']
#vars = ['rlut','rsdt','rsut','rsutcs','rlutcs','rsds','rsus','rlus','rlds','rsuscs','rsdscs','rldscs','pr','prw','psl','ts','tas','tauu','tauv','uas','vas','huss', 'ta','ua','va','zg','hus']
vars = ['rsdt']

#### END PARAMETERS SET BY USER #######################################################################################

if exp == 'cmip5-historical':
  pathin_template = '/work/cmip5/historical/REALM/mo/'
  pathin = '/work/cmip5/historical/atm/mo/'

if exp == 'cmip5-amip':
  pathin_template = '/work/cmip5/amip/REALM/mo/'
  pathin = '/work/cmip5/amip/atm/mo/'



try:
 os.mkdir(outpath_base + exp)
except:
 pass
try:
 os.mkdir(outpath_base + exp + '/seas')
except:
 pass

outpath = outpath_base + exp

for var in vars:
  modruns = os.popen('ls ' + pathin + var + '/*CESM1-CAM5.*r1i1p1*.latestX.xml').readlines()
# modruns = os.popen('ls ' + pathin + var + '/*r1i1p1*.latestX.xml').readlines()

  positive = "" 
  if var in ['rlut','rsut','rsutcs','rlus','rsus','rsuscs','hfls','hfss']: positive = ' -X ' + "'{" + '"positive"' + ':' + '"up"' + "}'"  
  if var in ['rsdt','rldscs','rsdscs','rlds','rsds','tauu','tauv']: positive = ' -X ' + "'{" + '"positive"' + ':' + '"down"' + "}'"

  for run in modruns:
     mod = string.split(run,'.')[1]    
 
#    cmd1 = run[:-1] + ' -v ' + var + ' -X ' + '"{"positive":"up"}"  -s 1979-01 -e 1989-12 -T pcmdi_metrics' 
#    cmd1 = run[:-1] + ' -v ' + var + ' -X ' + "'{" + '"positive"' + ':' + '"up"' + "}'"  + ' -s 1979-01 -e 1989-12 -T ../lib/CMOR_Amon_pmp_02052016 '  + '-O ' + outpath  
#    cmd1 = run[:-1] + ' -v ' + var + positive + ' -s 1979-01 -e 1989-12 -T pcmdi_metrics '  + '-O ' + outpath  
     cmd1 = run[:-1] + ' -v ' + var + positive + ' -s 1979-01 -e 1989-12 -T CMOR_Amon_pmp_02052016 '  + '-O ' + outpath

     print run

     cmd = ClimCodePath + ' ' + cmd1 
     cmd = 'pcmdi_compute_climatologies.py -f ' + cmd1



     print cmd

#    p = Popen(cmd,shell=True)

     os.popen(cmd).readlines()
     print 'done with model ', mod

     time.sleep(1)

     print 'JOB COMPLETE ', run

     cmd_mv_seas = 'mv ' + outpath_base + exp + '/*djf.nc ' + outpath_base + exp + '/*mam.nc ' + outpath_base + exp + '/*jja.nc ' + outpath_base + exp + '/*son.nc ' + outpath_base + exp + '/*year.nc ' + outpath_base + exp + '/seas'

#    p = Popen(cmd_mv_seas,shell=True)

print 'JOB COMPLETE'

#    w = sys.stdin.readline()



