#!/usr/bin/env python
import xarray as xr
import xcdat
import pandas as pd
import numpy as np
import cftime
import datetime
import sys
import os
import math

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
        # Get the 5-day mean dataset
        self.pentad = self.ds.rolling_5day()
        
    def annual_stats(self,stat,pentad=False):
        # Acquire annual statistics
        # Arguments:
        #     stat: Can be "max", "min"
        #     pentad: True to run on 5-day mean
        # Returns:
        #     ds_ann: Dataset containing annual max or min grid

        if pentad == True:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.ds.return_data_array()
        cal = self.ds.calendar

        if self.annual_strict:
            # This setting is for means using 5 day rolling average values, where
            # we do not want to include any data from the prior year
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
        
        # Need to fix time axis if groupby operation happened
        if "year" in ds_ann.coords:
            ds_ann = ds_ann.rename({"year": "time"})
            y_to_cft = [cftime.datetime(y,1,1,calendar=cal) for y in ds_ann.time]
            ds_ann["time"] = y_to_cft
            ds_ann.time.attrs["axis"] = "T"
            ds_ann['time'].encoding['calendar'] = cal
            ds_ann['time'].attrs['standard_name'] = 'time'
            ds_ann.time.encoding['units'] = "days since 0000-01-01"
        return ds_ann

    def seasonal_stats(self,season,stat,pentad=False):
        # Acquire statistics for a given season
        # Arguments:
        #     season: Can be "DJF","MAM","JJA","SON"
        #     stat: Can be "max", "min"
        #     pentad: True to run on 5-day mean
        # Returns:
        #     ds_stat: Dataset containing seasonal max or min grid

        year_range = self.ds.year_range

        if pentad == True:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.ds.return_data_array()
        cal = self.ds.calendar

        if season == "DJF" and self.dec_mode =="DJF":
            # Resample DJF to count prior DJF in current year
            if stat == "max":
                ds_stat = ds.resample(time='QS-DEC').max(dim="time")
            elif stat=="min":
                ds_stat = ds.resample(time='QS-DEC').min(dim="time")

            ds_stat = ds_stat.isel(time=ds_stat.time.dt.month.isin([12]))
            
            if self.drop_incomplete_djf:
                ds_stat = ds_stat.sel(time=slice(str(year_range[0]),str(year_range[-1]-1)))
                #ds_stat["time"] = np.arange(year_range[0]+1,year_range[-1]+1)
                ds_stat["time"] = [cftime.datetime(y,1,1,calendar=cal) for y in np.arange(year_range[0]+1,year_range[-1]+1)]
            else:
                ds_stat = ds_stat.sel(time=slice(str(year_range[0]-1),str(year_range[-1])))
                #ds_stat["time"] = np.arange(year_range[0],year_range[-1]+2)
                ds_stat["time"] = [cftime.datetime(y,1,1,calendar=cal) for y in np.arange(year_range[0],year_range[-1]+2)]
    
        elif season == "DJF" and self.dec_mode == "JFD":

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

        # Need to fix time axis if groupby operation happened
        if "year" in ds_stat.coords:
            ds_stat = ds_stat.rename({"year": "time"})
            
            y_to_cft = [cftime.datetime(y,1,1,calendar=cal) for y in ds_stat.time]
            ds_stat["time"] = y_to_cft
            ds_stat.time.attrs["axis"] = "T"
            ds_stat['time'].encoding['calendar'] = cal
            ds_stat['time'].attrs['standard_name'] = 'time'
            ds_stat.time.encoding['units'] = "days since 0000-01-01"
            
        return ds_stat

def init_metrics_dict(dec_mode,drop_incomplete_djf,annual_strict):
    # Return initial version of the metrics dictionary
    metrics = {
        "DIMENSIONS": {
            "json_structure": ["model","realization","region","metric","season"],
            "region": {"land": "Areas where 50<=sftlf<=100"},
            "season": ["ANN","DJF","MAM","JJA","SON"],
            "index": {        
                "Rx5day": "Maximum consecutive 5-day mean precipitation",
                "Rx1day": "Maximum daily precipitation",
                "TXx": "Maximum value of daily maximum temperature",
                "TXn": "Minimum value of daily maximum temperature",
                "TNx": "Maximum value of daily minimum temperature",
                "TNn": "Minimum value of daily minimum temperature",},
            "model": [],
            "realization": []
        },
        "RESULTS": {},
        "PROVENANCE": {
            "Settings": {
                "december_mode": str(dec_mode),
                "drop_incomplete_djf": str(drop_incomplete_djf),
                "annual_strict": str(annual_strict)
            }
        }
    }

    return metrics


