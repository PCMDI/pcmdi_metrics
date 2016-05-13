import numpy as np
import matplotlib.pyplot as plt
import sys

def plot_metrics_unify(cat1,cat2,mods,data):

  #
  # Canvas setup
  #
  if test:
    plt.ion()

  fig, ax = plt.subplots()
  #fig, ax = plt.subplots(figsize=(18,5))
  #fig, ax = plt.subplots(figsize=(12,7))

  #
  # Conditions .... OMG THIS IS SUPER MESSY... I should find advanced way...
  # 
  if test:
    print cat1, cat2, len(mods), len(data)

  if cat1 == 'ENSO_stdv':
    unit_adjust = 1
    unit = '$^\circ$C'
    ymax = 2
    ymin = 0
    yint = 0.5
    ylstart = 0
  elif cat1 == 'ENSO_seasonality':
    unit_adjust = 1
    unit = 'Std(NDJ)/Std(MAM)' 
    ymax = 2.5
    ymin = 0
    yint = 0.5
    ylstart = 0
  elif cat1 == 'ENSO_mean_stat':
    if cat2 == 'SST_RMSE':
      unit_adjust = 1
      unit = '$^\circ$C'
      ymax = 3
      ymin = -0.1
      yint = 0.5
      ylstart = 0
    elif cat2 == 'SST_AMP':
      unit_adjust = 1.
      unit = '$^\circ$C'
      ymax = 1.5
      ymin = -0.1
      yint = 0.2
      ylstart = 0
    elif cat2 == 'TAUU_RMSE':
      unit_adjust = 1000. # [N m-2] to [10^-3 N m-2]
      unit = '10^-3 Nm^-2'
      ymax = 33
      ymin = -2
      yint = 5
      ylstart = 0
    elif cat2 == 'PR_RMSE':
      unit_adjust = 86400. # [kg m-2 s-1] to [mm/day]
      unit = 'mm/day'
      ymax = 3.3
      ymin = -0.2
      yint = 0.5
      ylstart = 0
    else:
      sys.exit(cat2+' in '+cat1+' is not defined yet')

  elif cat1 == 'Atm_feedback':
    if cat2 == 'AtmBjk':
      unit_adjust = 1000.
      unit = '10^-3 Nm^-2/$^\circ$C'
      ymax = 15
      ymin = 0
      yint = 2
      ylstart = 0
    elif cat2 == 'SfcFlx':
      unit_adjust = 1.
      unit = 'Wm^-2/$^\circ$C'
      ymax = 0
      ymin = -21
      yint = 5
      ylstart = -20
      print "MEMO: SfcFlx plot is not ready yet. Net flux calc. needed"
    elif cat2 == 'SrtWav':
      unit_adjust = 1.
      unit = 'Wm^-2/$^\circ$C'
      ymax = 10
      ymin = -20
      yint = 5
      ylstart = -20
    elif cat2 == 'LthFlx':
      unit_adjust = -1.
      unit = 'Wm^-2/$^\circ$C'
      ymax = 1
      ymin = -21
      yint = 5
      ylstart = -20
    else:
      sys.exit(cat2+' in '+cat1+' is not defined yet')

  else:
    sys.exit(cat1+'is not defined yet')

  #
  # Array setup
  # 
  num_mods = len(mods)
  x = np.linspace(0,num_mods-1,num_mods)
  y = np.array(data) * unit_adjust
  labels = mods

  # 
  # Plotting
  #
  #ax.plot(x,y,'o',c='red')
  ax.scatter(x,y,c='red',s=80)

  ax.set_title(cat1+', '+cat2+'\n'+mip+', '+exp+', '+run)
  ax.set_xlabel('Models')
  ax.set_ylabel(unit)
  ax.set_xlim([-1.,len(y)-0.5])
  #ax.set_ylim([ymin,ymax])
  ax.set_ylim([y.min()*1.1,y.max()*1.1])
  ax.grid(True)

  plt.xticks(x,labels,rotation='vertical') ## Label x-axis as model names
  ax.yaxis.set_ticks(np.arange(ylstart, ymax+1, yint))

  # Multi model mean / std. dev. / min / max
  yave=np.mean(y)
  ystd=np.std(y)
  ymin=np.amin(y)
  ymax=np.amax(y)

  ax.plot(-0.5,yave,'x',c='red',markersize=12) # ave
  ax.plot(-0.5,ymin,'+',c='red',markersize=12) # min
  ax.plot(-0.5,ymax,'+',c='red',markersize=12) # max
  ax.errorbar(-0.5,yave,yerr=ystd,ls='solid',color='red',linewidth=1) # inter-model std. dev.

  # 
  # Save image file
  #
  plt.tight_layout()
  plt.show()
  fig.savefig('test_'+cat1+'_'+cat2+'.png',dpi=300)
