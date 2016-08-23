#!/usr/bin/env python

import numpy as NP
import matplotlib.pyplot as PLT
import json
import sys, os
import getopt
#import pcmdi_metrics
#from pcmdi_metrics.bias_bar_chart import BarChart
libfiles = ['plot_barChart.py',\
            'plot_scatter.py']

for lib in libfiles:
  #execfile(os.path.join('../lib/',lib))
  execfile(os.path.join('./',lib))

#debug = True
debug = False

args=sys.argv[1:]
letters='j:v:s:e:d:o:m:'
keywords=['json=','var=','season=','exp=','plotpath=']
json_path = 'default'
season ='default'
var = 'default'
pathout = './'
mip = 'cmip5'

opts,pargs = getopt.getopt(args,letters,keywords)
for o,p in opts:
    if o in ['-j','--json']:
        json_path = p
    if o in ['-v','--var']:
        var = p
    if o in ['-s','--season']: # DJF / MAM / JJA / SON / all / monthly
        season_option = p
    if o in ['-o','--plotpath']:
        pathout = p
    if o in ['-e','--exp']:
        exp = p
    if o in ['-m','--mode']:
        mode = p

print json_path,' ',season,' ', pathout,' ', exp,' ', var 
print 'after args'

fj = open(json_path)
dd = json.loads(fj.read())
fj.close()

models = dd['RESULTS'].keys()
models = sorted(models, key=lambda s:s.lower()) # Sort list alphabetically, case-insensitive

# Bar charts
data={}

stats = ['rms', 'rms_glo', 'rms_alt', 'rms_alt_glo', \
         'cor', 'cor_glo', 'cor_alt', 'cor_alt_glo', \
         'frac' ]

if debug: stats = ['rms', 'cor']

for stat in stats:
  data[stat]={}

  if season_option == 'all':
    seasons = ['DJF', 'MAM', 'JJA', 'SON']
    rects = {'DJF':511, 'MAM':512, 'JJA':513, 'SON':514} # subplot location
    fig = PLT.figure(figsize=(10,20)) # optimized figure size for five subplots
    fig_filename = mode + '_' + var + '_' + exp + '_4panel_' + season_option + '_' + stat
  else:
    seasons = [season_option]
    rects = {}
    rects[season_option] = 111 # subplot location
    fig = PLT.figure(figsize=(10,6)) # optimized figure size for one subplot
    fig_filename = mode + '_' + var + '_' + exp + '_1panel_' + season_option + '_' + stat

  fig.suptitle(mode+', '+var.title()+', EOF1, '+(exp).upper()+', '+stat, size='x-large') # Giving title for the entire canvas

  for season in seasons:

      data[stat][season]={}

      # Read in data ---
      data_all = []
      for model in models:
        tmp = float(dd['RESULTS'][model]['defaultReference'][mode][season][stat])
        data_all.append(tmp)

      data[stat][season] = data_all

      dia = BarChart(models,data_all,fig=fig, rect=rects[season])
      dia._ax.set_title(season.upper()) # Give title for individual subplot
      dia._ax.set_ylabel(stat)

      if stat == 'rms' or stat == 'rms_glo' or stat == 'rms_alt' or stat == 'rms_alt_glo':
        # Normalize rms
        #data[stat][season] = ( data[stat][season] - NP.mean(data[stat][season]) ) / NP.std(data[stat][season])
        #dia._ax.set_ylim(0,3.5)
        dia._ax.set_ylim(0,6)
      elif stat == 'cor' or stat == 'cor_glo' or stat == 'cor_alt' or stat == 'cor_alt_glo':
        dia._ax.set_ylim(-1,1)
      elif stat == 'frac':
        dia._ax.set_ylim(0,1)

      if len(seasons) > 1:
        if season != seasons[-1]: # Hide x-axis labels for upper panels if plotting multiple panels
          #dia._ax.axes.xaxis.set_ticklabels([])
          index = range(1,len(models)+1)
          dia._ax.axes.xaxis.set_ticklabels(index)
          dia._ax.set_xlabel('')
          #dia._fig.subplots_adjust(bottom=0.01,top=0.95,wspace=0.5,hspace=0.5)
          dia._fig.subplots_adjust(bottom=0.01,top=0.92,hspace=0.5)
        else: # For bottom panel
          labels = []
          for i in index:
            labels.append(str(str(index[i-1])+': '+models[i-1]))
            dia._ax.axes.xaxis.set_ticklabels(labels)
      else:
        fig.subplots_adjust(bottom=0.3) # Give more bottom margins to model name show up

  print 'bar chart: ', stat, season
  PLT.savefig(pathout + '/' + fig_filename + '.png')

  if debug:
    PLT.ion()
    PLT.show()

for season in seasons:
  print 'scatter plot: ', season
  plot_scatter(models, data['cor'][season], data['rms'][season], mode+'_'+season+'_cor_rms','cor','rms')
  if not debug:
    plot_scatter(models, data['rms'][season], data['rms_alt'][season], mode+'_'+season+'_rms_rms_alt','rms','rms_alt')
    plot_scatter(models, data['cor'][season], data['cor_alt'][season], mode+'_'+season+'_cor_cor_alt','cor','cor_alt')
    plot_scatter(models, data['cor_alt'][season], data['rms_alt'][season], mode+'_'+season+'_cor_alt_rms_alt','cor_alt','rms_alt')

