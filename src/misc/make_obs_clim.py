#!/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Thu May 30 10:19:45 2013

Paul J. Durack 30th May 2013

This script takes an input file and creates an annual cycle and annual mean climatology

PJD 30 May 2013     - Updated to copy across variable attributes from source file
                    /work/durack1/Shared/obs_data/temperature/HadCRUT3/130122_HadISST_sst.nc
                    /work/durack1/Shared/obs_data/temperature/NOAA_OISSTv2/130528_sst.mnmean.nc
PJD  4 Jun 2013     - Updated to include source file global attributes and wgne attribute stamps
PJD  4 Jun 2013     - TODO: Fix issues with incomplete or years outside of 1980-2005 being referenced:
                      case zos_CNES_AVISO_L4_199201-200512_ac.nc - infile: zos_AVISO_L4_199210-201012.nc
                      case nofile - infile 130509_AQUARIUS_V2_monthly_SSS_20110817-20130416.nc
PJD  5 Jun 2013     - Generated tos/sos from WOA09 data
PJD  6 Jun 2013     - Replaced "." delimiters with "_" or "-" - to comply with DRS and obs4mips documentation
PJD  6 Jun 2013     - Obtained month from start_time and end_time to replace default '01' and '12' in outfile
PJD  6 Jun 2013     - Updated tos data to correct CMIP5 units, degC -> K
PJD 12 Jun 2013     - Removed unused att_dic variable
PJD 14 Jan 2014     - Updated outfile conventions
PJD 14 Jan 2014     - Updated shebang ; was #!/usr/local/uvcdat/latest/bin/python
                    - TODO: Argo data downloaded, process into format
                    - TODO: Obtain SMOS sos data and process

