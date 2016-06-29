#### USED TO GENERATE XML FILES FOR NCAR CLIMATOLGIES
# NCAR PRODUCES CLIMATOLOGIES FOR EACH CALENDAR MONTH AS SEPERATE FILES
# XMLS PRODUCED BY THIS CODES COMBINE THESE SO THAT THE MONTHLY CLIMATOLOGICAL ANNUAL CYCLE CAN BE READ BY A SINGLE (XML) FILE  

## THIS CODE NEEDS TO BE IMPROVED USING argparse SO THAT OPTIONS CAN BE SENT VIA COMMAND LINE.  CURRENTLY HARDWIRED

# LAST UPDATE 6/29/16 PJG

####

import cdms2 as cdms
import os, string
import time
import sys
# Set cdms preferences - no compression, no shuffling, no complaining
cdms.setNetcdfDeflateFlag(1)
cdms.setNetcdfDeflateLevelFlag(9) ; # 1-9, min to max - Comes at heavy IO (read/write time cost)
cdms.setNetcdfShuffleFlag(0)
cdms.setCompressionWarnings(0) ; # Turn off nag messages
# Set bounds automagically
#cdm.setAutoBounds(1) ; # Use with caution


pathin = '/work/gleckler1/processed_data/ncar_clims/'
#pathin = '/work/gleckler1/processed_data/ncar_clims/46L_cam5301_B03F2_taper2_D05_FAMIP/'

lst  = os.listdir(pathin)

runs = []

for l in lst:
   if l not in ['ncar-older','older-older', 'ncar-crap']: runs.append(l)

runs = ['46L_cam5301_B03F2_taper2_D05_FAMIP']
print runs 

for run in runs:

     filename = run   #string.split(test_dic[exp][test],'/')[0]
     filenamea = filename + '_0*_climo.nc' 
     filenameb = filename + '_1*_climo.nc'

#    cmd = 'cdscan -x text.xml '  +  pathin + '/' + test_dic[exp][test] + '/' + filename + '_[0-9]*_climo.nc' 

     xmldir = 'xmls/'

     try:  
      cmd = 'cdscan -x ' + xmldir + filename + '.xml ' + pathin + filename + '/' + filenamea  + ' ' + pathin + filename + '/' + filenameb  
      print cmd
#    w = sys.stdin.readline()    
      os.popen(cmd).readlines()
     except:
      pass

     try: 
      cmd = 'cdscan -x ' + xmldir + filename + '.xml ' + pathin + filename + '/climo/' + filenamea  + ' ' + pathin + filename + '/climo/' + filenameb
      print cmd
#    w = sys.stdin.readline()    
      os.popen(cmd).readlines()
     except:
      pass



