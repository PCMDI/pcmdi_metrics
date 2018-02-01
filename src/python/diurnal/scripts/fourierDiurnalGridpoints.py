#!/usr/bin/env python

# For a few selected gridpoints, read previously computed composite-mean and standard deviation of the diurnal
# cycle, compute Fourier harmonics and write output in a form suitable for Mathematica. The Fourier output of
# this script should match the output fields of
# ./fourierDiurnalAllGrid*.py at the selected gridpoints

#       Curt Covey                                              June 2017

# (from ~/CMIP5/Tides/OtherFields/Models/CMCC-CM_etal/old_fourierDiurnalGridpoints.py)
# -------------------------------------------------------------------------
from __future__ import print_function
import cdms2
import MV2
import sys
import glob
import os

from pcmdi_metrics.diurnal.common import monthname_d, P, populateStringConstructor
from pcmdi_metrics.diurnal.fourierFFT import fastFT

P.add_argument("-t", "--filename_template",
               default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_avg.nc",
               help="template for file names containing diurnal average")
P.add_argument("--model", default="*")
P.add_argument("--filename_template_LST",
               default="pr_%(model)_LocalSolarTimes.nc",
               help="template for file names point to Local Solar Time Files")
P.add_argument("--filename_template_std",
               default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_std.nc",
               help="template for file names containing diurnal std")
P.add_argument(
    "-l",
    "--lats",
    nargs="*",
    default=[
        31.125,
        31.125,
        36.4,
        5.125,
        45.125,
        45.125],
    help="latitudes")
P.add_argument("-L", "--lons", nargs="*",
               default=[-83.125, 111.145, -97.5, 147.145, -169.145, -35.145], help="longitudes")
P.add_argument("-A", "--outnameasc",
               type=str,
               dest='outnameasc',
               default='pr_%(month)_%(firstyear)-%(lastyear)_fourierDiurnalGridPoints.asc',
               help="Output name for ascs")
args = P.parse_args(sys.argv[1:])
month = args.month
monthname = monthname_d[month]
startyear = args.firstyear
finalyear = args.lastyear
yearrange = "%s-%s" % (startyear, finalyear)

template = populateStringConstructor(args.filename_template, args)
template.month = monthname
template_std = populateStringConstructor(args.filename_template_std, args)
template_std.month = monthname
template_LST = populateStringConstructor(args.filename_template_LST, args)
template_LST.month = monthname

LSTfiles = glob.glob(os.path.join(args.modroot, template_LST()))
print("LSTFILES:", LSTfiles)
print("TMPL", template_LST())

ascFile = populateStringConstructor(args.outnameasc, args)
ascFile.month = monthname
ascname = os.path.join(os.path.abspath(args.output_directory), ascFile())

if not os.path.exists(os.path.dirname(ascname)):
    os.makedirs(os.path.dirname(ascname))
fasc = open(ascname, "w")


gridptlats = [float(x) for x in args.lats]
gridptlons = [float(x) for x in args.lons]
nGridPoints = len(gridptlats)
assert(len(gridptlons) == nGridPoints)

# gridptlats = [-29.125, -5.125,   45.125,  45.125]
# gridptlons = [-57.125, 75.125, -169.145, -35.145]
# Gridpoints for JULY    samples in Figure 4 of Covey et al., JClimate 29: 4461 (2016):
# nGridPoints = 6
# gridptlats = [ 31.125,  31.125,  36.4,   5.125,   45.125,  45.125]
# gridptlons = [-83.125, 111.145, -97.5, 147.145, -169.145, -35.145]

