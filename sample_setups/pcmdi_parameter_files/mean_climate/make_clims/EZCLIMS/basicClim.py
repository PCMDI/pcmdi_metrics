#!/usr/bin/env python
from pcmdi_metrics.pcmdi.pmp_parser import *
import cdms2
import cdutil
import cdtime
import ast

# P Gleckler
# Prototyping a simple version of pcmdi_compute_climatologies.py
# Omits using CMOR and formalizing time coordinate with bounds
# 20191211


###
# INPUT PARAMETERS OFTEN STORED IN SEPRATE FILE FOR PMP METRICS

parser = PMPParser() # Includes all default options

parser.add_argument(
    '--model',
    type=ast.literal_eval, # python list 
    dest='model',
    help='model or observational data',
    default=None,
    required=False)

parser.add_argument(
    '--filename_template',
    dest='filename_template',
    help='description',
    required=False)

parser.add_argument(
    '--output_filename_template',
    dest='output_filename_template',
    help='description',
    required=False)

parser.use('--results_dir')
parser.use('--modpath')

parser.add_argument(
    '--start', 
    dest='start',
    help='description',
    required=False)

parser.add_argument(
    '--end', 
    dest='end',
    help='description',
    required=False)

parser.add_argument(
    '--variable',
    type=ast.literal_eval, # python list
    dest='variable',
    help='description',
    required=False)

parameter = parser.get_parameter()

models = parameter.model
modpath = parameter.modpath
filename_template = parameter.filename_template
start = parameter.start
end = parameter.end
variables = parameter.variable
results_dir = parameter.results_dir
output_filename_template = parameter.output_filename_template

start_mo = int(start.split('-')[1])
start_yr = int(start.split('-')[0])
end_mo = int(end.split('-')[1])
end_yr = int(end.split('-')[0])


# COMPUTE AND SAVE ANNUAL CYCLE CLIMATOLOGY
for mod in models:
 for var in variables:
  pathin = modpath + filename_template  
  pathin = pathin.replace('VARIABLE',var)
  pathin = pathin.replace('MODEL',mod)
  print(pathin)

  f = cdms2.open(pathin)
  d = f(var,time = (cdtime.comptime(start_yr,start_mo),cdtime.comptime(end_yr,end_mo)))
  t = d.getTime()
  c = t.asComponentTime()
  bm = c[0].year
  by = c[0].month
  ey = c[len(c)-1].year
  em = c[len(c)-1].month
  print(mod,' ', by,' ',bm,' ',ey,' ',em)

  d_ac = cdutil.ANNUALCYCLE.climatology(d)
# d_djf = cdutil.DJF.climatology(d)

  d_ac.id = var
  print(d.shape,d_ac.shape)

  pathout = results_dir+output_filename_template 
  pathout = pathout.replace('VARIABLE',var)
  pathout = pathout.replace('MODEL',mod)
  g = cdms2.open(pathout,'w+')
  g.write(d_ac)
  g.close()


