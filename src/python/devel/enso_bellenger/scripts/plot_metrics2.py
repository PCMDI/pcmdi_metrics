import numpy as np
import matplotlib.pyplot as plt

def plot_metrics2(reg,mods):

  # 
  # Options...
  #
  debug = True
  centry_stdv = True

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
  #num_mods = len(stdv[reg]) ## len(stdv[reg]) == len(mods)

  if debug:
    print len(mods), len(stdv[reg])

  #x=np.linspace(0,len(stdv[reg])-1,len(stdv[reg]))
  x=np.linspace(0,num_mods-1,num_mods)
  y=np.array(stdv[reg])
  labels = mods

  if centry_stdv == True:
    labels=[]
    t_keys=[]
    for i in xrange(0,num_mods,1):
      yrs = int(reg_time[i])/12
      labels.append(str(mods[i])+': '+str(yrs)) 
      t_keys = d[mods[i]][reg]['std'].keys()
      for t in t_keys:
        if t != 'entire':
          if debug:
            #print i, mods[i], t, d[mods[i]][reg]['std'][t]
            print i, mods[i], t, d[mods[i]][reg]['std_NDJ'][t], d[mods[i]][reg]['std_MAM'][t]
          #ax.plot(i,d[mods[i]][reg]['std'][t],'x',c='red')
          ax.plot(i,float(d[mods[i]][reg]['std_NDJ'][t])/float(d[mods[i]][reg]['std_MAM'][t]),'x',c='red')

  ax.plot(x,y,'o',c='red')

  #  
  # Plot perimeter setup: title and axis label
  #
  #ax.set_title('Std. dev., '+reg+', '+var+'\n'+mip+', '+exp+', '+run)
  ax.set_title('Seasonality Metric, '+reg+', '+var+'\n'+mip+', '+exp+', '+run)
  if centry_stdv == True:
    ax.set_xlabel('Models')
  else:
    ax.set_xlabel('Models: Simulation years')
  #ax.set_ylabel('$^\circ$C') # Print Celcius symbol
  ax.set_ylabel('Std(NDJ)/Std(MAM)')
  ax.set_xlim([-1.,len(y)-0.5])
  #ax.set_ylim([-0.1,2.1])
  ax.set_ylim([0.6,2.6])
  ax.grid(True)

  #ax.xaxis.set_ticks(np.arange(0, len(y), 1)) ## Label x-axis as numbers
  plt.xticks(x,labels,rotation='vertical') ## Label x-axis as model names
  #ax.yaxis.set_ticks(np.arange(0, 2.5, 0.5))
  ax.yaxis.set_ticks(np.arange(1.0, 3.0, 0.5))

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
  fig.savefig('test_enso_'+reg+'_'+var+'.png',dpi=300)
