#!/usr/bin/env python
#######################################################################################
# THIS PROGRAM USES pcmdi_compute_climatologies.py FOR MASS PRODUCTION OF CMORized MODEL CLIMATOLOGIES FROM DATA AVAILABLE FROM PCMDI CMIP DATABASE
# ASPIRATIONAL GOAL IS TO BE THE WORKHORSE FOR PRODUCING ALL CMIP CLIMATOLGIES
# TODO:
## LOG FILE SHOULD BE ADDED
## NEED TO ADD OCEAN VARS AND CMOR TABLE
## PERIODS OK FOR HISTORICAL AND AMIP BUT NEED TO ADD OPTION FOR CONTROL WITH FLEXIBILITY IN NOT JUST HOW LONG BUT WHERE IN SIMULATION PERIOD IS FORM
## CURRENTLY ONLY OPERATING ON FIRST REALIZATION (r1) ... NEEDS TO BE GENERALIZED TO COMPUTE CLIMS FOR ALL REALIZATIONS
## ADD TO PARAMETER SET 'all' MODELS OR A LIST OF MODELS
## POSITIVE ATTRIBUTES SHOULD BE STORED EXTERNAL TO THIS PROGRAM 
## CMOR TABLES HARDWIRED - PROBABLY SHOULD BE OPTION ON PARAMETER LIST

#Last modified: PJG 03/04/16
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
#EXPERIMENT
exp = 'cmip5-historical'
exp = 'cmip5-amip'

## LIST OF ALL VARIABLES USED FROM EXPERIMENT

if exp == 'cmip5-amip': allvars = ['rlut','rsdt','rsut','rsutcs','rlutcs','rsds','rsus','rlus','rlds','rsuscs','rsdscs','rldscs','pr','prw','psl','ts','tas','tauu','tauv','uas','vas','huss', 'ta','ua','va','zg','hus']

# OUTPUT TARGET ROOT DIRECTORY
outpath_base = '/work/metricspackage/mod_clims/'

# VARIABLES TO COMPUTE (if not 'all' or list of individual vars)
vars = ['all']
#vars = ['rlut','rsdt','pr','ts','ta']
#vars = ['rlut','rsdt','rsut','rsutcs','rlutcs','rsds','rsus','rlus','rlds','rsuscs','rsdscs','rldscs','pr','prw','psl','ts','tas','tauu','tauv','uas','vas','huss', 'ta','ua','va','zg','hus']
#vars = ['rsdt']

# CLIMATOLOGY PERIOD 
begyrmo = '1979-12'     # Beginning year and month of period
endyrmo = '1989-12'     # End year and month of period

#### END PARAMETERS SET BY USER #######################################################################################
# INPUT PATHS
if exp == 'cmip5-historical': pathin = '/work/cmip5/historical/atm/mo/'
if exp == 'cmip5-amip': pathin = '/work/cmip5/amip/atm/mo/'

outpath = outpath_base + exp    # OUTPUT DIR

## CREATE DIRECTORIES AS NEEDED
for newdir in [outpath_base + exp, outpath_base + exp + '/seas']:
 try:
   os.mkdir(newdir)
 except:
   pass

## TRAP ALL VARS AS NEEDED 
if vars[0] == 'all':
   vars = []
   lst = os.popen('ls ' + pathin + '/*/*r1i1p1*.latestX.xml').readlines() 
   for l in lst:
     var = string.split(l,'/')[7] 
     if var not in vars and var in allvars: 
        vars.append(var)

## LOOP THROUGH VARIABLES
print 'working on ', vars
for var in vars:
  modruns = os.popen('ls ' + pathin + var + '/*NorESM1-M.*r1i1p1*.latestX.xml').readlines()  #KEEP FOR QUICK TESTING
# modruns = os.popen('ls ' + pathin + var + '/*r1i1p1*.latestX.xml').readlines()

  positive = "" 
  if var in ['rlut','rsut','rsutcs','rlus','rsus','rsuscs','hfls','hfss']: positive = ' -X ' + "'{" + '"positive"' + ':' + '"up"' + "}'"  
  if var in ['rsdt','rldscs','rsdscs','rlds','rsds','tauu','tauv']: positive = ' -X ' + "'{" + '"positive"' + ':' + '"down"' + "}'"

## LOOP THROUGH MODELS
  for run in modruns:
     print run
     mod = string.split(run,'.')[1]    
     cmd1 = run[:-1] + ' -v ' + var + positive + ' -s ' + begyrmo + ' -e ' + endyrmo + ' -T CMOR_Amon_pmp_02052016 '  + '-O ' + outpath
     cmd = 'pcmdi_compute_climatologies.py -f ' + cmd1
     print cmd
     os.popen(cmd).readlines()
     print 'done with model ', mod
#    time.sleep(1)

     print 'JOB COMPLETE ', run

cmd_mv_seas = 'mv ' + outpath_base + exp + '/*djf.nc ' + outpath_base + exp + '/*mam.nc ' + outpath_base + exp + '/*jja.nc ' + outpath_base + exp + '/*son.nc ' + outpath_base + exp + '/*year.nc ' + outpath_base + exp + '/seas'

p = Popen(cmd_mv_seas,shell=True)

print 'JOB COMPLETE'

#    w = sys.stdin.readline()



