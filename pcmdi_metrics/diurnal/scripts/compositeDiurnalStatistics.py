#!/usr/bin/env python

# /export/covey1/CMIP5/Precipitation/DiurnalCycle/HistoricalRuns/compositeDiurnalStatisticsWrapped.py

# This modifiction of ./compositeDiurnalStatistics.py will have the PMP Parser "wrapped" around it,
# so that it can be executed with input parameters in the Unix command line, for example:
# ---> python compositeDiurnalStatisticsWrapped.py -t "sample_data_%(variable)_%(model).nc" -m 7

# These are the models with CMIP5 historical run output at 3h frequency, which this script is designed to process:
# 'ACCESS1-0', 'ACCESS1-3', 'bcc-csm1-1', 'bcc-csm1-1-m', 'BNU-ESM',
# 'CCSM4',  'CMCC-CM',      'CNRM-CM5',     'EC-EARTH',
# 'FGOALS-g2', 'GFDL-CM3',  'GFDL-ESM2M', 'GISS-E2-R',
# 'GISS-E2-H', 'inmcm4', 'IPSL-CM5A-LR', 'IPSL-CM5A-MR',
# 'MIROC4h',   'MIROC5',    'MIROC-ESM',  'MIROC-ESM-CHEM'

from __future__ import division, print_function

import glob
import multiprocessing as mp
import os

import cdms2
import cdp
import cdtime
import genutil
import MV2

from pcmdi_metrics.diurnal.common import (
    INPUT,
    P,
    monthname_d,
    populateStringConstructor,
)


