#!/usr/bin/env python

# Globally average the variance of daily mean precipitation values from a given month spanning a given set of years,
# then take the square root. This is the correct order of operations to get the fraction of total variance, as shown
# by Covey and Gehne 2016 (https://e-reports-ext.llnl.gov/pdf/823104.pdf).

# For Januarys, taking the square root before globally averaging would be close to the DJF results mapped in the
# middle-right panel of Figure 2 in Trenberth, Zhang & Gehne (2107) "Intermittency in Precipitation," J. Hydromet.
# This is done in ./plot_std_of_dailymeans.py.)

# This has the PMP Parser "wrapped" around it, so it's executed with both input and output parameters specified in the
# Unix command line. For example:

# ---> python std_of_dailymeansWrappedInOut.py -i out -o jsons -m 7

#       Charles Doutriaux September 2017
#	Curt Covey (from ./old_std_of_dailymeansWrappedInOut.py)		            July 2017

import cdms2, cdutil, os
import numpy.ma
import pcmdi_metrics
import collections
import glob
import sys
import genutil

from pcmdi_metrics.diurnal.common import monthname_d, P, populateStringConstructor

P.add_argument("-j", "--outnamejson",
                      type = str,
                      dest = 'outnamejson',
                      default = 'pr_%(month)_%(firstyear)_%(lastyear)_std_of_dailymeans.json',
                      help = "Output name for jsons")

P.add_argument("--lat1",type=float,default=-49.875,help="First latitude")
P.add_argument("--lat2",type=float,default=49.875,help="Last latitude")
P.add_argument("--lon1",type=float,default=0.125,help="First longitude")
P.add_argument("--lon2",type=float,default=359.875,help="Last longitude")

P.add_argument("-t","--filename_template",
       default = "pr_%(month)_%(firstyear)-%(lastyear)_std_of_dailymeans.nc")
P.add_argument("--model",default="*")

args = P.parse_args(sys.argv[1:])
month = args.month
monthname = monthname_d[month]
startyear = args.firstyear
finalyear = args.lastyear

template = populateStringConstructor(args.filename_template, args)
template.month = monthname

print "TEMPLATE NAME:",template()

print 'Specifying latitude / longitude domain of interest ...'
# TRMM (observed) domain:
latrange = (args.lat1,args.lat2)
lonrange =  (args.lon1,args.lon2)

# Amazon basin:
# latrange = (-15.0,  -5.0)
# lonrange = (285.0, 295.0)

datanameID = 'dailySD' # Short ID name of output data

print 'Preparing to write output to JSON file ...'           
if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
jsonFile = populateStringConstructor(args.outnamejson,args)
jsonFile.month = monthname

jsonname = os.path.join(os.path.abspath(args.output_directory),jsonFile())

if not os.path.exists(jsonname) or args.append is False:
    print 'Initializing dictionary of statistical results ...'
    stats_dic = {}
else:
    with open(jsonname) as f:
        j = json.load(f)
        stats_dic = j["RESULTS"]

OUT = pcmdi_metrics.io.base.Base(os.path.abspath(args.output_directory),jsonFile())
disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pmp",
        "disclaimer.txt")).read()
metrics_dictionary = collections.OrderedDict()
metrics_def_dictionary = collections.OrderedDict()
metrics_dictionary["DISCLAIMER"] = disclaimer
metrics_dictionary["REFERENCE"] = "The statistics in this file are based on Trenberth, Zhang & Gehne, J Hydromet. 2017"


files = glob.glob(os.path.join(args.modroot,template()))
print files
for fnameRoot in files:
    print 'Reading %s ...' % fnameRoot
    reverted = template.reverse(os.path.basename(fnameRoot))
    model = reverted["model"]
    f = cdms2.open(fnameRoot)
    x = f(datanameID, lat = latrange, lon = lonrange)
    units = x.units
    print '  Shape =', x.shape
    print 'Finding RMS area-average ...'
    x = x*x
    x = cdutil.averager(x, axis = 'xy')
    x = numpy.ma.sqrt(x)
    print 'For %8s in %s, average variance of daily values = (%5.2f %s)^2' % (model, monthname, x, units)
    stats_dic[model] = float(x) # Converts singleton transient variable to plain floating-point number
    f.close()


print 'Writing output to JSON file ...'
metrics_dictionary["RESULTS"] = stats_dic
OUT.write(
                metrics_dictionary,
                json_structure=["model","domain"],
                indent=4,
                separators=(
                    ',',
                    ': '))
print 'done'
