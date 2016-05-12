import numpy as np
import matplotlib.pyplot as plt
import sys

def plot_metrics_monsoon(mods,reg,data,var):

  #
  # Canvas setup
  #
  if test:
    plt.ion()

  #fig, ax = plt.subplots(figsize=(18,5))
  fig, ax = plt.subplots(figsize=(12,7))

  #
  # Array setup and plot
  # 
  num_mods = len(mods)

  if test:
    print len(mods), len(data)

  if var == 'cor':
    unit_adjust = 1
    unit = 'cor'
    ymax = 1
    ymin = 0 
    yint = 0.1
    ylstart = 0
  elif var == 'rmsn':
    unit_adjust = 1.
    unit = 'rmsn'
    ymax = 1.5
    ymin = -0.1
    yint = 0.2
    ylstart = 0
  else:
    sys.exit(var+'is not defined yet')

  x = np.linspace(0,num_mods-1,num_mods)
  y = np.array(data) * unit_adjust
  labels = mods

  ax.plot(x,y,'o',c='red')

  #  
  # Plot perimeter setup: title and axis label
  #
  ax.set_title(var+'\n'+mip+', '+exp+', '+reg)
  ax.set_xlabel('Models')
  ax.set_ylabel(unit)
  ax.set_xlim([-1.,len(y)-0.5])
  ax.set_ylim([ymin,ymax])
  ax.grid(True)

  plt.xticks(x,labels,rotation='vertical') ## Label x-axis as model names
  ax.yaxis.set_ticks(np.arange(ylstart, ymax+yint/2., yint))

  #
  # Multi model mean / std. dev. / min / max
  #
  yave=np.mean(y)
  ystd=np.std(y)
  ymin=np.amin(y)
  ymax=np.amax(y)

  ax.plot(-0.5,yave,'x',c='red') # ave
  ax.plot(-0.5,ymin,'+',c='red') # min
  ax.plot(-0.5,ymax,'+',c='red') # max
  ax.errorbar(-0.5,yave,yerr=ystd,ls='solid',color='red') # inter-model std. dev.

  # 
  # Save image file
  #
  plt.tight_layout()
  fig.savefig('test_monsoon_'+reg+'_'+var+'.png',dpi=300)
  if test:
    plt.show()
