import numpy as np
import matplotlib.pyplot as plt
import sys
import matplotlib.cm as cm

def plot_scatter_monsoon(mods,reg,data1,data2):

  #
  # Canvas setup
  #
  if test:
    plt.ion()

  fig, ax = plt.subplots(figsize=(7,7))

  #
  # Array setup and plot
  # 
  if test:
    print len(data1), len(data2)

  # 
  # Simple quality control
  #
  if len(data1) == len(data2) and len(mods)==len(data1):
    num_dots = len(data1)
  else:
    sys.exit("data size dose not match")

  xlabel = 'PCC'
  xmax = 1
  xmin = 0.5
  xint = 0.1
  xlstart = 0.6

  ylabel = 'RMSN'
  ymax = 1.0
  ymin = 0.2
  yint = 0.1
  ylstart = 0.2

  #colors = cm.rainbow(np.linspace(0, 1, num_dots))
  #colors = cm.gist_rainbow(np.linspace(0, 1, num_dots))
  #colors = cm.gist_ncar(np.linspace(0, 1, num_dots))
  colors = cm.Paired(np.linspace(0, 1, num_dots))
  #colors = cm.Set1(np.linspace(0, 1, num_dots))
  #colors = cm.nipy_spectral(np.linspace(0, 1, num_dots))
  #colors = cm.hsv(np.linspace(0, 1, num_dots))
  #colors = cm.jet(np.linspace(0, 1, num_dots))

  #import six
  #from matplotlib import colors
  #colors_ = list(six.iteritems(colors.cnames))
  #colors = [str(i[0]) for i in colors_]

  for i in range(0,num_dots):
    x = float(data1[i])
    y = float(data2[i])
    mod = str(mods[i])
    ax.scatter(x,y,label=mod,c=colors[i],s=80,linewidth=0.15)
    
  ax.legend(frameon=False,scatterpoints=1, loc=3, 
            borderaxespad=0., fontsize='small',labelspacing=0.1)

  #  
  # Title and axis labeling
  #
  ax.set_title(reg+'\n'+mip+', '+exp)
  ax.set_xlabel(xlabel)
  ax.set_ylabel(ylabel)
  ax.set_xlim([xmin,xmax])
  ax.set_ylim([ymin,ymax])
  ax.grid(True)

  ax.xaxis.set_ticks(np.arange(xlstart, xmax+xint/2., xint))
  ax.yaxis.set_ticks(np.arange(ylstart, ymax+yint/2., yint))

  # 
  # Save image file
  #
  plt.tight_layout()
  fig.savefig('test_monsoon_'+reg+'_scatter.png',dpi=300)
  if test:
    plt.show()
