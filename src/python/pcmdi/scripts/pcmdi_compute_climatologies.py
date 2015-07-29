#!/usr/bin/env python
import argparse
import os
import sys
import glob
import tempfile
import subprocess
import shlex
import cdms2
import cdutil

parser = argparse.ArgumentParser(
    description='Generates Climatologies from files')

p = parser.add_argument_group('processing')
p.add_argument("-v", "--vars",
               nargs="*",
               dest="vars",
               default=None,
               required=True,
               help="variables to use for climatology")
p.add_argument("-t", "--threshold",
               dest='threshold',
               default=.5,
               type=float,
               help="Threshold bellow which a season is considered as " +
               "not having enough data to be computed")
p.add_argument("-S", "--season",
               dest="seasons",
               default=["all"],
               nargs="*",
               choices=["djf", "DJF", "ann", "ANN", "all", "ALL",
                        "mam", "MAM", "jja", "JJA", "son", "SON", "year",
                        "YEAR"],
               help="Which season you wish to produce"
               )
p.add_argument("-s", "--start",
               dest="start",
               default=None,
               help="Start for climatology: date, value or index " +
               "as determined by -I arg")
p.add_argument("-e", "--end",
               dest="end",
               default=None,
               help="End for climatology: date, value or index " +
               "as determined by -I arg")
p.add_argument("-I", "--indexation-type",
               dest="index",
               default="date",
               choices=["date", "value", "index"],
               help="indexation type")
p.add_argument("-f", "--files",
               dest="files",
               help="Input file",
               nargs="+")
p.add_argument("-b", "--bounds",
               action="store_true",
               dest="bounds",
               default=False,
               help="reset bounds to monthly")
c = parser.add_argument_group("CMOR options")
c.add_argument("-d", "--drs",
               action="store_true",
               dest="drs",
               default=False,
               help="Use drs for output path"
               )
c.add_argument("-T", "--tables",
               dest="tables",
               help="path where CMOR tables reside")
c.add_argument("-V", "--cf-var",
               dest="cf_var",
               nargs="*",
               help="variable(s) name in CMOR tables, in same order " +
               "as -v argument")

A = parser.parse_args(sys.argv[1:])
print A
if len(A.files) == 0:
    raise RuntimeError("You need to provide at least one file for input")

if len(A.files) == 1:
    A.files = glob.glob(A.files[0])

for f in A.files:
    if not os.path.exists(f):
        raise RuntimeError("file '%s' doe not exits" % f)
if len(A.files) > 1:
    print "Multiple files sent, running cdscan on them"
    xml = tempfile.mkstemp(suffix=".xml")[1]
    P = subprocess.Popen(
        shlex.split(
            "cdscan -x %s %s" %
            (xml,
             " ".join(
                 A.files))))
    P.wait()
    A.files = xml
else:
    A.files = A.files[0]
    xml = None


# season dictionary
season_function = {
    "djf": cdutil.times.DJF,
    "mam": cdutil.times.MAM,
    "jja": cdutil.times.JJA,
    "son": cdutil.times.SON,
    "ann": cdutil.times.ANNUALCYCLE,
    "year": cdutil.times.YEAR,
}
filein = cdms2.open(A.files)
fvars = filein.variables.keys()
for v in A.vars:
    if v not in fvars:
        raise RuntimeError(
            "Variable '%s' is not contained in input file(s)" %
            v)
    V = filein[v]
    tim = V.getTime().clone()
    # "monthly"
    if A.bounds:
        cdutil.times.setTimeBoundsMonthly(tim)
    # Now make sure we can get the requested period
    if A.start is None:
        i0 = 0
    else:  # Ok user specified a start time
        if A.index == "index":  # index-based slicing
            if int(A.start) >= len(tim):
                raise RuntimeError(
                    "For variable %s you requested start time to be at index: %i but the file only has %i time steps" %
                    (v, int(
                        A.start), len(tim)))
            i0 = int(A.start)
        elif A.index == "value":  # actual value used for slicing
            v0 = float(A.start)
            try:
                i0, tmp = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find value %s for start time for variable %s" %
                    (A.start, v))
        elif A.index == "date":
            v0 = A.start
            try:
                i0, tmp = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find start time %s for variable: %s" %
                    (A.start, v))

    if A.end is None:
        i1 = None
    else:  # Ok user specified a end time
        if A.index == "index":  # index-based slicing
            if int(A.end) >= len(tim):
                raise RuntimeError(
                    "For variable %s you requested end time to be at index: %i but the file only has %i time steps" %
                    (v, int(
                        A.end), len(tim)))
            i1 = int(A.end)
        elif A.index == "value":  # actual value used for slicing
            v0 = float(A.end)
            try:
                tmp, i1 = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find value %s for end time for variable %s" %
                    (A.end, v))
        elif A.index == "date":
            v0 = A.end
            try:
                tmp, i1 = tim.mapInterval((v0, v0, 'cob'))
            except:
                raise RuntimeError(
                    "Could not find end time %s for variable: %s" %
                    (A.end, v))
    # Read in data
    data = V(time=slice(i0, i1))
    print "DATA:", data.shape
    if A.bounds:
        cdutil.times.setTimeBoundsMonthly(data)
    # Now we can actually read and compute the climo
    seasons = [s.lower() for s in A.seasons]
    if "all" in seasons:
        seasons = ["djf", "mam", "jja", "son", "year", "ann"]

    for season in seasons:
        s = season_function[season].climatology(data)
        print season, s.shape

# clean up
if xml is not None:
    os.remove(xml)
