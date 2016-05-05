import numpy as np
import matplotlib.pyplot as plt
import sys

def plot_metrics_AtmFeedback(mods,data):

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

  if fdb == 'AtmBjk':
    unit_adjust = 1000.
    unit = '10^-3 Nm^-2/$^\circ$C'
    ymax = 14.5
    ymin = -0.5
    yint = 2
    ylstart = 0
  elif fdb == 'SfcFlx':
    unit_adjust = 1.
    unit = 'Wm^-2/$^\circ$C'
    ymax = 1
    ymin = -21
    yint = 5
    ylstart = -20
    print "MEMO: SfcFlx plot is not ready yet. Net flux calc. needed"
  elif fdb == 'SrtWav':
    unit_adjust = 1.
    unit = 'Wm^-2/$^\circ$C'
    ymax = 11
    ymin = -21
    yint = 5
    ylstart = -20
  elif fdb == 'LthFlx':
    unit_adjust = -1.
    unit = 'Wm^-2/$^\circ$C'
    ymax = 1
    ymin = -21
    yint = 5
    ylstart = -20
  else:
    sys.exit(fdb+'is not defined yet')

  x = np.linspace(0,num_mods-1,num_mods)
  y = np.array(data) * unit_adjust
  labels = mods

  ax.plot(x,y,'o',c='red')

  #  
  # Plot perimeter setup: title and axis label
  #
  ax.set_title(fdb+'\n'+mip+', '+exp+', '+run)
  ax.set_xlabel('Models')
  ax.set_ylabel(unit) # Print Celcius symbol
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
  fig.savefig('test_AtmFeedback_'+fdb+'.png',dpi=300)
