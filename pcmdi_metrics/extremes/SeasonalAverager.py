class SeasonalAverager():
    def __init__(self, ds, ds_var, dec_mode="DJF", drop_incomplete_djf=True, annual_strict=True):
        self.ds = ds
        self._set_years()
        self._set_calendar()
        self.dec_mode = dec_mode
        self.drop_incomplete_djf = drop_incomplete_djf
        self.annual_strict = annual_strict
        self.del_one_d = datetime.timedelta(days=1)
        self.del_zero_d = datetime.timedelta(days=0)
        self.ds_var = ds_var
    
    def _set_years(self):
        self.year_beg = self.ds.isel({"time": 0}).time.dt.year.item()
        self.year_end = self.ds.isel({"time": -1}).time.dt.year.item()

        if year_end < year_beg + 1:
            print("Error: Final year must be greater than beginning year.")
            sys.exit(1)

        self.year_range = np.arange(year_beg,year_end+1,1)
        
    def _set_calendar(self):
        self.calendar = self.ds.time.encoding["calendar"]
        
    def rolling(self):
        # Use on daily data
        return self.ds[self.ds_var].rolling(time=5).mean()
    
    def daily_total(self):
        # Use on sub-daily data
        return  self.ds.resample(time='1D').sum(dim="time")
    
    def daily_min(self):
        # Use on sub-daily data
        return  self.ds.resample(time='1D').min(dim="time")
        
    def daily_max(self):
        # Use on sub-daily data
        return self.ds.resample(time='1D').max(dim="time")
        
    def annual_stats(self,ds1,stat):
        if self.annual_strict:
            # Only use data from that year - start on Jan 5 avg
            date_range = [xr.cftime_range(
                            start=cftime.datetime(year,1,5,calendar=self.calendar)-self.del_zero_d,
                            end = cftime.datetime(year+1,1,1,calendar=self.calendar)-self.del_one_d,
                            freq='D',
                            calendar=self.calendar) for year in self.year_range]
            date_range = [item for sublist in date_range for item in sublist]
            if stat=="max":
                ds_ann = ds1.sel(time=date_range).groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_ann = ds1.sel(time=date_range).groupby("time.year").min(dim="time")
        else:
            # Mean can include rolling data from past year
            if stat=="max":
                ds_ann = ds1.groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_ann = ds1.groupby("time.year").min(dim="time")
            ds_ann = ds_ann.rename({"year": "time"})
        return ds_ann

    def seasonal_stats(self,ds1,season,stat):
        # Seasons can be "DJF","MAM","JJA","SON"
        # Stat can be "max", "min"

        if season == "DJF" and self.dec_mode =="DJF":
            # Resample DJF to count prior DJF in current year
            if stat == "max":
                ds_stat = ds.resample(time='QS-DEC').max(dim="time")
            elif stat=="min":
                ds_stat = ds.resample(time='QS-DEC').min(dim="time")

            ds_stat = ds_stat.isel(time=ds_stat.time.dt.month.isin([12]))
            
            if self.drop_incomplete_djf:
                ds_stat = ds_stat.sel(time=slice(str(self.year_beg),str(self.year_end-1)))
                ds_stat["time"] = np.arange(self.year_beg+1,self.year_end+1)
            else:
                ds_stat = ds_stat.sel(time=slice(str(self.year_beg-1),str(self.year_end)))
                ds_stat["time"] = np.arange(self.year_beg,self.year_end+2)
    
        elif season == "DJF" and self.dec_mode == "JFD":
            # Make date lists that capture JF and D in all years, then merge and sort
            date_range_1 = [xr.cftime_range(
                                start=cftime.datetime(year,1,1,calendar=self.calendar)-self.del_zero_d,
                                end=cftime.datetime(year,3,1,calendar=self.calendar)-self.del_one_d,
                                freq='D',
                                calendar=cal) for year in self.year_range]
            date_range_1 = [item for sublist in date_range_1 for item in sublist]
            date_range_2 = [xr.cftime_range(
                                start=cftime.datetime(year,12,1,calendar=self.calendar)-self.del_zero_d,
                                end=cftime.datetime(year+1,1,1,calendar=self.calendar)-self.del_one_d,
                                freq='D',
                                calendar=cal) for year in self.year_range]
            date_range_2 = [item for sublist in date_range_2 for item in sublist]
            date_range = sorted(date_range_1 + date_range_2)
            
            if stat=="max":
                ds_stat = ds.sel(time=date_range).groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_stat = ds.sel(time=date_range).groupby("time.year").min(dim="time")
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
            
            date_range = [xr.cftime_range(
                            start=cftime.datetime(year,mo_st,day_st,calendar=self.calendar)-self.del_zero_d,
                            end=cftime.datetime(year,mo_en,day_en,calendar=self.calendar)-self.del_one_d,
                            freq='D',
                            calendar=self.calendar) for year in self.year_range]
            date_range = [item for sublist in date_range for item in sublist]
            
            if stat=="max":
                ds_stat = ds.sel(time=date_range).groupby("time.year").max(dim="time")
            elif stat=="min":
                ds_stat = ds.sel(time=date_range).groupby("time.year").min(dim="time")
            ds_stat = ds_stat.rename({"year": "time"})  
            
        return ds_stat