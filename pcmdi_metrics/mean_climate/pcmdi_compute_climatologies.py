#!/usr/bin/env python

import datetime

from pcmdi_metrics.mean_climate.lib import calculate_climatology
from pcmdi_metrics.mean_climate.lib.pmp_parser import PMPMetricsParser
from pcmdi_metrics.io import StringConstructor

ver = datetime.datetime.now().strftime("v%Y%m%d")

P = PMPMetricsParser()

P.add_argument(
    "--vars", dest="vars", help="List of variables", nargs="+", required=False
)
P.add_argument("--infile", dest="infile", help="Defines infile", required=False)
P.add_argument(
    "--outfile", dest="outfile", help="Defines output path and filename", required=False
)
P.add_argument("--outpath", dest="outpath", help="Defines outpath only", required=False)
P.add_argument(
    "--outfilename",
    dest="outfilename",
    help="Defines out filename only",
    required=False,
)
P.add_argument(
    "--start", dest="start", help="Defines start year and month", required=False
)
P.add_argument("--end", dest="end", help="Defines end year and month", required=False)

P.add_argument(
    "--periodinname",
    dest="periodinname",
    help="Include clim period in name (default yes) or not",
    required=False,
)

P.add_argument(
    "--climlist",
    dest="climlist",
    help="Defines list of clim seasons to output (default='all')",
    required=False,
)

args = P.get_parameter()

infile_template = args.infile
outfile_template = args.outfile
outpath_template = args.outpath
outfilename_template = args.outfilename
varlist = args.vars
start = args.start
end = args.end
periodinname = args.periodinname
climlist = args.climlist

print("start and end are ", start, " ", end)
print("variable list: ", varlist)
print("ver:", ver)

InFile = StringConstructor(infile_template)
OutFile = StringConstructor(outfile_template)
OutFileName = StringConstructor(outfilename_template)
OutPath = StringConstructor(outpath_template)

for var in varlist:
    # Build filenames
    InFile.variable = var
    OutFile.variable = var
    OutFileName.variable = var
    OutPath.variable = var
    infile = InFile()
    outfile = OutFile()
    outfilename = OutFileName()
    outpath = OutPath()

    print("var:", var)
    print("infile:", infile)
    print("outfile:", outfile)
    print("outfilename:", outfilename)
    print("outpath:", outpath)

    # calculate climatologies for this variable
    calculate_climatology(
        var,
        infile,
        outfile,
        outpath,
        outfilename,
        start,
        end,
        ver,
        periodinname,
        climlist,
    )