def main():
    def compute(params):
        fileName = params.fileName
        month = params.args.month
        monthname = params.monthname
        varbname = params.varname
        template = populateStringConstructor(args.filename_template, args)
        template.variable = varbname
        # Units on output (*may be converted below from the units of input*)
        outunits = "mm/d"
        startime = 1.5  # GMT value for starting time-of-day

        dataname = params.args.model
        if dataname is None or dataname.find("*") != -1:
            # model not passed or passed as *
            reverted = template.reverse(os.path.basename(fileName))
            print("REVERYING", reverted, dataname)
            dataname = reverted["model"]
        if dataname not in args.skip:
            try:
                print("Data source:", dataname)
                print("Opening %s ..." % fileName)
                f = cdms2.open(fileName)

                # Composite-mean and composite-s.d diurnal cycle for month and year(s):
                iYear = 0
                for year in range(args.firstyear, args.lastyear + 1):
                    print("Year %s:" % year)
                    startTime = cdtime.comptime(year, month)
                    # Last possible second to get all tpoints
                    finishtime = startTime.add(1, cdtime.Month).add(-1, cdtime.Minute)
                    print(
                        "Reading %s from %s for time interval %s to %s ..."
                        % (varbname, fileName, startTime, finishtime)
                    )
                    # Transient variable stores data for current year's month.
                    tvarb = f(varbname, time=(startTime, finishtime))
                    # *HARD-CODES conversion from kg/m2/sec to mm/day.
                    tvarb *= 86400
                    print("Shape:", tvarb.shape)
                    # The following tasks need to be done only once, extracting
                    # metadata from first-year file:
                    if year == args.firstyear:
                        tc = tvarb.getTime().asComponentTime()
                        print("DATA FROM:", tc[0], "to", tc[-1])
                        day1 = cdtime.comptime(tc[0].year, tc[0].month)
                        day1 = tc[0]
                        firstday = tvarb(time=(day1, day1.add(1.0, cdtime.Day), "con"))
                        dimensions = firstday.shape
                        print("  Shape = ", dimensions)
                        # Number of time points in the selected month for one year
                        N = dimensions[0]
                        nlats = dimensions[1]
                        nlons = dimensions[2]
                        deltaH = 24.0 / N
                        dayspermo = tvarb.shape[0] // N
                        print(
                            "  %d timepoints per day, %d hr intervals between timepoints"
                            % (N, deltaH)
                        )
                        comptime = firstday.getTime()
                        modellons = tvarb.getLongitude()
                        modellats = tvarb.getLatitude()
                        # Longitude values are needed later to compute Local Solar
                        # Times.
                        lons = modellons[:]
                        print("  Creating temporary storage and output fields ...")
                        # Sorts tvarb into separate GMTs for one year
                        tvslice = MV2.zeros((N, dayspermo, nlats, nlons))
                        # Concatenates tvslice over all years
                        concatenation = MV2.zeros((N, dayspermo * nYears, nlats, nlons))
                        LSTs = MV2.zeros((N, nlats, nlons))
                        for iGMT in range(N):
                            hour = iGMT * deltaH + startime
                            print(
                                "  Computing Local Standard Times for GMT %5.2f ..."
                                % hour
                            )
                            for j in range(nlats):
                                for k in range(nlons):
                                    LSTs[iGMT, j, k] = (hour + lons[k] / 15) % 24
                    for iGMT in range(N):
                        hour = iGMT * deltaH + startime
                        print("  Choosing timepoints with GMT %5.2f ..." % hour)
                        print("days per mo :", dayspermo)
                        # Transient-variable slice: every Nth tpoint gets all of
                        # the current GMT's tpoints for current year:
                        tvslice[iGMT] = tvarb[iGMT::N]
                        concatenation[
                            iGMT, iYear * dayspermo : (iYear + 1) * dayspermo
                        ] = tvslice[iGMT]
                    iYear += 1
                f.close()

                # For each GMT, take mean and standard deviation over all years for
                # the chosen month:
                avgvalues = MV2.zeros((N, nlats, nlons))
                stdvalues = MV2.zeros((N, nlats, nlons))
                for iGMT in range(N):
                    hour = iGMT * deltaH + startime
                    print(
                        "Computing mean and standard deviation over all GMT %5.2f timepoints ..."
                        % hour
                    )
                    # Assumes first dimension of input ("axis#0") is time
                    avgvalues[iGMT] = MV2.average(concatenation[iGMT], axis=0)
                    stdvalues[iGMT] = genutil.statistics.std(concatenation[iGMT])
                avgvalues.id = "diurnalmean"
                stdvalues.id = "diurnalstd"
                LSTs.id = "LST"
                avgvalues.units = outunits
                # Standard deviation has same units as mean (not so for
                # higher-moment stats).
                stdvalues.units = outunits
                LSTs.units = "hr"
                LSTs.longname = "Local Solar Time"
                avgvalues.setAxis(0, comptime)
                avgvalues.setAxis(1, modellats)
                avgvalues.setAxis(2, modellons)
                stdvalues.setAxis(0, comptime)
                stdvalues.setAxis(1, modellats)
                stdvalues.setAxis(2, modellons)
                LSTs.setAxis(0, comptime)
                LSTs.setAxis(1, modellats)
                LSTs.setAxis(2, modellons)
                avgoutfile = ("%s_%s_%s_%s-%s_diurnal_avg.nc") % (
                    varbname,
                    dataname,
                    monthname,
                    str(args.firstyear),
                    str(args.lastyear),
                )
                stdoutfile = ("%s_%s_%s_%s-%s_diurnal_std.nc") % (
                    varbname,
                    dataname,
                    monthname,
                    str(args.firstyear),
                    str(args.lastyear),
                )
                LSToutfile = "%s_%s_LocalSolarTimes.nc" % (varbname, dataname)
                if not os.path.exists(args.results_dir):
                    os.makedirs(args.results_dir)
                f = cdms2.open(os.path.join(args.results_dir, avgoutfile), "w")
                g = cdms2.open(os.path.join(args.results_dir, stdoutfile), "w")
                h = cdms2.open(os.path.join(args.results_dir, LSToutfile), "w")
                f.write(avgvalues)
                g.write(stdvalues)
                h.write(LSTs)
                f.close()
                g.close()
                h.close()
            except Exception as err:
                print("Failed for model %s with erro: %s" % (dataname, err))

    print("done")
    args = P.get_parameter()

    month = args.month  # noqa: F841
    monthname = monthname_d[args.month]  # noqa: F841

    # -------------------------------------HARD-CODED INPUT (add to command line later?):

    # These models have been processed already (or tried and found wanting,
    # e.g. problematic time coordinates):
    skipMe = args.skip  # noqa: F841

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
    # startGMT =  '0:0:0.0' # Include 00Z as a possible starting time, to accomodate (0, 3, 6,..., 21)GMT in the input
    # data.
    # startime = -1.5 # Subtract 1.5h from (0, 3, 6,..., 21)GMT input data. This is needed for BNU-ESM, CCSM4 and
    # CNRM-CM5.
    # startime = -3.0 # Subtract 1.5h from (0, 3, 6,..., 21)GMT input
    # data. This is needed for CMCC-CM.

    # -------------------------------------

    nYears = args.lastyear - args.firstyear + 1

    template = populateStringConstructor(args.filename_template, args)
    template.variable = varbname

    print("TEMPLATE:", template())
    fileList = glob.glob(os.path.join(args.modpath, template()))
    print("FILES:", fileList)
    params = [INPUT(args, name, template) for name in fileList]
    print("PARAMS:", params)
    cdp.cdp_run.multiprocess(compute, params, num_workers=args.num_workers)


# Good practice to place contents of script under this check
if __name__ == "__main__":
    # Related to script being installed as executable
    mp.freeze_support()

    main()
