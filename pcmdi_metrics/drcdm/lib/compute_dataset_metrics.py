# flake8: noqa
import datetime
import operator
from itertools import groupby

import cftime
import dask
import matplotlib.pyplot as plt
import numpy as np
import pint_xarray
import xarray as xr
import xcdat as xc
import xclim
from pint import Unit, UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

from pcmdi_metrics.io.xcdat_dataset_io import get_latitude_key, get_longitude_key
from pcmdi_metrics.stats import compute_statistics_dataset as pmp_stats

bgclr = [0.45, 0.45, 0.45]


class TimeSeriesData:
    # Track years and calendar for time series grids
    # Store methods to act on time series grids
    def __init__(self, ds, ds_var):
        self.ds = ds
        self.ds_var = ds_var
        self.freq = xr.infer_freq(ds.time)
        self._set_years()
        self.calendar = ds.time.encoding["calendar"]
        self.time_units = ds.time.encoding["units"]

    def _set_years(self):
        self.year_beg = self.ds.isel({"time": 0}).time.dt.year.item()
        self.year_end = self.ds.isel({"time": -1}).time.dt.year.item()

        if self.year_end < self.year_beg + 1:  # if self.year_end < self.year_beg + 1:
            raise Exception("Error: Final year must be greater than beginning year.")

        self.year_range = np.arange(self.year_beg, self.year_end + 1, 1)

    def return_data_array(self):
        return self.ds[self.ds_var]

    def rolling_5day(self):
        # Use on daily data
        return self.ds[self.ds_var].rolling(time=5).mean()

    def rolling_nday(self, n):
        return self.ds[self.ds_var].rolling(time=n).mean()

    # def rolling_5day_sum(self):
    #     return self.ds[self.ds_var].rolling(time=5).sum()


