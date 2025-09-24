#!/usr/bin/env python

# QBO-MJO Metric Prototyping

import json
import os

import xarray as xr
import xcdat as xc
from kf_filter import KFfilter
from utils import (
    diag_plot,
    generate_target_grid,
    select_time_range,
    standardize_lat_lon_name_in_dataset,
    test_plot_maps,
    test_plot_time_series,
)

from pcmdi_metrics.mean_climate.lib import load_and_regrid


def main():
    # model = "CESM2"
    model = "ERA5"

    if model == "CESM2":
        # User-defining parameters
        params = {
            "model": "CESM2",
            "exp": "historical",
            "member": "r1i1p1f1",
            "input_file": "sample_data/ua_Amon_CESM2_historical_r1i1p1f1_gn_185001-201412.nc",
            "input_file2": "sample_data/rlut_day_CESM2_historical_r1i1p1f1_gn_19800101-19891231.nc",
            "varname": "ua",
            "level": 50,  # hPa (=mb)
            "varname2": "rlut",
            "start": "1981-01",
            "end": "1988-12",
            "regrid": False,
            "regrid_tool": "xesmf",
            "target_grid": "2x2",
            "taper_to_mean": True,
            "output_dir": "./output_data",
            "debug": False,
        }
    elif model == "ERA5":
        # User-defining parameters for ERA5
        params = {
            "model": "ERA5",
            "exp": None,
            "member": None,
            "input_file": "/work/lee1043/DATA/ERA5/ERA5_u50_monthly_1979-2021_rewrite.nc",
            "input_file2": "/work/lee1043/DATA/ERA5/ERA5_olr_daily_40s40n_1979-2021_rewrite.nc",
            "varname": "u50",
            "level": None,  # hPa (=mb)
            "varname2": "olr",
            "start": "1979-01",
            # "end": "2014-12",
            "end": "2010-12",
            "regrid": True,
            "regrid_tool": "xesmf",
            "target_grid": "2x2",
            "taper_to_mean": True,
            "output_dir": "./output_data",
            "debug": False,
        }

    output_metrics = process_qbo_mjo_metrics(params)
    print(output_metrics)


