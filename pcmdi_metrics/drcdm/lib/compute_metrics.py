#!/usr/bin/env python
import datetime

import cftime
import numpy as np
import xarray as xr
import xcdat as xc

from pcmdi_metrics.stats import compute_statistics_dataset as pmp_stats


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

        if self.year_end < self.year_beg + 1:
            raise Exception("Error: Final year must be greater than beginning year.")

        self.year_range = np.arange(self.year_beg, self.year_end + 1, 1)

    def return_data_array(self):
        return self.ds[self.ds_var]

    def rolling_5day(self):
        # Use on daily data
        return self.ds[self.ds_var].rolling(time=5).mean()


class SeasonalAverager:
    # Make seasonal averages of data in TimeSeriesData class

    def __init__(
        self, TSD, sftlf, dec_mode="DJF", drop_incomplete_djf=True, annual_strict=True
    ):
        self.TSD = TSD
        self.dec_mode = dec_mode
        self.drop_incomplete_djf = drop_incomplete_djf
        self.annual_strict = annual_strict
        self.del1d = datetime.timedelta(days=1)
        self.del0d = datetime.timedelta(days=0)
        self.pentad = None
        self.sftlf = sftlf["sftlf"]

    def masked_ds(self, ds):
        # Mask land where 0.5<=sftlf<=1
        return ds.where(self.sftlf >= 0.5).where(self.sftlf <= 1)

    def calc_5day_mean(self):
        # Get the 5-day mean dataset
        self.pentad = self.TSD.rolling_5day()

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

    def annual_stats(self, stat, pentad=False):
        # Acquire annual statistics
        # Arguments:
        #     stat: Can be "max", "min"
        #     pentad: True to run on 5-day mean
        # Returns:
        #     ds_ann: Dataset containing annual max or min grid

        if pentad:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.TSD.return_data_array()
        cal = self.TSD.calendar

        if self.annual_strict and pentad:
            # This setting is for means using 5 day rolling average values, where
            # we do not want to include any data from the prior year
            year_range = self.TSD.year_range
            hr = int(ds.time[0].dt.hour)  # get hour to help with selecting nearest time

            # Only use data from that year - start on Jan 5 avg
            date_range = [
                xr.cftime_range(
                    start=cftime.datetime(year, 1, 5, hour=hr, calendar=cal)
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
                    .quantile(num, dim="time")
                )
            elif stat.startswith("ge"):
                num = int(stat.replace("ge", ""))
                ds_ann = (
                    ds.where(ds >= num)
                    .groupby("time.year")
                    .sel(time=date_range, method="nearest")
                    .count(dim="time")
                    / ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .count(dim="time")
                    * 100
                )
            elif stat.startswith("le"):
                num = int(stat.replace("le", ""))
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
            elif stat.startswith("q"):
                num = float(stat.replace("q", "").replace("p", ".")) / 100.0
                ds_ann = ds.groupby("time.year").quantile(num, dim="time")
            elif stat.startswith("ge"):
                num = int(stat.replace("ge", ""))
                ds_ann = (
                    ds.where(ds >= num).groupby("time.year").count(dim="time")
                    / ds.groupby("time.year").count(dim="time")
                    * 100
                )
            elif stat.startswith("le"):
                num = int(stat.replace("le", ""))
                ds_ann = (
                    ds.where(ds <= num).groupby("time.year").count(dim="time")
                    / ds.groupby("time.year").count(dim="time")
                    * 100
                )

        # Need to fix time axis if groupby operation happened
        if "year" in ds_ann.coords:
            ds_ann = self.fix_time_coord(ds_ann)
        return self.masked_ds(ds_ann)

    def seasonal_stats(self, season, stat, pentad=False):
        # Acquire statistics for a given season
        # Arguments:
        #     season: Can be "DJF","MAM","JJA","SON"
        #     stat: Can be "max", "min"
        #     pentad: True to run on 5-day mean
        # Returns:
        #     ds_stat: Dataset containing seasonal max or min grid

        year_range = self.TSD.year_range

        if pentad:
            if self.pentad is None:
                self.calc_5day_mean()
            ds = self.pentad
        else:
            ds = self.TSD.return_data_array()
        cal = self.TSD.calendar

        hr = int(ds.time[0].dt.hour)  # help with selecting nearest time

        if season == "DJF" and self.dec_mode == "DJF":
            # Resample DJF to count prior DJF in current year
            if stat == "max":
                ds_stat = ds.resample(time="QS-DEC").max(dim="time")
            elif stat == "min":
                ds_stat = ds.resample(time="QS-DEC").min(dim="time")
            elif stat == "mean":
                ds_stat = ds.resample(time="QS-DEC").mean(dim="time")
            elif stat == "median":
                ds_stat = ds.resample(time="QS-DEC").median(dim="time")

            ds_stat = ds_stat.isel(time=ds_stat.time.dt.month.isin([12]))

            # Deal with inconsistencies between QS-DEC calendar and block exremes calendar
            if self.drop_incomplete_djf:
                ds_stat = ds_stat.sel(
                    {"time": slice(str(year_range[0]), str(year_range[-1] - 1))}
                )
                ds_stat["time"] = [
                    cftime.datetime(y, 1, 1, calendar=cal)
                    for y in np.arange(year_range[0] + 1, year_range[-1] + 1)
                ]
            else:
                ds_stat = ds_stat.sel(
                    {"time": slice(str(year_range[0] - 1), str(year_range[-1] - 1))}
                )
                ds_stat["time"] = [
                    cftime.datetime(y, 1, 1, calendar=cal)
                    for y in np.arange(year_range[0], year_range[-1] + 1)
                ]

        elif season == "DJF" and self.dec_mode == "JFD":
            # Make date lists that capture JF and D in all years, then merge and sort
            if self.annual_strict and pentad:
                # Only use data from that year - start on Jan 5 avg
                date_range_1 = [
                    xr.cftime_range(
                        start=cftime.datetime(year, 1, 5, hour=hr, calendar=cal)
                        - self.del0d,
                        end=cftime.datetime(year, 3, 1, hour=hr, calendar=cal)
                        - self.del1d,
                        freq="D",
                        calendar=cal,
                    )
                    for year in year_range
                ]
            else:
                date_range_1 = [
                    xr.cftime_range(
                        start=cftime.datetime(year, 1, 1, hour=hr, calendar=cal)
                        - self.del0d,
                        end=cftime.datetime(year, 3, 1, hour=hr, calendar=cal)
                        - self.del1d,
                        freq="D",
                        calendar=cal,
                    )
                    for year in year_range
                ]
            date_range_1 = [item for sublist in date_range_1 for item in sublist]
            date_range_2 = [
                xr.cftime_range(
                    start=cftime.datetime(year, 12, 1, hour=hr, calendar=cal)
                    - self.del0d,
                    end=cftime.datetime(year + 1, 1, 1, hour=hr, calendar=cal)
                    - self.del1d,
                    freq="D",
                    calendar=cal,
                )
                for year in year_range
            ]
            date_range_2 = [item for sublist in date_range_2 for item in sublist]
            date_range = sorted(date_range_1 + date_range_2)

            if stat == "max":
                ds_stat = (
                    ds.sel(
                        time=date_range, method="nearest"
                    )  # could also do ds.sel(time = slice(*(begin_cftime, end_cftime)))
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
            elif stat == "median":
                ds_stat = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .median(dim="time")
                )

        else:  # Other 3 seasons
            dates = {  # Month/day tuples
                "MAM": [(3, 1), (6, 1)],
                "JJA": [(6, 1), (9, 1)],
                "SON": [(9, 1), (12, 1)],
            }

            mo_st = dates[season][0][0]
            day_st = dates[season][0][1]
            mo_en = dates[season][1][0]
            day_en = dates[season][1][1]

            cal = self.TSD.calendar

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
            elif stat == "median":
                ds_stat = (
                    ds.sel(time=date_range, method="nearest")
                    .groupby("time.year")
                    .median(dim="time")
                )

        # Need to fix time axis if groupby operation happened
        if "year" in ds_stat.coords:
            ds_stat = self.fix_time_coord(ds_stat)
        return self.masked_ds(ds_stat)


def update_nc_attrs(ds, dec_mode, drop_incomplete_djf, annual_strict):
    # Add bounds and record user settings in attributes
    # Use this function for any general dataset updates.
    ds.lat.attrs["standard_name"] = "Y"
    ds.lon.attrs["standard_name"] = "X"
    bnds_dict = {"lat": "Y", "lon": "X", "time": "T"}
    for item in bnds_dict:
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
    ds.lat.encoding["_FillValue"] = None
    ds.lon.encoding["_FillValue"] = None
    ds.time.encoding["_FillValue"] = None
    ds.lat_bnds.encoding["_FillValue"] = None
    ds.lon_bnds.encoding["_FillValue"] = None
    ds.time_bnds.encoding["_FillValue"] = None
    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
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
            "KtoF": "-273)*(9/5)+32",
        }
        if str(units_adjust[1]) not in op_dict:
            print(
                "Error in units conversion. Operation must be add, subtract, multiply, or divide."
            )
            print("Skipping units conversion.")
            return data
        op = op_dict[str(units_adjust[1])]
        val = float(units_adjust[2])
        if units_adjust[1] in ["KtoF", "CtoF"]:
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


