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
# Curt Covey (from ./old_std_of_dailymeansWrappedInOut.py)
# July 2017

import cdms2
import cdutil
import os
import numpy.ma
import pcmdi_metrics
import collections
import glob
import sys
import json

from pcmdi_metrics.diurnal.common import monthname_d, P, populateStringConstructor, INPUT
import cdp


def compute(param):
    template = populateStringConstructor(args.filename_template, args)
    template.variable = param.varname
    template.month = param.monthname
    fnameRoot = param.fileName
    reverted = template.reverse(os.path.basename(fnameRoot))
    model = reverted["model"]
    print('Specifying latitude / longitude domain of interest ...')
    datanameID = 'dailySD'  # Short ID name of output data
    latrange = (param.args.lat1, param.args.lat2)
    lonrange = (param.args.lon1, param.args.lon2)
    region = cdutil.region.domain(latitude=latrange, longitude=lonrange)
    if param.args.region_name == "":
        region_name = "{:g}_{:g}&{:g}_{:g}".format(*(latrange + lonrange))
    else:
        region_name = param.args.region_name
    print('Reading {} ...'.format(fnameRoot))
    try:
        f = cdms2.open(fnameRoot)
        x = f(datanameID, region)
        units = x.units
        print('  Shape =', x.shape)
        print('Finding RMS area-average ...')
        x = x * x
        x = cdutil.averager(x, axis='xy')
        x = numpy.ma.sqrt(x)
        print('For %8s in %s, average variance of daily values = (%5.2f %s)^2' % (model, monthname, x, units))
        f.close()
    except Exception as err:
        print("Failed for model %s with error %s" % (model, err))
        x = 1.e20
    return model, region, {region_name: x}


P.add_argument("-j", "--outnamejson",
               type=str,
               dest='outnamejson',
               default='pr_%(month)_%(firstyear)_%(lastyear)_std_of_dailymeans.json',
               help="Output name for jsons")

P.add_argument("--lat1", type=float, default=-50., help="First latitude")
P.add_argument("--lat2", type=float, default=50., help="Last latitude")
P.add_argument("--lon1", type=float, default=0., help="First longitude")
P.add_argument("--lon2", type=float, default=360., help="Last longitude")
P.add_argument("--region_name", type=str, default="TRMM",
               help="name for the region of interest")

P.add_argument("-t", "--filename_template",
               default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_std_of_dailymeans.nc")
P.add_argument("--model", default="*")

args = P.get_parameter()
month = args.month
monthname = monthname_d[month]
startyear = args.firstyear
finalyear = args.lastyear

template = populateStringConstructor(args.filename_template, args)
template.month = monthname

print("TEMPLATE NAME:", template())


print('Preparing to write output to JSON file ...')
if not os.path.exists(args.output_directory):
    os.makedirs(args.output_directory)
jsonFile = populateStringConstructor(args.outnamejson, args)
jsonFile.month = monthname

jsonname = os.path.join(os.path.abspath(args.output_directory), jsonFile())

if not os.path.exists(jsonname) or args.append is False:
    print('Initializing dictionary of statistical results ...')
    stats_dic = {}
    metrics_dictionary = collections.OrderedDict()
else:
    with open(jsonname) as f:
        metrics_dictionary = json.load(f)
        stats_dic = metrics_dictionary["RESULTS"]

OUT = pcmdi_metrics.io.base.Base(
    os.path.abspath(
        args.output_directory),
    jsonFile())
disclaimer = open(
    os.path.join(
        sys.prefix,
        "share",
        "pmp",
        "disclaimer.txt")).read()
metrics_dictionary["DISCLAIMER"] = disclaimer
metrics_dictionary["REFERENCE"] = "The statistics in this file are based on Trenberth, Zhang & Gehne, J Hydromet. 2017"


files = glob.glob(os.path.join(args.modroot, template()))
print(files)
params = [INPUT(args, name, template) for name in files]
print("PARAMS:", params)

results = cdp.cdp_run.multiprocess(
    compute, params, num_workers=args.num_workers)

for r in results:
    m, region, res = r
    if r[0] not in stats_dic:
        stats_dic[m] = res
    else:
        stats_dic[m].update(res)

print('Writing output to JSON file ...', stats_dic)
metrics_dictionary["RESULTS"] = stats_dic
rgmsk = metrics_dictionary.get("RegionalMasking", {})
print("REG MASK:", rgmsk)
nm = list(res.keys())[0]
region.id = nm
rgmsk[nm] = {"id": nm, "domain": region}
metrics_dictionary["RegionalMasking"] = rgmsk
OUT.write(
    metrics_dictionary,
    json_structure=["model", "domain"],
    indent=4,
    separators=(
        ',',
        ': '))
print('done')