def temperature_metrics(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict):
    # Returns annual max and min of provided temperature dataset
    # Temperature input can be "tasmax" or "tasmin".

    print("Generating temperature block extrema.")

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
    Tmax.attrs["december_mode"] = str(dec_mode)
    Tmax.attrs["drop_incomplete_djf"] = str(drop_incomplete_djf)
    Tmax.attrs["annual_strict"] = str(annual_strict)
    Tmin.attrs["december_mode"] = str(dec_mode)
    Tmin.attrs["drop_incomplete_djf"] = str(drop_incomplete_djf)
    Tmin.attrs["annual_strict"] = str(annual_strict)

    return Tmax, Tmin

def precipitation_metrics(ds,sftlf,dec_mode,drop_incomplete_djf,annual_strict):
    # Returns annual Rx1day and Rx5day of provided precipitation dataset.
    # Precipitation variable must be called "pr".

    print("Generating precipitation block extrema.")

    ds["pr"] = ds["pr"] * 86400
    ds["pr"].attrs["units"] = "mm day-1"

    PR = TimeSeriesData(ds,"pr")

    S = SeasonalAverager(PR,dec_mode=dec_mode,drop_incomplete_djf=drop_incomplete_djf,annual_strict=annual_strict)

    # Rx1day
    P1day = xr.Dataset()
    P1day["ANN"] = S.annual_stats("max",pentad=False)

    for season in ["DJF","MAM","JJA","SON"]:
        P1day[season] = S.seasonal_stats(season,"max",pentad=False)

    P1day = P1day.bounds.add_missing_bounds() 
    P1day.attrs["december_mode"] = str(dec_mode)
    P1day.attrs["drop_incomplete_djf"] = str(drop_incomplete_djf)
    P1day.attrs["annual_strict"] = str(annual_strict)

    # Rx5day
    P5day = xr.Dataset()
    P5day["ANN"] = S.annual_stats("max",pentad=True)

    for season in ["DJF","MAM","JJA","SON"]:
        P5day[season] = S.seasonal_stats(season,"max",pentad=True)

    P5day = P5day.bounds.add_missing_bounds()
    P5day.attrs["december_mode"] = str(dec_mode)
    P5day.attrs["drop_incomplete_djf"] = str(drop_incomplete_djf)
    P5day.attrs["annual_strict"] = str(annual_strict)

    return P1day,P5day

def metrics_json(data_dict,sftlf,obs_dict={}):
    # Format, calculate, and return the global mean value over land
    # for all datasets in the input dictionary
    # Arguments:
    #   data_dict: Dictionary containing block extrema datasets
    #   sftlf: Land sea mask
    # Returns:
    #   met_dict: A dictionary containing metrics
    met_dict = {}

    for m in data_dict:
        met_dict[m] = {
            "land": {
                "mean":{
                    "ANN": "",
                    "DJF": "",
                    "MAM": "",
                    "JJA": "",
                    "SON": ""
                }
            }
        }

    # If obs available, add metrics comparing with obs
        if len(obs_dict) > 0:
            met_dict[m]["land"]["rmse_error"] = {
                "ANN": "",
                "DJF": "",
                "MAM": "",
                "JJA": "",
                "SON": ""
            }

        ds_m = data_dict[m]
        for season in ["ANN","DJF","MAM","JJA","SON"]:

            # Global mean over land
            seas_mean = ds_m.where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100).spatial.average(season)[season].mean()
            met_dict[m]["land"]["mean"][season] = float(seas_mean)

            if len(obs_dict) > 0:
                # RMSE Error between reference and model
                #dif_square = (
                #            ds_m.where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100).temporal.average(season)[season] - 
                #            obs_dict[m].where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100).temporal.average(season)[season]) ** 2
                #weights = ds_m.spatial.get_weights(axis=['X', 'Y'])
                #stat = float(math.sqrt(dif_square.weighted(weights).mean(("lon", "lat"))))
                #met_dict[m]["land"]["rmse_error"][season] = stat
                a = ds_m.temporal.average(season)[season].where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100)
                b = obs_dict[m].temporal.average(season)[season].where(sftlf.sftlf >= 50).where(sftlf.sftlf <= 100)
                dif_square = (a - b) ** 2
                #print(a.shape,b.shape)
                #print(dif_square)
                weights = ds_m.spatial.get_weights(axis=['X', 'Y'])
                stat = math.sqrt(dif_square.weighted(weights).mean(("lon", "lat")))
                met_dict[m]["land"]["rmse_error"][season] = stat
                #print(stat)
                #print(a.shape,b.shape)

    return met_dict

