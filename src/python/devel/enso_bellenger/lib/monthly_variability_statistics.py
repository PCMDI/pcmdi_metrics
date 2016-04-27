def interannual_variabilty_std_annual_cycle_removed(d):
   import cdutil, MV2 
   d_area_avg = cdutil.averager(d,axis='xy')
   d_area_avg_anom = cdutil.ANNUALCYCLE.departures(d_area_avg)
   d_area_avg_anom_sd = genutil.statistics.std(d_area_avg_anom)
   return(float(d_area_avg_anom_sd))

def interannual_variability_seasonal_std_mean_removed(d,season_string):
   import cdutil, MV2 
   d_area_avg = cdutil.averager(d,axis='xy')
   ## If season is NOT pre-defined...
   #if season_string == 'NDJ':
   #  NDJ = cdutil.times.Seasons('NDJ')
   #  d_area_avg_anom = NDJ.departures(d_area_avg)
   # If season is pre-defined...
   ##if season_string == 'MAM':
   #  #d_area_avg_anom = cdutil.MAM.departures(d_area_avg)
   #  d_area_avg_anom=getattr(cdutil,season_string).departures(d_area_avg)
   pre_defined_seasons = ['DJF', 'MAM', 'JJA', 'SON', 'YEAR']
   if season_string in pre_defined_seasons:
     d_area_avg_anom=getattr(cdutil,season_string).departures(d_area_avg)
   else:
     CustomSeason = cdutil.times.Seasons(season_string)
     d_area_avg_anom = CustomSeason.departures(d_area_avg)
   d_area_avg_anom_sd = genutil.statistics.std(d_area_avg_anom)
   return(float(d_area_avg_anom_sd))
