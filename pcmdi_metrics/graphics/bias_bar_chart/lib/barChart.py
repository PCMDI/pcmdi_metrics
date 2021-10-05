import numpy as np
import matplotlib.pyplot as PLT
import sys

class BarChart(object):

  def __init__(self, mods, data, fig=None, rect=111):

    # Canvas setup
    if fig is None:
      fig = PLT.figure
    ax = fig.add_subplot(rect)

    # Enable to control ax options outside of this file
    self._ax = ax

    # Axis setup
    unit_adjust = 1.
    unit = 'Unit needed here ...'
    ymax = max(data)
    ymin = min(data)
    yint = int((ymax-ymin)/3)

    # Array setup
    num_mods = len(mods)
    x = np.linspace(0,num_mods-1,num_mods)
    y = np.array(data) * unit_adjust
    labels = mods

    # Plotting
    ax.bar(x,y,bottom=0,align='center')
    ax.axhline(0, color='black')

    # Title and axis
    ax.set_title('Subtitle needed here..')
    ax.set_xlabel('Models')
    ax.set_ylabel(unit)
    ax.set_xlim([-1.,len(y)-0.5])
    ax.set_ylim([y.min()*1.1,y.max()*1.1])
    ax.grid(True)

    # Axis labels
    PLT.xticks(x,labels,rotation='vertical') ## Label x-axis as model names
    ax.yaxis.set_ticks(np.arange(int(ymin-yint), int(ymax+yint), yint))

    # Multi model mean / std. dev. / min / max
    yave=np.mean(y)
    ystd=np.std(y)
    ymin=np.amin(y)
    ymax=np.amax(y)

    ax.plot(-0.7,yave,'x',c='red',markersize=12) # ave
    ax.plot(-0.7,ymin,'+',c='red',markersize=12) # min
    ax.plot(-0.7,ymax,'+',c='red',markersize=12) # max
    ax.errorbar(-0.7,yave,yerr=ystd,ls='solid',color='red',linewidth=1) # inter-model std. dev.