def process_qbo_mjo_metrics(params):
    """
    Process QBO-MJO Metric based on the provided parameters.

    Args:
        params (dict): A dictionary containing user-defined parameters.

    Returns:
        dict: A dictionary containing the calculated metrics.
    """
    output = {}

    model = params["model"]
    exp = params["exp"]
    member = params["member"]
    input_file = params["input_file"]
    input_file2 = params["input_file2"]
    varname = params["varname"]
    level = params["level"]
    varname2 = params["varname2"]
    start = params["start"]
    end = params["end"]
    regrid = params["regrid"]
    regrid_tool = params["regrid_tool"]
    target_grid = params["target_grid"]
    taper_to_mean = params["taper_to_mean"]
    output_dir = params["output_dir"]
    debug = params["debug"]

    # =======================================================================================
    # ## Part 1: U50
    #
    # 1. reads in monthly U data and handles the calendar/extracts the desired time range
    #    ( this phenomenon occurs in the recent record ~1979+)
    #
    # 2. calculates the DJF mean QBO index consistent with our paper.
    # - reads in monthly zonal wind at 50mb level
    # - calculates monthly anomalies for U50
    # - averages the data across latitudes for 10S-10N and all longitudes
    # - calculates a 3-month running mean of these and then the standard deviation
    #   of that smoothed timeseries
    # - then, we extract and average only the DJF season

    os.makedirs(output_dir, exist_ok=True)

    output_file_tag = "_" + model
    if exp is not None:
        output_file_tag += "_" + exp
    if member is not None:
        output_file_tag += "_" + member
    output_file_tag += "_" + start + "_" + end

    if regrid:
        # generate target grid
        t_grid = generate_target_grid(target_grid)

        # reads in monthly zonal wind at 50mb level
        ds = load_and_regrid(
            data_path=input_file,
            varname=varname,
            level=level,
            t_grid=t_grid,
            decode_times=True,
            regrid_tool=regrid_tool,
            debug=debug,
        )

        output_file_tag += "_" + regrid_tool + "_" + target_grid

    else:
        ds = xc.open_dataset(input_file)
        if level is not None:
            ds = ds.sel(plev=level * 100)  # hPa to Pa

    # Subset time
    ds = select_time_range(ds, start, end)

    # Standardize coordinate (lat, lon)
    ds = standardize_lat_lon_name_in_dataset(ds)

    # Subset region (latitude 10S to 10N)
    ds_region = ds.sel(lat=slice(-10, 10))

    if debug:
        print("range for u")
        print(ds_region[varname].min().values)
        print(ds_region[varname].max().values)
        print(ds_region[varname].to_numpy().shape)
        print("------------")

    # calculates monthly anomalies for U50
    # remove annaul cycle
    ds_region_ano = ds_region.temporal.departures(varname, "month")

    if debug:
        print("U anomalies")
        print(ds_region_ano[varname].min().values)
        print(ds_region_ano[varname].max().values)
        print(ds_region_ano[varname].to_numpy().shape)
        print("------------")

    # Averages the data across latitudes for 10S-10N and all longitudes
    ds_region_ano_ave = ds_region_ano.spatial.average(
        varname, axis=["X", "Y"]
    ).compute()

    if debug:
        print("range of u avgd in lat/lon")
        print(ds_region_ano_ave[varname].min().values)
        print(ds_region_ano_ave[varname].max().values)
        print(ds_region_ano_ave[varname].to_numpy().shape)

    # calculates a 3-month running mean of these and then the standard deviation of that smoothed timeseries
    ds_region_ano_ave_runningmean = (
        ds_region_ano_ave.rolling(time=3, center=True)
        .construct("window")
        .mean("window")
        .isel(time=slice(1, -1))
    )
    ds_region_ano_ave_runningmean["time_bnds"] = ds_region_ano_ave["time_bnds"].isel(
        time=slice(1, -1)
    )  # re-add missed time bnds from the above line step

    if debug:
        print("u range with seasonal smoothing")
        print(ds_region_ano_ave_runningmean[varname].min().values)
        print(ds_region_ano_ave_runningmean[varname].max().values)
        print(ds_region_ano_ave_runningmean[varname].to_numpy().shape)
        print("------")

        try:
            ds_region_ano_ave_runningmean.to_netcdf(
                os.path.join(
                    output_dir,
                    "ds_region_ano_ave_runningmean" + output_file_tag + ".nc",
                )
            )
        except Exception as e:
            print(e)
            pass

    # standard deviation (std)
    std = float(ds_region_ano_ave_runningmean[varname].std(dim="time"))
    print(
        "sd of entire qbo index - smoothed u50 anomalies averaged 10s-10n and all lons"
    )
    print(std)

    # calculate seasonal mean of the smoothed time series (to get average DJF)
    ds_region_ano_ave_runningmean_season = (
        ds_region_ano_ave_runningmean.temporal.group_average(
            varname,
            freq="season",
            season_config={
                "custom_seasons": None,
                "dec_mode": "DJF",
                "drop_incomplete_djf": True,
            },
        )
    )

    # then, we extract only the average of DJF
    ds_region_ano_ave_runningmean_season_djf = (
        ds_region_ano_ave_runningmean_season.groupby("time.season")["DJF"]
    )

    if debug:
        print("range for djf-mean qbo index")
        print(ds_region_ano_ave_runningmean_season_djf[varname].min().values)
        print(ds_region_ano_ave_runningmean_season_djf[varname].max().values)
        print(ds_region_ano_ave_runningmean_season_djf[varname].to_numpy().shape)
        print("------")

        try:
            ds_region_ano_ave_runningmean_season_djf.to_netcdf(
                os.path.join(
                    output_dir,
                    "ds_region_ano_ave_runningmean_season_djf"
                    + output_file_tag
                    + ".nc",
                )
            )
        except Exception as e:
            print(e)
            pass

    # Test plots (time series)
    if debug:
        test_plot_time_series(
            ds_region_ano_ave[varname],
            output_file=os.path.join(
                output_dir, "ds_region_ano_ave" + output_file_tag + ".png"
            ),
            std=std,
            title=f"{model} ({member})",
        )

        test_plot_time_series(
            ds_region_ano_ave_runningmean[varname],
            output_file=os.path.join(
                output_dir, "ds_region_ano_ave_runningmean" + output_file_tag + ".png"
            ),
            std=std,
            title=f"{model} ({member})",
        )

        test_plot_time_series(
            ds_region_ano_ave_runningmean_season_djf[varname],
            output_file=os.path.join(
                output_dir,
                "ds_region_ano_ave_runningmean_season_djf" + output_file_tag + ".png",
            ),
            std=std,
            title=f"{model} ({member})",
        )

    # ## Part 2: OLR
    #
    # 3. we read in daily OLR for 30S-30N, again extracting the same desired time period, and calculate the mjo-filtered OLR following wheeler and kiladis 2009.
    # - use the kf_filter function (https://github.com/tmiyachi/mcclimate/blob/master/kf_filter.py) which transforms the data to frequency space and filters out all waves except the mjo and back-transforms.
    # - use the criteria in the kf_filter for periods 20-100 days, waves 1 to 5, and wavetype kelvin to get the mjo filtered olr.
    # - then,  we extract only the DJF season
    # - and calculate the standard deviation of mjo-filtered olr for DJF

    # we read in daily OLR for 30S-30N, again extracting the same desired time period, and calculate the mjo-filtered OLR following wheeler and kiladis 2009.

    if regrid:
        ds2 = load_and_regrid(
            data_path=input_file2,
            varname=varname2,
            t_grid=t_grid,
            decode_times=True,
            regrid_tool=regrid_tool,
            debug=debug,
        )
    else:
        ds2 = xc.open_mfdataset(input_file2)

    ds2 = select_time_range(ds2, start, end)

    # Subset region
    ds2_region = ds2.sel(lat=slice(-30, 30))

    if debug:
        print("range of olr for desired time range and 30s to 30n")
        print(ds2_region[varname2].min().values)
        print(ds2_region[varname2].max().values)
        print(ds2_region[varname2].to_numpy().shape)

    # Apply KF filter
    kf = KFfilter(
        datain=ds2_region[varname2].to_numpy(),
        spd=1,
        tim_taper=0.05,
        taper_to_mean=taper_to_mean,
    )  # 5% tapering each side, following Kim et al., 2020, GRL
    kf_filtered = kf.kelvinfilter(
        fmin=0.01, fmax=0.05, kmin=1, kmax=5, hmin=0.000001, hmax=8
    )  # periods 20-100 days, waves 1 to 5, equivalent depth 0 to 8
    ds2_region["mjo_olr"] = (
        ["time", "lat", "lon"],
        kf_filtered,
    )  # Convert the numpy as xarray DataArray and add it to the DataSet

    if debug:
        print("range of mjolr")
        print(ds2_region["mjo_olr"].min().values)
        print(ds2_region["mjo_olr"].max().values)
        print(ds2_region["mjo_olr"].to_numpy().shape)

        ds2_region["window"] = (["time"], kf.window)
        ds2_region["mjo_olr_detrended"] = (["time", "lat", "lon"], kf.detrended)
        ds2_region["mjo_olr_tapered"] = (["time", "lat", "lon"], kf.tapered)

    # Extract DJF only
    ds2_region_djf = ds2_region.groupby("time.season")["DJF"]

    # Calculate the standard deviation of mjo-filtered olr for DJF
    std2_map = ds2_region_djf["mjo_olr"].std(dim="time")  # time steps collapse

    ds2_region["mjo_olr_stdmap"] = std2_map

    # ## Part 3: Diagnostics
    #
    # 4. then we partition the DJF seasons by QBO phase (easterly or westerly)
    #      - we use the threshold of +/- 0.5 standard deviation to define the QBO phase
    #      - and we partition all daily mjo-filtered olr for that DJF season into east, west, and neutral QBO phase
    #      - then take the standard deviation of QBOE mjo-filtered olr and QBOW mjo-filtered olr for plotting
    #
    # 5. currently in separate code, we plot the stddev of mjo-filtered olr for DJF along with the difference between QBOE and QBOW stddev of mjo-filtered olr.

    std2_map_phase = dict()
    qbo_phase_years = dict()

    for qbo_phase in ["east", "west"]:
        if qbo_phase == "west":
            condition = ds_region_ano_ave_runningmean_season_djf[varname] > 0.5 * std
        elif qbo_phase == "east":
            condition = ds_region_ano_ave_runningmean_season_djf[varname] < -0.5 * std

        if any(condition.values.tolist()):
            qbo_phase_ds = ds_region_ano_ave_runningmean_season_djf.where(
                condition, drop=True
            )
            qbo_phase_years[qbo_phase] = [
                t.year - 1 for t in qbo_phase_ds.indexes["time"].to_datetimeindex()
            ]  # define the year of the event by december of the djf season to simplify, thus t.year-1
            print(
                "qbo_phase, qbo_phase_year_list:", qbo_phase, qbo_phase_years[qbo_phase]
            )

            datasets = []

            for year in qbo_phase_years[qbo_phase]:
                tmp_dec = (
                    ds2_region_djf["mjo_olr"]
                    .groupby("time.year")[year]
                    .groupby("time.month")[12]
                )
                tmp_jan = (
                    ds2_region_djf["mjo_olr"]
                    .groupby("time.year")[year + 1]
                    .groupby("time.month")[1]
                )
                tmp_feb = (
                    ds2_region_djf["mjo_olr"]
                    .groupby("time.year")[year + 1]
                    .groupby("time.month")[2]
                )
                datasets.extend([tmp_dec, tmp_jan, tmp_feb])

            combined = xr.concat(datasets, dim="time")
            std2_map_phase[qbo_phase] = combined.std(dim="time")  # time steps collapse

            ds2_region["mjo_olr_stdmap_" + qbo_phase] = std2_map_phase[qbo_phase]

    std2_map_diff = std2_map_phase["east"] - std2_map_phase["west"]
    ds2_region["mjo_olr_stdmap_east_minus_west"] = std2_map_diff

    if debug:
        # Save all variables
        ds2_region.to_netcdf(
            os.path.join(output_dir, "mjo_olr" + output_file_tag + ".nc")
        )
    else:
        # Save only selected variables that is shown in the diagnostic plot
        ds2_region[
            [
                "mjo_olr_stdmap",
                "mjo_olr_stdmap_east",
                "mjo_olr_stdmap_west",
                "mjo_olr_stdmap_east_minus_west",
            ]
        ].to_netcdf(
            os.path.join(output_dir, "mjo_olr_stddev_DJF" + output_file_tag + ".nc")
        )

    # Test plot (MJO filtered OLR MAP)
    if debug:
        test_plot_maps(
            std2_map,
            std2_map_phase,
            fig_title=f"{model} ({member}): OLR DJF temporal STD map ("
            + start
            + " to "
            + end
            + ")",
            output_file=os.path.join(
                output_dir, "test_OLR_DJF_temporal_STD_map" + output_file_tag + ".png"
            ),
        )

    # Diagnostic plot: the associated plot, with the gray contour lines for mjo activity and color filled contours for the qboe-qbow mjo activity difference
    diag_plot(
        std2_map,
        std2_map_diff,
        fig_title=f"{model} ({member}): Stddev of DJF MJO-Filtered OLR",
        output_file=os.path.join(
            output_dir, "mjo_olr_stddev_DJF" + output_file_tag + ".png"
        ),
        sub_region=(50, 170, -20, 5),
    )

    # ## Part 4: Metrics

    # mjo olr activity (standard deviation) over all years average over the maritime continent region in our kim et al 2020 paper (50E-170E, 20S-5N)
    metric1 = float(
        ds2_region.spatial.average(
            data_var="mjo_olr_stdmap", lat_bounds=(-20, 5), lon_bounds=(50, 170)
        )["mjo_olr_stdmap"].values
    )

    # mjo olr activity difference between qboe and qbow averaged over the maritime continent region
    metric2 = float(
        ds2_region.spatial.average(
            data_var="mjo_olr_stdmap_east_minus_west",
            lat_bounds=(-20, 5),
            lon_bounds=(50, 170),
        )["mjo_olr_stdmap_east_minus_west"].values
    )

    print("metric1 (mjo_activity):", metric1)
    print("metric2 (mjo_activity_diff):", metric2)

    # Prepare output dictionary
    output[model] = dict()
    output[model][member] = dict()
    output[model][member]["mjo_activity"] = metric1
    output[model][member]["mjo_activity_diff"] = metric2
    output[model][member]["qbo_east_years"] = qbo_phase_years["east"]
    output[model][member]["qbo_west_years"] = qbo_phase_years["west"]

    # Write the dictionary to the JSON file
    json_file_path = os.path.join(
        output_dir, "mjo_olr_stddev_DJF" + output_file_tag + ".json"
    )

    with open(json_file_path, "w") as json_file:
        json.dump(output, json_file, indent=4)

    print("json file saved:", json_file_path)

    return output


if __name__ == "__main__":
    main()
