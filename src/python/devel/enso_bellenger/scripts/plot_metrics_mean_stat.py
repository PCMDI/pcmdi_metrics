import numpy as np
import matplotlib.pyplot as plt
import sys

def plot_metrics_mean_stat(mods,data):

  #
  # Canvas setup
  #
  if test:
    plt.ion()

  fig, ax = plt.subplots(figsize=(18,5))
  #fig, ax = plt.subplots(figsize=(12,7))

  #
  # Array setup and plot
  # 
  num_mods = len(mods)

  if test:
    print len(mods), len(data)

  if stat == 'SST_RMSE':
    unit_adjust = 1
    unit = '$^\circ$C'
    ymax = 3
    ymin = -0.1
    yint = 0.5
    ylstart = 0
  elif stat == 'SST_AMP':
    unit_adjust = 1.
    #unit_adjust = 0.5
    ymax = 1.5
    ymin = -0.1
    yint = 0.2
    ylstart = 0
  elif stat == 'TAUU_RMSE':
    unit_adjust = 1000. # [N m-2] to [10^-3 N m-2]
    unit = '10^-3 Nm^-2'
    ymax = 33
    ymin = -2
    yint = 5
    ylstart = 0
  elif stat == 'PR_RMSE':
    unit_adjust = 86400. # [kg m-2 s-1] to [mm/day]
    unit = 'mm/day'
    ymax = 3.3
    ymin = -0.2
    yint = 0.5
    ylstart = 0
  else:
    sys.exit(stat+'is not defined yet')

  x = np.linspace(0,num_mods-1,num_mods)
  y = np.array(data) * unit_adjust
  labels = mods

  ax.plot(x,y,'o',c='red')

  #  
  # Plot perimeter setup: title and axis label
  #
  ax.set_title(stat+'\n'+mip+', '+exp+', '+run)
  ax.set_xlabel('Models')
  ax.set_ylabel(unit)
  ax.set_xlim([-1.,len(y)-0.5])
  ax.set_ylim([ymin,ymax])
  ax.grid(True)

  plt.xticks(x,labels,rotation='vertical') ## Label x-axis as model names
  ax.yaxis.set_ticks(np.arange(ylstart, ymax+1, yint))

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
  plt.show()
  fig.savefig('test_ENSO_mean_stat_'+stat+'.png',dpi=300)
