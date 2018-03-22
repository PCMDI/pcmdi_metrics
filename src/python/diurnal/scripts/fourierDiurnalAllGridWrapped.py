#!/usr/bin/env python

# This modifiction of ./fourierDiurnalAllGrid.py has the PMP Parser "wrapped" around it, so it's executed
# with input parameters in the Unix command line. For example:

# ---> python fourierDiurnalAllGridWrapped.py -m7

# Charles Doutriaux                     September 2017
# Curt Covey                                        January 2017

# -------------------------------------------------------------------------

from __future__ import print_function
import cdms2
import MV2
from pcmdi_metrics.diurnal.fourierFFT import fastAllGridFT
import glob
import os

from pcmdi_metrics.diurnal.common import monthname_d, P, populateStringConstructor

P.add_argument("-t", "--filename_template",
               default="pr_%(model)_%(month)_%(firstyear)-%(lastyear)_diurnal_avg.nc",
               help="template for file names containing diurnal average")
P.add_argument("--model", default="*")
P.add_argument("--filename_template_LST",
               default="pr_%(model)_LocalSolarTimes.nc",
               help="template for file names point to Local Solar Time Files")

args = P.get_parameter()
month = args.month
monthname = monthname_d[month]
startyear = args.firstyear
finalyear = args.lastyear
yearrange = "%s-%s" % (startyear, finalyear)

template = populateStringConstructor(args.filename_template, args)
template.month = monthname
template_LST = populateStringConstructor(args.filename_template_LST, args)
template_LST.month = monthname

<<<<<<< HEAD
LSTfiles = glob.glob(os.path.join(args.modpath, template_LST()))
print "LSTFILES:", LSTfiles
print "TMPL", template_LST()
=======
LSTfiles = glob.glob(os.path.join(args.modroot, template_LST()))
print("LSTFILES:", LSTfiles)
print("TMPL", template_LST())
>>>>>>> origin/master
for LSTfile in LSTfiles:
    print('Reading %s ...' % LSTfile, os.path.basename(LSTfile))
    reverted = template_LST.reverse(os.path.basename(LSTfile))
    model = reverted["model"]
    print('====================')
    print(model)
    print('====================')
    template.model = model
    avgfile = template()
    print('Reading time series of mean diurnal cycle ...')
    f = cdms2.open(LSTfile)
    g = cdms2.open(os.path.join(args.modpath, avgfile))
    LSTs = f('LST')
    avgs = g('diurnalmean')
    print('Input shapes: ', LSTs.shape, avgs.shape)

    print('Getting latitude and longitude coordinates.')
    # Any file with grid info will do, so use Local Standard Times file:
    modellats = LSTs.getLatitude()
    modellons = LSTs.getLongitude()

    f.close()
    g.close()

    print('Taking fast Fourier transform of the mean diurnal cycle ...')
    cycmean, maxvalue, tmax = fastAllGridFT(avgs, LSTs)
    print('  Output:')
    print('    cycmean', cycmean.shape)
    print('    maxvalue', maxvalue.shape)
    print('    tmax', tmax.shape)

    print('"Re-decorating" Fourier harmonics with grid info, etc., ...')
    cycmean = MV2.array(cycmean)
    maxvalue = MV2.array(maxvalue)
    tmax = MV2.array(tmax)

    cycmean.setAxis(0, modellats)
    cycmean.setAxis(1, modellons)
    cycmean.id = 'tmean'
    cycmean.units = 'mm / day'

    maxvalue.setAxis(1, modellats)
    maxvalue.setAxis(2, modellons)
    maxvalue.id = 'S'
    maxvalue.units = 'mm / day'

    tmax.setAxis(1, modellats)
    tmax.setAxis(2, modellons)
    tmax.id = 'tS'
    tmax.units = 'GMT'

    print('... and writing to netCDF.')
    f = cdms2.open(
        os.path.join(
            args.results_dir,
            'pr_' +
            model +
            '_' +
            monthname +
            '_' +
            yearrange +
            '_tmean.nc'),
        'w')
    g = cdms2.open(
        os.path.join(
            args.results_dir,
            'pr_' +
            model +
            '_' +
            monthname +
            '_' +
            yearrange +
            '_S.nc'),
        'w')
    h = cdms2.open(
        os.path.join(
            args.results_dir,
            'pr_' +
            model +
            '_' +
            monthname +
            '_' +
            yearrange +
            '_tS.nc'),
        'w')
    f.write(cycmean)
    g.write(maxvalue)
    h.write(tmax)
    f.close()
    g.close()
    h.close()
