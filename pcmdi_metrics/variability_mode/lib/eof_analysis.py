def eof_analysis_get_variance_mode(mode, timeseries, eofn, EofScaling):
  # Input required:
  # - mode (string): mode of variability is needed for arbitrary sign control, which is characteristics of EOF analysis
  # - timeseries (cdms variable): time varying 2d array, so 3d array (time, lat, lon)
  # - eofn (integer): Which mode neet to be returned? 1st? 2nd? 3rd? ...

  import cdms2 as cdms
  from eofs.cdms import Eof
  import cdutil
  import MV2

  # EOF (take only first variance mode...) ---
  solver = Eof(timeseries, weights='area')
  eof = solver.eofsAsCovariance(neofs=eofn, pcscaling=1) # pcscaling=1 by default, return normalized EOFs
  if not EofScaling:
    pc = solver.pcs(npcs=eofn) # pcscaling=0 by default 
  else:
    pc = solver.pcs(npcs=eofn, pcscaling=1) # pcscaling=1: scaled to unit variance 
                                            # (divided by the square-root of their eigenvalue)
  frac = solver.varianceFraction()

  # Remove unnessasary dimensions (make sure only taking first variance mode) ---
  eof_n = eof[eofn-1]
  pc_n = pc[:,eofn-1] 
  frac_n = cdms.createVariable(frac[eofn-1])

  # Arbitrary sign control, attempt to make all plots have the same sign ---
  reverse_sign = arbitrary_checking(mode, eof_n)

  if reverse_sign:
    eof_n = MV2.multiply(eof_n,-1.)
    pc_n = MV2.multiply(pc_n,-1.)

  # Supplement NetCDF attributes 
  frac_n.units = 'ratio'
  pc_n.comment='Non-scaled time series for principal component of '+str(eofn)+'th variance mode'

  return(eof_n, pc_n, frac_n, solver, reverse_sign)

