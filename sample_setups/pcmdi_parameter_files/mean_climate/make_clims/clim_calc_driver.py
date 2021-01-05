import glob, os,sys
import cdms2, MV2
import cdutil
import argparse
import datetime
import pcmdi_metrics
from clim_module import clim_calc
from pcmdi_metrics.pcmdi.pmp_parser import PMPParser

ver = datetime.datetime.now().strftime('v%Y%m%d')

cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

P = pcmdi_metrics.driver.pmp_parser.PMPMetricsParser()

P.add_argument(
        '--var',
        dest='var',
        help='Defines var',
        required=False)
P.add_argument(
        '--infile',
        dest='infile',
        help='Defines infile', 
        required=False)
P.add_argument(
        '--outfile',
        dest='outfile',
        help='Defines output path and filename',
        required=False)
P.add_argument(
        '--outpath',
        dest='outpath',
        help='Defines outpath only',
        required=False)
P.add_argument(
        '--outfilename',
        dest='outfilename',
        help='Defines out filename only',
        required=False)
P.add_argument(
        '--start',
        dest='start',
        help='Defines start year and month',
        required=False)
P.add_argument(
        '--end',
        dest='end',
        help='Defines end year and month',
        required=False)

args = P.get_parameter()

infile = args.infile
outfile = args.outfile
outpath = args.outpath
outfilename = args.outfilename
var = args.var
start = args.start
end = args.end

print('end is ', end)

print('var is ', var)
clim_calc(var,infile,outfile,outpath,outfilename,start,end)
#'''
#'''
