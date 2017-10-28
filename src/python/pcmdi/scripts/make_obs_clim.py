#!/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Thu May 30 10:19:45 2013

Paul J. Durack 30th May 2013

This script takes an input file and creates
an annual cycle and annual mean climatology

@author: durack1
"""

import argparse
import gc
import os
import sys
import cdms2 as cdm
import cdtime as cdt
import cdutil as cdu
# sys.path.insert(1,'/export/durack1/git/pylib')
from durolib import globalAttWrite, spyderClean
from numpy.core.fromnumeric import shape
from string import replace

# Cleanup spyder - not currently working
spyderClean()
# Cleanup interactive/spyder sessions
if 'e' in locals():
    del(e, pi, sctypeNA, typeNA)  # noqa
    gc.collect()

# Set netcdf file criterion - turned on from default 0s
cdm.setCompressionWarnings(0)  # Suppress warnings
cdm.setNetcdfShuffleFlag(0)
cdm.setNetcdfDeflateFlag(1)
cdm.setNetcdfDeflateLevelFlag(9)
# Hi compression: 1.4Gb file ; # Single salt variable
# No compression: 5.6Gb ; Standard (compression/shuffling): 1.5Gb ; Hi
# compression w/ shuffling: 1.5Gb

# Set conditional whether files are created or just numbers are calculated
parser = argparse.ArgumentParser()
parser.add_argument(
    'file',
    metavar='str',
    type=str,
    help="'file' will select one file to process")
parser.add_argument(
    'file_variable',
    metavar='str',
    type=str,
    help="'file_variable' will select one variable to process")
parser.add_argument(
    'target_variable',
    metavar='str',
    type=str,
    help="'target_variable' will select one variable to process")
parser.add_argument(
    'data_source',
    metavar='str',
    type=str,
    help="'data_source' will use this descriptor" +
            " in outfile name creation")
parser.add_argument(
    'start_yr',
    nargs='?',
    metavar='int',
    type=int,
    help="'start_yr' set a start year from which" +
            " to process(default=1980)")
parser.add_argument(
    'end_yr',
    nargs='?',
    metavar='int',
    type=int,
    help="'end_yr' set an end year from which to process (default=2005)")
args = parser.parse_args()

# Test and validate file
if (args.file == ""):
    print "** No valid file specified - no *.nc " +\
        "files will be written **"
    sys.exit()
elif os.path.isfile(args.file) is False:
    print "** No valid file specified - no " +\
        "*.nc files will be written **"
    sys.exit()

# Get CMOR_table_id
if args.target_variable in ['sos', 'tos', 'zos']:
    cmor_table = 'Omon'
elif args.target_variable in ['tas', 'pr']:
    cmor_table = 'Amon'
elif args.target_variable in ['sftlf']:
    cmor_table = 'fx'

# Open file instance
print "".join(['** Processing: ', args.file])
f_h = cdm.open(args.file)
try:
    start_time = f_h.getAxis('time').asComponentTime()[0]
    print ''.join(['start_time: ', str(start_time)])
    end_time = f_h.getAxis('time').asComponentTime()[-1]
    print ''.join(['end_time:   ', str(end_time)])
except BaseException:
    print '** No time access associated with file_variable'
    start_time = cdt.comptime(int(args.start_yr), 1, 1)
    end_time = cdt.comptime(int(args.end_yr), 12, 31)

# Test and validate file_variable
if (args.file_variable == ""):
    print "** No valid variable specified - " +\
        "no *.nc files will be written **"
    sys.exit()
if args.file_variable not in f_h.variables.keys():
    print "** No valid variable specified - " +\
        "no *.nc files will be written **"
    f_h.close()
    sys.exit()
# Test target_variable
if (args.target_variable == ""):
    print "** No valid target_variable specified - " +\
        "no *.nc files will be written **"
    sys.exit()
# Test data_source
if (args.data_source == ""):
    print "** No valid data_source specified - " +\
        "no *.nc files will be written **"
    sys.exit()
else:
    # Convert data_source to standard - saving '_' for field delimiters
    data_source = replace(replace(args.data_source, '_', '-'), '.', '-')
# Set default years
start_yr = 1980
end_yr = 2005

# Test start_yr
if args.start_yr is None:
    print "** No valid start_yr specified           " +\
        "- defaulting to start_yr=1980 **"
    start_yr = 1980
    start_yr_s = str(start_yr)
elif args.start_yr is not None and start_time.year == 0:
    start_yr = args.start_yr
    start_yr_s = str(start_yr)
    print '** Start year specified by user - ' +\
        'resetting to start_yr= %s **' % start_yr_s
elif args.start_yr is not None:
    start_yr = args.start_yr
    start_yr_s = str(start_yr)
    print '** Start year specified by user ' +\
        '- resetting to start_yr= %s **' % start_yr_s
elif start_time.year < start_yr:
    start_yr = 1980
    start_yr_s = str(start_yr)
    print '** Start year != 1980           ' +\
        '- resetting to start_yr=1980 **'
elif start_time.year > start_yr:
    start_yr = start_time.year
    start_yr_s = str(start_yr)
    print '** Start year != 1980           "+\
            "- resetting to start_yr= %s **' % start_yr_s
# Test end_yr
if args.end_yr is None:
    print "** No valid end_yr specified             " +\
        "- defaulting to end_yr=2005 **"
    end_yr = 2005
    end_yr_s = str(end_yr)
elif args.end_yr is not None and end_time.year == 0:
    end_yr = args.end_yr
    end_yr_s = str(end_yr)
    print '** End year specified by user   ' +\
        '- resetting to end_yr= %s **' % end_yr_s
elif args.end_yr is not None:
    end_yr = args.end_yr
    end_yr_s = str(end_yr)
    print '** End year specified by user   -' +\
        ' resetting to end_yr= %s **' % end_yr_s
elif end_time.year < end_yr:
    end_yr = end_time.year
    end_yr_s = str(end_yr)
    print '** End year != 2005             ' +\
        '- resetting to start_yr= %s **' % end_yr_s
elif end_time.year > end_yr and start_time.year > end_yr:
    end_yr = args.end_yr
    end_yr_s = str(end_yr)
    print '** End year specified by user   ' +\
        '- resetting to end_yr= %s **' % end_yr_s
elif end_time.year > end_yr:
    end_yr = 2005
    end_yr_s = str(end_yr)
    print '** End year != 2005             - resetting to start_yr=2005 **'

# Open and process file
f_h = cdm.open(args.file)
d = f_h[args.file_variable]
# Deal with data formats
if args.target_variable == 'sftlf':
    if args.data_source == 'ECMWF-ERAInterim':
        clim_ac = f_h(args.file_variable)
        for i, key in enumerate(clim_ac.attributes.keys()):
            if key in ['add_offset', 'missing_value', 'scale_factor']:
                continue
            else:
                print key
                delattr(clim_ac, key)
        start_month_s = '01'
        end_month_s = '12'
    elif args.data_source == 'UKMetOffice-HadISST':
        print args.data_source
        clim_ac = f_h(args.file_variable)[0, ...]
        clim_ac1 = cdm.createVariable(clim_ac.mask, id='sftlf')
        clim_ac1.setGrid(clim_ac.getGrid())
        clim_ac = clim_ac1
        del(clim_ac1)
        start_month_s = '01'
        end_month_s = '07'

elif d.getAxisIndex('depth') != -1 and\
        shape(d)[d.getAxisIndex('time')] == 12 and\
        'WOA' in args.data_source:
    # Case WOA09 - test for 3d and trim off top layer
    clim_ac = cdu.ANNUALCYCLE.climatology(d[:, 0, :, :])  # shape 12,24,180,360
    start_month_s = '01'
    end_month_s = '12'
elif d.getAxisIndex('PRESSURE') != -1 and\
        shape(d)[d.getAxisIndex('time')] == 12 and\
        'UCSD' in args.data_source:
    # Case ARGO UCSD - test for 3d and trim off top layer
    if args.target_variable in 'sos':
        d_mean = f_h('ARGO_SALINITY_MEAN')
    elif args.target_variable in 'tos':
        d_mean = f_h('ARGO_TEMPERATURE_MEAN')
    # Create annual cycle from annual mean
    d_ancycle = d_mean + d
    # print d_ancycle.shape
    # print d_ancycle[:,0,...].shape
    # print d_ancycle.getAxisIds()
    d_ancycle = d_ancycle[:, 0, ...]
    # print d_ancycle.getAxisIds()
    cdu.setTimeBoundsMonthly(d_ancycle)
    # clim_ac = cdu.ANNUALCYCLE.climatology(d_ancycle) ; #shape 12,58,260,720
    clim_ac = d_ancycle
    start_month_s = '01'
    end_month_s = '12'
else:
    if args.data_source in 'HadISST':
        boundnodes = 'co'
    elif args.data_source in 'NOAA_OISSTv2':
        boundnodes = 'oob'
    else:
        boundnodes = 'ocn'
    cdu.setTimeBoundsMonthly(d)  # Set bounds before trying to chop up
    clim_ac = cdu.ANNUALCYCLE.climatology(
        d(
            time=(
                cdt.comptime(
                    int(start_yr_s), 1, 1), cdt.comptime(
                    int(end_yr_s) + 1, 1, 1), boundnodes)))  # shape 12,180,360

    # Determine start_month and end_month from variable time axis
    tmp = d(
        time=(
            cdt.comptime(
                int(start_yr_s), 1, 1), cdt.comptime(
                (int(start_yr_s) + 1), 1, 1), boundnodes))
    t = tmp.getAxis(0)
    start_month_s = format(t.asComponentTime()[0].month, "02d")
    tmp = d(
        time=(
            cdt.comptime(
                int(end_yr_s), 1, 1), cdt.comptime(
                (int(end_yr_s) + 1), 1, 1), boundnodes))
    t = tmp.getAxis(0)
    end_month_s = format(t.asComponentTime()[-1].month, "02d")
# Test units and convert if necessary
# print d.units
if d.units in ['degC', 'degree_C', 'degree celcius (ITS-90)']:
    clim_ac = clim_ac + 273.15  # Correct to Kelvin
    clim_ac.units = 'K'
elif args.target_variable == 'sftlf':
    pass
else:
    clim_ac.units = d.units
# Rewrite variable attributes
print args.target_variable
print clim_ac.shape
clim_ac.id = args.target_variable
clim_ac.name = args.target_variable
clim_ac.source_name = args.file_variable
att_keys = d.attributes.keys()
for i, key in enumerate(d.attributes.keys()):
    if key in ['Conventions', 'conventions', 'add_offset',
               'history', 'institution',
               'missing_value', 'name',
               'scale_factor', 'source_name', 'units']:
        continue
    setattr(clim_ac, key, d.attributes.get(key))

# Create outfile - following obs4mips notation
outfile = "".join(["_".join([args.target_variable,
                             'pcmdi-metrics',
                             cmor_table,
                             data_source,
                             "-".join(["".join([start_yr_s,
                                                start_month_s]),
                                       "".join([end_yr_s,
                                                end_month_s]),
                                       'clim'])]),
                   '.nc'])
print "".join(['** Creating: ', outfile])

# Check file exists
if os.path.exists(outfile):
    print "** File exists.. removing **"
    os.remove(outfile)
f_out = cdm.open(outfile, 'w')
# Write new outfile global atts
# Use function to write standard global atts# Write to output file
globalAttWrite(f_out, options=None)
f_out.pcmdi_metrics_version = '0.1-alpha'
f_out.pcmdi_metrics_comment = 'This climatology was prepared by PCMDI ' +\
    'for the WGNE/WGCM metrics package and ' +\
    'is intended for research purposes only'
for i, key in enumerate(f_h.attributes.keys()):
    if key in ['history']:
        continue
    # Rewrite source file global_atts to file
    setattr(f_out, key, f_h.attributes.get(key))
# Write clim first as it has all grid stuff
f_out.write(clim_ac.astype('float32'))
# Close all files
f_h.close()
f_out.close()