def arbitrary_checking(mode, eof_n):
  import cdutil
  
  reverse_sign = False

  if mode == 'PDO': # Explicitly check average of geographical region for each mode
    if float(cdutil.averager(eof_n(latitude=(30,40),longitude=(150,180)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  elif mode == 'PNA':
    if float(cdutil.averager(eof_n(latitude=(80,90)), axis='xy', weights='weighted')) <= 0:
      reverse_sign = True
  elif mode == 'NAM' or  mode == 'NAO':
    if float(cdutil.averager(eof_n(latitude=(60,80)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  elif mode == 'SAM':
    if float(cdutil.averager(eof_n(latitude=(-60,-90)), axis='xy', weights='weighted')) >= 0:
      reverse_sign = True
  else: # Minimum sign control part was left behind for any future usage..
    if float(eof_n[-1][-1]) is not eof_n.missing:
      if float(eof_n[-1][-1]) >= 0:
        reverse_sign = True
    elif float(eof_n[-2][-2]) is not eof_n.missing:
      if float(eof_n[-2][-2]) >= 0: # Double check in case pole has missing value
        reverse_sign = True

  return reverse_sign

def linear_regression(x,y):
  # input x: 1d timeseries (time)
  #       y: time varying 2d field (time, lat, lon)

  import numpy as np 
  import MV2

  # get original global dimension 
  lat = y.getLatitude()
  lon = y.getLongitude()

  # Convert 3d (time, lat, lon) to 2d (time, lat*lon) for polyfit applying
  im = y.shape[2]
  jm = y.shape[1]
  y_2d = y.reshape(y.shape[0],jm*im)

  # Linear regression
  slope_1d, intercept_1d = np.polyfit(x,y_2d,1)

  # Retreive to cdms variabile from numpy array
  slope = MV2.array(slope_1d.reshape(jm,im))
  intercept = MV2.array(intercept_1d.reshape(jm,im))

  # Set lat/lon coordinates
  slope.setAxis(0,lat); intercept.setAxis(0,lat)
  slope.setAxis(1,lon); intercept.setAxis(1,lon)
  slope.mask = y.mask ; intercept.mask = y.mask

  return(slope, intercept)
 
def gain_pseudo_pcs(solver, field_to_be_projected, eofn, reverse_sign, EofScaling):
  # Given a data set, projects it onto the n-th EOF to generate a corresponding set of pseudo-PCs 
  if not EofScaling:
    pseudo_pcs = solver.projectField(field_to_be_projected, neofs=eofn, eofscaling=0)
  else:
    pseudo_pcs = solver.projectField(field_to_be_projected, neofs=eofn, eofscaling=1)
  
  pseudo_pcs = pseudo_pcs[:,eofn-1]

  # Arbitrary sign control, attempt to make all plots have the same sign ---
  if reverse_sign: 
    pseudo_pcs = MV2.multiply(pseudo_pcs, -1)

  return(pseudo_pcs)

def gain_pcs_fraction(full_field, eof_pattern, pcs):
  # This function is designed for getting fraction of variace obtained by pseudo pcs
  # Input:
  # - full_field (t,y,x)
  # - eof_pattern (y,x)
  # - pcs (t)
  # dimension x, y, t should be identical for above inputs
  
  import genutil, cdutil

  # 1) Get total variacne ---
  variance_total = genutil.statistics.variance(full_field, axis='t')
  variance_total_area_ave = cdutil.averager(variance_total, axis='xy', weights='weighted')

  # 2) Get variance for pseudo pattern ---
  # 2-1) Reconstruct field based on pseudo pattern
  reconstructed_field = genutil.grower(full_field, eof_pattern)[1] # Matching dimension (add time axis)
  for t in range(0,len(pcs)):
    reconstructed_field[t] = MV2.multiply(reconstructed_field[t], pcs[t])
  # 2-2) Get variance of reconstructed field
  variance_partial = genutil.statistics.variance(reconstructed_field, axis='t')
  variance_partial_area_ave = cdutil.averager(variance_partial, axis='xy', weights='weighted')

  # 3) Calculate fraction ---
  fraction = variance_partial_area_ave / variance_total_area_ave

  return(fraction)

def get_anomaly_timeseries(timeseries, mode, season):
  import cdutil
  if season == 'DJF':
    timeseries = timeseries[2:-1,:,:] # Truncate first Jan Feb and last Dec === Assuming input field is monthly, starting at Jan and ending at Dec

  timeseries_ano = cdutil.ANNUALCYCLE.departures(timeseries) # Reomove annual cycle 

  if season not in [ 'monthly', 'yearly']: 
    # Get seasonal mean time series, each season chunk should have 100% of data to get mean
    timeseries_ano = getattr(cdutil,season)(timeseries_ano, criteriaarg=[1.0,None])
  elif season == 'yearly':
    timeseries_ano = cdutil.YEAR(timeseries_ano)
  else:
    pass

  return(timeseries_ano)

def get_residual_timeseries(timeseries_ano, mode, RemoveDomainMean):
  import cdutil 
  import MV2
  # Calculate residual by subtracting domain average (or global mean) ---

  if RemoveDomainMean:
    # Subtract regional mean ---
    regional_ano_mean_timeseries = cdutil.averager(timeseries_ano(regions_specs[mode]['domain']), axis='xy', weights='weighted')
    timeseries_ano, regional_ano_mean_timeseries = \
                                 genutil.grower(timeseries_ano, regional_ano_mean_timeseries) # Match dimension
    timeseries_residual = MV2.subtract(timeseries_ano, regional_ano_mean_timeseries)

  else:
    if mode == 'PDO': 
      # Subtract global mean ---
      global_ano_mean_timeseries = cdutil.averager(timeseries_ano(latitude=(-60,70)), axis='xy', weights='weighted')
      timeseries_ano, global_ano_mean_timeseries = \
                                  genutil.grower(timeseries_ano, global_ano_mean_timeseries) # Match dimension
      timeseries_residual = MV2.subtract(timeseries_ano, global_ano_mean_timeseries)
    else:
      timeseries_residual = timeseries_ano

  return(timeseries_residual)