@author: durack1
"""

import argparse,gc,os,sys
import cdms2 as cdm
import cdtime as cdt
import cdutil as cdu
#sys.path.insert(1,'/export/durack1/git/pylib')
from durolib import globalAttWrite,spyderClean
from numpy.core.fromnumeric import shape
from string import replace

# Cleanup spyder - not currently working
spyderClean()
# Cleanup interactive/spyder sessions
if 'e' in locals():
    del(e,pi,sctypeNA,typeNA)
    gc.collect()

# Set netcdf file criterion - turned on from default 0s
cdm.setCompressionWarnings(0) ; # Suppress warnings
cdm.setNetcdfShuffleFlag(0)
cdm.setNetcdfDeflateFlag(1)
cdm.setNetcdfDeflateLevelFlag(9)
# Hi compression: 1.4Gb file ; # Single salt variable
# No compression: 5.6Gb ; Standard (compression/shuffling): 1.5Gb ; Hi compression w/ shuffling: 1.5Gb

# Set conditional whether files are created or just numbers are calculated
parser = argparse.ArgumentParser()
parser.add_argument('file',metavar='str',type=str,help='\'file\' will select one file to process')
parser.add_argument('file_variable',metavar='str',type=str,help='\'file_variable\' will select one variable to process')
parser.add_argument('target_variable',metavar='str',type=str,help='\'target_variable\' will select one variable to process')
parser.add_argument('data_source',metavar='str',type=str,help='\'data_source\' will use this descriptor in outfile name creation')
parser.add_argument('start_yr',nargs='?',metavar='int',type=int,help='\'start_yr\' set a start year from which to process (default=1980)')
parser.add_argument('end_yr',nargs='?',metavar='int',type=int,help='\'end_yr\' set an end year from which to process (default=2005)')
args = parser.parse_args()

# Test and validate file
if (args.file == ""):
    print "** No valid file specified - no *.nc files will be written **"
    sys.exit()
elif os.path.isfile(args.file) is False:
    print "** No valid file specified - no *.nc files will be written **"
    sys.exit()

# Get CMOR_table_id
if args.target_variable in ['sos','tos','zos']:
    cmor_table = 'Omon'
elif args.target_variable in ['tas','pr']:
    cmor_table = 'Amon'

# Open file instance
print "".join(['** Processing: ',args.file])
f_h = cdm.open(args.file)
try:
    start_time = f_h.getAxis('time').asComponentTime()[0]
    print ''.join(['start_time: ',str(start_time)])
    end_time = f_h.getAxis('time').asComponentTime()[-1]
    print ''.join(['end_time:   ',str(end_time)])
except:
    print '** No time access associated with file_variable'
    start_time = cdt.comptime(int(args.start_yr),1,1)
    end_time = cdt.comptime(int(args.end_yr),12,31)

# Test and validate file_variable
if (args.file_variable == ""):
    print "** No valid variable specified - no *.nc files will be written **"
    sys.exit()
if args.file_variable not in f_h.variables.keys():
    print "** No valid variable specified - no *.nc files will be written **"
    f_h.close()
    sys.exit()
# Test target_variable
if (args.target_variable == ""):
    print "** No valid target_variable specified - no *.nc files will be written **"
    sys.exit()
# Test data_source
if (args.data_source == ""):
    print "** No valid data_source specified - no *.nc files will be written **"
    sys.exit()
else:
    # Convert data_source to standard - saving '_' for field delimiters
    data_source = replace(replace(args.data_source,'_','-'),'.','-')
# Set default years
start_yr = 1980
end_yr   = 2005

# Test start_yr
if args.start_yr == None:
    print "** No valid start_yr specified           - defaulting to start_yr=1980 **"
    start_yr = 1980
    start_yr_s = str(start_yr)
elif args.start_yr != None and start_time.year == 0:
    start_yr = args.start_yr
    start_yr_s = str(start_yr)    
    print "".join(['** Start year specified by user - resetting to start_yr=',start_yr_s,' **'])
elif args.start_yr != None:
    start_yr = args.start_yr
    start_yr_s = str(start_yr)    
    print "".join(['** Start year specified by user - resetting to start_yr=',start_yr_s,' **'])
elif start_time.year < start_yr:
    start_yr = 1980
    start_yr_s = str(start_yr)    
    print "".join(['** Start year != 1980           - resetting to start_yr=1980 **'])
elif start_time.year > start_yr:
    start_yr = start_time.year
    start_yr_s = str(start_yr)    
    print "".join(['** Start year != 1980           - resetting to start_yr=',start_yr_s,' **'])
# Test end_yr
if args.end_yr == None:
    print "** No valid end_yr specified             - defaulting to end_yr=2005 **"
    end_yr = 2005
    end_yr_s = str(end_yr)
elif args.end_yr != None and end_time.year == 0:
    end_yr = args.end_yr
    end_yr_s = str(end_yr)    
    print "".join(['** End year specified by user   - resetting to end_yr=',end_yr_s,' **'])
elif args.end_yr != None:
    end_yr = args.end_yr
    end_yr_s = str(end_yr)    
    print "".join(['** End year specified by user   - resetting to end_yr=',end_yr_s,' **'])
elif end_time.year < end_yr:
    end_yr = end_time.year
    end_yr_s = str(end_yr)
    print "".join(['** End year != 2005             - resetting to start_yr=',end_yr_s,' **'])
elif end_time.year > end_yr and start_time.year > end_yr:
    end_yr = args.end_yr
    end_yr_s = str(end_yr)
    print "".join(['** End year specified by user   - resetting to end_yr=',end_yr_s,' **'])
elif end_time.year > end_yr:
    end_yr = 2005
    end_yr_s = str(end_yr)
    print "".join(['** End year != 2005             - resetting to start_yr=2005 **'])

# Open and process file
f_h = cdm.open(args.file)
d = f_h[args.file_variable]
# Deal with data formats
if d.getAxisIndex('depth') != -1 and shape(d)[d.getAxisIndex('time')] == 12 and 'WOA' in args.data_source:
    # Case WOA09 - test for 3d and trim off top layer
    clim_ac = cdu.ANNUALCYCLE.climatology(d[:,0,:,:]) ; #shape 12,24,180,360
    start_month_s   = '01'
    end_month_s     = '12'
elif d.getAxisIndex('PRESSURE') != -1 and shape(d)[d.getAxisIndex('time')] == 12 and 'UCSD' in args.data_source:
    # Case ARGO UCSD - test for 3d and trim off top layer
    if args.target_variable in 'sos':
        d_mean = f_h('ARGO_SALINITY_MEAN')
    elif args.target_variable in 'tos':
        d_mean = f_h('ARGO_TEMPERATURE_MEAN')
    # Create annual cycle from annual mean
    d_ancycle = d_mean + d
    #print d_ancycle.shape
    #print d_ancycle[:,0,...].shape
    #print d_ancycle.getAxisIds()
    d_ancycle = d_ancycle[:,0,...]
    #print d_ancycle.getAxisIds()
    cdu.setTimeBoundsMonthly(d_ancycle)
    #clim_ac = cdu.ANNUALCYCLE.climatology(d_ancycle) ; #shape 12,58,260,720
    clim_ac = d_ancycle;    
    start_month_s   = '01'
    end_month_s     = '12'
else:
    if args.data_source in 'HadISST':
        boundnodes = 'co'
    elif args.data_source in 'NOAA_OISSTv2':
        boundnodes = 'oob'
    else:
        boundnodes = 'ocn'
    cdu.setTimeBoundsMonthly(d) ; # Set bounds before trying to chop up
    clim_ac = cdu.ANNUALCYCLE.climatology(d(time=(cdt.comptime(int(start_yr_s),1,1),cdt.comptime(int(end_yr_s)+1,1,1),boundnodes))) ; #shape 12,180,360
    # Methods to calculate annual cycle/12 months
    #clim_an = cdutil.YEAR.climatology(d(time=(start_yr_s,end_yr_s,"cob")))
    #a = cdutil.ANNUALCYCLE(d(time=(start_yr_s,end_yr_s,'co'))) ; #shape 301,180,360
    #b = cdutil.SEASONALCYCLE(d(time=(str(start_yr),str(end_yr),'co'))) ; #shape 101,180,360
    #c = cdutil.times.SEASONALCYCLE(d(time=(str(start_yr),str(end_yr),'co'))) ; #shape 101,180,360
    #clim_ac = cdutil.ANNUALCYCLE.climatology(d(time=(str(start_yr),str(end_yr),'co'))) ; #shape 12,180,360
    
    # Determine start_month and end_month from variable time axis
    tmp = d(time=(cdt.comptime(int(start_yr_s),1,1),cdt.comptime((int(start_yr_s)+1),1,1),boundnodes))
    t = tmp.getAxis(0)
    start_month_s = format(t.asComponentTime()[0].month,"02d")
    tmp = d(time=(cdt.comptime(int(end_yr_s),1,1),cdt.comptime((int(end_yr_s)+1),1,1),boundnodes))
    t = tmp.getAxis(0)
    end_month_s = format(t.asComponentTime()[-1].month,"02d")
# Test units and convert if necessary
#print d.units
if d.units in ['degC','degree_C','degree celcius (ITS-90)']:
    clim_ac = clim_ac+273.15 ; # Correct to Kelvin
    clim_ac.units = 'K'
else:
    clim_ac.units = d.units
# Rewrite variable attributes
clim_ac.id = args.target_variable
clim_ac.name = args.target_variable
clim_ac.source_name = args.file_variable
att_keys = d.attributes.keys()
for i,key in enumerate(d.attributes.keys()):
    if key in ['Conventions','conventions','add_offset','history','institution','missing_value','name','scale_factor','source_name','units']:
        continue
    setattr(clim_ac,key,d.attributes.get(key))

# Create outfile - following obs4mips notation
# satellite datasets = <variable>_<instrument>_<processing_level>_<processing_version>_<start_date>-<end_date>.nc
# in-situ datasets = <variable>_<project>_<location>_<instrument>_<processing_level_and_product_version>_<start_date>-<end_date>.nc
#outfile = "_".join([args.target_variable,'wgne-wgcm-metrics','global','instrument',data_source,"-".join(["".join([start_yr_s,start_month_s]),"".join([end_yr_s,end_month_s])]),'ac.nc']) ; #140114
outfile = "".join(["_".join([args.target_variable,'pcmdi-metrics',cmor_table,data_source,"-".join(["".join([start_yr_s,start_month_s]),"".join([end_yr_s,end_month_s]),'clim'])]),'.nc'])
print "".join(['** Creating: ',outfile])

# Check file exists
if os.path.exists(outfile):
    print "** File exists.. removing **"
    os.remove(outfile)
f_out = cdm.open(outfile,'w')
# Write new outfile global atts
globalAttWrite(f_out,options=None) ; # Use function to write standard global atts# Write to output file
f_out.pcmdi_metrics_version = '0.1-alpha'
f_out.pcmdi_metrics_comment = 'This climatology was prepared by PCMDI for the WGNE/WGCM metrics package and is intended for research purposes only'
for i,key in enumerate(f_h.attributes.keys()):
    setattr(f_out,key,f_h.attributes.get(key)) ; # Rewrite source file global_atts to file
f_out.write(clim_ac.astype('float32')) ; # Write clim first as it has all grid stuff
# Close all files
f_h.close()
f_out.close()