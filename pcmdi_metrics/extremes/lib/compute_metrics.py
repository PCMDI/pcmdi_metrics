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

from pcmdi_metrics.mean_climate.lib import compute_statistics

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

    def __init__(self, TS, sftlf, dec_mode="DJF", drop_incomplete_djf=True, annual_strict=True):
        self.TS = TS
        self.dec_mode = dec_mode
        self.drop_incomplete_djf = drop_incomplete_djf
        self.annual_strict = annual_strict
        self.del1d = datetime.timedelta(days=1)
        self.del0d = datetime.timedelta(days=0)
        self.pentad = None
        self.sftlf = sftlf["sftlf"]

    def masked_ds(self,ds):
        # Mask land where 50<=sftlf<=100
        return ds.where(self.sftlf>=50).where(self.sftlf<=100)
        
    def calc_5day_mean(self):
        # Get the 5-day mean dataset
        self.pentad = self.TS.rolling_5day()

    def fix_time_coord(self,ds,cal):
        ds = ds.rename({"year": "time"})
        y_to_cft = [cftime.datetime(y,1,1,calendar=cal) for y in ds.time]
        ds["time"] = y_to_cft
        ds.time.attrs["axis"] = "T"
        ds['time'].encoding['calendar'] = cal
        ds['time'].attrs['standard_name'] = 'time'
        ds.time.encoding['units'] = "days since 0000-01-01"
        return ds
        
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
            ds = self.TS.return_data_array()
        cal = self.TS.calendar

        if self.annual_strict and pentad:
            # This setting is for means using 5 day rolling average values, where
            # we do not want to include any data from the prior year
            year_range = self.TS.year_range
            hr = int(ds.time[0].dt.hour) # help with selecting nearest time

            # Only use data from that year - start on Jan 5 avg
            date_range = [xr.cftime_range(
                            start=cftime.datetime(year,1,5,hour=hr,calendar=cal)-self.del0d,
                            end = cftime.datetime(year+1,1,1,hour=hr,calendar=cal)-self.del1d,
                            freq='D',
                            calendar=cal) for year in year_range]
            date_range = [item for sublist in date_range for item in sublist]
            if stat=="max":
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
            ds_ann = self.fix_time_coord(ds_ann,cal)
        return self.masked_ds(ds_ann)

    def seasonal_stats(self,season,stat,pentad=False):
        # Acquire statistics for a given season
        # Arguments:
        #     season: Can be "DJF","MAM","JJA","SON"
        #     stat: Can be "max", "min"
        #     pentad: True to run on 5-day mean
        # Returns:
        #     ds_stat: Dataset containing seasonal max or min grid

        year_range = self.TS.year_range

        if pentad == True:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.TS.return_data_array()
        cal = self.TS.calendar

        hr = int(ds.time[0].dt.hour) # help with selecting nearest time

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
                                start=cftime.datetime(year,1,1,hour=hr,calendar=cal)-self.del0d,
                                end=cftime.datetime(year,3,1,hour=hr,calendar=cal)-self.del1d,
                                freq='D',
                                calendar=cal) for year in year_range]
            date_range_1 = [item for sublist in date_range_1 for item in sublist]
            date_range_2 = [xr.cftime_range(
                                start=cftime.datetime(year,12,1,hour=hr,calendar=cal)-self.del0d,
                                end=cftime.datetime(year+1,1,1,hour=hr,calendar=cal)-self.del1d,
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
            
            cal = self.TS.calendar

            date_range = [xr.cftime_range(
                            start=cftime.datetime(year,mo_st,day_st,hour=hr,calendar=cal)-self.del0d,
                            end=cftime.datetime(year,mo_en,day_en,hour=hr,calendar=cal)-self.del1d,
                            freq='D',
                            calendar=cal) for year in year_range]
            date_range = [item for sublist in date_range for item in sublist]
            
            if stat=="max":
                ds_stat = ds.sel(time=date_range,method="nearest").groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_stat = ds.sel(time=date_range,method="nearest").groupby("time.year").min(dim="time")

        # Need to fix time axis if groupby operation happened
        if "year" in ds_stat.coords:
            ds_stat = self.fix_time_coord(ds_stat,cal)
        return self.masked_ds(ds_stat)

def update_nc_attrs(ds,dec_mode,drop_incomplete_djf,annual_strict):
    # Add bounds and record user settings in attributes
    # Use this function for any general dataset updates.
    ds = ds.bounds.add_missing_bounds() 
    ds.attrs["december_mode"] = str(dec_mode)
    ds.attrs["drop_incomplete_djf"] = str(drop_incomplete_djf)
    ds.attrs["annual_strict"] = str(annual_strict)
    return ds

def temperature_indices(ds,varname,sftlf,dec_mode,drop_incomplete_djf,annual_strict):
    # Returns annual max and min of provided temperature dataset
    # Temperature input can be "tasmax" or "tasmin".

    print("Generating temperature block extrema.")

    TS = TimeSeriesData(ds,varname)
    S = SeasonalAverager(TS,sftlf,dec_mode=dec_mode,drop_incomplete_djf=drop_incomplete_djf,annual_strict=annual_strict)

    Tmax = xr.Dataset()
    Tmin = xr.Dataset()
    Tmax["ANN"] = S.annual_stats("max")
    Tmin["ANN"] = S.annual_stats("min")

    for season in ["DJF","MAM","JJA","SON"]:
        Tmax[season] = S.seasonal_stats(season,"max")
        Tmin[season] = S.seasonal_stats(season,"min")
    
    Tmax = update_nc_attrs(Tmax,dec_mode,drop_incomplete_djf,annual_strict)
    Tmin = update_nc_attrs(Tmin,dec_mode,drop_incomplete_djf,annual_strict)

    return Tmax, Tmin

def precipitation_indices(ds,sftlf,dec_mode,drop_incomplete_djf,annual_strict):
    # Returns annual Rx1day and Rx5day of provided precipitation dataset.
    # Precipitation variable must be called "pr".
    # Input data expected to have units of kg/m2/s

    print("Generating precipitation block extrema.")

    ds["pr"] = ds["pr"] * 86400
    ds["pr"].attrs["units"] = "mm day-1"

    PR = TimeSeriesData(ds,"pr")
    S = SeasonalAverager(PR,sftlf,dec_mode=dec_mode,drop_incomplete_djf=drop_incomplete_djf,annual_strict=annual_strict)

    # Rx1day
    P1day = xr.Dataset()
    P1day["ANN"] = S.annual_stats("max",pentad=False)
    for season in ["DJF","MAM","JJA","SON"]:
        P1day[season] = S.seasonal_stats(season,"max",pentad=False)
    P1day = update_nc_attrs(P1day,dec_mode,drop_incomplete_djf,annual_strict)

    # Rx5day
    P5day = xr.Dataset()
    P5day["ANN"] = S.annual_stats("max",pentad=True)
    for season in ["DJF","MAM","JJA","SON"]:
        P5day[season] = S.seasonal_stats(season,"max",pentad=True)
    P5day = update_nc_attrs(P5day,dec_mode,drop_incomplete_djf,annual_strict)

    return P1day,P5day

def init_metrics_dict(model_list,dec_mode,drop_incomplete_djf,annual_strict,region_name):
    # Return initial version of the metrics dictionary
    metrics = {
        "DIMENSIONS": {
            "json_structure": ["model","realization","region","index","season","statistic"],
            "region": {region_name: "Areas where 50<=sftlf<=100"},
            "season": ["ANN","DJF","MAM","JJA","SON"],
            "index": {        
                "Rx5day": "Maximum consecutive 5-day mean precipitation, mm/day",
                "Rx1day": "Maximum daily precipitation, mm/day",
                "TXx": "Maximum value of daily maximum temperature",
                "TXn": "Minimum value of daily maximum temperature",
                "TNx": "Maximum value of daily minimum temperature",
                "TNn": "Minimum value of daily minimum temperature",},
            "statistic": {
                "mean": compute_statistics.mean_xy(None),
                "std_xy": compute_statistics.std_xy(None,None),
                "bias_xy": compute_statistics.bias_xy(None,None),
                "cor_xy": compute_statistics.cor_xy(None,None),
                "mae_xy": compute_statistics.meanabs_xy(None,None),
                "rms_xy": compute_statistics.rms_xy(None,None),
                "rmsc_xy": compute_statistics.rmsc_xy(None,None),
                "pct_dif": {
                    "Abstract": "Bias xy as a percentage of the Observed mean.",
                    "Contact": "pcmdi-metrics@llnl.gov",
                    "Name": "Spatial Difference Percentage"}
                },
            "model": model_list,
            "realization": []
        },
        "RESULTS": {},
        "RUNTIME_CALENDAR_SETTINGS": {
            "december_mode": str(dec_mode),
            "drop_incomplete_djf": str(drop_incomplete_djf),
            "annual_strict": str(annual_strict)
        }
    }

    return metrics

def metrics_json(data_dict,sftlf,obs_dict={},region="land",regrid=True):
    # Format, calculate, and return the global mean value over land
    # for all datasets in the input dictionary
    # Arguments:
    #   data_dict: Dictionary containing block extrema datasets
    #   sftlf: Land sea mask
    #   obs_dict: Dictionary containing block extrema for 
    #             reference dataset
    #   region: Name of region.
    # Returns:
    #   met_dict: A dictionary containing metrics

    met_dict = {}
    seasons_dict = {
                "ANN": "",
                "DJF": "",
                "MAM": "",
                "JJA": "",
                "SON": ""
            }

    # Looping over each type of extrema in data_dict
    for m in data_dict:
        met_dict[m] = {
            region: {
                "mean": seasons_dict.copy(),
                "std_xy": seasons_dict.copy()
            }
        }
        # If obs available, add metrics comparing with obs
        # If new statistics are added, be sure to update
        # "statistic" entry in init_metrics_dict()
        if len(obs_dict) > 0:
            for k in ["difference","percent_difference","bias_xy","cor_xy","mae_xy","rms_xy","rmsc_xy"]:
                met_dict[m][region][k] = seasons_dict.copy()

        ds_m = data_dict[m]
        for season in ["ANN","DJF","MAM","JJA","SON"]:
            # Global mean over land
            seas_mean = ds_m.spatial.average(season)[season].mean()
            met_dict[m][region]["mean"][season] = float(seas_mean)
            a = ds_m.temporal.average(season)
            std_xy = compute_statistics.std_xy(a, season)
            met_dict[m][region]["std_xy"][season] = std_xy

            if len(obs_dict) > 0 and not obs_dict[m].equals(ds_m):
                # Regrid obs to model grid
                if regrid:
                    obs_m = obs_dict[m].regridder.horizontal(season, ds_m, tool='regrid2')
                else:
                    obs_m = obs_dict[m]
                    shp1 = (len(ds_m[season].lat),len(ds_m[season].lon))
                    shp2 = (len(obs_m[season].lat),len(obs_m[season].lon))
                    assert shp1 == shp2, "Model and Reference data dimensions 'lat' and 'lon' must match."
                    

                # Get xy stats for temporal average
                a = ds_m.temporal.average(season)
                b = obs_m.temporal.average(season)
                weights = ds_m.spatial.get_weights(axis=['X', 'Y'])
                #dif = float((a - b).spatial.average(season, axis=['X', 'Y'],weights=weights)[season])
                rms_xy = compute_statistics.rms_xy(a, b, var=season, weights=weights)
                meanabs_xy = compute_statistics.meanabs_xy(a, b, var=season, weights=weights)
                bias_xy = compute_statistics.bias_xy(a, b, var=season, weights=weights)
                cor_xy = compute_statistics.cor_xy(a, b, var=season, weights=weights)
                rmsc_xy = compute_statistics.rmsc_xy(a, b, var=season, weights=weights)
                percent_difference=float(100.*bias_xy/b.spatial.average(season,axis=['X','Y'],weights=weights)[season])

                met_dict[m][region]["pct_dif"][season] = percent_difference
                met_dict[m][region]["rms_xy"][season] = rms_xy
                met_dict[m][region]["mae_xy"][season] = meanabs_xy
                met_dict[m][region]["bias_xy"][season] = bias_xy
                met_dict[m][region]["cor_xy"][season] = cor_xy
                met_dict[m][region]["rmsc_xy"][season] = rmsc_xy

    return met_dict

