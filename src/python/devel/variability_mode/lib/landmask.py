def model_land_mask_out(mip,model,model_timeseries):
  import genutil
  import numpy as NP
  import MV2
  #-------------------------------------------------
  # Extract SST (mask out land region)
  #- - - - - - - - - - - - - - - - - - - - - - - - -
  # Read model's land fraction
  #model_lf_path = get_latest_pcmdi_mip_lf_data_path(mip,model,'sftlf')
  #model_lf_path = '/work/cmip5/fx/fx/sftlf/cmip5.'+model+'.historical.r0i0p0.fx.atm.fx.sftlf.ver-1.latestX.xml'

  if model == 'CESM1-CAM5' or model == 'CESM1-BGC':
    model_lf_path = '/work/lee1043/ESGF/CMIP5/CESM1-CAM5/cmip5.CESM1-CAM5.historical.r0i0p0.fx.atm.fx.sftlf.ver-v20120614.latestX.xml'
  if model == 'FIO-ESM':
    model_lf_path = get_latest_pcmdi_mip_lf_data_path(mip,'fio-esm','sftlf')
  else:
    model_lf_path = get_latest_pcmdi_mip_lf_data_path(mip,model,'sftlf')
    #model_lf_path = '/work/cmip5/fx/fx/sftlf/cmip5.'+model+'.historical.r0i0p0.fx.atm.fx.sftlf.ver-1.latestX.xml'


  f_lf = cdms.open(model_lf_path)
  lf = f_lf('sftlf', latitude=(-90,90))

  # Check land fraction variable to see if it meets criteria (0 for ocean, 100 for land, no missing value)
  #lf[ lf == lf.missing_value ] = 0
  lat = lf.getAxis(0) 
  lon = lf.getAxis(1)
  lf_id = lf.id

  lf = MV2.array(lf.filled(0.))

  lf.setAxis(0, lat)
  lf.setAxis(1, lon)
  lf.id = lf_id

  if NP.max(lf) == 1.:
    lf = lf * 100

  # Matching dimension
  model_timeseries, lf_timeConst = genutil.grower(model_timeseries, lf)

  #opt1 = True
  opt1 = False

  if opt1: # Masking out partial land grids as well
    model_timeseries_masked = NP.ma.masked_where(lf_timeConst>0, model_timeseries) # mask out land even fractional (leave only pure ocean grid)
  else: # Masking out only full land grid but use weighting for partial land grids
    model_timeseries_masked = NP.ma.masked_where(lf_timeConst==100, model_timeseries) # mask out pure land grids
    if model == 'EC-EARTH':
      model_timeseries_masked = NP.ma.masked_where(lf_timeConst>=90, model_timeseries) # mask out over 90% land grids for models those consider river as part of land-sea fraction. So far only 'EC-EARTH' does..
    lf2 = (100.-lf)/100.
    model_timeseries,lf2_timeConst = genutil.grower(model_timeseries,lf2) # Matching dimension
    model_timeseries_masked = model_timeseries_masked * lf2_timeConst # consider land fraction like as weighting

  # Retrive dimension coordinate ---

  time = model_timeseries.getTime()
  lat = model_timeseries.getLatitude()
  lon = model_timeseries.getLongitude()

  model_timeseries_masked.setAxis(0,time)
  model_timeseries_masked.setAxis(1,lat)
  model_timeseries_masked.setAxis(2,lon)

  model_timeseries = model_timeseries_masked

  return(model_timeseries)
