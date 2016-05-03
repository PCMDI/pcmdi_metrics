import numpy as np
import matplotlib.pyplot as plt

def plot_metrics_AtmFeedback(mods):

  # 
  # Options...
  #
  debug = True

  #
  # Canvas setup
  #
  if test:
    plt.ion()

  fig, ax = plt.subplots(figsize=(18,5))

  #
  # Array setup and plot
  # 
  num_mods = len(mods)

  if debug:
    print len(mods), len(stdv)

  x=np.linspace(0,num_mods-1,num_mods)
  y=np.array(stdv)*1000
  labels = mods

  ax.plot(x,y,'o',c='red')

  #  
  # Plot perimeter setup: title and axis label
  #
  ax.set_title('Atm. Bjerknes feedback, '+var+'\n'+mip+', '+exp+', '+run)
  ax.set_xlabel('Models')
  ax.set_ylabel('10^-3 Nm^-2/$^\circ$C') # Print Celcius symbol
  ax.set_xlim([-1.,len(y)-0.5])
  #ax.set_ylim([-0.1,2.1])
  ax.set_ylim([-0.5,14.5])
  ax.grid(True)

  #ax.xaxis.set_ticks(np.arange(0, len(y), 1)) ## Label x-axis as numbers
  plt.xticks(x,labels,rotation='vertical') ## Label x-axis as model names
  ax.yaxis.set_ticks(np.arange(0, 15, 2))

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
  fig.savefig('test_AtmFeedback_'+var+'.png',dpi=300)
