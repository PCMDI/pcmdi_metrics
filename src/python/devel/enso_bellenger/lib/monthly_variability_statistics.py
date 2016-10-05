def interannual_variabilty_std_annual_cycle_removed(d):
   import cdutil, genutil
   d_area_avg = cdutil.averager(d,axis='xy')
   d_area_avg_anom = cdutil.ANNUALCYCLE.departures(d_area_avg)
   d_area_avg_anom_sd = genutil.statistics.std(d_area_avg_anom)
   return(float(d_area_avg_anom_sd))

def interannual_variability_seasonal_std_mean_removed(d,season_string):
   import cdutil, genutil
   d_area_avg = cdutil.averager(d,axis='xy')
   pre_defined_seasons = ['DJF', 'MAM', 'JJA', 'SON', 'YEAR']
   if season_string in pre_defined_seasons:
     d_area_avg_anom=getattr(cdutil,season_string).departures(d_area_avg)
   else:
     CustomSeason = cdutil.times.Seasons(season_string)
     d_area_avg_anom = CustomSeason.departures(d_area_avg)
   d_area_avg_anom_sd = genutil.statistics.std(d_area_avg_anom)
   return(float(d_area_avg_anom_sd))

def get_slope_linear_regression(y,x):
   import cdutil, genutil
   results = genutil.statistics.linearregression(y,x=x)
   slope, intercept = results
   return(float(slope))

def get_slope_linear_regression_from_anomaly(y,x):
   import cdutil, genutil
   y_area_avg = cdutil.averager(y,axis='xy')
   x_area_avg = cdutil.averager(x,axis='xy')
   x_area_avg_anom = cdutil.ANNUALCYCLE.departures(x_area_avg)
   y_area_avg_anom = cdutil.ANNUALCYCLE.departures(y_area_avg)
   results = genutil.statistics.linearregression(y_area_avg_anom,x=x_area_avg_anom)
   slope, intercept = results
   return(float(slope))

def get_area_avg_annual_cycle_removed(d):
   import cdutil
   d_area_avg = cdutil.averager(d,axis='xy')
   d_area_avg_anom = cdutil.ANNUALCYCLE.departures(d_area_avg)
   return(d_area_avg_anom)

def get_axis_base_dataset(var, reg, path): # to be called from Atm Feedback driver
   f = cdms.open(path)
   if debug:
     reg_timeseries = f(var, regions_specs[reg]['domain'], time = slice(0,60)) # RUN CODE FAST ON 5 YEARS OF DATA
   else:
     reg_timeseries = f(var, regions_specs[reg]['domain'])
   # Get area averaged and annual cycle removed 1-D time series
   reg_timeseries_area_avg_anom = get_area_avg_annual_cycle_removed(reg_timeseries)
   return(reg_timeseries_area_avg_anom)
   f.close()
