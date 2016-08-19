def eof_analysis_get_first_variance_mode(mode, timeseries):
  # Input required:
  # - mode : mode of variability is needed for arbitrary sign control, which is characteristics of EOF analysis
  # - timeseries: time varying 2d array, so 3d array (time, lat, lon)

  import cdms2 as cdms
  from eofs.cdms import Eof
  import cdutil

  # EOF (take only first variance mode...) ---
  solver = Eof(timeseries, weights='area')
  eof = solver.eofsAsCovariance(neofs=1)
  pc = solver.pcs(npcs=1, pcscaling=1) # pcscaling=1: scaled to unit variance 
                                       # (divided by the square-root of their eigenvalue)
  frac = solver.varianceFraction()

  # Remove unnessasary dimensions (make sure only taking first variance mode) ---
  eof1 = eof(squeeze=1) # same as... eof1 = eof[0]
  pc1 = pc(squeeze=1)   #      pc1 = pc[:,0] 
  frac1 = cdms.createVariable(frac[0])

  # Arbitrary sign control, attempt to make all plots have the same sign ---
  reverse_sign = False

  if mode == 'PDO': # Explicitly check average of geographical region for each mode
    if float(cdutil.averager(eof1(latitude=(30,40),longitude=(150,180)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  elif mode == 'PNA': 
    if float(cdutil.averager(eof1(latitude=(80,90)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  elif mode == 'NAM' or  mode == 'NAO':
    if float(cdutil.averager(eof1(latitude=(60,80)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  elif mode == 'SAM':
    if float(cdutil.averager(eof1(latitude=(-60,-90)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  else: # Minimum sign control part was left behind for any future usage..
    if float(eof1[-1][-1]) is not eof1.missing: 
      if float(eof1[-1][-1]) >= 0:
        reverse_sign = True
    elif float(eof1[-2][-2]) is not eof1.missing:
      if float(eof1[-2][-2]) >= 0: # Double check in case pole has missing value
        reverse_sign = True

  if reverse_sign:
    eof1 = eof1*-1.
    pc1 = pc1*-1.

  # Supplement NetCDF attributes 
  frac1.units = 'ratio'
  pc1.comment='Scaled time series for principal component of first variance mode'

  return(eof1, pc1, frac1, solver, reverse_sign)

def linear_regression(x,y):
  # input x: 1d timeseries (time)
  #       y: time varying 2d field (time, lat, lon)

  from scipy import stats
  import numpy as NP
  import MV2 as MV

  # get original global dimension 
  lat = y.getLatitude()
  lon = y.getLongitude()

  # Convert 3d (time, lat, lon) to 2d (time, lat*lon) for polyfit applying
  im_y = y.shape[2]
  jm_y = y.shape[1]
  y_2d = y.reshape(y.shape[0],im_y*jm_y)

  # Linear regression
  z = NP.polyfit(x,y_2d,1)

  # Retreive to 3d (index, lat, lon), index 0: coefficient (i.e. slope), 1: intercept
  zz = MV.array(z.reshape(z.shape[0],jm_y,im_y))

  # Set lat/lon coordinates
  zz.setAxis(1,lat)
  zz.setAxis(2,lon)
  zz.mask = y.mask

  # Take only coefficient, not intercept
  zz = zz[0,:,:]
 
  return(zz)
