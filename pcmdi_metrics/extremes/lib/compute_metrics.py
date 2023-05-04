#!/usr/bin/env python
import xarray as xr
import xcdat
import pandas as pd
import numpy as np
import cftime
import datetime
import sys
import os


class TimeSeriesData():
    # Track years and calendar for time series grids
    # Store methods to act on time series grids
    def __init__(self, ds, ds_var):
        self.ds = ds
        self.ds_var = ds_var
        self.freq = xr.infer_freq(ds.time)
        self._set_years()
        self._set_calendar()
    
    def _set_years(self):
        self.year_beg = self.ds.isel({"time": 0}).time.dt.year.item()
        self.year_end = self.ds.isel({"time": -1}).time.dt.year.item()

        if self.year_end < self.year_beg + 1:
            raise Exception("Error: Final year must be greater than beginning year.")

        self.year_range = np.arange(self.year_beg,self.year_end+1,1)
        
    def _set_calendar(self):
        self.calendar = self.ds.time.encoding["calendar"]

    def return_data_array(self):
        return self.ds[self.ds_var]
        
    def rolling_5day(self):
        # Use on daily data
        return self.ds[self.ds_var].rolling(time=5).mean()

    def daily_total(self):
        # Use on sub-daily data
        return  self.ds[self.ds_var].resample(time='1D').sum(dim="time")
    
    def daily_min(self):
        # Use on sub-daily data
        return  self.ds[self.ds_var].resample(time='1D').min(dim="time")
        #return self.ds[self.ds_var].min(dim="time")
        
    def daily_max(self):
        # Use on sub-daily data
        return self.ds[self.ds_var].resample(time='1D').max(dim="time")
        #return self.ds[self.ds_var].min(dim="time")

class SeasonalAverager():
    # Make seasonal averages of data in TimeSeriesData class

    def __init__(self, ds, dec_mode="DJF", drop_incomplete_djf=True, annual_strict=True):
        self.ds = ds
        self.dec_mode = dec_mode
        self.drop_incomplete_djf = drop_incomplete_djf
        self.annual_strict = annual_strict
        self.del1d = datetime.timedelta(days=1)
        self.del0d = datetime.timedelta(days=0)
        self.pentad = None
        
    def calc_5day_mean(self):
        self.pentad = self.ds.rolling_5day()
        
    def annual_stats(self,stat,pentad=False):

        if pentad == True:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.ds.return_data_array()

        if self.annual_strict:
            # This setting is for means using 5 day rolling average values, where
            # we do not want to include any data from the prior year
            cal = self.ds.calendar
            year_range = self.ds.year_range

            # Only use data from that year - start on Jan 5 avg
            date_range = [xr.cftime_range(
                            start=cftime.datetime(year,1,5,calendar=cal)-self.del0d,
                            end = cftime.datetime(year+1,1,1,calendar=cal)-self.del1d,
                            freq='D',
                            calendar=cal) for year in year_range]
            date_range = [item for sublist in date_range for item in sublist]
            if stat=="max":
                # TODO: Is nearest best method to get data in this day?
                ds_ann = ds.sel(time=date_range,method="nearest").groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_ann = ds.sel(time=date_range,method="nearest").groupby("time.year").min(dim="time")
        else:
            # Group by date
            if stat=="max":
                ds_ann = ds.groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_ann = ds.groupby("time.year").min(dim="time")
        ds_ann = ds_ann.rename({"year": "time"})
        return ds_ann

    def seasonal_stats(self,season,stat,pentad=False):
        # Seasons can be "DJF","MAM","JJA","SON"
        # Stat can be "max", "min"

        year_range = self.ds.year_range

        if pentad == True:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.ds.return_data_array()

        if season == "DJF" and self.dec_mode =="DJF":
            # Resample DJF to count prior DJF in current year
            if stat == "max":
                ds_stat = ds.resample(time='QS-DEC').max(dim="time")
            elif stat=="min":
                ds_stat = ds.resample(time='QS-DEC').min(dim="time")

            ds_stat = ds_stat.isel(time=ds_stat.time.dt.month.isin([12]))
            
            if self.drop_incomplete_djf:
                ds_stat = ds_stat.sel(time=slice(str(year_range[0]),str(year_range[-1]-1)))
                ds_stat["time"] = np.arange(year_range[0]+1,year_range[-1]+1)
            else:
                ds_stat = ds_stat.sel(time=slice(str(year_range[0]-1),str(year_range[-1])))
                ds_stat["time"] = np.arange(year_range[0],year_range[-1]+2)
    
        elif season == "DJF" and self.dec_mode == "JFD":
            cal = self.ds.calendar

            # Make date lists that capture JF and D in all years, then merge and sort
            date_range_1 = [xr.cftime_range(
                                start=cftime.datetime(year,1,1,calendar=cal)-self.del0d,
                                end=cftime.datetime(year,3,1,calendar=cal)-self.del1d,
                                freq='D',
                                calendar=cal) for year in year_range]
            date_range_1 = [item for sublist in date_range_1 for item in sublist]
            date_range_2 = [xr.cftime_range(
                                start=cftime.datetime(year,12,1,calendar=cal)-self.del0d,
                                end=cftime.datetime(year+1,1,1,calendar=cal)-self.del1d,
                                freq='D',
                                calendar=cal) for year in year_range]
            date_range_2 = [item for sublist in date_range_2 for item in sublist]
            date_range = sorted(date_range_1 + date_range_2)
            
            if stat=="max":
                ds_stat = ds.sel(time=date_range,method="nearest").groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_stat = ds.sel(time=date_range,method="nearest").groupby("time.year").min(dim="time")
            ds_stat = ds_stat.rename({"year": "time"})
        
        else:  # Other 3 seasons
            dates = { # Month/day tuples
                "MAM": [(3,1), (6,1)],
                "JJA": [(6,1), (9,1)],
                "SON": [(9,1), (12,1)]
            }
            
            mo_st = dates[season][0][0]
            day_st = dates[season][0][1]
            mo_en = dates[season][1][0]
            day_en = dates[season][1][1]
            
            cal = self.ds.calendar

            date_range = [xr.cftime_range(
                            start=cftime.datetime(year,mo_st,day_st,calendar=cal)-self.del0d,
                            end=cftime.datetime(year,mo_en,day_en,calendar=cal)-self.del1d,
                            freq='D',
                            calendar=cal) for year in year_range]
            date_range = [item for sublist in date_range for item in sublist]
            
            if stat=="max":
                ds_stat = ds.sel(time=date_range,method="nearest").groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_stat = ds.sel(time=date_range,method="nearest").groupby("time.year").min(dim="time")
            ds_stat = ds_stat.rename({"year": "time"})  
            
        return ds_stat