class SeasonalAverager:
    # Make seasonal averages of data in TimeSeriesData class

    def __init__(
        self,
        TSD,
        sftlf,
        dec_mode="DJF",
        drop_incomplete_djf=True,
        annual_strict=True,
    ):
        self.TSD = TSD
        self.dec_mode = dec_mode
        self.drop_incomplete_djf = drop_incomplete_djf
        self.annual_strict = annual_strict
        self.del1d = datetime.timedelta(days=1)
        self.del0d = datetime.timedelta(days=0)
        self.pentad = None
        self.nTuple = None
        self.sftlf = sftlf["sftlf"]
        self.month_lookup = {
            1: "JAN",
            2: "FEB",
            3: "MAR",
            4: "APR",
            5: "MAY",
            6: "JUNE",
            7: "JULY",
            8: "AUG",
            9: "SEP",
            10: "OCT",
            11: "NOV",
            12: "DEC",
        }

    def masked_ds(self, ds):
        # Mask land where 0.5<=sftlf<=1
        return ds.where(self.sftlf >= 0.5).where(self.sftlf <= 1)
        return ds

    def calc_5day_mean(self):
        # Get the 5-day mean dataset
        self.pentad = self.TSD.rolling_5day()

    def calc_nday_mean(self, n):
        self.nTuple = self.TSD.rolling_nday(n)

    def fix_time_coord(self, ds):
        cal = self.TSD.calendar
        ds = ds.rename({"year": "time"})
        y_to_cft = [cftime.datetime(y, 1, 1, calendar=cal) for y in ds.time]
        ds["time"] = y_to_cft
        ds.time.attrs["axis"] = "T"
        ds["time"].encoding["calendar"] = cal
        ds["time"].attrs["standard_name"] = "time"
        ds.time.encoding["units"] = self.TSD.time_units

        return ds

    def fix_monthly_time_coord(self, ds):
        cal = self.TSD.calendar
        ds.time.attrs["axis"] = "T"
        ds["time"].encoding["calendar"] = cal
        ds["time"].attrs["standard_name"] = "time"
        ds.time.encoding["units"] = self.TSD.time_units

        return ds

    def fix_DJF_time_coord(self, ds):
        # In the rare case where only winter is calculated, there was a problem where the time coordinate had no calendar/units attrs.
        cal = self.TSD.calendar
        ds.time.attrs["axis"] = "T"
        ds["time"].encoding["calendar"] = cal
        ds["time"].attrs["standard_name"] = "time"
        ds.time.encoding["units"] = self.TSD.time_units
        return ds

    def annual_stats(
        self,
        stat,
        tmax_da=None,
        ref_da=None,
        nTuple=False,
        pentad=False,
        n=None,
        threshold=None,
    ):
        # Acquire annual statistics
        # Arguments:
        #     stat: Can be "max", "min"
        #     pentad: True to run on 5-day mean
        #     ref_da: DataArray containing 2D reference data.
        # Returns:
        #     ds_ann: Dataset containing annual max or min grid
        if (stat == "first_date_below") or (stat == "last_date_below"):
            if threshold is None:
                raise Exception("Provide threshold for computing the first/last date")
        if pentad:
            if self.pentad is None:
                self.calc_5day_mean()  # initializes self.pentad - 5-day mean
            ds = self.pentad
        elif nTuple:
            if n is None:
                raise Exception("Provide n for n-day averaging")
            if self.nTuple is None:
                self.calc_nday_mean(n)
            ds = self.nTuple
        else:
            ds = self.TSD.return_data_array()
        cal = self.TSD.calendar

        # if self.annual_strict and pentad:
        if self.annual_strict and nTuple:
            # This setting is for means using n day rolling average values, where
            # we do not want to include any data from the prior year
            year_range = self.TSD.year_range
            hr = int(ds.time[0].dt.hour)  # get hour to help with selecting nearest time

            # Only use data from that year - start on Jan 5 avg
            date_range = [
                xr.cftime_range(
                    start=cftime.datetime(year, 1, n, hour=hr, calendar=cal)
                    - self.del0d,
                    end=cftime.datetime(year + 1, 1, 1, hour=hr, calendar=cal)
                    - self.del1d,
                    freq="D",
                    calendar=cal,
                )
                for year in year_range
            ]
            date_range = [item for sublist in date_range for item in sublist]
            if stat == "max":
                ds_ann = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .max(dim="time")
                )
            elif stat == "min":
                ds_ann = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .min(dim="time")
                )
            elif stat == "mean":
                ds_ann = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .mean(dim="time")
                )
            elif stat == "median":
                ds_ann = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .median(dim="time")
                )
            elif stat.startswith("q"):
                num = float(stat.replace("q", "").replace("p", ".")) / 100.0
                ds_ann = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .quantile(num, dim="time", skipna=True)
                )
            elif stat.startswith("ge"):
                num = float(stat.replace("ge", ""))
                ds_ann = (
                    ds.where(ds >= num)
                    .sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .count(dim="time")
                    / ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .count(dim="time")
                    * 100
                )
            elif stat.startswith("le"):
                num = float(stat.replace("le", ""))
                ds_ann = (
                    ds.where(ds <= num)
                    .groupby("time.year")
                    .sel(time=date_range, method="nearest")
                    .count(dim="time")
                    / ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .count(dim="time")
                    * 100
                )
        else:
            # Group by date
            if stat == "max":
                ds_ann = ds.groupby("time.year").max(dim="time")
            elif stat == "min":
                ds_ann = ds.groupby("time.year").min(dim="time")
            elif stat == "mean":
                ds_ann = ds.groupby("time.year").mean(dim="time")
            elif stat == "median":
                ds_ann = ds.groupby("time.year").median(dim="time")
            elif stat == "total":
                ds_ann = ds.groupby("time.year").sum(dim="time")
            elif (
                stat == "cool_deg_days"
            ):  # must be a mean daily temperature dataset in F
                thresh = Q_(65, "degF")

                unit_str = ds.attrs["units"]
                data_units = Unit(f"deg{unit_str}")

                thresh = thresh.to(data_units).magnitude
                ds_ge_65 = ds - thresh
                ds_ge_65 = ds_ge_65.where(
                    ds_ge_65 >= 0
                )  # don't care if mean temperature is < 65 F
                ds_ann = ds_ge_65.groupby("time.year").sum(dim="time")  # annual total
                delta_units = f"delta_{data_units}"

                ds_ann_units = Q_(ds_ann.data, delta_units)
                ds_ann_arr = ds_ann_units.to("delta_degF").magnitude
                ds_ann = xr.DataArray(
                    ds_ann_arr,
                    coords=ds_ann.coords,
                    dims=ds_ann.dims,
                )
            elif (
                stat == "heat_deg_days"
            ):  # must be a mean daily temperature dataset in F
                thresh = Q_(65, "degF")
                unit_str = ds.attrs["units"]
                data_units = Unit(f"deg{unit_str}")

                thresh = thresh.to(data_units).magnitude

                ds_le_65 = thresh - ds
                ds_le_65 = ds_le_65.where(
                    ds_le_65 >= 0
                )  # don't care if mean temperature is < 65 F
                ds_ann = ds_le_65.groupby("time.year").sum(dim="time")  # annual total

                delta_units = f"delta_{data_units}"
                ds_ann_units = Q_(ds_ann.data, delta_units)
                ds_ann_arr = ds_ann_units.to("delta_degF").magnitude
                ds_ann = xr.DataArray(
                    ds_ann_arr,
                    coords=ds_ann.coords,
                    dims=ds_ann.dims,
                )

            elif (
                stat == "grow_deg_days"
            ):  # must be a mean daily temperature dataset in F
                thresh = Q_(50, "degF")

                unit_str = ds.attrs["units"]
                data_units = Unit(f"deg{unit_str}")

                thresh = thresh.to(data_units).magnitude

                ds_ge_50 = ds - thresh
                ds_ge_50 = ds_ge_50.where(
                    ds_ge_50 >= 0
                )  # don't care if mean temperature is < 50 F
                ds_ann = ds_ge_50.groupby("time.year").sum(
                    dim="time"
                )  # annual total in converted units

                delta_units = f"delta_{data_units}"
                ds_ann_units = Q_(ds_ann.data, delta_units)
                ds_ann_arr = ds_ann_units.to("delta_degF").magnitude
                ds_ann = xr.DataArray(
                    ds_ann_arr,
                    coords=ds_ann.coords,
                    dims=ds_ann.dims,
                )
            elif stat.startswith("q"):
                num = float(stat.replace("q", "").replace("p", ".")) / 100.0
                ds_ann = ds.groupby("time.year").quantile(num, dim="time", skipna=True)

            elif stat.startswith(
                "ge"
            ):  # % of days per year greater than or equal to some value (xarray or float)
                if ref_da is None:  # discrete temperature value to compare to
                    num = float(stat.replace("ge", ""))

                    if num == 0:
                        # Set the operator (<) to be used later
                        oper = operator.gt
                    else:
                        oper = operator.ge

                else:  # quantile reference dataset
                    num = ref_da
                    oper = operator.gt

                ds_ann = (
                    ds.where(oper(ds, num)).groupby("time.year").count(dim="time")
                    / ds.groupby("time.year").count(dim="time")
                    * 100
                )
            elif stat.startswith("le"):  # discrete temperature values to compare to
                if ref_da is None:  # A single threshold i.e. 90F was given
                    num = float(stat.replace("le", ""))  # Define that number
                else:  # quantile reference dataset
                    num = ref_da
                ds_ann = (
                    ds.where(ds <= num).groupby("time.year").count(dim="time")
                    / ds.groupby("time.year").count(dim="time")
                    * 100
                )
            elif stat == "sum_gt_q":
                if ref_da is None:
                    raise Exception("Must provide observational dataset")
                ds_ann = ds.where(ds >= ref_da).groupby("time.year").sum(
                    dim="time"
                ) / ds.groupby("time.year").sum(dim="time")
            elif stat == "first_date_below":
                # Assume for now the temperature data is in Fahrenheit

                # The first fall freeze is defined as the date of the first occurrence of 32°F or lower in the nine months following midnight August 1.
                # Grid points with more than 10 of the 30 years not experiencing an occurrence of 32°F or lower  are excluded from the analysis.
                def group_by_aug_to_apr(time):
                    """Return a group identifier for each August-to-April segment."""
                    year = time.dt.year
                    month = time.dt.month
                    # Assign group ID based on the year and whether the month is in the range 8-12 or 1-4
                    return xr.where(month >= 8, year, year - 1)

                def get_first_date(ds_cond):
                    return ds_cond.where(ds_cond.any(dim="time"), ds_cond, 0).argmax(
                        dim="time"
                    )

                start_year = ds.time.dt.year.data[0]
                end_year = ds.time.dt.year.data[-1]

                time_slice = slice(
                    *(f"{start_year}-08-01", f"{end_year:02}-04-30")
                )  # slice to years where were have the full 9 months for freezing season
                ds = ds.copy(deep=True).sel(time=time_slice)
                months = [8, 9, 10, 11, 12, 1, 2, 3, 4]
                ds = ds.copy(deep=True).isel(time=ds.time.dt.month.isin(months))
                ds_cond = ds <= threshold
                group_ids = group_by_aug_to_apr(ds_cond["time"])
                ds_ann = ds_cond.groupby(group_ids).apply(get_first_date)
                ds_ann = ds_ann.rename({"group": "year"})
                ds_ann = ds_ann.where(ds_ann > 0)

            elif stat == "last_date_below":

                def group_by_nov_july(time):
                    """Return a group identifier for each Nov-July segment."""
                    year = time.dt.year
                    month = time.dt.month
                    # Assign group ID based on the year and whether the month is in the range 8-12 or 1-4
                    return xr.where(month >= 11, year, year - 1)

                def get_last_date(ds_cond):
                    ds_cond = ds_cond.sel(time=slice(*(None, None, -1)))
                    first_occ_reversed = ds_cond.where(
                        ds_cond.any(dim="time"), ds_cond, 0
                    ).argmax(dim="time")
                    last_occ = len(ds_cond.time) - first_occ_reversed - 1
                    return last_occ.where(last_occ < len(ds_cond.time) - 1)

                start_year = ds.time.dt.year.data[0]
                end_year = ds.time.dt.year.data[-1]
                time_slice = slice(
                    *(f"{start_year}-11-01", f"{end_year:02}-07-30")
                )  # slice to years where were have the full 9 months for freezing season
                ds = ds.copy(deep=True).sel(time=time_slice)
                months = [11, 12, 1, 2, 3, 4, 5, 6, 7]
                ds = ds.copy(deep=True).isel(time=ds.time.dt.month.isin(months))
                ds_cond = ds <= threshold
                group_ids = group_by_nov_july(ds_cond["time"])
                ds_ann = ds_cond.groupby(group_ids).apply(get_last_date)
                ds_ann = ds_ann.rename({"group": "year"})
                ds_ann = ds_ann.where(ds_ann > 0)

            elif stat == "chill_hours":
                tref = Q_(45, "degF")
                tfreeze = Q_(32, "degF")

                unit_str = ds.attrs["units"]
                data_units = Unit(f"deg{unit_str}")

                tref = tref.to(data_units).magnitude
                tfreeze = tfreeze.to(data_units).magnitude

                def group_by_july_june(time):
                    year = time.dt.year
                    month = time.dt.month
                    # Assign group ID based on the year and whether the month is in the range 8-12 or 1-4
                    return xr.where(month >= 7, year, year - 1)

                start_year = ds.time.dt.year.data[0]
                end_year = ds.time.dt.year.data[-1]
                time_slice = slice(*(f"{start_year}-07-01", f"{end_year:02}-06-30"))

                ds = ds.copy(deep=True)  # .sel(time=time_slice)
                ch = 24 * (tref - ds) / (tmax_da - ds)
                ch = ch.where(ch > 0, 0)
                ch = ch.where(ch <= 24, 24)
                k = 24 * (tfreeze - ds) / (tmax_da - ds)
                k = k.where(k > 0, 0)
                chill_hours_gt_32 = ch - k
                chill_hours_gt_32 = chill_hours_gt_32.where(chill_hours_gt_32 >= 0)
                # group_ids = group_by_july_june(chill_hours_gt_32["time"])
                # ds_ann = chill_hours_gt_32.groupby(group_ids).sum(dim="time")
                # ds_ann = ds_ann.rename({"group": "year"})
                ds_ann = chill_hours_gt_32.where(chill_hours_gt_32 > 0)

        # Need to fix time axis if groupby operation happened
        if "year" in ds_ann.coords:
            ds_ann = self.fix_time_coord(ds_ann)
        return self.masked_ds(ds_ann)

    # def seasonal_stats(self, season, stat, nTuple = False, pentad = False, n = None):
    def seasonal_stats(self, season, stat, nTuple=False, pentad=False, n=None):
        year_range = self.TSD.year_range

        if pentad:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.TSD.return_data_array()

        # cal = self.TSD.calendar
        # hr = int(ds.time[0].dt.hour)

        months = {
            "DJF": [12, 1, 2],
            "MAM": [3, 4, 5],
            "JJA": [6, 7, 8],
            "SON": [9, 10, 11],
        }
        ds_stat = ds.isel(time=ds.time.dt.month.isin(months[season]))

        if stat == "max":
            ds_stat = ds_stat.groupby("time.year").max(dim="time")
        elif stat == "min":
            ds_stat = ds_stat.groupby("time.year").min(dim="time")
        elif stat == "mean":
            ds_stat = ds_stat.groupby("time.year").mean(dim="time")

        elif stat == "median":
            ds_stat = ds_stat.groupby("time.year").median(dim="time")

        if "year" in ds_stat.coords:
            ds_stat = self.fix_time_coord(ds_stat)

        return ds_stat

    # def seasonal_stats(self, season, stat, nTuple=False, pentad=False, n=None):

    #     # Acquire statistics for a given season
    #     # Arguments:
    #     #     season: Can be "DJF","MAM","JJA","SON"
    #     #     stat: Can be "max", "min"
    #     #     pentad: True to run on 5-day mean
    #     # Returns:
    #     #     ds_stat: Dataset containing seasonal max or min grid

    #     year_range = self.TSD.year_range

    #     if pentad:
    #         if self.pentad is None:
    #             self.calc_5day_mean()
    #         ds = self.pentad
    #     else:
    #         ds = self.TSD.return_data_array()
    #     cal = self.TSD.calendar

    #     hr = int(ds.time[0].dt.hour)  # help with selecting nearest time

    #     if season == "DJF" and self.dec_mode == "DJF":
    #         # Resample DJF to count prior DJF in current year
    #         if stat == "max":
    #             ds_stat = ds.resample(time="QS-DEC").max(dim="time")
    #         elif stat == "min":
    #             ds_stat = ds.resample(time="QS-DEC").min(dim="time")
    #         elif stat == "mean":
    #             ds_stat = ds.resample(time="QS-DEC").mean(dim="time")
    #         elif stat == "median":
    #             ds_stat = ds.resample(time="QS-DEC").median(dim="time")

    #         ds_stat = ds_stat.isel(time=ds_stat.time.dt.month.isin([12]))

    #         # Deal with inconsistencies between QS-DEC calendar and block exremes calendar
    #         if self.drop_incomplete_djf:
    #             ds_stat = ds_stat.sel(
    #                 {"time": slice(str(year_range[0]), str(year_range[-1] - 1))}
    #             )
    #             ds_stat["time"] = [
    #                 cftime.datetime(y, 1, 1, calendar=cal)
    #                 for y in np.arange(year_range[0] + 1, year_range[-1] + 1)
    #             ]
    #         else:
    #             ds_stat = ds_stat.sel(
    #                 {"time": slice(str(year_range[0] - 1), str(year_range[-1] - 1))}
    #             )
    #             ds_stat["time"] = [
    #                 cftime.datetime(y, 1, 1, calendar=cal)
    #                 for y in np.arange(year_range[0], year_range[-1] + 1)
    #             ]
    #     elif season == "DJF" and self.dec_mode == "JFD":
    #         # Make date lists that capture JF and D in all years, then merge and sort

    #         if self.annual_strict and pentad:
    #             # Only use data from that year - start on Jan 5 avg
    #             date_range_1 = [
    #                 xr.cftime_range(
    #                     start=cftime.datetime(year, 1, 5, hour=hr, calendar=cal)
    #                     - self.del0d,
    #                     end=cftime.datetime(year, 3, 1, hour=hr, calendar=cal)
    #                     - self.del1d,
    #                     freq="D",
    #                     calendar=cal,
    #                 )
    #                 for year in year_range
    #             ]
    #         else:
    #             date_range_1 = [
    #                 xr.cftime_range(
    #                     start=cftime.datetime(year, 1, 1, hour=hr, calendar=cal)
    #                     - self.del0d,
    #                     end=cftime.datetime(year, 3, 1, hour=hr, calendar=cal)
    #                     - self.del1d,
    #                     freq="D",
    #                     calendar=cal,
    #                 )
    #                 for year in year_range
    #             ]
    #         date_range_1 = [item for sublist in date_range_1 for item in sublist]
    #         date_range_2 = [
    #             xr.cftime_range(
    #                 start=cftime.datetime(year, 12, 1, hour=hr, calendar=cal)
    #                 - self.del0d,
    #                 end=cftime.datetime(year + 1, 1, 1, hour=hr, calendar=cal)
    #                 - self.del1d,
    #                 freq="D",
    #                 calendar=cal,
    #             )
    #             for year in year_range
    #         ]
    #         date_range_2 = [item for sublist in date_range_2 for item in sublist]
    #         date_range = sorted(date_range_1 + date_range_2)

    #         if stat == "max":
    #             ds_stat = (
    #                 ds.sel(
    #                     time=date_range, method="nearest"
    #                 )  # could also do ds.sel(time = slice(*(begin_cftime, end_cftime)))
    #                 .groupby("time.year")
    #                 .max(dim="time")
    #             )
    #         elif stat == "min":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .min(dim="time")
    #             )
    #         elif stat == "mean":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .mean(dim="time")
    #             )
    #         elif stat == "median":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .median(dim="time")
    #             )

    #     else:  # Other 3 seasons
    #         dates = {  # Month/day tuples
    #             "MAM": [(3, 1), (6, 1)],
    #             "JJA": [(6, 1), (9, 1)],
    #             "SON": [(9, 1), (12, 1)],
    #         }

    #         mo_st = dates[season][0][0]
    #         day_st = dates[season][0][1]
    #         mo_en = dates[season][1][0]
    #         day_en = dates[season][1][1]

    #         cal = self.TSD.calendar

    #         date_range = [
    #             xr.cftime_range(
    #                 start=cftime.datetime(year, mo_st, day_st, hour=hr, calendar=cal)
    #                 - self.del0d,
    #                 end=cftime.datetime(year, mo_en, day_en, hour=hr, calendar=cal)
    #                 - self.del1d,
    #                 freq="D",
    #                 calendar=cal,
    #             )
    #             for year in year_range
    #         ]
    #         date_range = [item for sublist in date_range for item in sublist]

    #         if stat == "max":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .max(dim="time")
    #             )
    #         elif stat == "min":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .min(dim="time")
    #             )
    #         elif stat == "mean":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .mean(dim="time")
    #             )

    #         elif stat == "median":
    #             ds_stat = (
    #                 ds.sel(time=date_range, method="nearest")
    #                 .groupby("time.year")
    #                 .median(dim="time")
    #             )

    #     # Need to fix time axis if groupby operation happened
    #     if "year" in ds_stat.coords:
    #         ds_stat = self.fix_time_coord(ds_stat)
    #     else:
    #         ds_stat = self.fix_DJF_time_coord(ds_stat)

    #     return self.masked_ds(ds_stat)

    def monthly_stats(self, month, stat):
        # Aquire statistics for a given month

        # Arguments:
        #     stat: Can be "max", "min", "mean"
        #     month: [1,2,3,...,12] representing month of the year
        # Returns:
        #     ds_ann: Dataset containing annual max or min grid

        ds = self.TSD.return_data_array()
        year_range = self.TSD.year_range
        cal = self.TSD.calendar
        hr = int(ds.time[0].dt.hour)

        if month < 12:
            mo_st = month
            day_st = 1
            mo_en = month + 1
            day_en = 1

            date_range = [
                xr.cftime_range(
                    start=cftime.datetime(year, mo_st, day_st, hour=hr, calendar=cal)
                    - self.del0d,
                    end=cftime.datetime(year, mo_en, day_en, hour=hr, calendar=cal)
                    - self.del1d,
                    freq="D",
                    calendar=cal,
                )
                for year in year_range
            ]
            date_range = [item for sublist in date_range for item in sublist]

        else:
            mo_st = month
            day_st = 1
            mo_en = 1
            day_en = 1

            date_range = [
                xr.cftime_range(
                    start=cftime.datetime(year, mo_st, day_st, hour=hr, calendar=cal)
                    - self.del0d,
                    end=cftime.datetime(year + 1, mo_en, day_en, hour=hr, calendar=cal)
                    - self.del1d,
                    freq="D",
                    calendar=cal,
                )
                for year in year_range
            ]
            date_range = [item for sublist in date_range for item in sublist]

        if stat == "max":
            ds_stat = (
                ds.sel(time=date_range, method="nearest")
                .groupby("time.year")
                .max(dim="time")
            )
        elif stat == "min":
            ds_stat = (
                ds.sel(time=date_range, method="nearest")
                .groupby("time.year")
                .min(dim="time")
            )
        elif stat == "mean":
            ds_stat = (
                ds.sel(time=date_range, method="nearest")
                .groupby("time.year")
                .mean(dim="time")
            )

        # print(ds_stat.time.dt.month)

        # ds_stat = self.fix_monthly_time_coord(ds_stat)

        if "year" in ds_stat.coords:
            ds_stat = self.fix_time_coord(ds_stat)

        return self.masked_ds(ds_stat)


