import argparse
import os
import sys
import glob
import tempfile
import subprocess
import shlex
import cdms2

parser = argparse.ArgumentParser(
    description='Generates Climatologies from files')

p = parser.add_argument_group('processing')
p.add_argument("-v", "--vars",
               nargs="*",
               dest="vars",
               default=None,
               required = True,
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
p.add_argument("files",
               help="Input file",
               nargs="*")
p.add_argument("-b","--bounds",
        action = "store_true",
        dest = "bounds",
        default=False,
        help = "reset bounds to monthly")
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

if len(A.files) == 0:
    raise RuntimeError("You need to provide at least one file for input")

if len(A.files) == 1:
    A.files = glob.glob(A.files[0])

for f in A.files:
    if not os.path.exists(f):
        raise RuntimeError("file '%s' doe not exits" % f)
if len(A.files)>1:
    print "Multiple files sent, running cdscan on them"
    xml = tempfile.mkstemp(suffix=".xml")[1]
    P = subprocess.Popen(shlex.split("cdscan -x %s %s" % (xml, " ".join(A.files))))
    P.wait()
    A.files = xml
else:
    A.files = A.files[0]

filein = cdms2.open(A.files)
fvars = filein.variables.keys()
for v in A.vars:
    if v not in fvars:
        raise RuntimeError("Variable '%s' is not contained in input file(s)" % v)
#clean up
os.remove(xml)
