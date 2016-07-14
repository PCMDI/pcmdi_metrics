def eof_analysis_get_first_variance_mode(timeseries):

  # input, timeseries: time varying 2d array

  import cdms2 as cdms
  from eofs.cdms import Eof

  # EOF (take only first variance mode...) ---
  solver = Eof(timeseries, weights='coslat')
  eof = solver.eofsAsCovariance(neofs=1)
  pc = solver.pcs(npcs=1, pcscaling=1) # pcscaling=1: scaled to unit variance 
                                       # (divided by the square-root of their eigenvalue)
  frac = solver.varianceFraction()

  # Remove unnessasary dimensions (make sure only taking first variance mode) ---
  eof1 = eof(squeeze=1) # same as... eof1 = eof[0]
  pc1 = pc(squeeze=1)   #      pc1 = pc[:,0] 
  frac1 = cdms.createVariable(frac[0])

  # Arbitrary control, attempt to make all plots have the same sign ---
  if float(eof1[-1][-1]) >= 0:
    eof1 = eof1*-1.
    pc1 = pc1*-1.

  # Supplement NetCDF attributes 
  frac1.units = 'ratio'
  pc1.comment='Scaled time series for principal component of first variance mode'

  return(eof1, pc1, frac1)
