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
        else:
            # Group by date
            if stat == "max":
                ds_ann = ds.groupby("time.year").max(dim="time")
            elif stat == "min":
                ds_ann = ds.groupby("time.year").min(dim="time")

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
        op_dict = {"add": "+", "subtract": "-", "multiply": "*", "divide": "/"}
        if str(units_adjust[1]) not in op_dict:
            print(
                "Error in units conversion. Operation must be add, subtract, multiply, or divide."
            )
            print("Skipping units conversion.")
            return data
        op = op_dict[str(units_adjust[1])]
        val = float(units_adjust[2])
        operation = "data {0} {1}".format(op, val)
        data = eval(operation)
        data.attrs["units"] = str(units_adjust[3])
    else:
        # No adjustment, but check that units attr is populated
        if "units" not in data.attrs:
            data.attrs["units"] = ""
    return data


def temperature_indices(
    ds, varname, sftlf, units_adjust, dec_mode, drop_incomplete_djf, annual_strict
):
    # Returns annual max and min of provided temperature dataset
    # Temperature input can be "tasmax" or "tasmin".

    print("Generating temperature block extrema.")

    ds[varname] = convert_units(ds[varname], units_adjust)

    TS = TimeSeriesData(ds, varname)
    S = SeasonalAverager(
        TS,
        sftlf,
        dec_mode=dec_mode,
        drop_incomplete_djf=drop_incomplete_djf,
        annual_strict=annual_strict,
    )

    Tmax = xr.Dataset()
    Tmin = xr.Dataset()
    Tmax["ANN"] = S.annual_stats("max")
    Tmin["ANN"] = S.annual_stats("min")

    for season in ["DJF", "MAM", "JJA", "SON"]:
        Tmax[season] = S.seasonal_stats(season, "max")
        Tmin[season] = S.seasonal_stats(season, "min")

    Tmax = update_nc_attrs(Tmax, dec_mode, drop_incomplete_djf, annual_strict)
    Tmin = update_nc_attrs(Tmin, dec_mode, drop_incomplete_djf, annual_strict)

    return Tmax, Tmin


def precipitation_indices(
    ds, sftlf, units_adjust, dec_mode, drop_incomplete_djf, annual_strict
):
    # Returns annual Rx1day and Rx5day of provided precipitation dataset.
    # Precipitation variable must be called "pr".
    # Input data expected to have units of kg/m2/s

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
    P1day["ANN"] = S.annual_stats("max", pentad=False)
    # Can end up with very small negative values that should be 0
    # Possibly related to this issue? https://github.com/pydata/bottleneck/issues/332
    # (from https://github.com/pydata/xarray/issues/3855)
    P1day["ANN"] = (
        P1day["ANN"].where(P1day["ANN"] > 0, 0).where(~np.isnan(P1day["ANN"]), np.nan)
    )
    for season in ["DJF", "MAM", "JJA", "SON"]:
        P1day[season] = S.seasonal_stats(season, "max", pentad=False)
        P1day[season] = (
            P1day[season]
            .where(P1day[season] > 0, 0)
            .where(~np.isnan(P1day[season]), np.nan)
        )
    P1day = update_nc_attrs(P1day, dec_mode, drop_incomplete_djf, annual_strict)

    # Rx5day
    P5day = xr.Dataset()
    P5day["ANN"] = S.annual_stats("max", pentad=True)
    P5day["ANN"] = (
        P5day["ANN"].where(P5day["ANN"] > 0, 0).where(~np.isnan(P5day["ANN"]), np.nan)
    )
    for season in ["DJF", "MAM", "JJA", "SON"]:
        P5day[season] = S.seasonal_stats(season, "max", pentad=True)
        P5day[season] = (
            P5day[season]
            .where(P5day[season] > 0, 0)
            .where(~np.isnan(P5day[season]), np.nan)
        )
    P5day = update_nc_attrs(P5day, dec_mode, drop_incomplete_djf, annual_strict)

    return P1day, P5day


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
            metrics["DIMENSIONS"]["index"].update(
                {"TXx": "Maximum value of daily maximum temperature"}
            )
            metrics["DIMENSIONS"]["index"].update(
                {"TXn": "Minimum value of daily maximum temperature"}
            )
        if v == "tasmin":
            metrics["DIMENSIONS"]["index"].update(
                {"TNx": "Maximum value of daily minimum temperature"}
            )
            metrics["DIMENSIONS"]["index"].update(
                {"TNn": "Minimum value of daily minimum temperature"}
            )
        if v in ["pr", "PRECT", "precip"]:
            metrics["DIMENSIONS"]["index"].update(
                {"Rx5day": "Maximum consecutive 5-day mean precipitation, mm/day"}
            )
            metrics["DIMENSIONS"]["index"].update(
                {"Rx1day": "Maximum daily precipitation, mm/day"}
            )

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

    return met_dict


