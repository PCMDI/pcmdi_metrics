import numpy as NP
import matplotlib.pyplot as plt
import sys
import matplotlib.cm as cm

def plot_scatter(models,data1,data2,file_out,label1,label2):

  print 'scatter plot: ', label1, label2  

  #
  # Canvas setup
  #
  if debug: 
    plt.ion()

  fig = plt.figure(figsize=(13,12))
  ax = plt.subplot(111)
  plt.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1, wspace=0, hspace=0)

  #
  # Array setup and plot
  # 
  if debug:
    print len(data1), len(data2)

  # 
  # Simple quality control
  #
  if len(data1) == len(data2) and len(models)==len(data1):
    num_dots = len(data1)
  else:
    sys.exit("data size dose not match")

  # X axis ---
  xlabel = str.upper(label1)
  #xmax = NP.max(data1)*1.1
  xmax = NP.max(data1)
  xmin = NP.min(data1)
  if xmin < 0: xmin = xmin*1.1
  else: xmin = xmin*0.9
  xint = (xmax-xmin)/5.
  if xint < 0.1: xint = round(xint,2)
  elif xint < 1: xint = round(xint,1)
  else: xint = int(xint)
  xlstart = xmin//1
  if debug: print 'xmin, xmax, xint:',xmin, xmax, xint

  # Y axis ---
  ylabel = str.upper(label2)
  #ymax = NP.max(data2)*1.1
  ymax = NP.max(data2)
  ymin = NP.min(data2)
  if ymin < 0: ymin = ymin*1.1
  else: ymin = ymin*0.9
  yint = (ymax-ymin)/5.
  if yint < 0.1: yint = round(yint,2)
  elif yint < 1: yint = round(yint,1)
  else: yint = int(yint)
  ylstart = ymin//1
  if debug: print 'ymin, ymax, yint:',ymin, ymax, yint

  #colors = cm.rainbow(NP.linspace(0, 1, num_dots))
  #colors = cm.gist_rainbow(NP.linspace(0, 1, num_dots))
  #colors = cm.gist_ncar(NP.linspace(0, 1, num_dots))
  colors = cm.Paired(NP.linspace(0, 1, num_dots))
  #colors = cm.Set1(NP.linspace(0, 1, num_dots))
  #colors = cm.nipy_spectral(NP.linspace(0, 1, num_dots))
  #colors = cm.hsv(NP.linspace(0, 1, num_dots))
  #colors = cm.jet(NP.linspace(0, 1, num_dots))

  for i, mod in enumerate(models):
    x = float(data1[i])
    y = float(data2[i])
    mod = str(models[i])
    ax.scatter(x, y, label=str(i+1)+' '+mod, c=colors[i], s=200, linewidth=0.15)
    # Show index numbers
    ax.annotate(str(i+1), (x,y), fontsize='small', verticalalignment='center', horizontalalignment='center', color='white')
    
  ax.legend(frameon=True, scatterpoints=1, bbox_to_anchor=(1.05, 1), loc=2,
            borderaxespad=0., fontsize=11, labelspacing=0.435, ncol=1)

  #  
  # Title and axis labeling
  #
  ax.set_title(file_out, fontsize=18)
  ax.set_xlabel(xlabel, fontsize=17)
  ax.set_ylabel(ylabel, fontsize=17)
  #ax.set_xlim([xmin,xmax])
  #ax.set_ylim([ymin,ymax])
  ax.grid(True)

  #ax.xaxis.set_ticks(NP.arange(xlstart, xmax+xint/2., xint))
  #ax.yaxis.set_ticks(NP.arange(ylstart, ymax+yint/2., yint))
  plt.tick_params(labelsize=15) # Tick label font size

  #
  # Text test
  #
  x0, xmax = plt.xlim()
  y0, ymax = plt.ylim()
  data_width = xmax - x0
  data_height = ymax - y0
  #plt.text(x0 + data_width * 0.5, y0 + data_height * 0.5, 'Some text')

  #
  # Linear regression
  #
  fit = NP.polyfit(data1, data2, 1) 
  fit_fn = NP.poly1d(fit)
  plt.plot(data1, fit_fn(data1), '-')
  slope = fit[0]
  #ax.text(xmax, ymax, 'Regression slope ='+str(round(slope,2)), va='center', ha='left', color='blue', fontsize=15) 
  ax.text(x0 + data_width * 0.65, y0 + data_height * 0.95, 'Regression slope ='+str(round(slope,2)), va='center', ha='left', color='blue', fontsize=15) 

  # 
  # Save image file
  #
  fig.savefig(file_out+'_scatter.png',dpi=300)
  if debug:
    plt.show()
