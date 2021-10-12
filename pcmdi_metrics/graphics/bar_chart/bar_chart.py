#!/usr/bin/env python

import matplotlib.pyplot as plt
import json
import sys
import os
import getopt
from pcmdi_metrics.graphics.bias_bar_chart import BarChart

args = sys.argv[1:]
letters = 'j:v:s:e:d:o:'
keywords = ['json=', 'var=', 'season=', 'exp=', 'domain=', 'pathout=']
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
    if o in ['-o', '--pathout']:
        pathout = p
    if o in ['-e', '--exp']:
        exp = p
    if o in ['-d', '--domain']:
        domain = p

print('json_path:', json_path)
print('season:', season)
print('pathout:', pathout)
print('exp:', exp)
print('variable:', var)
print('domain:', domain)

os.makedirs(pathout, exist_ok=True)

fj = open(json_path)
dd = json.loads(fj.read())
fj.close()

mods = sorted(dd['RESULTS'].keys())

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
fig_filename = '_'.join([var, exp, stat, xpanel, season, domain])
fig.suptitle(', '.join([stat, var.title(), exp.upper(), domain.upper()]), size='x-large')  # Title for the entire canvas

for season in seasons:
    all_mods = []
    for mod in mods:
        try:
            tmp = float(dd['RESULTS'][mod]["default"]['r1i1p1'][domain][stat+'_xy'][season])  # current format
        except Exception as err1:
            print(err1)
            try:
                tmp = float(dd['RESULTS'][mod]["defaultReference"]['r1i1p1']['global'][stat+'_xy_'+season+'_'+domain])  # old format
            except Exception as err2:
                print(err2)
                tmp = None
        all_mods.append(tmp)
    dia = BarChart(mods, all_mods, fig=fig, rect=rects[season])
    dia._ax.set_title(season.upper())  # Give title for individual subplot
    if season != seasons[-1]:  # Hide x-axis labels for upper panels if plotting multiple panels
        dia._ax.axes.xaxis.set_ticklabels([])
        dia._ax.set_xlabel('')

if len(seasons) == 1:
    fig.subplots_adjust(bottom=0.3)  # Give more bottom margins to model name show up

figfile = os.path.join(pathout, fig_filename + '.png')
plt.savefig(figfile)
print('Figure saved as '+figfile)