def update_nc_attrs(ds, dec_mode, drop_incomplete_djf, annual_strict):
    # Add bounds and record user settings in attributes
    # Use this function for any general dataset updates.
    xvar = get_longitude_key(ds)
    yvar = get_latitude_key(ds)
    xvarbnds = xvar + "_bnds"
    yvarbnds = yvar + "_bnds"
    ds[yvar].attrs["standard_name"] = "Y"
    ds[xvar].attrs["standard_name"] = "X"
    if "time" in ds:
        bnds_dict = {yvar: "Y", xvar: "X", "time": "T"}
    else:
        bnds_dict = {yvar: "Y", xvar: "X"}
    for item in bnds_dict:
        if item not in ds:
            continue  # without this, 'time not in dataset' was an issue for quantile variables
        if "bounds" in ds[item].attrs:
            bnds_var = ds[item].attrs["bounds"]
            if bnds_var not in ds.keys():
                ds[item].attrs["bounds"] = ""
                ds = ds.bounds.add_missing_bounds([bnds_dict[item]])
        else:
            ds = ds.bounds.add_missing_bounds([bnds_dict[item]])
    ds.attrs["december_mode"] = str(dec_mode)
    ds.attrs["drop_incomplete_djf"] = str(drop_incomplete_djf)
    ds.attrs["annual_strict"] = str(annual_strict)

    # Update fill value encoding
    ds[yvar].encoding["_FillValue"] = None
    ds[xvar].encoding["_FillValue"] = None
    ds[yvarbnds].encoding["_FillValue"] = None
    ds[xvarbnds].encoding["_FillValue"] = None
    if "time" in ds:
        ds.time.encoding["_FillValue"] = None
        if "time_bnds" in ds:
            ds.time_bnds.encoding["_FillValue"] = None
    for season in [
        "ANN",
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUNE",
        "JULY",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
        "DJF",
        "MAM",
        "JJA",
        "SON",
        "ANN5",
        "median",
        "q95p0",
        "q99p9",
        "q99p0",
    ]:
        if season in ds:
            ds[season].encoding["_FillValue"] = float(1e20)

    # Drop type attribute that comes from land mask
    if "type" in ds:
        ds = ds.drop("type")
    return ds


def convert_units(data, units_adjust):
    # Convert the units of the input data
    # units_adjust is a tuple of form
    # (flag (bool), operation (str), value (float), units (str)).
    # For example, (True, "multiply", 86400., "mm/day")
    # If flag is False, data is returned unaltered.
    if bool(units_adjust[0]):
        op_dict = {
            "add": "+",
            "subtract": "-",
            "multiply": "*",
            "divide": "/",
            "CtoF": ")*(9/5)+32",
            "KtoF": "-273.15)*(9/5)+32",
            "FtoK": "−32)*5/9)+273.15",
            "FtoC": "−32)*5/9)",
            "KtoC": "-273.15)",
            "CtoK": "+273.15)",
        }
        if str(units_adjust[1]) not in op_dict:
            print(
                "Error in units conversion. Operation must be add, subtract, multiply, or divide."
            )
            print("Skipping units conversion.")
            return data
        op = op_dict[str(units_adjust[1])]
        val = float(units_adjust[2])
        if "to" in units_adjust[1]:
            # more complex equation for fahrenheit conversion
            operation = "(data{0}".format(op)
        else:
            operation = "data {0} {1}".format(op, val)
        data = eval(operation)
        data.attrs["units"] = str(units_adjust[3])
    else:
        # No adjustment, but check that units attr is populated
        if "units" not in data.attrs:
            data.attrs["units"] = ""
    return data


# Max Temperature Metics
def get_mean_tasmax(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual and seasonal mean maximum daily temperature.
    index = f"mean_tasmax"
    print("Metric:", index)
    varname = "tasmax"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmean = xr.Dataset()

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        if season == "ANN":
            Tmean["ANN"] = S.annual_stats("mean")
        else:
            Tmean[season] = S.seasonal_stats(season, "mean")

    Tmean = update_nc_attrs(Tmean, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmean}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            if season == "ANN":
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/annual/{varname}/"
                ).replace("$index", "_".join([index, season]))
            else:
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/seasonal/{varname}/"
                ).replace("$index", "_".join([index, season]))
            Tmean[season].mean("time").plot(
                cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"Average {season} daily high temperature")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    if nc_file is not None:
        out_means = []
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            out_means.append(Tmean[season].mean(dim="time"))
        da_out = xr.concat(out_means, dim="season")
        da_out = da_out.assign_coords(
            season=("season", ["ANN", "DJF", "MAM", "JJA", "SON"])
        )
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )

        da_out.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_out

    del Tmean
    return result_dict


