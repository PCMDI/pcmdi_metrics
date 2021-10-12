#!/usr/bin/env python

import argparse
import json
import matplotlib.pyplot as plt
import os
from pcmdi_metrics.graphics.bias_bar_chart import BarChart

parser = argparse.ArgumentParser()
parser.add_argument("-j", "--json", help="path for input json file")
parser.add_argument("-v", "--var", help="variable")
parser.add_argument("-s", "--season", help="season: djf, mam, jja, son, ann, or all")
parser.add_argument("-o", "--pathout", help="directory path for output files")
parser.add_argument("-e", "--exp", help="experiment")
parser.add_argument("-d", "--domain", help="domain")
parser.add_argument("--stat", help="statistics")
args = parser.parse_args()

print('args:', args)

json_path = args.json
var = args.var
season = args.season
pathout = args.pathout
exp = args.exp
domain = args.domain
stat = args.stat

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
            tmp = float(dd['RESULTS'][mod]["default"]['r1i1p1'][domain][stat][season])  # current format
        except Exception as err1:
            print(err1)
            try:
                tmp = float(dd['RESULTS'][mod]["defaultReference"]['r1i1p1']['global'][stat+'_'+season+'_'+domain])  # old format
            except Exception as err2:
                print(err2)
                tmp = None
        all_mods.append(tmp)
    dia = BarChart(mods, all_mods, stat, fig=fig, rect=rects[season])
    dia._ax.set_title(season.upper())  # Give title for individual subplot
    if season != seasons[-1]:  # Hide x-axis labels for upper panels if plotting multiple panels
        dia._ax.axes.xaxis.set_ticklabels([])
        dia._ax.set_xlabel('')

if len(seasons) == 1:
    fig.subplots_adjust(bottom=0.3)  # Give more bottom margins to model name show up

figfile = os.path.join(pathout, fig_filename + '.png')
plt.savefig(figfile)
print('Figure saved as '+figfile)