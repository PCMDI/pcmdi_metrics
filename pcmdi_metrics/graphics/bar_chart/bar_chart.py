#!/usr/bin/env python

import matplotlib.pyplot as plt
import json
import sys
import os
import getopt
from pcmdi_metrics.graphics.bias_bar_chart import BarChart

args = sys.argv[1:]
letters = 'j:v:s:e:d:o:'
keywords = ['json=', 'var=', 'season=', 'exp=', 'domain=', 'plotpath=']
json_path = 'default'
season = 'default'
domain = 'NHEX'
var = 'default'
pathout = './example_plot'

stat = 'bias'
opts, pargs = getopt.getopt(args, letters, keywords)

for o, p in opts:
    if o in ['-j', '--json']:
        json_path = p
    if o in ['-v', '--var']:
        var = p
    if o in ['-s', '--season']:  # djf / mam / jja / son / ann
        season = p
    if o in ['-o', '--plotpath']:
        pathout = p
    if o in ['-e', '--exp']:
        exp = p
    if o in ['-d', '--domain']:
        dom = p

print(json_path, season, pathout, exp, var, dom)

fj = open(json_path)
dd = json.loads(fj.read())
fj.close()

mods = dd['RESULTS'].keys()

seasons = [season]
if season == 'all':
    seasons = ['ann', 'djf', 'mam', 'jja', 'son']
    rects = {'ann': 511, 'djf': 512, 'mam': 513, 'jja': 514, 'son': 515}  # subplot location
    figsize = (10, 16)  # optimized figure size for five subplots
    xpanel = '5panel'
else:
    rects = {}
    rects[season] = 111  # subplot location
    figsize = (10, 6)  # optimized figure size for one subplot
    xpanel = '1panel'

fig = plt.figure(figsize=figsize)
fig_filename = '_'.join([var, exp, stat, xpanel, season, dom])
fig.suptitle(', '.join([stat, var.title(), exp.upper(), dom.upper()]), size='x-large')  # Title for the entire canvas

for season in seasons:
    all_mods = []
    for mod in mods:
        tmp = float(dd['RESULTS'][mod]["defaultReference"]['r1i1p1']['global'][stat+'_xy_'+season+'_'+dom])
        all_mods.append(tmp)
    dia = BarChart(mods, all_mods, fig=fig, rect=rects[season])
    dia._ax.set_title(season.upper())  # Give title for individual subplot
    if season != seasons[-1]:  # Hide x-axis labels for upper panels if plotting multiple panels
        dia._ax.axes.xaxis.set_ticklabels([])
        dia._ax.set_xlabel('')

if len(seasons) == 1:
    fig.subplots_adjust(bottom=0.3)  # Give more bottom margins to model name show up

plt.savefig(os.path.join(pathout, fig_filename + '.png'))