def get_mean_tasmax(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual and seasonal mean maximum daily temperature.
    index = "mean_tasmax"
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
    Tmean["ANN"] = S.annual_stats("mean")
    for season in ["DJF", "MAM", "JJA", "SON"]:
        Tmean[season] = S.seasonal_stats(season, "mean")
    Tmean = update_nc_attrs(Tmean, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmean}, obs_dict={}, region="land", regrid=False)

    if fig_file is not None:
        # Figures:
        # Map of time mean value of Tmean
        #

        # can replace the $index substring with any other string
        # for specific file name. fig_file already contains the
        # rest of the file path and the model and run names.
        fig_file1 = fig_file.replace("$index", index)
        print(fig_file1)

    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        Tmean.to_netcdf(nc_file, "w")

    del Tmean
    return result_dict


def get_annual_txx(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual max of maximum daily temperature.
    index = "annual_txx"
    print(index)
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

    del Tmax
    return result_dict


def get_tasmax_q50(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual median maximum daily temperature
    index = "tasmax_q50"
    varname = "tasmax"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tmedian = xr.Dataset()
    Tmedian["ANN"] = S.annual_stats("median")
    Tmedian = update_nc_attrs(Tmedian, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tmedian}, obs_dict={}, region="land", regrid=False
    )

    del Tmedian
    return result_dict


def get_tasmax_q99p9(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual 99.9 percentile maximum daily temperature.
    index = "tasmax_q99p9"
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
    Tq99p9 = xr.Dataset()
    Tq99p9["ANN"] = S.annual_stats("q99p9")
    Tq99p9 = update_nc_attrs(Tq99p9, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tq99p9}, obs_dict={}, region="land", regrid=False
    )

    del Tq99p9
    return result_dict


def get_annual_tasmax_ge_95F(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual fraction of days with max temperature greater than or equal to 95F
    index = "annual_tasmax_ge_95F"
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
    Tge95 = xr.Dataset()
    Tge95["ANN"] = S.annual_stats("ge95")
    Tge95.attrs["units"] = "%"
    Tge95 = update_nc_attrs(Tge95, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tge95}, obs_dict={}, region="land", regrid=False)

    del Tge95
    return result_dict


def get_annual_tasmax_ge_100F(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual fraction of days with max temperature greater than or equal to 100F
    index = "annual_tasmax_ge_100F"
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
    Tge100 = xr.Dataset()
    Tge100["ANN"] = S.annual_stats("ge95")
    Tge100.attrs["units"] = "%"
    Tge100 = update_nc_attrs(Tge100, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json(
        {index: Tge100}, obs_dict={}, region="land", regrid=False
    )

    del Tge100
    return result_dict


def get_annual_tasmax_ge_105F(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual fraction of days with max temperature greater than or equal to 105F
    index = "annual_tasmax_ge_105F"
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
    Tge105 = xr.Dataset()
    Tge105["ANN"] = S.annual_stats("ge95")
    Tge105.attrs["units"] = "%"
    Tge105 = update_nc_attrs(Tge105, dec_mode, drop_incomplete_djf, annual_strict)

    # Do plots or saving files here

    # Compute statistics
    result_dict = metrics_json(
        {index: Tge105}, obs_dict={}, region="land", regrid=False
    )

    del Tge105
    return result_dict


def get_annual_tnn(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual minimum daily minimum temperature.
    index = "annual_tnn"
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
    Tmean["ANN"] = S.annual_stats("mean")
    Tmean = update_nc_attrs(Tmean, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmean}, obs_dict={}, region="land", regrid=False)

    del Tmean
    return result_dict


def get_annualmean_tasmin(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual mean daily minimum temperature.
    index = "annualmean_tasmin"
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
    Tmin = xr.Dataset()
    Tmin["ANN"] = S.annual_stats("min")
    Tmin = update_nc_attrs(Tmin, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tmin}, obs_dict={}, region="land", regrid=False)

    del Tmin
    return result_dict


def get_annual_tasmin_le_32F(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    # Get annual percentage of days with daily minimum temperature less than or
    # equal to 32F.
    index = "annual_tasmin_le_32F"
    varname = "tasmin"
    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    Tle32 = xr.Dataset()
    Tle32["ANN"] = S.annual_stats("le32")
    Tle32.attrs["units"] = "%"
    Tle32 = update_nc_attrs(Tle32, dec_mode, drop_incomplete_djf, annual_strict)

    # Compute statistics
    result_dict = metrics_json({index: Tle32}, obs_dict={}, region="land", regrid=False)

    del Tle32
    return result_dict


# TODO: Fill out precipitation metrics
def get_annualmean_pr(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "annualmean_pr"
    varname = "pr"
    print("Metric:", index)

    # Get annual mean precipitation

    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    PRmean = xr.Dataset()
    PRmean["ANN"] = S.annual_stats("mean")

    PRmean = update_nc_attrs(PRmean, dec_mode, drop_incomplete_djf, annual_strict)

    # compute statistics
    result_dict = metrics_json(
        {index: PRmean}, obs_dict={}, region="land", regrid=False
    )

    del PRmean
    return result_dict


def get_seasonalmean_pr(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "seasonalmean_pr"
    varname = "pr"
    print("Metric", index)

    # Get seasonal mean precipitation
    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    PRmean = xr.Dataset()
    for season in ["DJF", "MAM", "JJA", "SON"]:
        PRmean[season] = S.seasonal_stats(season, "mean")
    PRmean = update_nc_attrs(PRmean, dec_mode, drop_incomplete_djf, annual_strict)

    result_dict = metrics_json(
        {index: PRmean}, obs_dict={}, region="land", regrid=False
    )

    del PRmean
    return result_dict


def get_pr_q50(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "pr_q50"
    varname = "pr"
    print("Metric:", index)

    # Get median (q50) precipitation
    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    PRq50 = xr.Dataset()
    PRq50["ANN"] = S.annual_stats("median")
    PRq50 = update_nc_attrs(PRq50, dec_mode, drop_incomplete_djf, annual_strict)

    result_dict = metrics_json({index: PRq50}, obs_dict={}, region="land", regrid=False)

    del PRq50
    return result_dict


def get_pr_q99p9(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    index = "pr_q99p9"
    varname = "pr"
    print("Metric:", index)

    # Get 99.9th percentile daily precipitation
    PR = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )
    PRq99p9 = xr.Dataset()
    PRq99p9["ANN"] = S.annual_stats("q99p9")
    PRq99p9 = update_nc_attrs(PRq99p9, dec_mode, drop_incomplete_djf, annual_strict)
    result_dict = metrics_json(
        {index: PRq99p9}, obs_dict={}, region="land", regrid=False
    )

    if nc_file is not None:
        nc_file = nc_file.replace("$index", index)
        PRq99p9.to_netcdf(nc_file, "w")

    del PRq99p9
    return result_dict


def get_annual_pxx(
    ds, sftlf, dec_mode, drop_incomplete_djf, annual_strict, fig_file=None, nc_file=None
):
    varname = "pr"
    index = "annual_pxx"

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

    result_dict = metrics_json({index: Pmax}, obs_dict={}, region="land", regrid=False)

    del Pmax
    return result_dict


def precipitation_indices(
    ds, sftlf, units_adjust, dec_mode, drop_incomplete_djf, annual_strict
):
    # TODO: the precipitation metrics need to be broken out the way the
    # temperature metrics were.

    # annualmean_pr, seasonalmean_pr, pr_q50, pr_q99p9, annual pxx

    print("Generating precipitation block extrema.")

    ds["pr"] = convert_units(ds["pr"], units_adjust)

    PR = TimeSeriesData(ds, "pr")
    S = SeasonalAverager(
        PR,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    # Rx1day
    P1day = xr.Dataset()
    P1day["ANN"] = S.annual_stats("mean", pentad=False)
    # Can end up with very small negative values that should be 0
    # Possibly related to this issue? https://github.com/pydata/bottleneck/issues/332
    # (from https://github.com/pydata/xarray/issues/3855)
    P1day["ANN"] = (
        P1day["ANN"].where(P1day["ANN"] > 0, 0).where(~np.isnan(P1day["ANN"]), np.nan)
    )
    for season in ["DJF", "MAM", "JJA", "SON"]:
        P1day[season] = S.seasonal_stats(season, "mean", pentad=False)
        P1day[season] = (
            P1day[season]
            .where(P1day[season] > 0, 0)
            .where(~np.isnan(P1day[season]), np.nan)
        )
    P1day = update_nc_attrs(P1day, dec_mode, drop_incomplete_djf, annual_strict)

    return P1day


# A couple of statistics that aren't being loaded from mean_climate
def mean_xy(data, varname):
    # Spatial mean of single dataset
    mean_xy = data.spatial.average(varname)[varname].mean()
    return float(mean_xy)


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

    # Looping over each type of extrema in data_dict
    for m in data_dict:
        met_dict[m] = {
            region: {"mean": seasons_dict.copy(), "std_xy": seasons_dict.copy()}
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
                met_dict[m][region][k] = seasons_dict.copy()

        ds_m = data_dict[m]
        for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
            if season in ds_m:
                # Global mean over land
                met_dict[m][region]["mean"][season] = mean_xy(ds_m, season)
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