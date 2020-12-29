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
        help='Defines outfile',
        required=False)

args = P.get_parameter()

infile = args.infile
outfile = args.outfile
var = args.var

print('var is ', var)
clim_calc(var,infile,outfile)
#'''
#'''
