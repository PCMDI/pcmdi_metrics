#### USED TO GENERATE XML FILES FOR NCAR CLIMATOLGIES

# NCAR OUTPUT PRODUCES CLIMATOLOGIES FOR EACH CALENDAR MONTH AS SEPERATE FILES
# XMLS PRODUCED BY THIS CODES COMBINE THESE SO THAT THE MONTHLY CLIMATOLOGICAL ANNUAL CYCLE CAN BE READ BY A SINGLE (XML) FILE
# THE VARIABLES "filenamea" AND "filenameb" BELOW ARE NOT LIKELY TO WORK FOR THE GENERAL CASE.  THE LOGIC TO TRAP months "01", "02"... and "10", "11" and "12" MAY NEED TO BE MODIFIED DEPENDING ON THE FILES AVAILABLE.

# LAST UPDATE 6/29/16 PJG

####

import cdms2 as cdms
import os, string
import time
import sys
import argparse

# Set cdms preferences - no compression, no shuffling, no complaining
cdms.setNetcdfDeflateFlag(1)
cdms.setNetcdfDeflateLevelFlag(9) ; # 1-9, min to max - Comes at heavy IO (read/write time cost)
cdms.setNetcdfShuffleFlag(0)
cdms.setCompressionWarnings(0) ; # Turn off nag messages
# Set bounds automagically
#cdm.setAutoBounds(1) ; # Use with caution

parser = argparse.ArgumentParser(description='Given a list of directories with simulation clims, use cdscan to produce xmls for annual cycle climatologies ')
parser.add_argument("-b","--basedir",help="root directory below which subdirectories of individual simulations are expected")  #,default="*.nc",nargs="*")
parser.add_argument("-o","--outdir",help="output directory",default=None)

args =parser.parse_args(sys.argv[1:])

pathin = args.basedir + '/' # Get string from first index of list - only one directory expected

xmldir = args.outdir + '/'

try:
       os.mkdir(xmldir)
except:
       pass

print 'pathin is...', pathin
print 'pathout is...', xmldir

# It is assummed that each subdirectory (run) with the path xmldir includes climatological files
runs  = os.listdir(pathin)

print runs

for run in runs:

     filename = run

# In this case the clim files are in the run directory
     try:
      filenamea = filename + '.001_0*_climo.nc'
      filenameb = filename + '.001_1*_climo.nc'
      cmd = 'cdscan -x ' + xmldir + filename + '.xml ' + pathin + filename + '/' + filenamea  + ' ' + pathin + filename + '/' + filenameb
      print cmd
      os.popen(cmd).readlines()
     except:
      pass

# In this case the clim files are in the run/climo directory
     try:
      filenamea = filename + '_0*_climo.nc'
      filenameb = filename + '_1*_climo.nc'

      cmd = 'cdscan -x ' + xmldir + filename + '.xml ' + pathin + filename + '/climo/' + filenamea  + ' ' + pathin + filename + '/climo/' + filenameb
      os.popen(cmd).readlines()
     except:
      pass



