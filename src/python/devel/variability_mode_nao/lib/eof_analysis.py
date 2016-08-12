def eof_analysis_get_first_variance_mode(timeseries):
  # input, timeseries: time varying 2d array

  import cdms2 as cdms
  from eofs.cdms import Eof

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
  if float(eof1[-1][-1]) is not eof1.missing and float(eof1[-1][-1]) >= 0:
    eof1 = eof1*-1.
    pc1 = pc1*-1.
    reverse_sign = True
  elif float(eof1[eof1.shape[0]//2][eof1.shape[1]//2]) >= 0:
    eof1 = eof1*-1.
    pc1 = pc1*-1.
    reverse_sign = True

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
