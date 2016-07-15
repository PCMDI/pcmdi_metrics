#!/usr/bin/env python

import numpy as NP
import matplotlib.pyplot as PLT
import json
import sys, os
import getopt
#import pcmdi_metrics
#from pcmdi_metrics.bias_bar_chart import BarChart
libfiles = ['barChart.py']

for lib in libfiles:
  execfile(os.path.join('../lib/',lib))

test = False
test = True

args=sys.argv[1:]
letters='j:v:s:e:d:o:'
keywords=['json=','var=','season=','exp=','plotpath=']
json_path = 'default'
season ='default'
var = 'default'
pathout = './'
opts,pargs=getopt.getopt(args,letters,keywords)
for o,p in opts:
    if o in ['-j','--json']:
        json_path=p
    if o in ['-v','--var']:
        var = p
    if o in ['-s','--season']: # djf / mam / jja / son
        season=p
    if o in ['-o','--plotpath']:
        pathout=p
    if o in ['-e','--exp']:
        exp=p

print json_path,' ',season,' ', pathout,' ', exp,' ', var 
print 'after args'

fj = open(json_path)
dd = json.loads(fj.read())
fj.close()

mods = dd['RESULTS'].keys()

mode = 'nao'

stat = 'rms'
stat = 'cor'


seasons = [season]
if season == 'all':
  seasons = ['djf', 'mam', 'jja', 'son']
  rects = {'djf':411, 'mam':412, 'jja':413, 'son':414} # subplot location
  fig = PLT.figure(figsize=(10,16)) # optimized figure size for five subplots
  fig_filename = mode + '_' + var + '_' + exp + '_4panel_' + season + '_' + stat
else:
  rects = {}
  rects[season] = 111 # subplot location
  fig = PLT.figure(figsize=(10,6)) # optimized figure size for one subplot
  fig_filename = mode + '_' + var + '_' + exp + '_1panel_' + season + '_' + stat

fig.suptitle(mode.upper()+', '+var.title()+', EOF1, '+(exp).upper(), size='x-large') # Giving title for the entire canvas

for season in seasons:
    all_mods = []
    for mod in mods:
        tmp = float(dd['RESULTS'][mod]['defaultReference'][mode][str.upper(season)][stat])
        all_mods.append(tmp)
    dia = BarChart(mods,all_mods,fig=fig, rect=rects[season])
    dia._ax.set_title(season.upper()) # Give title for individual subplot
    dia._ax.set_ylabel(stat)

    if stat == 'rms':
      dia._ax.set_ylim(0,3.5)
    elif stat == 'cor':
      dia._ax.set_ylim(-1,1)

    if season != seasons[-1]: # Hide x-axis labels for upper panels if plotting multiple panels
      dia._ax.axes.xaxis.set_ticklabels([])
      dia._ax.set_xlabel('')

if len(seasons) == 1:
  fig.subplots_adjust(bottom=0.3) # Give more bottom margins to model name show up

PLT.savefig(pathout + '/' + fig_filename + '.png')

if test:
    PLT.ion()
    PLT.show()