def init_metrics_dict():
    # TODO: Runtime settings like Dec mode should be recorded
    metrics = {
        "DIMENSIONS": {
            "json_structure": ["model","realization","metric","region","season","year"],
            "region": {"land": "Areas where 50<=sftlf<=100"},
            "season": ["ANN","DJF","MAM","JJA","SON"],
            "metric": {},
            "year": [],
            "model": [],
            "realization": []
        },
        "RESULTS": {}
    }
    return metrics


def temperature_metrics(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict):
    TS = TimeSeriesData(ds,varname)

    S = SeasonalAverager(TS,dec_mode=dec_mode,drop_incomplete_djf=drop_incomplete_djf,annual_strict=annual_strict)

    Tmax = xr.Dataset()
    Tmin = xr.Dataset()
    Tmax["ANN"] = S.annual_stats("max")
    Tmin["ANN"] = S.annual_stats("min")

    for season in ["DJF","MAM","JJA","SON"]:
        Tmax[season] = S.seasonal_stats(season,"max")
        Tmin[season] = S.seasonal_stats(season,"min")
    
    Tmax = Tmax.bounds.add_missing_bounds()
    Tmin = Tmin.bounds.add_missing_bounds()

    return Tmax, Tmin

def precipitation_metrics(ds,sftlf,dec_mode,drop_incomplete_djf,annual_strict):

    PR = TimeSeriesData(ds,"pr")

    S = SeasonalAverager(PR,dec_mode=dec_mode,drop_incomplete_djf=drop_incomplete_djf,annual_strict=annual_strict)

    # Rx1day
    P1day = xr.Dataset()
    P1day["ANN"] = S.annual_stats("max",pentad=False)

    for season in ["DJF","MAM","JJA","SON"]:
        P1day[season] = S.seasonal_stats(season,"max",pentad=False)

    P1day = P1day.bounds.add_missing_bounds()    

    # Rx5day
    P5day = xr.Dataset()
    P5day["ANN"] = S.annual_stats("max",pentad=True)

    for season in ["DJF","MAM","JJA","SON"]:
        P5day[season] = S.seasonal_stats(season,"max",pentad=True)

    P5day = P5day.bounds.add_missing_bounds()

    return P1day,P5day

def metrics_json(data_dict,sftlf):
    # Previously temperature metrics json, but it looks like I'm doing the
    # same thing for temperature and precip now.
    met_dict = {}

    for m in data_dict:
        met_dict[m] = {
            "land": {
                "ANN": {},
                "DJF": {},
                "MAM": {},
                "JJA": {},
                "SON": {}
            }
        }
        ds_m = data_dict[m]
        print(ds_m)
        for season in ["ANN","DJF","MAM","JJA","SON"]:
            tmp = ds_m.where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100).spatial.average(season)[season]
            tmp_list = [{int(yr.data): float("% .2f" %tmp.sel({"time":yr}).data)} for yr in tmp.time]
            tmp_dict ={}
            for d in tmp_list:
                tmp_dict.update(d)
            met_dict[m]["land"][season] = tmp_dict
    return met_dict

"""
def precipitation_metrics_json(data_dict,sftlf):
    met_dict = {}

    for m in data_dict:
    met_dict[m] = {"land": {
                        "ANN": [],
                        "DJF": [],
                        "MAM": [],
                        "JJA": [],
                        "SON": []
                    }
                }
        ds_m = data_dict[m]
        for season in ["ANN","DJF","MAM","JJA","SON"]:
            tmp = ds_m.where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100).spatial.average(season)[season] * 86400 # convert to mm
            tmp_list = [{int(yr.data): float("% .2f" %tmp.sel({"time":yr}).data)} for yr in tmp.time]
            tmp_dict ={}
            for d in tmp_list:
                tmp_dict.update(d)
            met_dict["land"][season] = tmp_dict
    return met_dict
"""

def mean_xy(d,varname):
    # Return the area weighted mean as a year: value dictionary
    weights = d.spatial.get_weights(axis=["X","Y"],data_var=varname)
    stat = d[varname].weighted(weights).mean(("lon","lat"))
    res = (dict(zip(d.time.data, stat.data)))
    return res
