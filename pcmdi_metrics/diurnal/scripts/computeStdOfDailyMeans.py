#!/usr/bin/env python

# From a high frequency (hourly, 3-hourly, ...) time series, compute daily means for one month over one or more years at
# each gridpoint, then their standard deviation. This version processes
# CMIP5 historical precipitation for years 1999-2005.

#               Charles Doutriaux                                       September 2017
#               Curt Covey                                       	July 2017
# (from ./old_computeDailyMeans.py)

# This version has the PMP Parser "wrapped" around it, so it can be executed with input parameters in the command line
# ---> computeStdDailyMeansWrapped.py -i data -m7 --realization="r1i1p1" -t "sample_data_%(variable)_%(model).nc"

from __future__ import print_function
import cdms2
import cdtime
import genutil
import numpy.ma
import os
import glob
import cdp
import multiprocessing as mp

from pcmdi_metrics.diurnal.common import monthname_d, P, populateStringConstructor, INPUT


def main():
    def compute(params):
        fileName = params.fileName
        startyear = params.args.firstyear
        finalyear = params.args.lastyear
        month = params.args.month
        monthname = params.monthname
        varbname = params.varname
        template = populateStringConstructor(args.filename_template, args)
        template.variable = varbname

        dataname = params.args.model
        if dataname is None or dataname.find("*") != -1:
            # model not passed or passed as *
            reverted = template.reverse(os.path.basename(fileName))
            dataname = reverted["model"]
        print('Data source:', dataname)
        print('Opening %s ...' % fileName)
        if dataname not in args.skip:
            try:
                print('Data source:', dataname)
                print('Opening %s ...' % fileName)
                f = cdms2.open(fileName)
                iYear = 0
                dmean = None
                for year in range(startyear, finalyear + 1):
                    print('Year %s:' % year)
                    startTime = cdtime.comptime(year, month)
                    # Last possible second to get all tpoints
                    finishtime = startTime.add(
                        1, cdtime.Month).add(-1, cdtime.Minute)
                    print('Reading %s from %s for time interval %s to %s ...' % (varbname, fileName, startTime, finishtime))
                    # Transient variable stores data for current year's month.
                    tvarb = f(varbname, time=(startTime, finishtime, "ccn"))
                    # *HARD-CODES conversion from kg/m2/sec to mm/day.
                    tvarb *= 86400
                    # The following tasks need to be done only once, extracting
                    # metadata from first-year file:
                    tc = tvarb.getTime().asComponentTime()
                    current = tc[0]
                    while current.month == month:
                        end = cdtime.comptime(
                            current.year,
                            current.month,
                            current.day).add(
                            1,
                            cdtime.Day)
                        sub = tvarb(time=(current, end, "con"))
                        # Assumes first dimension of input ("axis#0") is time
                        tmp = numpy.ma.average(sub, axis=0)
                        sh = list(tmp.shape)
                        sh.insert(0, 1)
                        if dmean is None:
                            dmean = tmp.reshape(sh)
                        else:
                            dmean = numpy.ma.concatenate(
                                (dmean, tmp.reshape(sh)), axis=0)
                        current = end
                    iYear += 1
                f.close()
                stdvalues = cdms2.MV2.array(genutil.statistics.std(dmean))
                stdvalues.setAxis(0, tvarb.getLatitude())
                stdvalues.setAxis(1, tvarb.getLongitude())
                stdvalues.id = 'dailySD'
                # Standard deviation has same units as mean.
                stdvalues.units = "mm/d"
                stdoutfile = ('%s_%s_%s_%s-%s_std_of_dailymeans.nc') % (varbname, dataname,
                                                                        monthname, str(startyear), str(finalyear))
            except Exception as err:
                print("Failed for model: %s with error: %s" % (dataname, err))
        if not os.path.exists(args.results_dir):
            os.makedirs(args.results_dir)
        g = cdms2.open(os.path.join(args.results_dir, stdoutfile), 'w')
        g.write(stdvalues)
        g.close()

    args = P.get_parameter()
    month = args.month
    startyear = args.firstyear
    finalyear = args.lastyear
    directory = args.modpath      # Input  directory for model data
    # These models have been processed already (or tried and found wanting,
    # e.g. problematic time coordinates):
    skipMe = args.skip
    print("SKIPPING:", skipMe)

    # Choose only one ensemble member per model, with the following ensemble-member code (for definitions, see
    # http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf):

    # NOTE--These models do not supply 3hr data from the 'r1i1p1' ensemble member,
    #       but do supply it from other ensemble members:
    #       bcc-csm1-1 (3hr data is from r2i1p1)
    #       CCSM4      (3hr data is from r6i1p1)
    #       GFDL-CM3   (3hr data is from r2i1p1, r3i1p1, r4i1p1, r5i1p1)
    #       GISS-E2-H  (3hr data is from r6i1p1, r6i1p3)
    #       GISS-E2-R  (3hr data is from r6i1p2)

    varbname = "pr"

    #           Note that CMIP5 specifications designate (01:30, 04:30, 07:30, ..., 22:30) GMT for 3hr flux fields, but
    # *WARNING* some GMT timepoints are actually (0, 3, 6,..., 21) in submitted CMIP5 data, despite character strings in
    #           file names (and time axis metadata) to the contrary. See CMIP5 documentation and errata! Overrides to
    #           correct these problems are given below:
    # Include 00Z as a possible starting time, to accomodate (0, 3, 6,...,
    # 21)GMT in the input data.
    # startime = -1.5     # Subtract 1.5h from (0, 3, 6,..., 21)GMT input
    # data. This is needed for BNU-ESM, CCSM4 and CNRM-CM5.
    # Subtract 1.5h from (0, 3, 6,..., 21)GMT input data. This is needed for
    # CMCC-CM.

    # -------------------------------------

    monthname = monthname_d[month]
    nYears = finalyear - startyear + 1
    # Character strings for starting and ending day/GMT (*HARD-CODES
    # particular GMT timepoints*):
    # *WARNING* GMT timepoints are actually (0, 3, 6,..., 21) in the original TRMM/Obs4MIPs data, despite character
    # strings in file names (and time axis metadata). See CMIP5 documentation and
    # errata!

    template = populateStringConstructor(args.filename_template, args)
    template.variable = varbname

    fileList = glob.glob(os.path.join(directory, template()))
    print("FILES:", fileList)

    params = [INPUT(args, name, template) for name in fileList]
    print("PARAMS:", params)

    cdp.cdp_run.multiprocess(compute, params, num_workers=args.num_workers)


# Good practice to place contents of script under this check
if __name__ == '__main__':
    # Related to script being installed as executable
    mp.freeze_support()

    main()
