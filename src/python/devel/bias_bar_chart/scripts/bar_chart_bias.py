#!/usr/bin/env python

import numpy as NP
import matplotlib.pyplot as PLT
import json
import sys, os
import getopt
import pcmdi_metrics
from pcmdi_metrics.taylor_diagram_mpl import TaylorDiagram
from pcmdi_metrics.taylor_diagram_mpl import BarChart

test = True

fjson = open(
    os.path.join(
        pcmdi_metrics.__path__[0],
        "..",
        "..",
        "..",
        "..",
        "share",
        "CMIP_metrics_results",
        "CMIP5",
        "amip",
        "rlut_2.5x2.5_esmf_linear_metrics.json"))
        #../../../../share/CMIP_metrics_results//CMIP5/amip
obs_dic = json.loads(fjson.read())
fjson.close()

print 'fjson is ', fjson

args=sys.argv[1:]
letters='j:v:s:e:d:o:'
keywords=['json=','var=','season=','exp=','domain=','plotpath=']
json_path = 'default'
season ='default'
domain ='NHEX'
var = 'default'
pathout = './'
opts,pargs=getopt.getopt(args,letters,keywords)
for o,p in opts:
    if o in ['-j','--json']:
        json_path=p
    if o in ['-v','--var']:
        var = p
    if o in ['-s','--season']: # djf / mam / jja / son / ann
        season=p
    if o in ['-o','--plotpath']:
        pathout=p
    if o in ['-e','--exp']:
        exp=p
    if o in ['-d','--domain']:
        dom=p

print json_path,' ',season,' ', pathout,' ', exp,' ', var , ' ', dom
print 'after args'

fjson = open(
    os.path.join(
        pcmdi_metrics.__path__[0],
        "..",
        "..",
        "..",
        "..",
        "share",
        "CMIP_metrics_results",
        "CMIP5",
        "amip",
        var+"_2.5x2.5_esmf_linear_metrics.json"))

dd = json.loads(fjson.read())
fjson.close()

if test:
    ### TEMPORARY UNTIL JSON FILES ARE UPDATED TO INCLUDED STD
    #pi = '/work/gleckler1/processed_data/metrics_package/metrics_results/cmip5clims_metrics_package-amip/v1.1/pr_2.5x2.5_esmf_linear_metrics.json'
    pi = '/Users/lee1043/Documents/Research/PMP/pcmdi_metrics/data/CMIP_metrics_results/CMIP5/amip/pr_2.5x2.5_esmf_linear_metrics.json'
    dd = json.load(open(pi,'rb'))
    var = 'pr'

if var == 'pr':
    unit_adj = 28.
else:
    unit_adj = 1.

mods = dd.keys()

for mod in mods:
   if mod in ['METRICS','GridInfo','RegionalMasking','References','DISCLAIMER', 'metrics_git_sha1','uvcdat_version']:
    try:
     mods.remove(mod)
    except:
     pass

seasons = [season]
if season == 'all':
  seasons = ['ann', 'djf', 'mam', 'jja', 'son']
  rects = {'ann':511, 'djf':512, 'mam':513, 'jja':514, 'son':515} # subplot location
  fig = PLT.figure(figsize=(10,16)) # optimized figure size for five subplots
  fig_filename = var + '_' + exp + '_bias_5panel_' + season + '_' + dom
else:
  rects = {}
  rects[season] = 111 # subplot location
  fig = PLT.figure(figsize=(10,6)) # optimized figure size for one subplot
  fig_filename = var + '_' + exp + '_bias_1panel_' + season + '_' + dom

fig.suptitle(var.title()+', '+(exp+', '+dom).upper(), size='x-large') # Giving title for the entire canvas

for season in seasons:
    all_mods = []
    for mod in mods:
        bias = float(dd[mod]["defaultReference"]['r1i1p1']['global']['bias_xy_'+season+'_'+dom])*unit_adj
        all_mods.append(bias)
    dia = BarChart(mods,all_mods,fig=fig, rect=rects[season])
    dia._ax.set_title(season.upper()) # Give title for individual subplot
    if season != seasons[-1]: # Hide x-axis labels for upper panels if plotting multiple panels
      dia._ax.axes.xaxis.set_ticklabels([])
      dia._ax.set_xlabel('')

if len(seasons) == 1:
  fig.subplots_adjust(bottom=0.3) # Give more bottom margins to model name show up

PLT.savefig(pathout + '/' + fig_filename + '.png')

if test:
    PLT.ion()
    PLT.show()