def metrics_json_return_value(
    rv, blockex, obs, blockex_obs, stat, region="land", regrid=True
):
    # Generate metrics for stationary return value comparing model and obs
    # Arguments:
    #   rv: dataset
    #   blockex: dataset
    #   obs: dataset
    #   stat: string
    #   region: string
    #   regrid: bool
    # Returns:
    #    met_dict: dictionary
    met_dict = {stat: {}}
    seasons_dict = {"ANN": "", "DJF": "", "MAM": "", "JJA": "", "SON": ""}

    # Looping over each type of extrema in data_dict
    met_dict[stat] = {
        region: {"mean": seasons_dict.copy(), "std_xy": seasons_dict.copy()}
    }
    # If obs available, add metrics comparing with obs
    # If new statistics are added, be sure to update
    # "statistic" entry in init_metrics_dict()
    if obs is not None:
        obs = obs.bounds.add_missing_bounds()
        for k in [
            "std-obs_xy",
            "pct_dif",
            "bias_xy",
            "cor_xy",
            "mae_xy",
            "rms_xy",
            "rmsc_xy",
        ]:
            met_dict[stat][region][k] = seasons_dict.copy()

    rv_tmp = rv.copy(deep=True)

    for season in ["ANN", "DJF", "MAM", "JJA", "SON"]:
        # Global mean over land
        rv_tmp[season] = remove_outliers(rv[season], blockex[season])
        met_dict[stat][region]["mean"][season] = mean_xy(rv_tmp, season)
        std_xy = pmp_stats.std_xy(rv_tmp, season)
        met_dict[stat][region]["std_xy"][season] = std_xy

        if obs is not None and not obs[season].equals(rv_tmp):
            obs[season] = remove_outliers(obs[season], blockex_obs[season])
            # Regrid obs to model grid
            if regrid:
                target = xc.create_grid(rv_tmp.lat, rv_tmp.lon)
                target = target.bounds.add_missing_bounds(["X", "Y"])
                obs_m = obs.regridder.horizontal(season, target, tool="regrid2")
            else:
                obs_m = obs
                shp1 = (len(rv_tmp.lat), len(rv_tmp.lon))
                shp2 = (len(obs.lat), len(obs.lon))
                assert (
                    shp1 == shp2
                ), "Model and Reference data dimensions 'lat' and 'lon' must match."

            # Get xy stats for temporal average
            weights = rv_tmp.spatial.get_weights(axis=["X", "Y"])
            rms_xy = pmp_stats.rms_xy(rv_tmp, obs_m, var=season, weights=weights)
            meanabs_xy = pmp_stats.meanabs_xy(
                rv_tmp, obs_m, var=season, weights=weights
            )
            bias_xy = pmp_stats.bias_xy(rv_tmp, obs_m, var=season, weights=weights)
            cor_xy = pmp_stats.cor_xy(rv_tmp, obs_m, var=season, weights=weights)
            rmsc_xy = pmp_stats.rmsc_xy(rv_tmp, obs_m, var=season, weights=weights)
            std_obs_xy = pmp_stats.std_xy(rv_tmp, season)
            pct_dif = percent_difference(obs_m, bias_xy, season, weights)

            met_dict[stat][region]["pct_dif"][season] = pct_dif
            met_dict[stat][region]["rms_xy"][season] = rms_xy
            met_dict[stat][region]["mae_xy"][season] = meanabs_xy
            met_dict[stat][region]["bias_xy"][season] = bias_xy
            met_dict[stat][region]["cor_xy"][season] = cor_xy
            met_dict[stat][region]["rmsc_xy"][season] = rmsc_xy
            met_dict[stat][region]["std-obs_xy"][season] = std_obs_xy

    return met_dict


def remove_outliers(rv, blockex):
    # Remove outlier return values for metrics computation
    # filtering by comparing to the block extreme values
    # rv: data array
    # blckex: data array
    block_max = blockex.max("time", skipna=True).data
    block_min = blockex.min("time", skipna=True).data
    block_std = blockex.std("time", skipna=True).data

    # Remove values that are either:
    # 8 standard deviations above the max value in block extema
    # 8 standard deviations below the min value in block extrema
    tol = 8 * block_std
    plussig = block_max + tol
    minsig = block_min - tol
    rv_remove_outliers = rv.where((rv < plussig) & (rv > minsig))
    return rv_remove_outliers