N = 8  # Number of timepoints in a 24-hour cycle
for LSTfile in LSTfiles:
    print('Reading %s ...' % LSTfile, os.path.basename(LSTfile), file=fasc)
    print('Reading %s ...' % LSTfile, os.path.basename(LSTfile), file=fasc)
    reverted = template_LST.reverse(os.path.basename(LSTfile))
    model = reverted["model"]
    print('====================', file=fasc)
    print(model, file=fasc)
    print('====================', file=fasc)
    template.model = model
    avgfile = template()
    template_std.model = model
    stdfile = template_std()
    print('Reading time series of mean diurnal cycle ...', file=fasc)
    f = cdms2.open(LSTfile)
    g = cdms2.open(os.path.join(args.modroot, avgfile))
    h = cdms2.open(os.path.join(args.modroot, stdfile))
    LSTs = f('LST')
    print('Input shapes: ', LSTs.shape, file=fasc)

    modellats = LSTs.getLatitude()
    modellons = LSTs.getLongitude()
    latbounds = modellats.getBounds()
    lonbounds = modellons.getBounds()

    # Gridpoints selected above may be offset slightly from points in full
    # grid ...
    closestlats = MV2.zeros(nGridPoints)
    closestlons = MV2.zeros(nGridPoints)
    pointLSTs = MV2.zeros((nGridPoints, N))
    avgvalues = MV2.zeros((nGridPoints, N))
    stdvalues = MV2.zeros((nGridPoints, N))
    # ... in which case, just pick the closest full-grid point:
    for i in range(nGridPoints):
        print('   (lat, lon) = (%8.3f, %8.3f)' %
              (gridptlats[i], gridptlons[i]), file=fasc)
        closestlats[i] = gridptlats[i]
        closestlons[i] = gridptlons[i] % 360
        print('   Closest (lat, lon) for gridpoint = (%8.3f, %8.3f)' %
              (closestlats[i], closestlons[i]), file=fasc)
        # Time series for selected grid point:
        avgvalues[i] = g(
            'diurnalmean', lat=(
                closestlats[i], closestlats[i], "cob"), lon=(
                closestlons[i], closestlons[i], "cob"), squeeze=1)
        stdvalues[i] = h(
            'diurnalstd', lat=(
                closestlats[i], closestlats[i], "cob"), lon=(
                closestlons[i], closestlons[i], "cob"), squeeze=1)
        pointLSTs[i] = f(
            'LST', lat=(
                closestlats[i], closestlats[i], "cob"), lon=(
                closestlons[i], closestlons[i], "cob"), squeeze=1)
        print(' ', file=fasc)
    f.close()
    g.close()
    h.close()
    # Print results for input to Mathematica.
    if monthname == 'Jan':
        # In printed output, numbers for January data follow 0-5 for July data,
        # hence begin with 6.
        deltaI = 6
    else:
        deltaI = 0
    prefix = args.modroot
    for i in range(nGridPoints):
        print(
            'For gridpoint %d at %5.1f deg latitude, %6.1f deg longitude ...' %
            (i, gridptlats[i], gridptlons[i]), file=fasc)
        print('   Local Solar Times are:', file=fasc)
        print((prefix + 'LST%d = {') % (i + deltaI), file=fasc)
        print(N * '%5.3f, ' % tuple(pointLSTs[i]), end="", file=fasc)
        print('};', file=fasc)
        print('   Mean values for each time-of-day are:', file=fasc)
        print((prefix + 'mean%d = {') % (i + deltaI), file=fasc)
        print(N * '%5.3f, ' % tuple(avgvalues[i]), end="", file=fasc)
        print('};', file=fasc)
        print('   Standard deviations for each time-of-day are:', file=fasc)
        print((prefix + 'std%d = {') % (i + deltaI), file=fasc)
        print(N * '%6.4f, ' % tuple(stdvalues[i]), end="", file=fasc)
        print('};', file=fasc)
        print(' ', file=fasc)

    # Take fast Fourier transform of the overall multi-year mean diurnal cycle.
    print('**************   ', avgvalues[0][0], file=fasc)
    cycmean, maxvalue, tmax = fastFT(avgvalues, pointLSTs)
    print('**************   ', avgvalues[0][0], file=fasc)
    # Print Fourier harmonics:
    for i in range(nGridPoints):
        print(
            'For gridpoint %d at %5.1f deg latitude, %6.1f deg longitude ...' %
            (i, gridptlats[i], gridptlons[i]), file=fasc)
        print('  Mean value over cycle = %6.2f' % cycmean[i], file=fasc)
        print('  Diurnal     maximum   = %6.2f at %6.2f hr Local Solar Time.' %
              (maxvalue[i, 0], tmax[i, 0] % 24), file=fasc)
        print('  Semidiurnal maximum   = %6.2f at %6.2f hr Local Solar Time.' %
              (maxvalue[i, 1], tmax[i, 1] % 24), file=fasc)
        print('  Terdiurnal  maximum   = %6.2f at %6.2f hr Local Solar Time.' %
              (maxvalue[i, 2], tmax[i, 2] % 24), file=fasc)

print("Results sent to:", ascname)