def get_annual_txx(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual max of maximum daily temperature.
    index = "annual_txx"
    print("Metric:", index)
    varname = "tasmax"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmax = xr.Dataset()
    Tmax["ANN"] = S.annual_stats("max")
    Tmax = update_nc_attrs(Tmax, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmax}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        Tmax["ANN"].mean("time").plot(
            cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("Average annual max daily high temperature")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Tmax.mean(dim="time").to_netcdf(nc_file, "w")

    del Tmax
    return result_dict


def get_tasmax_q50(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual median maximum daily temperature
    index = "tasmax_q50"
    varname = "tasmax"
    lat_name = get_latitude_key(ds)
    lon_name = get_longitude_key(ds)

    # Set up empty dataset
    Tmedian = xr.zeros_like(ds)
    Tmedian[lat_name] = ds[lat_name]
    Tmedian[lon_name] = ds[lon_name]
    Tmedian = Tmedian.drop_vars(["time", "time_bnds", varname], errors="ignore")
    if isinstance(ds[varname], dask.array.core.Array):
        Tmedian["q50"] = ds[varname].chunk({"time": -1}).median("time")
    else:
        Tmedian["q50"] = ds[varname].median("time")
    Tmedian = update_nc_attrs(Tmedian, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tmedian}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "median"])
        )
        Tmedian["q50"].plot(
            cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("Time median daily high temperature")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        Tmedian.to_netcdf(nc_file, "w")

    del Tmedian
    return result_dict


def get_tasmax_q99p9(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual 99.9 percentile maximum daily temperature.
    index = "tasmax_q99p9"
    print("Metric:", index)
    varname = "tasmax"
    lat_name = get_latitude_key(ds)
    lon_name = get_longitude_key(ds)
    # Set up empty dataset
    Tq99p9 = xr.zeros_like(ds.isel(time=0))
    Tq99p9[lat_name] = ds[lat_name]
    Tq99p9[lon_name] = ds[lon_name]
    Tq99p9 = Tq99p9.drop_vars(["time", "time_bnds", varname], errors="ignore")

    # PRISM threw errors if chunk not specified
    if isinstance(ds[varname], dask.array.core.Array):
        q99p9 = ds[varname].chunk({"time": -1}).quantile(0.999, dim="time")
    else:
        q99p9 = ds[varname].chunk({"time": -1}).quantile(0.999, dim="time")

    Tq99p9["q99p9"] = q99p9
    Tq99p9 = update_nc_attrs(Tq99p9, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tq99p9}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", index
        )
        Tq99p9["q99p9"].plot(
            cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("99.9th percentile daily high temperature")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        Tq99p9.to_netcdf(nc_file, "w")

    del Tq99p9
    return result_dict


def get_monthly_mean_tasmax(
    ds,
    sftlf,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Monthly mean tasmax

    index_base = "monthly_mean_tasmax"
    varname = "tasmax"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmax_monmean = xr.Dataset()

    for month in range(1, 13):
        index = index_base.replace("monthly", S.month_lookup[month])
        print("Metric:", index)
        Tmax_monmean[S.month_lookup[month]] = S.monthly_stats(month, "mean")

    Tmax_monmean = update_nc_attrs(
        Tmax_monmean, dec_mode, drop_incomplete_djf, annual_strict
    )

    if fig_file is not None:
        for month in range(1, 13):
            index = index_base.replace("monthly", S.month_lookup[month])
            fig_file1 = fig_file.replace(
                "/plots/", f"/plots/monthly/{varname}/"
            ).replace("$index", index)
            Tmax_monmean[S.month_lookup[month]].mean("time").plot(
                cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"{S.month_lookup[month]} Mean Maximum Temperature")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    # Compute statistics
    result_dict = metrics_json(
        {index_base: Tmax_monmean}, obs_dict={}, region="land", regrid=False
    )

    if nc_file is not None:
        names = []
        means = []
        for month in range(1, 13):
            month_name = S.month_lookup[month]
            mean_val = Tmax_monmean[month_name].mean(dim="time")

            means.append(mean_val)
            names.append(month_name)

        da_mean = xr.concat(means, dim="month")
        da_mean = da_mean.assign_coords(month=("month", names))

        nc_file = nc_file.replace("/netcdf/", f"/netcdf/monthly/{varname}/").replace(
            "$index", index_base
        )
        da_mean.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_mean

    del Tmax_monmean
    return result_dict


def get_annual_tasmax_5day(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Annual highest maximum temperature averaged over a 5-day period

    index = "annual_5day_tasmax"
    print("Metric:", index)
    varname = "tasmax"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmax5day = xr.Dataset()
    Tmax5day["ANN"] = S.annual_stats("max", nTuple=True, n=5)  # , #pentad=True)
    Tmax5day = update_nc_attrs(Tmax5day, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tmax5day}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        Tmax5day["ANN"].mean("time").plot(
            cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("Annual maximum 5-day averaged high temperature")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Tmax5day.mean(dim="time").to_netcdf(nc_file, "w")

    del Tmax5day
    return result_dict


def get_annual_tasmax_ge_XF(
    ds,
    sftlf,
    deg,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Get annual fraction of days with max temperature greater than or equal to deg F
    varname = "tasmax"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{deg.units:~}".lstrip("°")
    data_units = Unit(f"deg{unit_str}")  # Assumes degrees "K", "F", or "C"

    index = "annual_tasmax_ge_{0}{1}".format(deg.magnitude, out_unit_str)
    print("Metric:", index)
    threshold_pint_converted = deg.to(data_units)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    TgeX = xr.Dataset()
    TgeX["ANN"] = S.annual_stats("ge{0}".format(threshold_pint_converted.magnitude))
    TgeX.attrs["units"] = "%"
    TgeX = update_nc_attrs(TgeX, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: TgeX}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TgeX["ANN"].mean("time").plot(
            cmap="Oranges", vmin=0, vmax=100, cbar_kwargs={"label": "%"}
        )
        plt.title(
            "Mean percentage of days per year\nwith high temperature >= {0}{1}".format(
                deg.magnitude, out_unit_str
            )
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        TgeX.mean(dim="time").to_netcdf(nc_file, "w")

    del TgeX
    return result_dict


def get_annual_tasmax_le_XF(
    ds,
    sftlf,
    deg,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Get annual fraction of days with max temperature less than threshold
    varname = "tasmax"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{deg.units:~}".lstrip("°")
    data_units = Unit(f"deg{unit_str}")  # Assumes degrees "K", "F", or "C"

    index = "annual_tasmax_le_{0}{1}".format(deg.magnitude, out_unit_str)
    print("Metric:", index)
    threshold_pint_converted = deg.to(data_units)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    TleX = xr.Dataset()
    TleX["ANN"] = S.annual_stats("le{0}".format(threshold_pint_converted.magnitude))
    TleX.attrs["units"] = "%"
    TleX = update_nc_attrs(TleX, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: TleX}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TleX["ANN"].mean("time").plot(
            cmap="Blues", vmin=0, vmax=100, cbar_kwargs={"label": "%"}
        )
        plt.title(
            "Mean percentage of days per year\nwith high temperature < {0}F".format(
                deg.magnitude, out_unit_str
            )
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        TleX.mean(dim="time").to_netcdf(nc_file, "w")

    del TleX
    return result_dict


# observation variable
def get_tmax_days_above_Qth(
    ds,
    sftlf,
    quantile,
    file_name_ref_tmax_quant,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # open the reference dataset
    ds_reference = xr.open_dataset(file_name_ref_tmax_quant)[f"q{quantile}_ANN"]

    # Get annual fraction of days with max temperature less than deg F
    index = f"tmax_days_above_q{quantile}"
    print("Metric:", index)
    varname = "tasmax"
    # Rechunk Dask Arrays
    if isinstance(ds[varname], dask.array.core.Array):
        ds[varname] = ds[varname].chunk({"time": -1})
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    TgeQuant = xr.Dataset()
    TgeQuant["ANN"] = S.annual_stats("ge_q{0}".format(quantile), ref_da=ds_reference)
    TgeQuant.attrs["units"] = "%"
    TgeQuant = update_nc_attrs(TgeQuant, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: TgeQuant}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TgeQuant["ANN"].mean("time").plot(
            cmap="Oranges",
            vmin=np.nanmin(TgeQuant["ANN"].mean("time").data),
            vmax=np.nanmax(TgeQuant["ANN"].mean("time").data),
            cbar_kwargs={"label": "%"},
        )
        plt.title(
            f"Mean percentage of days per year\nwith high temperature > q{quantile}"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        TgeQuant.mean(dim="time").to_netcdf(nc_file, "w")

    del TgeQuant
    return result_dict


def get_tmax_days_below_Qth(
    ds,
    sftlf,
    quantile,
    file_name_ref_tmax_quant,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # open the reference dataset
    ds_reference = xr.open_dataset(file_name_ref_tmax_quant)[f"q{quantile}_ANN"]

    # Get annual fraction of days with max temperature less than deg F
    index = f"tmax_days_below_q{quantile}"
    print("Metric:", index)
    varname = "tasmax"

    # Rechunk Dask Arrays
    if isinstance(ds[varname], dask.array.core.Array):
        ds[varname] = ds[varname].chunk({"time": -1})

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    TleQuant = xr.Dataset()
    TleQuant["ANN"] = S.annual_stats("le_q{0}".format(quantile), ref_da=ds_reference)
    TleQuant.attrs["units"] = "%"
    TleQuant = update_nc_attrs(TleQuant, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: TleQuant}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TleQuant["ANN"].mean("time").plot(
            cmap="Blues",
            vmin=np.nanmin(TleQuant["ANN"].mean("time").data),
            vmax=np.nanmax(TleQuant["ANN"].mean("time").data),
            cbar_kwargs={"label": "%"},
        )
        plt.title(
            f"Mean percentage of days per year\nwith high temperature <= q{quantile}"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        TleQuant.mean(dim="time").to_netcdf(nc_file, "w")

    del TleQuant
    return result_dict


# Mean Temperature Metics
def get_mean_tasmean(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual and seasonal mean maximum daily temperature.
    index = f"mean_tasmean"
    print("Metric:", index)
    varname = "tas"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmean = xr.Dataset()

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        if season == "ANN":
            Tmean["ANN"] = S.annual_stats("mean")
        else:
            Tmean[season] = S.seasonal_stats(season, "mean")

    Tmean = update_nc_attrs(Tmean, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmean}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            if season == "ANN":
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/annual/{varname}/"
                ).replace("$index", "_".join([index, season]))
            else:
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/seasonal/{varname}/"
                ).replace("$index", "_".join([index, season]))
            Tmean[season].mean("time").plot(
                cmap="Oranges", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )  # ds[varname].attrs["units"]
            plt.title(f"Average {season} daily mean temperature")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    if nc_file is not None:
        out_means = []
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            # if season == "DJF":
            #     out_means.append(ds.isel(time = ds.time.dt.month.isin([12,1,2])).mean(dim = "time")[varname])
            # else:
            out_means.append(Tmean[season].mean(dim="time"))

        da_out = xr.concat(out_means, dim="season")
        da_out = da_out.assign_coords(
            season=("season", ["ANN", "DJF", "MAM", "JJA", "SON"])
        )
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )

        da_out.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_out

    del Tmean
    return result_dict


def get_annual_cooling_degree_days(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Cumulative number of degrees by which mean temperature exceeds 65 F
    index = "cool_deg_days"
    print("Metric:", index)
    varname = "tas"
    TS = TimeSeriesData(ds, varname)  # gets the mean temperature dataset
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    cdd = xr.Dataset()
    cdd["ANN"] = S.annual_stats("cool_deg_days")
    cdd = update_nc_attrs(cdd, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: cdd}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        cdd["ANN"].mean("time").plot(cmap="Reds", cbar_kwargs={"label": "F"})
        plt.title(f"Average annual number of cooling degree days")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        cdd.mean(dim="time").to_netcdf(nc_file, "w")

    del cdd
    return result_dict


def get_annual_heating_degree_days(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Cumulative number of degrees by which mean temperature exceeds 65 F
    index = "heat_deg_days"
    print("Metric:", index)
    varname = "tas"

    TS = TimeSeriesData(ds, varname)  # gets the mean temperature dataset
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    hdd = xr.Dataset()
    hdd["ANN"] = S.annual_stats("heat_deg_days")
    hdd = update_nc_attrs(hdd, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: hdd}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        hdd["ANN"].mean("time").plot(cmap="Blues", cbar_kwargs={"label": "F"})
        plt.title(f"Average annual number of heating degree days")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        hdd.mean(dim="time").to_netcdf(nc_file, "w")

    del hdd
    return result_dict


def get_annual_growing_degree_days(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Cumulative number of degrees by which mean temperature exceeds 65 F
    index = "growing_deg_days"
    print("Metric:", index)
    varname = "tas"
    TS = TimeSeriesData(ds, varname)  # gets the mean temperature dataset
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    gdd = xr.Dataset()
    gdd["ANN"] = S.annual_stats("grow_deg_days")
    gdd = update_nc_attrs(gdd, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: gdd}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        gdd["ANN"].mean("time").plot(cmap="Reds", cbar_kwargs={"label": "F"})
        plt.title(f"Average annual number of growing degree days")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        gdd.mean(dim="time").to_netcdf(nc_file, "w")

    del gdd
    return result_dict


# Minimum Temperature Metrics
def get_tnn(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual and winter minimum daily minimum temperature.
    index = "tnn"
    print("Metric:", index)
    varname = "tasmin"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmean = xr.Dataset()
    Tmean["ANN"] = S.annual_stats("min")
    Tmean["DJF"] = S.seasonal_stats("DJF", "min")
    Tmean = update_nc_attrs(Tmean, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmean}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        for season in ["ANN", "DJF"]:  # , "DJF"]:
            if season == "ANN":
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/annual/{varname}/"
                ).replace("$index", "_".join([index, season]))
            else:
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/seasonal/{varname}/"
                ).replace("$index", "_".join([index, season]))
            Tmean[season].mean("time").plot(
                cmap="YlGnBu_r", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"Average {season} minimum daily low temperature")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Tmean.mean(dim="time").to_netcdf(nc_file, "w")

    del Tmean
    return result_dict


# Min Temperature Metics
def get_mean_tasmin(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual and seasonal mean maximum daily temperature.
    index = f"mean_tasmin"
    print("Metric:", index)
    varname = "tasmin"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmean = xr.Dataset()

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        if season == "ANN":
            Tmean["ANN"] = S.annual_stats("mean")
        else:
            Tmean[season] = S.seasonal_stats(season, "mean")

    Tmean = update_nc_attrs(Tmean, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmean}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            if season == "ANN":
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/annual/{varname}/"
                ).replace("$index", "_".join([index, season]))
            else:
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/seasonal/{varname}/"
                ).replace("$index", "_".join([index, season]))
            Tmean[season].mean("time").plot(
                cmap="YlGnBu_r", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"Average {season} daily low temperature")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    if nc_file is not None:
        out_means = []
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            out_means.append(Tmean[season].mean(dim="time"))

        da_out = xr.concat(out_means, dim="season")
        da_out = da_out.assign_coords(
            season=("season", ["ANN", "DJF", "MAM", "JJA", "SON"])
        )
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )

        da_out.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_out

    del Tmean
    return result_dict


def get_monthly_mean_tasmin(
    ds,
    sftlf,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Monthly mean tasmax

    index_base = "monthly_mean_tasmin"
    varname = "tasmin"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmin_monmean = xr.Dataset()

    for month in range(1, 13):
        index = index_base.replace("monthly", S.month_lookup[month])
        print("Metric:", index)
        Tmin_monmean[S.month_lookup[month]] = S.monthly_stats(month, "mean")

    Tmin_monmean = update_nc_attrs(
        Tmin_monmean, dec_mode, drop_incomplete_djf, annual_strict
    )

    if fig_file is not None:
        for month in range(1, 13):
            index = index_base.replace("monthly", S.month_lookup[month])
            fig_file1 = fig_file.replace(
                "/plots/", f"/plots/monthly/{varname}/"
            ).replace("$index", index)
            Tmin_monmean[S.month_lookup[month]].mean("time").plot(
                cmap="YlGnBu_r", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"{S.month_lookup[month]} Mean Minimum Temperature")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    # Compute statistics
    result_dict = metrics_json(
        {index_base: Tmin_monmean}, obs_dict={}, region="land", regrid=False
    )

    if nc_file is not None:
        names = []
        means = []
        for month in range(1, 13):
            month_name = S.month_lookup[month]
            mean_val = Tmin_monmean[month_name].mean(dim="time")

            means.append(mean_val)
            names.append(month_name)

        da_mean = xr.concat(means, dim="month")
        da_mean = da_mean.assign_coords(month=("month", names))

        nc_file = nc_file.replace("/netcdf/", f"/netcdf/monthly/{varname}/").replace(
            "$index", index_base
        )
        da_mean.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_mean

    del Tmin_monmean
    return result_dict


def get_annual_tasmin_le_XF(
    ds,
    sftlf,
    deg,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Get annual percentage of days with daily minimum temperature less than or
    # equal to deg F.
    varname = "tasmin"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{deg.units:~}".lstrip("°")
    data_units = Unit(f"deg{unit_str}")  # Assumes degrees "K", "F", or "C"

    index = "annual_tasmin_le_{0}{1}".format(deg.magnitude, out_unit_str)
    print("Metric:", index)
    threshold_pint_converted = deg.to(data_units)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    TleX = xr.Dataset()
    TleX["ANN"] = S.annual_stats("le{0}".format(threshold_pint_converted.magnitude))
    TleX.attrs["units"] = "%"
    TleX = update_nc_attrs(TleX, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: TleX}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TleX["ANN"].mean("time").plot(
            cmap="RdPu", vmin=0, vmax=100, cbar_kwargs={"label": "%"}
        )
        plt.title(
            "Mean percentage of days per year\nwith low temperature <= {0}{1}".format(
                deg.magnitude, out_unit_str
            )
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        TleX.mean(dim="time").to_netcdf(nc_file, "w")

    del TleX
    return result_dict


def get_annual_tasmin_ge_XF(
    ds,
    sftlf,
    deg,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Get annual percentage of days with daily minimum temperature
    # greater than or equal to deg F (warm nights)
    varname = "tasmin"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{deg.units:~}".lstrip("°")
    data_units = Unit(f"deg{unit_str}")  # Assumes degrees "K", "F", or "C"

    index = "annual_tasmin_ge_{0}{1}".format(deg.magnitude, out_unit_str)
    print("Metric:", index)
    threshold_pint_converted = deg.to(data_units)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    TgeX = xr.Dataset()
    TgeX["ANN"] = S.annual_stats("ge{0}".format(threshold_pint_converted.magnitude))
    TgeX.attrs["units"] = "%"
    TgeX = update_nc_attrs(TgeX, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: TgeX}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TgeX["ANN"].mean("time").plot(
            cmap="RdPu", vmin=0, vmax=100, cbar_kwargs={"label": "%"}
        )
        plt.title(
            "Mean percentage of days per year\nwith low temperature >= {0}{1}".format(
                deg.magnitude, out_unit_str
            )
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        TgeX.mean(dim="time").to_netcdf(nc_file, "w")

    del TgeX
    return result_dict


def get_annual_min_tasmin_5day(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Annual lowest minimum temperature averaged over a 5-day period

    index = "annual_min_5day_tasmin"
    print("Metric:", index)
    varname = "tasmin"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmin5day = xr.Dataset()
    Tmin5day["ANN"] = S.annual_stats("min", pentad=True)
    Tmin5day = update_nc_attrs(Tmin5day, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tmin5day}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        Tmin5day["ANN"].mean("time").plot(
            cmap="YlGnBu_r", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("Annual minimum 5-day averaged low temperature")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Tmin5day.mean(dim="time").to_netcdf(nc_file, "w")

    del Tmin5day
    return result_dict


def get_annual_max_tasmin_5day(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Annual highest annual minimum temperature averaged over a 5-day period

    index = "annual_max_5day_tasmin"
    print("Metric:", index)
    varname = "tasmin"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmin5day = xr.Dataset()
    Tmin5day["ANN"] = S.annual_stats("max", pentad=True)
    Tmin5day = update_nc_attrs(Tmin5day, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tmin5day}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        Tmin5day["ANN"].mean("time").plot(
            cmap="jet", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("Annual maximum 5-day averaged low temperature")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Tmin5day.mean(dim="time").to_netcdf(nc_file, "w")

    del Tmin5day
    return result_dict


def get_first_date_belowX(
    ds,
    sftlf,
    threshold,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    varname = "tasmin"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{threshold.units:~}".lstrip("°")
    data_units = Unit(f"deg{unit_str}")  # Assumes degrees "K", "F", or "C"

    threshold_pint_converted = threshold.to(data_units)
    freeze = Q_(32, "degF").to(data_units)
    tolerance = 1e-6

    if abs(threshold_pint_converted.magnitude - freeze.magnitude) < tolerance:
        index = "first_freeze_date"
    else:
        index = f"first_date_below_{threshold.magnitude}{out_unit_str}"

    print("Metric:", index)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    FirstFreeze = xr.Dataset()
    FirstFreeze["ANN"] = S.annual_stats(
        "first_date_below", threshold=threshold_pint_converted.magnitude, pentad=False
    )
    FirstFreeze = update_nc_attrs(
        FirstFreeze, dec_mode, drop_incomplete_djf, annual_strict
    )

    # Compute statistics
    result_dict = metrics_json(
        {index: FirstFreeze}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        FirstFreeze["ANN"].mean("time").plot(cmap="jet", cbar_kwargs={"label": "days"})
        plt.title(
            f"First Date Below {threshold.magnitude}{out_unit_str}\nNumber of Days after August 1st"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        encoding = {
            "ANN": {
                "_FillValue": None,  # Disable _FillValue if not needed
            }
        }
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        FirstFreeze.mean(dim="time").to_netcdf(nc_file, "w", encoding=encoding)

    return result_dict, FirstFreeze["ANN"]


def get_last_date_belowX(
    ds,
    sftlf,
    threshold,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    varname = "tasmin"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{threshold.units:~}".lstrip("°")
    data_units = Unit(f"deg{unit_str}")  # Assumes degrees "K", "F", or "C"

    threshold_pint_converted = threshold.to(data_units)
    freeze = Q_(32, "degF").to(data_units)
    tolerance = 1e-6

    if abs(threshold_pint_converted.magnitude - freeze.magnitude) < tolerance:
        index = "last_freeze_date"
    else:
        index = f"last_date_below_{threshold.magnitude}{out_unit_str}"

    print("Metric:", index)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    LastFreeze = xr.Dataset()
    LastFreeze["ANN"] = S.annual_stats(
        "last_date_below", threshold=threshold_pint_converted.magnitude, pentad=False
    )
    LastFreeze = update_nc_attrs(
        LastFreeze, dec_mode, drop_incomplete_djf, annual_strict
    )

    # Compute statistics
    result_dict = metrics_json(
        {index: LastFreeze}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        LastFreeze["ANN"].mean("time").plot(cmap="jet_r", cbar_kwargs={"label": "days"})
        plt.title(
            f"Last Date Below {threshold.magnitude}{out_unit_str}\nNumber of Days after November 1st"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        encoding = {
            "ANN": {
                "_FillValue": None,  # Disable _FillValue if not needed
            }
        }
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        LastFreeze.mean(dim="time").to_netcdf(nc_file, "w", encoding=encoding)

    return result_dict, LastFreeze["ANN"]


def get_growing_season_length(
    ds_first_freeze,
    ds_last_freeze,
    threshold,
    sftlf,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    out_unit_str = f"{threshold.units:~}".lstrip("°")
    index = f"growing_season_{threshold.magnitude}{out_unit_str}"
    print("Metric:", index)

    nov_to_august_length = 273  # number of days (assumes no leap)

    gsl = xr.Dataset()
    gsl["ANN"] = (nov_to_august_length - ds_last_freeze) + ds_first_freeze
    gsl = update_nc_attrs(gsl, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: gsl}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/").replace(
            "$index", "_".join([index, "ANN"])
        )
        gsl["ANN"].mean("time").plot(cmap="YlGn", cbar_kwargs={"label": "days"})
        plt.title(f"Length of Growing Season ({threshold.magnitude}{out_unit_str})")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        encoding = {
            "ANN": {
                "_FillValue": None,  # Disable _FillValue if not needed
                "dtype": "int64",  # Ensure the data type matches your variable
            }
        }
        nc_file = nc_file.replace("$index", index)
        gsl.mean(dim="time").to_netcdf(nc_file, "w", encoding=encoding)

    del gsl
    return result_dict


def get_tmin_days_above_Qth(
    ds,
    sftlf,
    quantile,
    file_name_ref_tmin_quant,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # open the reference dataset
    ds_reference = xr.open_dataset(file_name_ref_tmin_quant)[f"q{quantile}"]

    # Get annual fraction of days with max temperature less than deg F
    index = f"tmin_days_above_q{quantile}"
    print("Metric:", index)
    varname = "tasmin"
    # Rechunk Dask Arrays
    if isinstance(ds[varname], dask.array.core.Array):
        ds[varname] = ds[varname].chunk({"time": -1})
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    TgeQuant = xr.Dataset()
    TgeQuant["ANN"] = S.annual_stats("ge_q{0}".format(quantile), ref_da=ds_reference)
    TgeQuant.attrs["units"] = "%"
    TgeQuant = update_nc_attrs(TgeQuant, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: TgeQuant}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TgeQuant["ANN"].mean("time").plot(
            cmap="Oranges",
            vmin=np.nanmin(TgeQuant["ANN"].mean("time").data),
            vmax=np.nanmax(TgeQuant["ANN"].mean("time").data),
            cbar_kwargs={"label": "%"},
        )
        plt.title(
            f"Mean percentage of days per year\nwith low temperature >= q{quantile}"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        TgeQuant.mean(dim="time").to_netcdf(nc_file, "w")

    del TgeQuant
    return result_dict


def get_tmin_days_below_Qth(
    ds,
    sftlf,
    quantile,
    file_name_ref_tmin_quant,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # open the reference dataset
    ds_reference = xr.open_dataset(file_name_ref_tmin_quant)[f"q{quantile}"]

    # Get annual fraction of days with max temperature less than deg F
    index = f"tmin_days_below_q{quantile}"
    print("Metric:", index)
    varname = "tasmin"

    # Rechunk Dask Arrays
    if isinstance(ds[varname], dask.array.core.Array):
        ds[varname] = ds[varname].chunk({"time": -1})

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    TleQuant = xr.Dataset()
    TleQuant["ANN"] = S.annual_stats("le_q{0}".format(quantile), ref_da=ds_reference)
    TleQuant.attrs["units"] = "%"
    TleQuant = update_nc_attrs(TleQuant, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: TleQuant}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        TleQuant["ANN"].mean("time").plot(
            cmap="Blues",
            vmin=np.nanmin(TleQuant["ANN"].mean("time").data),
            vmax=np.nanmax(TleQuant["ANN"].mean("time").data),
            cbar_kwargs={"label": "%"},
        )
        plt.title(
            f"Mean percentage of days per year\nwith low temperature <= q{quantile}"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        TleQuant.mean(dim="time").to_netcdf(nc_file, "w")

    del TleQuant
    return result_dict


def get_chill_hours(
    ds,
    ds_tasmax,
    sftlf,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    """Number of hours per year with temperature between 32F and 45F. Estimated using Baldocchi and Wong (2008)"""

    varname = "tasmin"
    index = "chill_hours"
    print("Metric:", index)

    TMIN = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TMIN,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    ChillHours = xr.Dataset()
    ChillHours["ANN"] = S.annual_stats(
        "chill_hours",
        tmax_da=ds_tasmax["tasmax"],
        pentad=False,
    )

    return ChillHours

    # ChillHours = update_nc_attrs(
    #     ChillHours, dec_mode, drop_incomplete_djf, annual_strict
    # )

    # # Compute statistics
    # result_dict = metrics_json(
    #     {index: ChillHours}, obs_dict={}, region="land", regrid=False
    # )

    # # if fig_file is not None:
    # #     fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
    # #         "$index", "_".join([index, "ANN"])
    # #     )
    # #     ChillHours["ANN"].mean("time").plot(
    # #         cmap="jet_r", cbar_kwargs={"label": "hours"}
    # #     )
    # #     plt.title("Cumulative Hours between 32F and 45F")
    # #     ax = plt.gca()
    # #     ax.set_facecolor(bgclr)
    # #     plt.savefig(fig_file1)
    # #     plt.close()

    # if nc_file is not None:
    #     encoding = {
    #         "ANN": {
    #             "_FillValue": None,  # Disable _FillValue if not needed
    #             "dtype": "int64",  # Ensure the data type matches your variable
    #         }
    #     }
    #     nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace("$index", index)
    #     ChillHours.mean(dim="time").to_netcdf(nc_file, "w", encoding=encoding)

    # del ChillHours
    # return result_dict


# Precipitation Metrics
def get_mean_pr(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual and seasonal mean maximum daily temperature.
    index = f"mean_pr"
    print("Metric:", index)
    varname = "pr"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    PRmean = xr.Dataset()

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        if season == "ANN":
            PRmean["ANN"] = S.annual_stats("mean")
        else:
            PRmean[season] = S.seasonal_stats(season, "mean")

    PRmean = update_nc_attrs(PRmean, dec_mode, drop_incomplete_djf, annual_strict)
    # Compute statistics
    result_dict = metrics_json(
        {index: PRmean}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            if season == "ANN":
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/annual/{varname}/"
                ).replace("$index", "_".join([index, season]))
            else:
                fig_file1 = fig_file.replace(
                    "/plots/", f"/plots/seasonal/{varname}/"
                ).replace("$index", "_".join([index, season]))
            PRmean[season].mean("time").plot(
                cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"Average {season} Daily Precipitation")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    if nc_file is not None:
        out_means = []
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            out_means.append(PRmean[season].mean(dim="time"))

        da_out = xr.concat(out_means, dim="season")
        da_out = da_out.assign_coords(
            season=("season", ["ANN", "DJF", "MAM", "JJA", "SON"])
        )

        # if season == "ANN":
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        # else:
        #     nc_file = nc_file.replace("/netcdf/", f"/netcdf/seasonal/{varname}/").replace("$index", index)

        da_out.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_out

    del PRmean
    return result_dict


def get_monthly_mean_pr(
    ds,
    sftlf,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Monthly mean precipitation

    index_base = "monthly_mean_pr"
    varname = "pr"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    PRmonmean = xr.Dataset()

    for month in range(1, 13):
        index = index_base.replace("monthly", S.month_lookup[month])
        print("Metric:", index)
        PRmonmean[S.month_lookup[month]] = S.monthly_stats(month, "mean")

    PRmonmean = update_nc_attrs(PRmonmean, dec_mode, drop_incomplete_djf, annual_strict)

    if fig_file is not None:
        for month in range(1, 13):
            index = index_base.replace("monthly", S.month_lookup[month])
            fig_file1 = fig_file.replace(
                "/plots/", f"/plots/monthly/{varname}/"
            ).replace("$index", index)
            PRmonmean[S.month_lookup[month]].mean("time").plot(
                cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]}
            )
            plt.title(f"{S.month_lookup[month]} Mean Precipitation")
            ax = plt.gca()
            ax.set_facecolor(bgclr)
            plt.savefig(fig_file1)
            plt.close()

    # Compute statistics
    result_dict = metrics_json(
        {index_base: PRmonmean}, obs_dict={}, region="land", regrid=False
    )

    if nc_file is not None:
        names = []
        means = []
        for month in range(1, 13):
            month_name = S.month_lookup[month]
            mean_val = PRmonmean[month_name].mean(dim="time")

            means.append(mean_val)
            names.append(month_name)

        da_mean = xr.concat(means, dim="month")
        da_mean = da_mean.assign_coords(month=("month", names))
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/monthly/{varname}/").replace(
            "$index", index_base
        )
        da_mean.to_dataset(name=varname).to_netcdf(nc_file, "w")
        del da_mean

    del PRmonmean
    return result_dict


def get_pr_q50(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "pr_q50"
    varname = "pr"
    lat_name = get_latitude_key(ds)
    lon_name = get_longitude_key(ds)
    print("Metric:", index)

    # Need at least 1mm rain
    # ds[varname] = ds[varname].where(ds[varname] >= 1)

    # Set up empty dataset
    PRq50 = xr.zeros_like(ds)
    PRq50[lat_name] = ds[lat_name]
    PRq50[lon_name] = ds[lon_name]
    PRq50 = PRq50.drop_vars(["time", "time_bnds", varname], errors="ignore")

    if isinstance(ds[varname], dask.array.core.Array):
        PRq50["q50"] = ds[varname].chunk({"time": -1}).median("time")
    else:
        PRq50["q50"] = ds[varname].median("time")

    PRq50 = update_nc_attrs(PRq50, dec_mode, drop_incomplete_djf, annual_strict)

    result_dict = metrics_json({index: PRq50}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", index
        )
        PRq50["q50"].plot(cmap="BuPu", cbar_kwargs={"label": "mm"})
        plt.title("Time-median Daily Precipitation")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        PRq50.to_netcdf(nc_file, "w")

    del PRq50
    return result_dict


def get_pr_q95p0(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "pr_q95p0"
    varname = "pr"
    print("Metric:", index)
    lat_name = get_latitude_key(ds)
    lon_name = get_longitude_key(ds)

    # Need at least 1mm rain
    # ds[varname] = ds[varname].where(ds[varname] >= 1)

    # Set up empty dataset
    PRq95p0 = xr.zeros_like(ds)
    PRq95p0[lat_name] = ds[lat_name]
    PRq95p0[lon_name] = ds[lon_name]
    PRq95p0 = PRq95p0.drop_vars(["time", "time_bnds", varname], errors="ignore")

    # PRISM threw errors if chunk not specified
    PRq95p0["q95p0"] = ds[varname].chunk({"time": -1}).quantile(0.950, dim="time")
    PRq95p0 = update_nc_attrs(PRq95p0, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {index: PRq95p0}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", index
        )
        PRq95p0["q95p0"].plot(
            cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("95th Percentile Daily precipitation")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        PRq95p0.to_netcdf(nc_file, "w")

    del PRq95p0
    return result_dict


def get_pr_q99p0(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "pr_q99p0"
    varname = "pr"
    print("Metric:", index)
    lat_name = get_latitude_key(ds)
    lon_name = get_longitude_key(ds)

    # Need at least 1mm rain
    # ds[varname] = ds[varname].where(ds[varname] >= 1)

    # Set up empty dataset
    PRq99p0 = xr.zeros_like(ds)
    PRq99p0[lat_name] = ds[lat_name]
    PRq99p0[lon_name] = ds[lon_name]
    PRq99p0 = PRq99p0.drop_vars(["time", "time_bnds", varname], errors="ignore")

    # PRISM threw errors if chunk not specified
    PRq99p0["q99p0"] = ds[varname].chunk({"time": -1}).quantile(0.990, dim="time")
    PRq99p0 = update_nc_attrs(PRq99p0, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {index: PRq99p0}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "q99p0"])
        )
        PRq99p0["q99p0"].plot(
            cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("99th Percentile Daily precipitation")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        PRq99p0.to_netcdf(nc_file, "w")

    del PRq99p0
    return result_dict


def get_pr_q99p9(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "pr_q99p9"
    varname = "pr"
    print("Metric:", index)
    lat_name = get_latitude_key(ds)
    lon_name = get_longitude_key(ds)

    # Need at least 1mm rain
    ds[varname] = ds[varname].where(ds[varname] >= 1)

    # Set up empty dataset
    PRq99p9 = xr.zeros_like(ds)
    PRq99p9[lat_name] = ds[lat_name]
    PRq99p9[lon_name] = ds[lon_name]
    PRq99p9 = PRq99p9.drop_vars(["time", "time_bnds", varname], errors="ignore")

    # PRISM threw errors if chunk not specified
    PRq99p9["q99p9"] = ds[varname].chunk({"time": -1}).quantile(0.999, dim="time")
    PRq99p9 = update_nc_attrs(PRq99p9, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {index: PRq99p9}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "q99p9"])
        )
        PRq99p9["q99p9"].plot(
            cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("99.9th percentile daily precipitation")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        PRq99p9.to_netcdf(nc_file, "w")

    del PRq99p9
    return result_dict


def get_annual_pxx(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    varname = "pr"
    index = "annual_pxx"
    print("Metric:", index)

    # Get annual max precipitation
    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    Pmax = xr.Dataset()
    Pmax["ANN"] = S.annual_stats("max")
    Pmax = update_nc_attrs(Pmax, dec_mode, drop_incomplete_djf, annual_strict)

    return Pmax

    # result_dict = metrics_json({index: Pmax}, obs_dict={}, region="land", regrid=False)

    # if fig_file is not None:
    #     fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
    #         "$index", "_".join([index, "ANN"])
    #     )
    #     Pmax["ANN"].mean("time").plot(cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]})
    #     plt.title("Average annual maximum daily precipitation")
    #     ax = plt.gca()
    #     ax.set_facecolor(bgclr)
    #     plt.savefig(fig_file1)
    #     plt.close()

    # if nc_file is not None:
    #     nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace("$index", index)
    #     Pmax.mean(dim="time").to_netcdf(nc_file, "w")

    # del Pmax
    # return result_dict


def get_annual_pr_total(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    varname = "pr"
    index = "annual_ptot"
    print("Metric:", index)

    PR = TimeSeriesData(ds, varname)

    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    Ptot = xr.Dataset()
    Ptot["ANN"] = S.annual_stats("total")
    Ptot = update_nc_attrs(Ptot, dec_mode, drop_incomplete_djf, annual_strict)

    return Ptot

    # result_dict = metrics_json({index: Ptot}, obs_dict={}, region="land", regrid=False)

    # if fig_file is not None:
    #     fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
    #         "$index", "_".join([index, "ANN"])
    #     )
    #     Ptot["ANN"].mean("time").plot(cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]})
    #     plt.title("Average annual total daily precipitation")
    #     ax = plt.gca()
    #     ax.set_facecolor(bgclr)
    #     plt.savefig(fig_file1)
    #     plt.close()

    # if nc_file is not None:
    #     nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace("$index", index)
    #     Ptot.mean(dim="time").to_netcdf(nc_file, "w")

    # del Ptot
    # return result_dict


def get_annual_pr_ge_X(
    ds,
    sftlf,
    threshold,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    varname = "pr"
    unit_str = ds[varname].attrs["units"]
    out_unit_str = f"{threshold.units:~}"
    data_units = Unit(f"{unit_str}")  # Assumes degrees "K", "F", or "C"

    index = "annual_pr_ge_{0}{1}".format(threshold.magnitude, out_unit_str)
    print("Metric:", index)
    threshold_pint_converted = threshold.to(data_units)

    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    PRgeX = xr.Dataset()
    PRgeX["ANN"] = S.annual_stats("ge{0}".format(threshold_pint_converted.magnitude))

    PRgeX.attrs["units"] = "%"
    PRgeX = update_nc_attrs(PRgeX, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: PRgeX}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        PRgeX["ANN"].mean("time").plot(
            cmap="RdPu", vmin=0, vmax=100, cbar_kwargs={"label": "%"}
        )
        plt.title(
            "Mean percentage of days per year\nwith precip >= {0}{1}".format(
                threshold.magnitude, out_unit_str
            )
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        PRgeX.mean(dim="time").to_netcdf(nc_file, "w")

    del PRgeX
    return result_dict


def get_pr_days_above_Qth(
    ds,
    sftlf,
    quantile,
    file_name_ref_pr_quant,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
    non_zero=False,
):
    # open the reference dataset
    ds_reference = xr.open_dataset(file_name_ref_pr_quant)[f"q{quantile}"].copy(
        deep=True
    )

    # Get annual fraction of days with precip > observations quanitle
    if non_zero:
        index = f"pr_days_above_non_zero_q{quantile}"
    else:
        index = f"pr_days_above_q{quantile}"
    print("Metric:", index)
    varname = "pr"

    # Rechunk Dask Arrays
    if isinstance(ds[varname], dask.array.core.Array):
        ds[varname] = ds[varname].chunk({"time": -1})

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    PRgeQuant = xr.Dataset()
    PRgeQuant["ANN"] = S.annual_stats("ge_q{0}".format(quantile), ref_da=ds_reference)
    PRgeQuant.attrs["units"] = "%"
    PRgeQuant = update_nc_attrs(PRgeQuant, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: PRgeQuant}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:  # save the figure
        nz_str = ""
        if non_zero:
            nz_str = "Non-Zero "
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        PRgeQuant["ANN"].mean("time").plot(
            cmap="Blues",
            vmin=np.nanmin(PRgeQuant["ANN"].mean("time").data),
            vmax=np.nanmax(PRgeQuant["ANN"].mean("time").data),
            cbar_kwargs={"label": "%"},
        )
        plt.title(
            f"Mean percentage of days per year\nwith precipitation >= {nz_str}q{quantile}"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        PRgeQuant.mean(dim="time").to_netcdf(nc_file, "w")

    del PRgeQuant
    return result_dict


def get_pr_sum_above_Qth(
    ds,
    sftlf,
    quantile,
    file_name_ref_pr_quant,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Will always be the quantile including zero precipitation

    # open the reference dataset
    ds_reference = xr.open_dataset(file_name_ref_pr_quant)[f"q{quantile}"].copy(
        deep=True
    )

    # Get annual fraction of days with precip > observations quanitle
    index = f"pr_sum_above_q{quantile}"
    print("Metric:", index)
    varname = "pr"

    # Rechunk Dask Arrays
    if isinstance(ds[varname], dask.array.core.Array):
        ds[varname] = ds[varname].chunk({"time": -1})

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    PRSUMgeQuant = xr.Dataset()
    PRSUMgeQuant["ANN"] = S.annual_stats("sum_gt_q", ref_da=ds_reference)
    PRSUMgeQuant.attrs["units"] = ds[varname].attrs["units"]
    PRSUMgeQuant = update_nc_attrs(
        PRSUMgeQuant, dec_mode, drop_incomplete_djf, annual_strict
    )

    # Compute statistics
    result_dict = metrics_json(
        {index: PRSUMgeQuant}, obs_dict={}, region="land", regrid=False
    )

    if fig_file is not None:  # save the figure
        fig_file1 = fig_file.replace("/plots/", f"/plots/quantile/{varname}/").replace(
            "$index", "_".join([index, "ANN"])
        )
        PRSUMgeQuant["ANN"].mean("time").plot(
            cmap="Blues",
            vmin=np.nanmin(PRSUMgeQuant["ANN"].mean("time").data),
            vmax=np.nanmax(PRSUMgeQuant["ANN"].mean("time").data),
            cbar_kwargs={"label": ds[varname].attrs["units"]},
        )
        plt.title(
            f"Percent of Total Precipitation per year on Days\nwith precipitation >= q{quantile}"
        )
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/quantile/{varname}/").replace(
            "$index", index
        )
        PRSUMgeQuant.mean(dim="time").to_netcdf(nc_file, "w")

    del PRSUMgeQuant
    return result_dict


def get_annual_pr_nday(
    ds,
    sftlf,
    n,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
):
    # Annual highest maximum precipitation over a 5-day period
    index = f"annual_max_precip_{n}day_total"
    print("Metric:", index)
    varname = "pr"

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    PRmaxNday = xr.Dataset()
    PRmaxNday["ANN"] = (
        S.annual_stats("max", nTuple=True, n=n) * n
    )  # Multiply by n to get the total amount of precipitation over the n day period
    PRmaxNday = update_nc_attrs(PRmaxNday, dec_mode, drop_incomplete_djf, annual_strict)

    return PRmaxNday
    # # Compute statistics
    # result_dict = metrics_json(
    #     {index: PRmaxNday}, obs_dict={}, region="land", regrid=False
    # )

    # if fig_file is not None:
    #     fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
    #         "$index", "_".join([index, "ANN"])
    #     )
    #     PRmaxNday["ANN"].mean("time").plot(cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]})
    #     plt.title(f"Annual maximum {n}-day total precipitation")
    #     ax = plt.gca()
    #     ax.set_facecolor(bgclr)
    #     plt.savefig(fig_file1)
    #     plt.close()

    # if nc_file is not None:
    #     nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace("$index", index)
    #     PRmaxNday.mean(dim="time").to_netcdf(nc_file, "w")

    # del PRmaxNday
    # return result_dict


def get_wettest_5yr(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    varname = "pr"
    index = "wettest_5yr"
    print("Metric:", index)

    # Get annual max precipitation
    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    Pmax = xr.Dataset()
    Pmax["ANN"] = S.annual_stats("max")

    # Get number of 5 year segments
    nseg = int(np.floor(len(Pmax.time) / 5))
    lo = int(len(Pmax.time)) % 5  # leftover

    # Set up empty dataset
    P5 = xr.zeros_like(Pmax.isel({"time": slice(0, nseg)}))
    P5["lat"] = Pmax["lat"]
    P5["lon"] = Pmax["lon"]

    # Will be updated time for 5 year quantity
    timelist = []

    # Fill dataset
    for seg in range(0, nseg):
        start = lo + 5 * seg
        end = lo + 5 * (seg + 1)
        myslice = (
            Pmax["ANN"].isel({"time": slice(start, end)}).max("time").compute().data
        )
        mytime = Pmax["time"].isel({"time": start}).data.item()
        timelist.append(mytime)
        P5["ANN"].loc[{"time": Pmax["time"][seg]}] = myslice

    P5["time"] = timelist
    P5.time.attrs["axis"] = "T"
    P5["time"].encoding["calendar"] = Pmax.time.encoding["calendar"]
    P5["time"].attrs["standard_name"] = "time"
    P5.time.encoding["units"] = Pmax.time.encoding["units"]
    P5 = update_nc_attrs(P5, dec_mode, drop_incomplete_djf, annual_strict)
    P5 = P5.rename({"ANN": "ANN5"})

    result_dict = metrics_json({index: P5}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/{varname}/").replace(
            "$index", "_".join([index, "ANN5"])
        )
        P5["ANN5"].mean("time").plot(
            cmap="BuPu", cbar_kwargs={"label": ds[varname].attrs["units"]}
        )
        plt.title("Average precipitation on wettest day in 5 years")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        P5.mean(dim="time").to_netcdf(nc_file, "w")
        del P5

    del Pmax
    return result_dict


def get_annual_cwd(
    ds,
    sftlf,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    fig_file=None,
    nc_file=None,
    thresh=0.254,
):
    varname = "pr"
    unit_str = ds[varname].attrs["units"]
    index = "annual_cwd"
    print("Metric:", index)

    # Attach units with Pint if not already present
    pr_units = Q_(ds[varname].data, unit_str)
    pr_mm_arr = pr_units.to("mm").magnitude
    pr_mm_da = xr.DataArray(
        pr_mm_arr,
        coords=ds[varname].coords,
        dims=ds[varname].dims,
    )
    pr_mm_da.attrs["units"] = "mm/day"
    # Get continuous wet days
    Pcwd = xr.Dataset()
    Pcwd["ANN"] = (
        xclim.indices.maximum_consecutive_wet_days(
            pr_mm_da, thresh="1 mm/day", freq="YS", resample_before_rl=True
        )
        .where(sftlf.sftlf >= 0.5)
        .where(sftlf.sftlf <= 1)
    )
    Pcwd.time.encoding["calendar"] = ds.time.encoding["calendar"]
    Pcwd = update_nc_attrs(Pcwd, dec_mode, drop_incomplete_djf, True)
    # Get continuous wet days
    # Pcwd = xr.Dataset()
    # Pcwd["ANN"] = (
    #     # xclim.indices.maximum_consecutive_wet_days(
    #     #     ds.pr, thresh="1 mm/day", freq="YS", resample_before_rl=True
    #     # )

    #     ##TODO Unit correction
    #     xclim.indices.maximum_consecutive_wet_days(
    #         ds[varname], thresh = threshold, freq="YS", resample_before_rl=True
    #     )
    #     .where(sftlf.sftlf >= 0.5)
    #     .where(sftlf.sftlf <= 1)
    # )
    # Pcwd.time.encoding["calendar"] = ds.time.encoding["calendar"]
    # Pcwd = update_nc_attrs(Pcwd, dec_mode, drop_incomplete_djf, True)

    result_dict = metrics_json({index: Pcwd}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/pr/").replace(
            "$index", "_".join([index, "ANN"])
        )
        Pcwd["ANN"].mean("time").plot(cmap="BuPu", cbar_kwargs={"label": "count"})
        plt.title("Average annual max count of consecutive wet days")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Pcwd.mean(dim="time").to_netcdf(nc_file, "w")

    del Pcwd
    return result_dict


def get_annual_consecDD(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    varname = "pr"
    unit_str = ds[varname].attrs["units"]
    index = "annual_cdd"
    print("Metric:", index)

    # Attach units with Pint if not already present
    pr_units = Q_(ds[varname].data, unit_str)
    pr_mm_arr = pr_units.to("mm").magnitude
    pr_mm_da = xr.DataArray(
        pr_mm_arr,
        coords=ds[varname].coords,
        dims=ds[varname].dims,
    )
    pr_mm_da.attrs["units"] = "mm/day"
    # Get continuous wet days
    Pcdd = xr.Dataset()
    Pcdd["ANN"] = (
        xclim.indices.maximum_consecutive_dry_days(
            pr_mm_da, thresh="1 mm/day", freq="YS", resample_before_rl=True
        )
        .where(sftlf.sftlf >= 0.5)
        .where(sftlf.sftlf <= 1)
    )
    Pcdd.time.encoding["calendar"] = ds.time.encoding["calendar"]

    Pcdd = update_nc_attrs(Pcdd, dec_mode, drop_incomplete_djf, True)

    return Pcdd

    # result_dict = metrics_json({index: Pcdd}, obs_dict={}, region="land", regrid=False)

    # if fig_file is not None:
    #     fig_file1 = fig_file.replace("/plots/", f"/plots/annual/pr/").replace(
    #         "$index", "_".join([index, "ANN"])
    #     )
    #     Pcdd["ANN"].mean("time").plot(cmap="YlOrRd", cbar_kwargs={"label": "count"})
    #     plt.title("Average annual max count of consecutive dry days")
    #     ax = plt.gca()
    #     ax.set_facecolor(bgclr)
    #     plt.savefig(fig_file1)
    #     plt.close()

    # if nc_file is not None:
    #     nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace("$index", index)
    #     Pcdd.mean(dim="time").to_netcdf(nc_file, "w")

    # del Pcdd
    # return result_dict


def get_JJA_consecDD(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # index = "JJA_cdd"
    # varname = "pr"
    # print("Metric:", index)

    varname = "pr"
    unit_str = ds[varname].attrs["units"]
    index = "JJA_cdd"
    print("Metric:", index)

    # Attach units with Pint if not already present
    pr_units = Q_(ds[varname].data, unit_str)
    pr_mm_arr = pr_units.to("mm").magnitude
    pr_mm_da = xr.DataArray(
        pr_mm_arr,
        coords=ds[varname].coords,
        dims=ds[varname].dims,
    )
    # Create an array like original precipitation dataArray, filled with ones
    prJJA = (
        xr.ones_like(pr_mm_da) * 10
    )  # dummmy array to only consider JJA precip < 1mm
    jja_mask = pr_mm_da.time.dt.month.isin([6, 7, 8])
    prJJA.loc[dict(time=jja_mask)] = pr_mm_da.loc[dict(time=jja_mask)]
    prJJA.attrs["units"] = "mm/day"

    # Get continuous dry days
    Pcdd = xr.Dataset()
    Pcdd["JJA"] = (
        xclim.indices.maximum_consecutive_dry_days(
            prJJA, thresh="1 mm/day", freq="YS", resample_before_rl=True
        )
        .where(sftlf.sftlf >= 0.5)
        .where(sftlf.sftlf <= 1)
    )
    Pcdd.time.encoding["calendar"] = ds.time.encoding["calendar"]
    Pcdd = update_nc_attrs(Pcdd, dec_mode, drop_incomplete_djf, True)

    result_dict = metrics_json({index: Pcdd}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        fig_file1 = fig_file.replace("/plots/", f"/plots/annual/pr/").replace(
            "$index", "_".join([index, "ANN"])
        )
        Pcdd["JJA"].mean("time").plot(cmap="YlOrBr", cbar_kwargs={"label": "count"})
        plt.title("Average Summer max count of consecutive dry days")
        ax = plt.gca()
        ax.set_facecolor(bgclr)
        plt.savefig(fig_file1)
        plt.close()

    if nc_file is not None:
        nc_file = nc_file.replace("/netcdf/", f"/netcdf/annual/{varname}/").replace(
            "$index", index
        )
        Pcdd.to_netcdf(nc_file, "w")

    del Pcdd
    return result_dict


# Reference Dataset Functions
def get_ref_tasmax_Q(
    ds,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    nc_file=None,
    quantiles=[1, 99],
    start_year=None,
    end_year=None,
):
    varname = "tasmax"

    season_dict = {
        "ANN": range(1, 13),
        "DJF": [12, 1, 2],
        "MAM": [3, 4, 5],
        "JJA": [6, 7, 8],
        "SON": [9, 10, 11],
    }

    if (start_year is not None) and (end_year is not None):
        ds = ds.isel(
            time=((ds.time.dt.year >= start_year) & (ds.time.dt.year <= end_year))
        )

    # Set up empty dataset
    RefTmaxQ = xr.zeros_like(ds)
    RefTmaxQ["lat"] = ds["lat"]
    RefTmaxQ["lon"] = ds["lon"]
    RefTmaxQ = RefTmaxQ.drop_vars(["time", "time_bnds", varname], errors="ignore")

    for season, months in season_dict.items():
        for quant in quantiles:  # which quantiles we need for the reference period
            indexQ = f"ref_tasmax_q{quant}_{season}"
            print("Metric:", indexQ)

            if isinstance(ds[varname], dask.array.core.Array):
                RefTmaxQ[f"q{quant}_{season}"] = (
                    ds[varname]
                    .isel(time=ds.time.dt.month.isin(months))
                    .chunk({"time": -1})
                    .quantile(quant / 100, dim="time")
                )
            else:
                RefTmaxQ[f"q{quant}_{season}"] = (
                    ds[varname]
                    .isel(time=ds.time.dt.month.isin(months))
                    .chunk({"time": -1})
                    .quantile(quant / 100, dim="time")
                )

    RefTmaxQ = update_nc_attrs(RefTmaxQ, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {indexQ: RefTmaxQ}, obs_dict={}, region="land", regrid=False
    )
    # We don't want to save a figure, since this is just for reference

    index = "ref_tasmax_quantile"
    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        RefTmaxQ.to_netcdf(nc_file, "w")

    del RefTmaxQ
    return result_dict, nc_file


def get_ref_tasmin_Q(
    ds,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    nc_file=None,
    quantiles=[1, 99],
    start_year=None,
    end_year=None,
):
    varname = "tasmin"

    if (start_year is not None) and (end_year is not None):
        ds = ds.isel(
            time=((ds.time.dt.year >= start_year) & (ds.time.dt.year <= end_year))
        )

    # Set up empty dataset
    RefTminQ = xr.zeros_like(ds)
    RefTminQ["lat"] = ds["lat"]
    RefTminQ["lon"] = ds["lon"]
    RefTminQ = RefTminQ.drop_vars(["time", "time_bnds", varname], errors="ignore")

    for quant in quantiles:  # which quantiles we need for the reference period
        indexQ = f"ref_tasmin_q{quant}"
        print("Metric:", indexQ)

        if isinstance(ds[varname], dask.array.core.Array):
            RefTminQ[f"q{quant}"] = (
                ds[varname].chunk({"time": -1}).quantile(quant / 100, dim="time")
            )
        else:
            RefTminQ[f"q{quant}"] = (
                ds[varname].chunk({"time": -1}).quantile(quant / 100, dim="time")
            )
    RefTminQ = update_nc_attrs(RefTminQ, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {indexQ: RefTminQ}, obs_dict={}, region="land", regrid=False
    )
    # We don't want to save a figure, since this is just for reference

    index = "ref_tasmin_quantile"
    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        RefTminQ.to_netcdf(nc_file, "w")

    del RefTminQ
    return result_dict, nc_file


def get_ref_pr_Q(
    ds,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    nc_file=None,
    quantiles=[10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99],
    non_zero=False,
    start_year=None,
    end_year=None,
):
    varname = "pr"

    if (start_year is not None) and (end_year is not None):
        ds = ds.isel(
            time=((ds.time.dt.year >= start_year) & (ds.time.dt.year <= end_year))
        )

    # Set up empty dataset
    if non_zero:
        pr_arr = ds.copy(deep=True)["pr"].where(ds["pr"] > 0)
    else:
        pr_arr = ds.copy(deep=True)["pr"]
    RefPRQ = xr.zeros_like(ds)
    RefPRQ["lat"] = ds["lat"]
    RefPRQ["lon"] = ds["lon"]
    RefPRQ = RefPRQ.drop_vars(["time", "time_bnds", varname], errors="ignore")

    for quant in quantiles:  # which quantiles we need for the reference period
        if non_zero:
            indexQ = f"ref_pr_non_zero_q{quant}"
        else:
            indexQ = f"ref_pr_q{quant}"
        print("Metric:", indexQ)

        if isinstance(
            pr_arr, dask.array.core.Array
        ):  # When run in parallel, it won't automatically be dask...
            RefPRQ[f"q{quant}"] = pr_arr.chunk({"time": -1}).quantile(
                quant / 100, dim="time"
            )
        else:
            RefPRQ[f"q{quant}"] = pr_arr.chunk({"time": -1}).quantile(
                quant / 100, dim="time"
            )  # .chunk({"time":-1})
    RefPRQ = update_nc_attrs(RefPRQ, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {indexQ: RefPRQ}, obs_dict={}, region="land", regrid=False
    )
    # We don't want to save a figure, since this is just for reference

    index = "ref_pr_quantile"

    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        if non_zero:
            nc_file = nc_file.replace(".nc", "_non_zero.nc")
        RefPRQ.to_netcdf(nc_file, "w")

    del RefPRQ
    return result_dict, nc_file


def clip_precip(ds):
    varname = "pr"
    thresh = Q_(1, "mm")

    unit_str = ds[varname].attrs["units"]  # e.g., 'mm' or 'inches'
    data_units = Unit(unit_str)

    thresh = thresh.to(data_units).magnitude
    print(f"Precipitation Clipping Threshold: {thresh} {unit_str}")
    # Clip: set all values below threshold to 0
    clipped = ds[varname].where(ds[varname] >= thresh, 0)

    # Make a copy of the dataset and assign the clipped variable
    ds_clipped = ds.copy()
    ds_clipped[varname] = clipped

    return ds_clipped


# A couple of statistics that aren't being loaded from mean_climate
def mean_xy(data, varname):
    # print(data)
    # Spatial mean of single dataset
    if "time" in data.coords:
        mean_xy = float(
            data.spatial.average(varname)[varname].mean()
        )  # this .mean() gets the temporal mean
    else:
        # TODO: Why aren't we using pmp_stats.mean_xy ?
        mean_xy = pmp_stats.mean_xy(data, varname, weights=None)
    return mean_xy


def percent_difference(ref, bias_xy, varname, weights):
    # bias as percentage of reference dataset "ref"
    pct_dif = float(
        100.0
        * bias_xy
        / ref.spatial.average(varname, axis=["X", "Y"], weights=weights)[varname]
    )
    return pct_dif


def init_metrics_dict(
    model_list, var_list, dec_mode, drop_incomplete_djf, annual_strict, region_name
):
    # Return initial version of the metrics dictionary
    metrics = {
        "DIMENSIONS": {
            "json_structure": [
                "model",
                "realization",
                "index",
                "region",
                "statistic",
                "season",
            ],
            "region": {region_name: "Areas where 0.5<=sftlf<=1"},
            "season": ["ANN", "DJF", "MAM", "JJA", "SON"],
            "index": {},
            "statistic": {
                "mean": pmp_stats.mean_xy(None),
                "std_xy": pmp_stats.std_xy(None, None),
                "bias_xy": pmp_stats.bias_xy(None, None),
                "cor_xy": pmp_stats.cor_xy(None, None),
                "mae_xy": pmp_stats.meanabs_xy(None, None),
                "rms_xy": pmp_stats.rms_xy(None, None),
                "rmsc_xy": pmp_stats.rmsc_xy(None, None),
                "std-obs_xy": pmp_stats.std_xy(None, None),
                "pct_dif": {
                    "Abstract": "Bias xy as a percentage of the Observed mean.",
                    "Contact": "pcmdi-metrics@llnl.gov",
                    "Name": "Spatial Difference Percentage",
                },
            },
            "model": model_list,
            "realization": [],
        },
        "RESULTS": {},
        "RUNTIME_CALENDAR_SETTINGS": {
            "december_mode": str(dec_mode),
            "drop_incomplete_djf": str(drop_incomplete_djf),
            "annual_strict": str(annual_strict),
        },
    }

    # Only include the definitions for the indices in this particular analysis.
    for v in var_list:
        if v == "tasmax":
            metrics["DIMENSIONS"]["index"].update({"": ""})
            metrics["DIMENSIONS"]["index"].update({"": ""})
        if v == "tasmin":
            metrics["DIMENSIONS"]["index"].update({"": ""})
            metrics["DIMENSIONS"]["index"].update({"": ""})
        if v in ["pr", "PRECT", "precip"]:
            metrics["DIMENSIONS"]["index"].update({"": ""})
            metrics["DIMENSIONS"]["index"].update({"": ""})

    return metrics


def metrics_json(data_dict, obs_dict={}, region="land", regrid=True):
    # Format, calculate, and return the global mean value over land
    # for all datasets in the input dictionary
    # Arguments:
    #   data_dict: Dictionary containing block extrema datasets
    #   obs_dict: Dictionary containing block extrema for
    #             reference dataset
    #   region: Name of region.
    # Returns:
    #   met_dict: A dictionary containing metrics

    met_dict = {}
    seasons_dict = {"ANN": "", "DJF": "", "MAM": "", "JJA": "", "SON": ""}
    # quantile_dict = {"q50": "", 'q99p9': "", "q99p0": ""}
    months_dict = {
        "JAN": "",
        "FEB": "",
        "MAR": "",
        "APR": "",
        "MAY": "",
        "JUNE": "",
        "JULY": "",
        "AUG": "",
        "SEP": "",
        "OCT": "",
        "NOV": "",
        "DEC": "",
    }
    misc_dict = {
        key: "" for key in ["ANN5"]
    }  # "q50", "q95p0", "q99p0", "q99p9" -> Don't work because no T dimension

    # Looping over each type of extrema in data_dict
    for m in data_dict:
        met_dict[m] = {
            region: {
                "mean": {**seasons_dict, **months_dict, **misc_dict}.copy(),
                "std_xy": {**seasons_dict, **months_dict, **misc_dict}.copy(),
            }
        }
        # If obs available, add metrics comparing with obs
        # If new statistics are added, be sure to update
        # "statistic" entry in init_metrics_dict()

        if len(obs_dict) > 0:
            for k in [
                "std-obs_xy",
                "pct_dif",
                "bias_xy",
                "cor_xy",
                "mae_xy",
                "rms_xy",
                "rmsc_xy",
            ]:
                met_dict[m][region][k] = {**seasons_dict, **months_dict, **misc_dict}

        ds_m = data_dict[m]

        for season in list({**seasons_dict, **months_dict, **misc_dict}.keys()):
            if season in ds_m.data_vars:
                # Global mean over land
                met_dict[m][region]["mean"][season] = mean_xy(
                    ds_m, season
                )  # problem line
                a = ds_m.temporal.average(season)
                std_xy = pmp_stats.std_xy(a, season)
                met_dict[m][region]["std_xy"][season] = std_xy

                if len(obs_dict) > 0 and not obs_dict[m].equals(ds_m):
                    # Regrid obs to model grid
                    if regrid:
                        target = xc.create_grid(ds_m.lat, ds_m.lon)
                        target = target.bounds.add_missing_bounds(["X", "Y"])
                        obs_m = obs_dict[m].regridder.horizontal(
                            season, target, tool="regrid2"
                        )
                    else:
                        obs_m = obs_dict[m]
                        shp1 = (len(ds_m[season].lat), len(ds_m[season].lon))
                        shp2 = (len(obs_m[season].lat), len(obs_m[season].lon))
                        assert (
                            shp1 == shp2
                        ), "Model and Reference data dimensions 'lat' and 'lon' must match."

                    # Get xy stats for temporal average
                    a = ds_m.temporal.average(season)
                    b = obs_m.temporal.average(season)
                    weights = ds_m.spatial.get_weights(axis=["X", "Y"])
                    rms_xy = pmp_stats.rms_xy(a, b, var=season, weights=weights)
                    meanabs_xy = pmp_stats.meanabs_xy(a, b, var=season, weights=weights)
                    bias_xy = pmp_stats.bias_xy(a, b, var=season, weights=weights)
                    cor_xy = pmp_stats.cor_xy(a, b, var=season, weights=weights)
                    rmsc_xy = pmp_stats.rmsc_xy(a, b, var=season, weights=weights)
                    std_obs_xy = pmp_stats.std_xy(b, season)
                    pct_dif = percent_difference(b, bias_xy, season, weights)

                    met_dict[m][region]["pct_dif"][season] = pct_dif
                    met_dict[m][region]["rms_xy"][season] = rms_xy
                    met_dict[m][region]["mae_xy"][season] = meanabs_xy
                    met_dict[m][region]["bias_xy"][season] = bias_xy
                    met_dict[m][region]["cor_xy"][season] = cor_xy
                    met_dict[m][region]["rmsc_xy"][season] = rmsc_xy
                    met_dict[m][region]["std-obs_xy"][season] = std_obs_xy
            else:
                for item in met_dict[m][region]:
                    met_dict[m][region][item].pop(season)

    return met_dict
