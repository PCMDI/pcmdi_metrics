import copy
import os
import sys

import cftime  # noqa: F401
import numpy as np
import rasterio.features
import regionmask
import xarray as xr
import xcdat as xc  # noqa: F401
from scipy.signal import savgol_filter
from shapely.geometry import MultiPolygon, Polygon

import pcmdi_metrics
from pcmdi_metrics import resources
from pcmdi_metrics.io import (
    get_latitude,
    get_latitude_key,
    get_longitude,
    get_longitude_key,
    get_time,
    xcdat_open,
)
from pcmdi_metrics.utils import create_land_sea_mask, create_target_grid, regrid


# ==================================================================================
def precip_distribution_frq_amt(
    dat, ds_rg, data_var, syr, eyr, res, outdir, ref, refdir, cmec, debug=False
):
    """
    - The metric algorithm is based on Dr. Pendergrass's work (https://github.com/apendergrass/rain-metrics-python)
    - Pre-processing and post-processing of data are modified for PMP as below:
      Regridding (in driver code) -> Month separation -> Distributions -> Domain average -> Metrics -> Write

    Parameters
    ----------
    dat : str
        name of the dataset
    ds_rg : xarray.Dataset
        input dataset
    data_var: str
        variable name of the dataset
    syr : int
        start year
    eyr : int
        end year
    res : list
        target resolution
    outdir : str
        output directory
    ref : str
        reference dataset
    refdir : str
        reference output directory
    cmec : bool
        flag for CMEC output
    debug : bool, optional
        if True, debug mode is enabled (default is False)
    """

    # Month separation
    months = get_all_season_and_months()

    drg = ds_rg[data_var]

    pdfpeakmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    pdfwidthmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    amtpeakmap = np.empty((len(months), drg.shape[1], drg.shape[2]))
    amtwidthmap = np.empty((len(months), drg.shape[1], drg.shape[2]))

    ppdfmap_list = []
    ppdfmap_tn_list = []
    pamtmap_list = []

    for im, mon in enumerate(months):
        print("im, mon:", im, mon)
        dmon = get_dmon(drg, mon, syr, eyr)
        pdata1 = dmon

        if debug:
            # Expected e.g., GPCP-1-3 ANN (731, 90, 180)
            print("dat, mon, dmon.shape:", dat, mon, dmon.shape)
            # Expected: <class 'xarray.core.dataarray.DataArray'>
            print("type of pdata1:", type(pdata1))
            # Expected e.g., (731, 90, 180)
            print("shape of pdata1:", pdata1.shape)

        # Calculate bin structure
        binl, binr, bincrates = CalcBinStructure(pdata1)

        # Calculate distributions at each grid point
        print("start MakeDists")
        ppdfmap, pamtmap, bins, ppdfmap_tn = MakeDists(pdata1, binl)

        if debug:
            print("ppdfmap type:", type(ppdfmap))
            print("ppdfmap shape:", ppdfmap.shape)
            print("pamtmap type:", type(pamtmap))
            print("pamtmap shape:", pamtmap.shape)
            print("bins type:", type(bins))
            print("bins shape:", bins.shape)
            print("ppdfmap_tn type:", type(ppdfmap_tn))
            print("ppdfmap_tn shape:", ppdfmap_tn.shape)

        print("completed MakeDists")

        # Calculate metrics from the distribution at each grid point
        print("start CalcRainMetrics for each grid point")
        for i in range(drg.shape[2]):
            for j in range(drg.shape[1]):
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    ppdfmap[:, j, i], bincrates
                )
                pdfpeakmap[im, j, i] = rainpeak
                pdfwidthmap[im, j, i] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pamtmap[:, j, i], bincrates
                )
                amtpeakmap[im, j, i] = rainpeak
                amtwidthmap[im, j, i] = rainwidth
        print("completed CalcRainMetrics for each grid point")

        # Make Spatial pattern of distributions with separated months

        ppdfmap_list.append(ppdfmap)
        ppdfmap_tn_list.append(ppdfmap_tn)
        pamtmap_list.append(pamtmap)

    pdfmapmon = xr.concat(ppdfmap_list, dim="month")
    pdfmapmon_tn = xr.concat(ppdfmap_tn_list, dim="month")
    amtmapmon = xr.concat(pamtmap_list, dim="month")

    if debug:
        print("pdfpeakmap type:", type(pdfpeakmap))
        print("pdfpeakmap shape:", pdfpeakmap.shape)
        print("pdfwidthmap type:", type(pdfwidthmap))
        print("pdfwidthmap shape:", pdfwidthmap.shape)
        print("amtpeakmap type:", type(amtpeakmap))
        print("amtpeakmap shape:", amtpeakmap.shape)
        print("amtwidthmap type:", type(amtwidthmap))
        print("amtwidthmap shape:", amtwidthmap.shape)

        print("pdfmapmon type:", type(pdfmapmon))
        print("pdfmapmon shape:", pdfmapmon.shape)
        print("pdfmapmon_tn type:", type(pdfmapmon_tn))
        print("pdfmapmon_tn shape:", pdfmapmon_tn.shape)
        print("amtmapmon type:", type(amtmapmon))
        print("amtmapmon shape:", amtmapmon.shape)
        print("bins type:", type(bins))
        print("bins shape:", bins.shape)

    axmon = xr.DataArray(months, dims="month", name="month")
    # axbin = xr.DataArray(binl, name="bin")
    lat = get_latitude(drg)
    lon = get_longitude(drg)

    dims = ["month", "lat", "lon"]
    coords = {"month": axmon, "lat": lat, "lon": lon}

    pdfpeakmap = numpy_to_xrda(pdfpeakmap, dims, coords)
    pdfwidthmap = numpy_to_xrda(pdfwidthmap, dims, coords)
    amtpeakmap = numpy_to_xrda(amtpeakmap, dims, coords)
    amtwidthmap = numpy_to_xrda(amtwidthmap, dims, coords)

    res_nxny = str(int(360 / res[0])) + "x" + str(int(180 / res[1]))

    # First file: spatial pattern of distributions
    outfilename = f"dist_frq.amt_regrid.{res_nxny}_{dat}.nc"
    output_diag_dir = outdir(output_type="diagnostic_results")
    outfile_path = os.path.join(output_diag_dir, outfilename)

    # Create a dataset from the individual DataArrays
    ds_distributions = xr.Dataset(
        {
            "pdf": pdfmapmon,
            "pdf_tn": pdfmapmon_tn,
            "amt": amtmapmon,
            "binbounds": bins,  # Ensure `bins` is an xarray.DataArray
        }
    )

    # Save to NetCDF
    ds_distributions.to_netcdf(outfile_path)

    # Second file: spatial pattern of metrics
    outfilename = f"dist_frq.amt_metrics_regrid.{res_nxny}_{dat}.nc"
    outfile_path = os.path.join(output_diag_dir, outfilename)

    # Create a dataset from the individual DataArrays
    ds_metrics = xr.Dataset(
        {
            "frqpeak": pdfpeakmap,
            "frqwidth": pdfwidthmap,
            "amtpeak": amtpeakmap,
            "amtwidth": amtwidthmap,
        }
    )

    ds_metrics.to_netcdf(outfile_path)

    # Calculate metrics from the distribution at each domain
    metricsdom = {"RESULTS": {dat: {}}}
    metricsdom3C = {"RESULTS": {dat: {}}}
    metricsdomAR6 = {"RESULTS": {dat: {}}}
    metricsdom["RESULTS"][dat], pdfdom, amtdom = CalcMetricsDomain(
        pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir
    )
    metricsdom3C["RESULTS"][dat], pdfdom3C, amtdom3C = CalcMetricsDomain3Clust(
        pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir
    )
    metricsdomAR6["RESULTS"][dat], pdfdomAR6, amtdomAR6 = CalcMetricsDomainAR6(
        pdfmapmon, amtmapmon, months, bincrates, dat, ref, refdir
    )

    # Write diagnostic output files
    # --- 1. Write distributions for standard domains ---
    outfilename = f"dist_frq.amt_domain_regrid.{res_nxny}_{dat}.nc"
    xr.Dataset({"pdf": pdfdom, "amt": amtdom, "binbounds": bins}).to_netcdf(
        os.path.join(output_diag_dir, outfilename)
    )
    # --- 2. Write distributions for 3-cluster domains ---
    outfilename = f"dist_frq.amt_domain3C_regrid.{res_nxny}_{dat}.nc"
    xr.Dataset({"pdf": pdfdom3C, "amt": amtdom3C, "binbounds": bins}).to_netcdf(
        os.path.join(output_diag_dir, outfilename)
    )
    # --- 3. Write distributions for AR6 domains ---
    outfilename = f"dist_frq.amt_domainAR6_regrid.{res_nxny}_{dat}.nc"
    xr.Dataset({"pdf": pdfdomAR6, "amt": amtdomAR6, "binbounds": bins}).to_netcdf(
        os.path.join(output_diag_dir, outfilename)
    )

    # Write Metrics data
    # Define the output directory
    output_metrics_dir = outdir(output_type="metrics_results")
    # --- 1. json file for domain metrics
    outfilename = f"dist_frq.amt_metrics_domain_regrid.{res_nxny}_{dat}.json"
    write_json(metricsdom, output_metrics_dir, outfilename, cmec=cmec)
    # --- 2. json file for domain metrics with 3 clustering regions
    outfilename = f"dist_frq.amt_metrics_domain3C_regrid.{res_nxny}_{dat}.json"
    write_json(metricsdom3C, output_metrics_dir, outfilename, cmec=cmec)
    # --- 3. json file for domain metrics with AR6 regions
    outfilename = f"dist_frq.amt_metrics_domainAR6_regrid.{res_nxny}_{dat}.json"
    write_json(metricsdomAR6, output_metrics_dir, outfilename, cmec=cmec)

    print("Completed metrics from precipitation frequency and amount distributions")


# ==================================================================================
def precip_distribution_cum(
    dat, ds_rg, data_var, cal, syr, eyr, res, outdir, cmec, debug=False
):
    """
    - The metric algorithm is based on Dr. Pendergrass's work (https://github.com/apendergrass/unevenprecip)
    - Pre-processing and post-processing of data are modified for PMP as below:
      Regridding (in driver code) -> Month separation -> Year separation -> Unevenness and other metrics -> Year median -> Domain median -> Write
    """

    # threshold of missing data fraction at which a year is thrown out
    missingthresh = 0.3

    # Month separation
    months = get_all_season_and_months()

    if "360" in cal:
        ndymon = [360, 90, 90, 90, 90, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
        ldy = 30
    else:
        # Only considered 365-day calendar becauase, in cumulative distribution as a function of the wettest days, the last part of the distribution is not affect to metrics.
        ndymon = [365, 92, 92, 91, 90, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        ldy = 31

    res_nxny = str(int(360 / res[0])) + "x" + str(int(180 / res[1]))

    # Open nc file for writing data of spatial pattern of cumulated fractions with separated month
    outfilename = f"dist_cumfrac_regrid.{res_nxny}_{dat}.nc"
    output_diag_dir = outdir(output_type="diagnostic_results")
    outfile_path = os.path.join(output_diag_dir, outfilename)

    drg = ds_rg[data_var]
    # new dataset
    outcumfrac_ds = xr.Dataset()
    ndm_list = []
    prdyfracm_list = []
    sdiim_list = []

    lat = get_latitude(drg)
    lat_key = get_latitude_key(drg)
    lon = get_longitude(drg)
    lon_key = get_longitude_key(drg)
    time = get_time(drg)
    time_class = type(time.values[0])

    for im, mon in enumerate(months):
        print("im, mon:", im, mon)
        dmon = get_dmon(drg, mon, syr, eyr)
        print("dat, mon, dmon.shape:", dat, mon, dmon.shape)

        # Calculate unevenness
        nyr = eyr - syr + 1
        if mon == "DJF":
            nyr = nyr - 1
        cfy = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        prdyfracyr = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        sdiiyr = np.full((nyr, dmon.shape[1], dmon.shape[2]), np.nan)
        pfracyr = np.full((nyr, ndymon[im], dmon.shape[1], dmon.shape[2]), np.nan)

        for iyr, year in enumerate(range(syr, eyr + 1)):
            if mon == "DJF":
                if year == eyr:
                    thisyear = None
                else:
                    start_time = time_class(year, 12, 1, 0, 0, 0)
                    end_time = time_class(year + 1, 3, 1, 23, 59, 59)
                    thisyear = dmon.sel(time=slice(start_time, end_time))
            else:
                start_time = time_class(year, 1, 1, 0, 0, 0)
                end_time = time_class(year, 12, ldy, 23, 59, 59)
                thisyear = dmon.sel(time=slice(start_time, end_time))

            if thisyear is not None:
                if debug:
                    print("thisyear type:", type(thisyear))
                    print("thisyear shape:", thisyear.shape)
                    print("thisyear dimensions:", thisyear.dims)
                print(year, thisyear.shape)
                pfrac, ndhy, prdyfrac, sdii = oneyear(thisyear, missingthresh)
                cfy[iyr, :, :] = ndhy
                prdyfracyr[iyr, :, :] = prdyfrac
                sdiiyr[iyr, :, :] = sdii
                pfracyr[iyr, :, :, :] = pfrac[: ndymon[im], :, :]
                print(
                    f"{year} pfrac.shape is {pfrac.shape}, but {pfrac[:ndymon[im], :, :].shape} is used"
                )

        ndm = np.nanmedian(cfy, axis=0)  # ignore years with zero precip
        prdyfracm = np.nanmedian(prdyfracyr, axis=0)
        sdiim = np.nanmedian(sdiiyr, axis=0)

        missingfrac = np.sum(np.isnan(cfy), axis=0) / nyr
        ndm[np.where(missingfrac > missingthresh)] = np.nan
        missingfrac = np.sum(np.isnan(prdyfracyr), axis=0) / nyr
        prdyfracm[np.where(missingfrac > missingthresh)] = np.nan
        missingfrac = np.sum(np.isnan(sdiiyr), axis=0) / nyr
        sdiim[np.where(missingfrac > missingthresh)] = np.nan

        pfracm = np.nanmedian(pfracyr, axis=0)
        missingfrac = np.sum(np.isnan(pfracyr), axis=0) / nyr
        pfracm[np.where(missingfrac > missingthresh)] = np.nan

        pfracm = xr.DataArray(
            data=pfracm,
            dims=("time", lat_key, lon_key),
            coords={"time": np.arange(1, ndymon[im] + 1), lat_key: lat, lon_key: lon},
        )
        outcumfrac_ds["cumfrac_" + mon] = pfracm

        # Make Spatial pattern with separated months
        dims = [lat_key, lon_key]
        coords = {lat_key: lat, lon_key: lon}

        ndm = numpy_to_xrda(ndm, dims, coords)
        prdyfracm = numpy_to_xrda(prdyfracm, dims, coords)
        sdiim = numpy_to_xrda(sdiim, dims, coords)

        ndm_list.append(ndm)
        prdyfracm_list.append(prdyfracm)
        sdiim_list.append(sdiim)

    ndmmon = xr.concat(ndm_list, dim="month")
    prdyfracmmon = xr.concat(prdyfracm_list, dim="month")
    sdiimmon = xr.concat(sdiim_list, dim="month")

    outcumfrac_ds.to_netcdf(outfile_path)

    if debug:
        print("ndmmon type:", type(ndmmon))
        print("ndmmon shape:", ndmmon.shape)
        print("months:", months)
        print("prdyfracmmon type:", type(prdyfracmmon))
        print("prdyfracmmon shape:", prdyfracmmon.shape)
        print("sdiimmon type:", type(sdiimmon))
        print("sdiimmon shape:", sdiimmon.shape)

    # Write data (nc file for spatial pattern of metrics)
    outfilename = f"dist_cumfrac_metrics_regrid.{res_nxny}_{dat}.nc"
    outfile_path = os.path.join(output_diag_dir, outfilename)
    cumfrac_metrics_regrid_ds = xr.Dataset(
        {"unevenness": ndmmon, "prdyfrac": prdyfracmmon, "sdiim": sdiimmon},
    )
    cumfrac_metrics_regrid_ds.to_netcdf(outfile_path)

    # Domain median
    metrics = {"RESULTS": {dat: {}}}
    metrics["RESULTS"][dat]["unevenness"] = MedDomain(ndmmon, months)
    metrics["RESULTS"][dat]["prdyfrac"] = MedDomain(prdyfracmmon, months)
    metrics["RESULTS"][dat]["sdii"] = MedDomain(sdiimmon, months)

    metrics3C = {"RESULTS": {dat: {}}}
    metrics3C["RESULTS"][dat]["unevenness"] = MedDomain3Clust(ndmmon, months)
    metrics3C["RESULTS"][dat]["prdyfrac"] = MedDomain3Clust(prdyfracmmon, months)
    metrics3C["RESULTS"][dat]["sdii"] = MedDomain3Clust(sdiimmon, months)

    metricsAR6 = {"RESULTS": {dat: {}}}
    metricsAR6["RESULTS"][dat]["unevenness"] = MedDomainAR6(ndmmon, months)
    metricsAR6["RESULTS"][dat]["prdyfrac"] = MedDomainAR6(prdyfracmmon, months)
    metricsAR6["RESULTS"][dat]["sdii"] = MedDomainAR6(sdiimmon, months)

    # Write data (json file for domain median metrics)
    # Define the output directory
    output_metrics_dir = outdir(output_type="metrics_results")
    # --- 1. json file for domain median metrics
    outfilename = f"dist_cumfrac_metrics_domain.median_regrid.{res_nxny}_{dat}.json"
    write_json(metrics, output_metrics_dir, outfilename, cmec=cmec)
    # --- 2. json file for domain median metrics with 3 clustering regions
    outfilename = f"dist_cumfrac_metrics_domain.median.3C_regrid.{res_nxny}_{dat}.json"
    write_json(metrics3C, output_metrics_dir, outfilename, cmec=cmec)
    # --- 3. json file for domain median metrics with AR6 regions
    outfilename = f"dist_cumfrac_metrics_domain.median.AR6_regrid.{res_nxny}_{dat}.json"
    write_json(metricsAR6, output_metrics_dir, outfilename, cmec=cmec)

    print("Completed metrics from precipitation cumulative distributions")


# ==================================================================================
def Regrid_xr(ds, data_var, resdeg):
    """
    Regridding horizontal resolution using xarray

    Input
    - ds: xarray Dataset or DataArray
    - data_var: name of the variable to regrid
    - resdeg: list of target horizontal resolution [degree] for lon and lat (e.g., [4, 4])

    Output
    - ds_regrid: xarray Dataset with target horizontal resolution
    """
    # if ds is dataArray convert to DataSet
    if isinstance(ds, xr.DataArray):
        ds = ds.to_dataset(name=data_var)

    # if there is missing bounds, set them
    ds = ds.bounds.add_missing_bounds()

    dlon = resdeg[0]
    dlat = resdeg[1]

    # Regridding
    tgrid = create_target_grid(
        lat1=-90.0,
        lat2=90.0,
        lon1=0.0,
        lon2=360.0,
        target_grid_resolution=f"{dlat}x{dlon}",
        grid_type="uniform",
    )
    ds_regrid = regrid(ds, data_var, tgrid)

    print(
        f"Completed regridding (via Regrid_xr) from {ds[data_var].shape} to {ds_regrid[data_var].shape}"
    )
    return ds_regrid


# ==================================================================================
def get_daily_calendar_month(d, months):
    """
    Extract daily data for specific calendar months from an xarray DataArray or Dataset.

    Parameters
    ----------
    d : xr.DataArray or xr.Dataset
        The input data with a time dimension.
    months : list of str
        List of month abbreviations (e.g., ['JAN'], ['FEB'], ['MAR', 'APR']).

    Returns
    -------
    xr.DataArray or xr.Dataset
        Subset of the input data containing only the specified months.
    """
    # Convert input month names to numerical values (e.g., 'JAN' -> 1)
    months = get_all_months()
    month_str_to_int = {
        month: i
        for i, month in enumerate(
            months,
            start=1,
        )
    }
    month_nums = [month_str_to_int[m.upper()] for m in months]

    # Ensure time coordinate exists
    if "time" not in d.coords:
        raise ValueError("Input data must have a 'time' coordinate.")

    # Subset by month
    filtered = d.sel(time=d["time"].dt.month.isin(month_nums))

    return filtered


def get_dmon(drg, mon, syr, eyr):
    """Get daily data for a specific calendar month from a drg object."""
    if mon == "ANN":
        dmon = drg
    elif mon == "MAM":
        dmon = get_daily_calendar_month(drg, ["MAR", "APR", "MAY"])
    elif mon == "JJA":
        dmon = get_daily_calendar_month(drg, ["JUN", "JUL", "AUG"])
    elif mon == "SON":
        dmon = get_daily_calendar_month(drg, ["SEP", "OCT", "NOV"])
    elif mon == "DJF":
        time_class = type(get_time(drg).values[0])
        start_time = time_class(syr, 3, 1, 0, 0, 0)
        end_time = time_class(eyr, 11, 30, 23, 59, 59)
        drg_subset = drg.sel(time=slice(start_time, end_time))
        dmon = get_daily_calendar_month(
            drg_subset,
            ["DEC", "JAN", "FEB"],
        )
    else:
        dmon = get_daily_calendar_month(drg, [mon])

    return dmon


def get_all_season_and_months():
    """Get all seasons and months."""
    seasons = [
        "ANN",
        "MAM",
        "JJA",
        "SON",
        "DJF",
    ]
    return seasons + get_all_months()


def get_all_months():
    """Get all months."""
    return [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]


# ==================================================================================
def CalcBinStructure(pdata1):
    L = 2.5e6  # w/m2. latent heat of vaporization of water
    # wm2tommd = 1.0 / L * 3600 * 24  # conversion from w/m2 to mm/d
    # pmax = pdata1.max() / wm2tommd
    maxp = 1500  # choose an arbitrary upper bound for initial distribution, in w/m2
    # arbitrary lower bound, in w/m2. Make sure to set this low enough that you catch most of the rain.
    minp = 1
    # thoughts: it might be better to specify the minimum threshold and the
    # bin spacing, which I have around 7%. The goals are to capture as much
    # of the distribution as possible and to balance sampling against
    # resolution. Capturing the upper end is easy: just extend the bins to
    # include the heaviest precipitation event in the dataset. The lower end
    # is harder: it can go all the way to machine epsilon, and there is no
    # obvious reasonable threshold for "rain" over a large spatial scale. The
    # value I chose here captures 97% of rainfall in CMIP5.
    nbins = 100
    binrlog = np.linspace(np.log(minp), np.log(maxp), nbins)
    dbinlog = np.diff(binrlog)
    binllog = binrlog - dbinlog[0]
    binr = np.exp(binrlog) / L * 3600 * 24
    binl = np.exp(binllog) / L * 3600 * 24
    dbin = dbinlog[0]
    binrlogex = binrlog
    # binrend = np.exp(binrlogex[len(binrlogex) - 1])
    # extend the bins until the maximum precip anywhere in the dataset falls
    # within the bins
    # switch maxp to pmax if you want it to depend on your data
    while maxp > binr[len(binr) - 1]:
        binrlogex = np.append(binrlogex, binrlogex[len(binrlogex) - 1] + dbin)
        # binrend = np.exp(binrlogex[len(binrlogex) - 1])
        binrlog = binrlogex
        binllog = binrlog - dbinlog[0]
        # this is what we'll use to make distributions
        binl = np.exp(binllog) / L * 3600 * 24
        binr = np.exp(binrlog) / L * 3600 * 24
    bincrates = np.append(0, (binl + binr) / 2)  # we'll use this for plotting.

    axbin = np.array(range(len(binl)))

    binl = xr.DataArray(binl, coords={"bin": axbin}, dims=["bin"], name="bin")
    binr = xr.DataArray(binr, coords={"bin": axbin}, dims=["bin"], name="bin")

    return binl, binr, bincrates


# ==================================================================================
def MakeDists(pdata, binl):
    """Calculate precipitation distributions from data.

    Parameters
    ----------
    pdata : xr.DataArray
        Precipitation data with dimensions (time, lat, lon).
    binl : xr.DataArray
        Left edges of the bins for the precipitation distribution.

    Returns
    -------
    xr.DataArray
        Precipitation distribution with dimensions (bin, lat, lon).
    xr.DataArray
        Precipitation amount distribution with dimensions (bin, lat, lon).
    xr.DataArray
        Bin edges for the precipitation distribution.
    xr.DataArray
        Precipitation distribution normalized by the number of days with non-missing data, with dimensions
    """
    # This is called from within makeraindist.
    # Caclulate distributions
    nlat = pdata.shape[1]
    nlon = pdata.shape[2]
    nd = pdata.shape[0]
    bins = np.append(0, binl)
    n = np.empty((len(binl), nlat, nlon))
    binno = np.empty(pdata.shape)
    for ilon in range(nlon):
        for ilat in range(nlat):
            # this is the histogram - we'll get frequency from this
            thisn, thisbin = np.histogram(pdata[:, ilat, ilon], bins)
            # n[:, ilat, ilon] = thisn
            thmiss = 0.7  # threshold for missing grid
            if np.sum(thisn) >= nd * thmiss:
                n[:, ilat, ilon] = thisn
            else:
                n[:, ilat, ilon] = np.nan

            # these are the bin locations. we'll use these for the amount dist
            binno[:, ilat, ilon] = np.digitize(pdata[:, ilat, ilon], bins)
    # Calculate the number of days with non-missing data, for normalization
    ndmat = np.tile(np.expand_dims(np.nansum(n, axis=0), axis=0), (len(bins) - 1, 1, 1))

    thisppdfmap = n / ndmat
    thisppdfmap_tn = thisppdfmap * ndmat

    # Iterate back over the bins and add up all the precip - this will be the rain amount distribution.
    # This step is probably the limiting factor and might be able to be made more efficient - I had a clever trick in matlab, but it doesn't work in python
    testpamtmap = np.empty(thisppdfmap.shape)
    for ibin in range(len(bins) - 1):
        testpamtmap[ibin, :, :] = (pdata * (ibin == binno)).sum(axis=0)
    thispamtmap = testpamtmap / ndmat

    # Change Inf to Nan
    thisppdfmap[np.isinf(thisppdfmap)] = np.nan
    thisppdfmap_tn[np.isinf(thisppdfmap_tn)] = np.nan
    thispamtmap[np.isinf(thispamtmap)] = np.nan

    # Assume binl is a list or 1D array of bin centers
    bin_coord = xr.DataArray(binl, dims="bin", name="bin")

    # Extract latitude and longitude from pdata
    lat = get_latitude(pdata)
    lon = get_longitude(pdata)

    # Create coordinate-aware DataArrays
    thisppdfmap = xr.DataArray(
        thisppdfmap,
        dims=("bin", "lat", "lon"),
        coords={"bin": bin_coord, "lat": lat, "lon": lon},
        name="ppdf",
    )

    thisppdfmap_tn = xr.DataArray(
        thisppdfmap_tn,
        dims=("bin", "lat", "lon"),
        coords={"bin": bin_coord, "lat": lat, "lon": lon},
        name="ppdf_tn",
    )

    thispamtmap = xr.DataArray(
        thispamtmap,
        dims=("bin", "lat", "lon"),
        coords={"bin": bin_coord, "lat": lat, "lon": lon},
        name="pamt",
    )

    # Create the bin boundaries as a separate 1D DataArray
    binbound = xr.DataArray(thisbin, dims="binbound", name="binbound")

    # return thisppdfmap, thispamtmap, thisbin, thisppdfmap_tn
    return thisppdfmap, thispamtmap, binbound, thisppdfmap_tn


# ==================================================================================
def CalcRainMetrics(pdistin, bincrates):
    # This calculation can be applied to rain amount or rain frequency distributions
    # Here we'll do it for a distribution averaged over a region, but you could also do it at each grid point
    pdist = np.copy(pdistin)
    # this is the threshold, 10% of rain amount or rain frequency
    tile = np.array(0.1)

    # If this is frequency, get rid of the dry frequency. If it's amount, it should already be zero or close to it. (Pendergrass and Hartmann 2014)
    # pdist[0] = 0
    # msahn, Days with precip<0.1mm/day are considered dry (Pendergrass and Deser 2017)
    thidx = np.argwhere(bincrates > 0.1)
    thidx = int(thidx[0][0])
    pdist[:thidx] = 0
    # -----------------------------------------------------

    pmax = pdist.max()
    if pmax > 0:
        imax = np.nonzero(pdist == pmax)
        rmax = np.interp(imax, range(0, len(bincrates)), bincrates)
        rainpeak = rmax[0][0]
        # we're going to find the width by summing downward from pmax to lines at different heights, and then interpolating to figure out the rain rates that intersect the line.
        theps = np.linspace(0.1, 0.99, 99) * pmax
        thefrac = np.empty(theps.shape)
        for i in range(len(theps)):
            thisp = theps[i]
            overp = (pdist - thisp) * (pdist > thisp)
            thefrac[i] = sum(overp) / sum(pdist)
        ptilerain = np.interp(-tile, -thefrac, theps)
        # ptilerain/db ### check this against rain amount plot
        # ptilerain*100/db ### check this against rain frequency plot
        diffraintile = pdist - ptilerain
        alli = np.nonzero(diffraintile > 0)
        afterfirst = alli[0][0]
        noistart = np.nonzero(diffraintile[0:afterfirst] < 0)
        beforefirst = noistart[0][len(noistart[0]) - 1]
        incinds = range(beforefirst, afterfirst + 1)
        # need error handling on these for when inter doesn't behave well and there are multiple crossings
        if np.all(np.diff(diffraintile[incinds]) > 0):
            # this is ideally what happens. note: r1 is a bin index, not a rain rate.
            r1 = np.interp(0, diffraintile[incinds], incinds)
        else:
            # in case interp won't return something meaningful, we use this kluge.
            r1 = np.average(incinds)
        beforelast = alli[0][len(alli[0]) - 1]
        noiend = (
            np.nonzero(diffraintile[beforelast : (len(diffraintile) - 1)] < 0)
            + beforelast
        )

        # msahn For treat noiend=[]
        # if bool(noiend.any()) is False:
        if np.array(noiend).size == 0:
            rainwidth = 0
            r2 = r1
        else:
            afterlast = noiend[0][0]
            decinds = range(beforelast, afterlast + 1)
            if np.all(np.diff(-diffraintile[decinds]) > 0):
                r2 = np.interp(0, -diffraintile[decinds], decinds)
            else:
                r2 = np.average(decinds)
            # Bin width - needed to normalize the rain amount distribution
            db = (bincrates[2] - bincrates[1]) / bincrates[1]
            rainwidth = (r2 - r1) * db + 1

        return rainpeak, rainwidth, (imax[0][0], pmax), (r1, r2, ptilerain)
    else:
        # return 0, 0, (0, pmax), (0, 0, 0)
        return np.nan, np.nan, (np.nan, pmax), (np.nan, np.nan, np.nan)


# ==================================================================================
def CalcMetricsDomain(pdf, amt, months, bincrates, dat, ref, ref_dir):
    """
    Input
    - pdf: pdf, xarray data array (4-dimensional)
    - amt: amount distribution, xarray data array (4-dimensional)
    - months: month list of input data
    - bincrates: bin centers
    - dat: data name
    - ref: reference data name
    - ref_dir: reference data directory
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """
    domains = [
        "Total_50S50N",
        "Ocean_50S50N",
        "Land_50S50N",
        "Total_30N50N",
        "Ocean_30N50N",
        "Land_30N50N",
        "Total_30S30N",
        "Ocean_30S30N",
        "Land_30S30N",
        "Total_50S30S",
        "Ocean_50S30S",
        "Land_50S30S",
    ]

    ddom = []

    mask = create_land_sea_mask(pdf[0, 0])

    for d in [pdf, amt]:
        # Ensure mask is broadcast to same shape as d if needed
        mask_broadcasted = mask.broadcast_like(d)

        # Create ocean and land masked data
        d_ocean = d.where(mask_broadcasted != 1.0)  # mask == 1.0 --> masked
        d_land = d.where(mask_broadcasted != 0.0)  # mask == 0.0 --> masked

        print("d.shape:", d.shape)
        print("type d:", type(d))

        for dom in domains:
            if "Ocean" in dom:
                dmask = d_ocean
            elif "Land" in dom:
                dmask = d_land
            else:
                dmask = d

            # dmask = MV.masked_where(~np.isfinite(dmask), dmask)
            dmask = dmask.where(np.isfinite(dmask))

            # Latitude slicing based on domain name
            if "50S50N" in dom:
                lat_range = slice(-50, 50)
            elif "30N50N" in dom:
                lat_range = slice(30, 50)
            elif "30S30N" in dom:
                lat_range = slice(-30, 30)
            elif "50S30S" in dom:
                lat_range = slice(-50, -30)
            else:
                lat_range = slice(None)  # no lat restriction

            # Subset and compute median over spatial dims (assumes dims are 'lat' and 'lon')
            lat_key = get_latitude_key(dmask)
            # lon_key = get_longitude_key(dmask)
            subset = (
                dmask.sel(**{lat_key: lat_range})
                .to_dataset(name="dmask")
                .bounds.add_missing_bounds()
            )
            am = subset.spatial.average("dmask")["dmask"]

            ddom.append(am)

    # ddom = MV.reshape(ddom, (-1, len(domains), am.shape[0], am.shape[1]))
    ddom = np.reshape(ddom, (-1, len(domains), am.shape[0], am.shape[1]))
    ddom = np.swapaxes(ddom, 1, 3)
    ddom = np.swapaxes(ddom, 1, 2)
    print(ddom.shape)

    pdfdom = ddom[0]
    amtdom = ddom[1]

    # Create the new domain coordinate
    domain_dim = "domains"
    domain_coords = np.arange(len(domains))  # or list of names if available

    dims = (am.dims[0], am.dims[1], domain_dim)
    coords = {
        am.dims[0]: am.coords[am.dims[0]],
        am.dims[1]: am.coords[am.dims[1]],
        domain_dim: domain_coords,
    }

    pdfdom = numpy_to_xrda(pdfdom, dims, coords)
    amtdom = numpy_to_xrda(amtdom.data, dims, coords)

    print("dat:", dat, "ref:", ref)

    if dat == ref:
        pdfdom_ref = pdfdom
        amtdom_ref = amtdom
    else:
        file = f"dist_frq.amt_domain_regrid.{pdf.shape[3]}x{pdf.shape[2]}_{ref}.nc"
        print("ref_dir:", ref_dir, "file:", file)

        ds_ref = xcdat_open(os.path.join(ref_dir, file))
        pdfdom_ref = ds_ref["pdf"]
        amtdom_ref = ds_ref["amt"]

    metrics = {}
    metrics["frqpeak"] = {}
    metrics["frqwidth"] = {}
    metrics["amtpeak"] = {}
    metrics["amtwidth"] = {}
    metrics["pscore"] = {}
    metrics["frqP10"] = {}
    metrics["frqP20"] = {}
    metrics["frqP80"] = {}
    metrics["frqP90"] = {}
    metrics["amtP10"] = {}
    metrics["amtP20"] = {}
    metrics["amtP80"] = {}
    metrics["amtP90"] = {}
    metrics["bimod"] = {}
    for idm, dom in enumerate(domains):
        metrics["frqpeak"][dom] = {"CalendarMonths": {}}
        metrics["frqwidth"][dom] = {"CalendarMonths": {}}
        metrics["amtpeak"][dom] = {"CalendarMonths": {}}
        metrics["amtwidth"][dom] = {"CalendarMonths": {}}
        metrics["pscore"][dom] = {"CalendarMonths": {}}
        metrics["frqP10"][dom] = {"CalendarMonths": {}}
        metrics["frqP20"][dom] = {"CalendarMonths": {}}
        metrics["frqP80"][dom] = {"CalendarMonths": {}}
        metrics["frqP90"][dom] = {"CalendarMonths": {}}
        metrics["amtP10"][dom] = {"CalendarMonths": {}}
        metrics["amtP20"][dom] = {"CalendarMonths": {}}
        metrics["amtP80"][dom] = {"CalendarMonths": {}}
        metrics["amtP90"][dom] = {"CalendarMonths": {}}
        metrics["bimod"][dom] = {"CalendarMonths": {}}
        for im, mon in enumerate(months):
            if mon in ["ANN", "MAM", "JJA", "SON", "DJF"]:
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pdfdom[im, :, idm], bincrates
                )
                metrics["frqpeak"][dom][mon] = rainpeak
                metrics["frqwidth"][dom][mon] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    amtdom[im, :, idm], bincrates
                )
                metrics["amtpeak"][dom][mon] = rainpeak
                metrics["amtwidth"][dom][mon] = rainwidth
                metrics["pscore"][dom][mon] = CalcPscore(
                    pdfdom[im, :, idm], pdfdom_ref[im, :, idm]
                )
                (
                    metrics["frqP10"][dom][mon],
                    metrics["frqP20"][dom][mon],
                    metrics["frqP80"][dom][mon],
                    metrics["frqP90"][dom][mon],
                    metrics["amtP10"][dom][mon],
                    metrics["amtP20"][dom][mon],
                    metrics["amtP80"][dom][mon],
                    metrics["amtP90"][dom][mon],
                ) = CalcP10P90(
                    pdfdom[im, :, idm],
                    amtdom[im, :, idm],
                    amtdom_ref[im, :, idm],
                    bincrates,
                )
                metrics["bimod"][dom][mon] = CalcBimodality(
                    pdfdom[im, :, idm], bincrates
                )

            else:
                calmon = get_all_months()
                imn = calmon.index(mon) + 1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pdfdom[im, :, idm], bincrates
                )
                metrics["frqpeak"][dom]["CalendarMonths"][imn] = rainpeak
                metrics["frqwidth"][dom]["CalendarMonths"][imn] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    amtdom[im, :, idm], bincrates
                )
                metrics["amtpeak"][dom]["CalendarMonths"][imn] = rainpeak
                metrics["amtwidth"][dom]["CalendarMonths"][imn] = rainwidth
                metrics["pscore"][dom]["CalendarMonths"][imn] = CalcPscore(
                    pdfdom[im, :, idm], pdfdom_ref[im, :, idm]
                )
                (
                    metrics["frqP10"][dom]["CalendarMonths"][imn],
                    metrics["frqP20"][dom]["CalendarMonths"][imn],
                    metrics["frqP80"][dom]["CalendarMonths"][imn],
                    metrics["frqP90"][dom]["CalendarMonths"][imn],
                    metrics["amtP10"][dom]["CalendarMonths"][imn],
                    metrics["amtP20"][dom]["CalendarMonths"][imn],
                    metrics["amtP80"][dom]["CalendarMonths"][imn],
                    metrics["amtP90"][dom]["CalendarMonths"][imn],
                ) = CalcP10P90(
                    pdfdom[im, :, idm],
                    amtdom[im, :, idm],
                    amtdom_ref[im, :, idm],
                    bincrates,
                )
                metrics["bimod"][dom]["CalendarMonths"][imn] = CalcBimodality(
                    pdfdom[im, :, idm], bincrates
                )

    print("Completed domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcMetricsDomain3Clust(
    pdf, amt, months, bincrates, dat, ref, ref_dir, debug=False
):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - months: month list of input data
    - bincrates: bin centers
    - dat: data name
    - ref: reference data name
    - ref_dir: reference data directory
    - debug: debug flag
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """
    domains = [
        "Total_HR_50S50N",
        "Total_MR_50S50N",
        "Total_LR_50S50N",
        "Total_HR_30N50N",
        "Total_MR_30N50N",
        "Total_LR_30N50N",
        "Total_HR_30S30N",
        "Total_MR_30S30N",
        "Total_LR_30S30N",
        "Total_HR_50S30S",
        "Total_MR_50S30S",
        "Total_LR_50S30S",
        "Ocean_HR_50S50N",
        "Ocean_MR_50S50N",
        "Ocean_LR_50S50N",
        "Ocean_HR_30N50N",
        "Ocean_MR_30N50N",
        "Ocean_LR_30N50N",
        "Ocean_HR_30S30N",
        "Ocean_MR_30S30N",
        "Ocean_LR_30S30N",
        "Ocean_HR_50S30S",
        "Ocean_MR_50S30S",
        "Ocean_LR_50S30S",
        "Land_HR_50S50N",
        "Land_MR_50S50N",
        "Land_LR_50S50N",
        "Land_HR_30N50N",
        "Land_MR_30N50N",
        "Land_LR_30N50N",
        "Land_HR_30S30N",
        "Land_MR_30S30N",
        "Land_LR_30S30N",
        "Land_HR_50S30S",
        "Land_MR_50S30S",
        "Land_LR_50S30S",
    ]

    egg_pth = resources.resource_path()
    file = "cluster3_pdf.amt_regrid.360x180_IMERG_ALL_90S90N.nc"
    cluster = xr.open_dataset(os.path.join(egg_pth, file))["cluster_nb"]

    regs = ["HR", "MR", "LR"]
    mpolygons = []
    regs_name = []
    for reg in regs:
        if reg == "HR":
            data = xr.where(cluster == 0, 1, 0)
            regs_name.append("Heavy precipitating region")
        elif reg == "MR":
            data = xr.where(cluster == 1, 1, 0)
            regs_name.append("Moderate precipitating region")
        elif reg == "LR":
            data = xr.where(cluster == 2, 1, 0)
            regs_name.append("Light precipitating region")
        else:
            print("ERROR: data is not defined")
            exit()

        shapes = rasterio.features.shapes(np.int32(data))

        polygons = []
        for shape in shapes:
            for idx, xy in enumerate(shape[0]["coordinates"][0]):
                lst = list(xy)
                lst[0] = lst[0]
                lst[1] = lst[1] - 89.5
                tup = tuple(lst)
                shape[0]["coordinates"][0][idx] = tup
            if shape[1] == 1:
                polygons.append(Polygon(shape[0]["coordinates"][0]))

        mpolygons.append(MultiPolygon(polygons).simplify(3, preserve_topology=False))

    region = regionmask.Regions(
        mpolygons,
        names=regs_name,
        abbrevs=regs,
        name="Heavy/Moderate/Light precipitating regions",
    )
    print(region)

    mask = create_land_sea_mask(pdf[0, 0])

    ddom = []
    for d in [pdf, amt]:
        d_xr = d[0, 0]
        mask_3D = region.mask_3D(d_xr)

        if debug:
            print("mask_3D shape", mask_3D.shape)
            print("mask_3D dims", mask_3D.dims)
            print("mask_3D coords", mask_3D.coords)

        # Ensure mask is broadcast to match mask_3D shape
        mask2 = mask.broadcast_like(mask_3D)

        # Ocean: where mask == 0.0, keep values from mask_3D, else False
        mask_3D_ocn = xr.where(mask2 == 0.0, mask_3D, False)

        # Land: where mask == 1.0, keep values from mask_3D, else False
        mask_3D_lnd = xr.where(mask2 == 1.0, mask_3D, False)

        for dom in domains:
            if "Ocean" in dom:
                mask_3D_tmp = mask_3D_ocn
            elif "Land" in dom:
                mask_3D_tmp = mask_3D_lnd
            else:
                mask_3D_tmp = mask_3D

            # Select correct mask slice based on resolution string
            if "HR" in dom:
                selected_mask = mask_3D_tmp.isel(region=0)
            elif "MR" in dom:
                selected_mask = mask_3D_tmp.isel(region=1)
            elif "LR" in dom:
                selected_mask = mask_3D_tmp.isel(region=2)
            else:
                print("ERROR: HR/MR/LR is not defined")
                sys.exit()

            # Broadcast mask to match d's dimensions
            mask3 = selected_mask.broadcast_like(d)

            # Apply mask and filter out non-finite values
            dmask = d.where(mask3)  # Masks where mask3 is False
            dmask = dmask.where(np.isfinite(dmask))  # Masks non-finite values

            # Latitude slicing based on domain name
            if "50S50N" in dom:
                lat_range = slice(-50, 50)
            elif "30N50N" in dom:
                lat_range = slice(30, 50)
            elif "30S30N" in dom:
                lat_range = slice(-30, 30)
            elif "50S30S" in dom:
                lat_range = slice(-50, -30)
            else:
                lat_range = slice(None)  # no lat restriction

            # Subset and compute median over spatial dims (assumes dims are 'lat' and 'lon')
            lat_key = get_latitude_key(dmask)
            # lon_key = get_longitude_key(dmask)
            subset = (
                dmask.sel(**{lat_key: lat_range})
                .to_dataset(name="dmask")
                .bounds.add_missing_bounds()
            )
            am = subset.spatial.average("dmask")["dmask"]

            ddom.append(am)

    # ddom = MV.reshape(ddom, (-1, len(domains), am.shape[0], am.shape[1]))
    ddom = np.reshape(ddom, (-1, len(domains), am.shape[0], am.shape[1]))
    ddom = np.swapaxes(ddom, 1, 3)
    ddom = np.swapaxes(ddom, 1, 2)
    print(ddom.shape)

    pdfdom = ddom[0]
    amtdom = ddom[1]

    # Create the new domain coordinate
    domain_dim = "domains"
    domain_coords = np.arange(len(domains))  # or list of names if available

    dims = (am.dims[0], am.dims[1], domain_dim)
    coords = {
        am.dims[0]: am.coords[am.dims[0]],
        am.dims[1]: am.coords[am.dims[1]],
        domain_dim: domain_coords,
    }

    # Convert numpy arrays to xarray DataArrays
    pdfdom = numpy_to_xrda(pdfdom, dims, coords)
    amtdom = numpy_to_xrda(amtdom.data, dims, coords)

    print("dat:", dat, "ref:", ref)

    if dat == ref:
        pdfdom_ref = pdfdom
        amtdom_ref = amtdom
    else:
        file = f"dist_frq.amt_domain3C_regrid.{pdf.shape[3]}x{pdf.shape[2]}_{ref}.nc"
        pdfdom_ref = xcdat_open(os.path.join(ref_dir, file))["pdf"]
        amtdom_ref = xcdat_open(os.path.join(ref_dir, file))["amt"]

    metrics = {}
    metrics["frqpeak"] = {}
    metrics["frqwidth"] = {}
    metrics["amtpeak"] = {}
    metrics["amtwidth"] = {}
    metrics["pscore"] = {}
    metrics["frqP10"] = {}
    metrics["frqP20"] = {}
    metrics["frqP80"] = {}
    metrics["frqP90"] = {}
    metrics["amtP10"] = {}
    metrics["amtP20"] = {}
    metrics["amtP80"] = {}
    metrics["amtP90"] = {}
    metrics["bimod"] = {}
    for idm, dom in enumerate(domains):
        metrics["frqpeak"][dom] = {"CalendarMonths": {}}
        metrics["frqwidth"][dom] = {"CalendarMonths": {}}
        metrics["amtpeak"][dom] = {"CalendarMonths": {}}
        metrics["amtwidth"][dom] = {"CalendarMonths": {}}
        metrics["pscore"][dom] = {"CalendarMonths": {}}
        metrics["frqP10"][dom] = {"CalendarMonths": {}}
        metrics["frqP20"][dom] = {"CalendarMonths": {}}
        metrics["frqP80"][dom] = {"CalendarMonths": {}}
        metrics["frqP90"][dom] = {"CalendarMonths": {}}
        metrics["amtP10"][dom] = {"CalendarMonths": {}}
        metrics["amtP20"][dom] = {"CalendarMonths": {}}
        metrics["amtP80"][dom] = {"CalendarMonths": {}}
        metrics["amtP90"][dom] = {"CalendarMonths": {}}
        metrics["bimod"][dom] = {"CalendarMonths": {}}
        for im, mon in enumerate(months):
            if mon in ["ANN", "MAM", "JJA", "SON", "DJF"]:
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pdfdom[im, :, idm], bincrates
                )
                metrics["frqpeak"][dom][mon] = rainpeak
                metrics["frqwidth"][dom][mon] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    amtdom[im, :, idm], bincrates
                )
                metrics["amtpeak"][dom][mon] = rainpeak
                metrics["amtwidth"][dom][mon] = rainwidth
                metrics["pscore"][dom][mon] = CalcPscore(
                    pdfdom[im, :, idm], pdfdom_ref[im, :, idm]
                )
                (
                    metrics["frqP10"][dom][mon],
                    metrics["frqP20"][dom][mon],
                    metrics["frqP80"][dom][mon],
                    metrics["frqP90"][dom][mon],
                    metrics["amtP10"][dom][mon],
                    metrics["amtP20"][dom][mon],
                    metrics["amtP80"][dom][mon],
                    metrics["amtP90"][dom][mon],
                ) = CalcP10P90(
                    pdfdom[im, :, idm],
                    amtdom[im, :, idm],
                    amtdom_ref[im, :, idm],
                    bincrates,
                )
                metrics["bimod"][dom][mon] = CalcBimodality(
                    pdfdom[im, :, idm], bincrates
                )

            else:
                calmon = get_all_months()
                imn = calmon.index(mon) + 1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pdfdom[im, :, idm], bincrates
                )
                metrics["frqpeak"][dom]["CalendarMonths"][imn] = rainpeak
                metrics["frqwidth"][dom]["CalendarMonths"][imn] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    amtdom[im, :, idm], bincrates
                )
                metrics["amtpeak"][dom]["CalendarMonths"][imn] = rainpeak
                metrics["amtwidth"][dom]["CalendarMonths"][imn] = rainwidth
                metrics["pscore"][dom]["CalendarMonths"][imn] = CalcPscore(
                    pdfdom[im, :, idm], pdfdom_ref[im, :, idm]
                )
                (
                    metrics["frqP10"][dom]["CalendarMonths"][imn],
                    metrics["frqP20"][dom]["CalendarMonths"][imn],
                    metrics["frqP80"][dom]["CalendarMonths"][imn],
                    metrics["frqP90"][dom]["CalendarMonths"][imn],
                    metrics["amtP10"][dom]["CalendarMonths"][imn],
                    metrics["amtP20"][dom]["CalendarMonths"][imn],
                    metrics["amtP80"][dom]["CalendarMonths"][imn],
                    metrics["amtP90"][dom]["CalendarMonths"][imn],
                ) = CalcP10P90(
                    pdfdom[im, :, idm],
                    amtdom[im, :, idm],
                    amtdom_ref[im, :, idm],
                    bincrates,
                )
                metrics["bimod"][dom]["CalendarMonths"][imn] = CalcBimodality(
                    pdfdom[im, :, idm], bincrates
                )

    print("Completed clustering domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcMetricsDomainAR6(pdf, amt, months, bincrates, dat, ref, ref_dir):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - months: month list of input data
    - bincrates: bin centers
    - dat: data name
    - ref: reference data name
    - ref_dir: reference data directory
    Output
    - metrics: metrics for each domain
    - pdfdom: pdf for each domain
    - amtdom: amt for each domain
    """
    ar6_all = regionmask.defined_regions.ar6.all
    ar6_land = regionmask.defined_regions.ar6.land
    # ar6_ocean = regionmask.defined_regions.ar6.ocean

    land_names = ar6_land.names
    land_abbrevs = ar6_land.abbrevs

    ocean_names = [
        "Arctic-Ocean",
        "Arabian-Sea",
        "Bay-of-Bengal",
        "Equatorial-Indian-Ocean",
        "S.Indian-Ocean",
        "N.Pacific-Ocean",
        "N.W.Pacific-Ocean",
        "N.E.Pacific-Ocean",
        "Pacific-ITCZ",
        "S.W.Pacific-Ocean",
        "S.E.Pacific-Ocean",
        "N.Atlantic-Ocean",
        "N.E.Atlantic-Ocean",
        "Atlantic-ITCZ",
        "S.Atlantic-Ocean",
        "Southern-Ocean",
    ]
    ocean_abbrevs = [
        "ARO",
        "ARS",
        "BOB",
        "EIO",
        "SIO",
        "NPO",
        "NWPO",
        "NEPO",
        "PITCZ",
        "SWPO",
        "SEPO",
        "NAO",
        "NEAO",
        "AITCZ",
        "SAO",
        "SOO",
    ]

    names = land_names + ocean_names
    abbrevs = land_abbrevs + ocean_abbrevs

    regions = {}
    for reg in abbrevs:
        if (
            reg in land_abbrevs
            or reg == "ARO"
            or reg == "ARS"
            or reg == "BOB"
            or reg == "EIO"
            or reg == "SIO"
        ):
            vertices = ar6_all[reg].polygon
        elif reg == "NPO":
            r1 = [[132, 20], [132, 25], [157, 50], [180, 59.9], [180, 25]]
            r2 = [
                [-180, 25],
                [-180, 65],
                [-168, 65],
                [-168, 52.5],
                [-143, 58],
                [-130, 50],
                [-125.3, 40],
            ]
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == "NWPO":
            vertices = Polygon([[139.5, 0], [132, 5], [132, 20], [180, 25], [180, 0]])
        elif reg == "NEPO":
            vertices = Polygon(
                [[-180, 15], [-180, 25], [-125.3, 40], [-122.5, 33.8], [-104.5, 16]]
            )
        elif reg == "PITCZ":
            vertices = Polygon(
                [[-180, 0], [-180, 15], [-104.5, 16], [-83.4, 2.2], [-83.4, 0]]
            )
        elif reg == "SWPO":
            r1 = Polygon([[155, -30], [155, -10], [139.5, 0], [180, 0], [180, -30]])
            r2 = Polygon([[-180, -30], [-180, 0], [-135, -10], [-135, -30]])
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == "SEPO":
            vertices = Polygon(
                [
                    [-135, -30],
                    [-135, -10],
                    [-180, 0],
                    [-83.4, 0],
                    [-83.4, -10],
                    [-74.6, -20],
                    [-78, -41],
                ]
            )
        elif reg == "NAO":
            vertices = Polygon(
                [
                    [-70, 25],
                    [-77, 31],
                    [-50, 50],
                    [-50, 58],
                    [-42, 58],
                    [-38, 62],
                    [-10, 62],
                    [-10, 40],
                ]
            )
        elif reg == "NEAO":
            vertices = Polygon(
                [[-52.5, 10], [-70, 25], [-10, 40], [-10, 30], [-20, 30], [-20, 10]]
            )
        elif reg == "AITCZ":
            vertices = Polygon(
                [[-50, 0], [-50, 7.6], [-52.5, 10], [-20, 10], [-20, 7.6], [8, 0]]
            )
        elif reg == "SAO":
            vertices = Polygon([[-39.5, -25], [-34, -20], [-34, 0], [8, 0], [8, -36]])
        elif reg == "EIO":
            vertices = Polygon([[139.5, 0], [132, 5], [132, 20], [180, 25], [180, 0]])
        elif reg == "SOO":
            vertices = Polygon(
                [
                    [-180, -56],
                    [-180, -70],
                    [-80, -70],
                    [-65, -62],
                    [-56, -62],
                    [-56, -75],
                    [-25, -75],
                    [5, -64],
                    [180, -64],
                    [180, -50],
                    [155, -50],
                    [110, -36],
                    [8, -36],
                    [-39.5, -25],
                    [-56, -40],
                    [-56, -56],
                    [-79, -56],
                    [-79, -47],
                    [-78, -41],
                    [-135, -30],
                    [-180, -30],
                ]
            )
        regions[reg] = vertices

    rdata = []
    for reg in abbrevs:
        rdata.append(regions[reg])
    ar6_all_mod_ocn = regionmask.Regions(
        rdata,
        names=names,
        abbrevs=abbrevs,
        name="AR6 reference regions with modified ocean regions",
    )

    ddom = []
    for d in [pdf, amt]:
        # Dynamically detect latitude and longitude dimension names
        lat_name = get_latitude_key(d)
        lon_name = get_longitude_key(d)

        mask_3D = ar6_all_mod_ocn.mask_3D(d, lon_name=lon_name, lat_name=lat_name)

        # Extract latitude coordinate
        lat = d.coords[lat_name]

        # Compute latitude-based weights
        weights = np.cos(np.deg2rad(lat))

        # Broadcast weights to match d’s shape
        weights_2d = weights.broadcast_like(d.sel({lon_name: d[lon_name]}))

        # Combine mask and weights
        combined_weights = mask_3D * weights_2d

        # Compute weighted mean over spatial dimensions
        am = d.weighted(combined_weights).mean(dim=(lat_name, lon_name))

        ddom.append(am)

    ddom = np.reshape(ddom, (-1, pdf.shape[0], pdf.shape[1], len(abbrevs)))
    print("ddom.shape:", ddom.shape)

    pdfdom = ddom[0]
    amtdom = ddom[1]

    # Create the new domain coordinate
    domain_dim = "domains"
    domain_coords = np.arange(len(abbrevs))  # or list of names if available

    pdfdom = xr.DataArray(
        pdfdom,
        dims=(am.dims[0], am.dims[1], domain_dim),
        coords={
            am.dims[0]: am.coords[am.dims[0]],
            am.dims[1]: am.coords[am.dims[1]],
            domain_dim: domain_coords,
        },
    )

    amtdom = xr.DataArray(
        amtdom.data,
        dims=(am.dims[0], am.dims[1], domain_dim),
        coords={
            am.dims[0]: am.coords[am.dims[0]],
            am.dims[1]: am.coords[am.dims[1]],
            domain_dim: domain_coords,
        },
    )

    print("dat:", dat, "ref:", ref)

    if dat == ref:
        pdfdom_ref = pdfdom
        amtdom_ref = amtdom
    else:
        file = f"dist_frq.amt_domainAR6_regrid.{pdf.shape[3]}x{pdf.shape[2]}_{ref}.nc"
        pdfdom_ref = xcdat_open(os.path.join(ref_dir, file))["pdf"]
        amtdom_ref = xcdat_open(os.path.join(ref_dir, file))["amt"]

    metrics = {}
    metrics["frqpeak"] = {}
    metrics["frqwidth"] = {}
    metrics["amtpeak"] = {}
    metrics["amtwidth"] = {}
    metrics["pscore"] = {}
    metrics["frqP10"] = {}
    metrics["frqP20"] = {}
    metrics["frqP80"] = {}
    metrics["frqP90"] = {}
    metrics["amtP10"] = {}
    metrics["amtP20"] = {}
    metrics["amtP80"] = {}
    metrics["amtP90"] = {}
    metrics["bimod"] = {}
    for idm, dom in enumerate(abbrevs):
        metrics["frqpeak"][dom] = {"CalendarMonths": {}}
        metrics["frqwidth"][dom] = {"CalendarMonths": {}}
        metrics["amtpeak"][dom] = {"CalendarMonths": {}}
        metrics["amtwidth"][dom] = {"CalendarMonths": {}}
        metrics["pscore"][dom] = {"CalendarMonths": {}}
        metrics["frqP10"][dom] = {"CalendarMonths": {}}
        metrics["frqP20"][dom] = {"CalendarMonths": {}}
        metrics["frqP80"][dom] = {"CalendarMonths": {}}
        metrics["frqP90"][dom] = {"CalendarMonths": {}}
        metrics["amtP10"][dom] = {"CalendarMonths": {}}
        metrics["amtP20"][dom] = {"CalendarMonths": {}}
        metrics["amtP80"][dom] = {"CalendarMonths": {}}
        metrics["amtP90"][dom] = {"CalendarMonths": {}}
        metrics["bimod"][dom] = {"CalendarMonths": {}}
        for im, mon in enumerate(months):
            if mon in ["ANN", "MAM", "JJA", "SON", "DJF"]:
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pdfdom[im, :, idm], bincrates
                )
                metrics["frqpeak"][dom][mon] = rainpeak
                metrics["frqwidth"][dom][mon] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    amtdom[im, :, idm], bincrates
                )
                metrics["amtpeak"][dom][mon] = rainpeak
                metrics["amtwidth"][dom][mon] = rainwidth
                metrics["pscore"][dom][mon] = CalcPscore(
                    pdfdom[im, :, idm], pdfdom_ref[im, :, idm]
                )
                (
                    metrics["frqP10"][dom][mon],
                    metrics["frqP20"][dom][mon],
                    metrics["frqP80"][dom][mon],
                    metrics["frqP90"][dom][mon],
                    metrics["amtP10"][dom][mon],
                    metrics["amtP20"][dom][mon],
                    metrics["amtP80"][dom][mon],
                    metrics["amtP90"][dom][mon],
                ) = CalcP10P90(
                    pdfdom[im, :, idm],
                    amtdom[im, :, idm],
                    amtdom_ref[im, :, idm],
                    bincrates,
                )
                metrics["bimod"][dom][mon] = CalcBimodality(
                    pdfdom[im, :, idm], bincrates
                )

            else:
                calmon = [
                    "JAN",
                    "FEB",
                    "MAR",
                    "APR",
                    "MAY",
                    "JUN",
                    "JUL",
                    "AUG",
                    "SEP",
                    "OCT",
                    "NOV",
                    "DEC",
                ]
                imn = calmon.index(mon) + 1
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    pdfdom[im, :, idm], bincrates
                )
                metrics["frqpeak"][dom]["CalendarMonths"][imn] = rainpeak
                metrics["frqwidth"][dom]["CalendarMonths"][imn] = rainwidth
                rainpeak, rainwidth, plotpeak, plotwidth = CalcRainMetrics(
                    amtdom[im, :, idm], bincrates
                )
                metrics["amtpeak"][dom]["CalendarMonths"][imn] = rainpeak
                metrics["amtwidth"][dom]["CalendarMonths"][imn] = rainwidth
                metrics["pscore"][dom]["CalendarMonths"][imn] = CalcPscore(
                    pdfdom[im, :, idm], pdfdom_ref[im, :, idm]
                )
                (
                    metrics["frqP10"][dom]["CalendarMonths"][imn],
                    metrics["frqP20"][dom]["CalendarMonths"][imn],
                    metrics["frqP80"][dom]["CalendarMonths"][imn],
                    metrics["frqP90"][dom]["CalendarMonths"][imn],
                    metrics["amtP10"][dom]["CalendarMonths"][imn],
                    metrics["amtP20"][dom]["CalendarMonths"][imn],
                    metrics["amtP80"][dom]["CalendarMonths"][imn],
                    metrics["amtP90"][dom]["CalendarMonths"][imn],
                ) = CalcP10P90(
                    pdfdom[im, :, idm],
                    amtdom[im, :, idm],
                    amtdom_ref[im, :, idm],
                    bincrates,
                )
                metrics["bimod"][dom]["CalendarMonths"][imn] = CalcBimodality(
                    pdfdom[im, :, idm], bincrates
                )

    print("Completed AR6 domain metrics")
    return metrics, pdfdom, amtdom


# ==================================================================================
def CalcPscore(pdf, pdf_ref):
    """
    Input
    - pdf: pdf
    - pdf_ref: pdf reference for Perkins score
    Output
    - pscore: Perkins score
    """
    pdf = pdf.where(np.isfinite(pdf))
    pdf_ref = pdf_ref.where(np.isfinite(pdf_ref))

    pscore = np.sum(np.minimum(pdf, pdf_ref), axis=0)
    pscore = np.array(pscore).tolist()

    return pscore


# ==================================================================================
def CalcP10P90(pdf, amt, amt_ref, bincrates):
    """
    Input
    - pdf: pdf
    - amt: amount distribution
    - amt_ref: amt reference
    - bincrates: bin centers
    Output
    - f10: fraction of frequency for lower 10 percentile amount
    - f20: fraction of frequency for lower 20 percentile amount
    - f80: fraction of frequency for upper 80 percentile amount
    - f90: fraction of frequency for upper 90 percentile amount
    - a10: fraction of amount for lower 10 percentile amount
    - a20: fraction of amount for lower 20 percentile amount
    - a80: fraction of amount for upper 80 percentile amount
    - a90: fraction of amount for upper 90 percentile amount
    """
    pdf = pdf.where(np.isfinite(pdf))
    amt = amt.where(np.isfinite(amt))
    amt_ref = amt_ref.where(np.isfinite(amt_ref))

    # Days with precip<0.1mm/day are considered dry (Pendergrass and Deser 2017)
    thidx = np.argwhere(bincrates > 0.1)
    thidx = int(thidx[0][0])
    pdf[:thidx] = 0
    amt[:thidx] = 0
    amt_ref[:thidx] = 0
    # -----------------------------------------------------

    # Cumulative PDF
    pdffrac = pdf / np.sum(pdf, axis=0)
    csum_pdf = np.cumsum(pdffrac, axis=0)

    # Cumulative amount fraction
    amtfrac = amt / np.sum(amt, axis=0)
    csum_amtfrac = np.cumsum(amtfrac, axis=0)

    # Reference cumulative amount fraction
    amtfrac_ref = amt_ref / np.sum(amt_ref, axis=0)
    csum_amtfrac_ref = np.cumsum(amtfrac_ref, axis=0)

    # Find 10, 20, 80, and 90 percentiles
    p10_all = np.argwhere((csum_amtfrac_ref <= 0.1).values)
    p20_all = np.argwhere((csum_amtfrac_ref <= 0.2).values)
    p80_all = np.argwhere((csum_amtfrac_ref >= 0.8).values)
    p90_all = np.argwhere((csum_amtfrac_ref >= 0.9).values)

    if np.array(p10_all).size == 0:
        f10 = np.nan
        a10 = np.nan
    else:
        p10 = int(p10_all[-1][0])
        f10 = csum_pdf[p10]
        a10 = csum_amtfrac[p10]

    if np.array(p20_all).size == 0:
        f20 = np.nan
        a20 = np.nan
    else:
        p20 = int(p20_all[-1][0])
        f20 = csum_pdf[p20]
        a20 = csum_amtfrac[p20]

    if np.array(p80_all).size == 0:
        f80 = np.nan
        a80 = np.nan
    else:
        p80 = int(p80_all[0][0])
        f80 = 1 - csum_pdf[p80]
        a80 = 1 - csum_amtfrac[p80]

    if np.array(p90_all).size == 0:
        f90 = np.nan
        a90 = np.nan
    else:
        p90 = int(p90_all[0][0])
        f90 = 1 - csum_pdf[p90]
        a90 = 1 - csum_amtfrac[p90]

    f10 = np.array(f10).tolist()
    f20 = np.array(f20).tolist()
    f80 = np.array(f80).tolist()
    f90 = np.array(f90).tolist()
    a10 = np.array(a10).tolist()
    a20 = np.array(a20).tolist()
    a80 = np.array(a80).tolist()
    a90 = np.array(a90).tolist()

    return f10, f20, f80, f90, a10, a20, a80, a90


# ==================================================================================
def CalcBimodality(pdf, distbin):
    """
    Input
    - pdf: pdf
    - distbin: bin centers
    Output
    - bimod: Bimodality
    """
    # pdf = pdf.filled(np.nan)
    pdf = pdf.where(np.isfinite(pdf))

    binrange = [0.1, 50]  # precipitation bin range for gradient calculation
    cofsmooth = [51, 10]  # window size and polynomial order for smoothing

    ## 1stBin=2ndBin before smoothing
    tmp = copy.deepcopy(pdf)
    tmp[0] = tmp[1]
    distsmt = savgol_filter(tmp, cofsmooth[0], cofsmooth[1])

    ## Bins lower than 10th percentile are excluded in searching peaks
    ascend = np.sort(distsmt)
    cumfrac = np.nancumsum(ascend) / np.nansum(ascend)
    ithres = np.argwhere(cumfrac >= 0.1)
    if np.array(ithres).size != 0:
        distsmt = np.where(distsmt >= ascend[ithres[0][0]], distsmt, 0)

    ## Gradient
    distsmtgrad = np.gradient(distsmt)

    ## Calculate bimodality
    inds = []
    for i, grad in enumerate(distsmtgrad):
        if distbin[i] > binrange[0] and distbin[i] < binrange[1]:
            if grad >= 0 and distsmtgrad[i + 1] < 0:
                inds.append(i)
    inds = np.array(inds)

    if len(inds) <= 1:
        bimod = 0
    else:
        inds_op = []
        for i, grad in enumerate(distsmtgrad):
            if i > inds[0] and i < inds[-1]:
                if grad <= 0 and distsmtgrad[i + 1] > 0:
                    inds_op.append(i)

        if np.array(inds_op).size == 0:
            bimod = 0
        else:
            peaks_op = []
            for ind in inds_op:
                peaks_op.append(distsmt[ind])

            indcenter = inds_op[np.argsort(peaks_op)[0]]
            indsleft = inds[inds < indcenter]
            indsright = inds[inds > indcenter]

            peaksleft = []
            for ind in indsleft:
                peaksleft.append(distsmt[ind])
            maxleft = np.nanmax(peaksleft)
            peaksright = []
            for ind in indsright:
                peaksright.append(distsmt[ind])
            maxright = np.nanmax(peaksright)

            bimod = (min(maxleft, maxright) - distsmt[indcenter]) / max(
                maxleft, maxright
            )
            if maxleft > maxright:
                bimod = -bimod

    return bimod


# ==================================================================================
def oneyear(thisyear, missingthresh, debug=False):
    # Given one year of precip data, calculate the number of days for half of precipitation
    # Ignore years with zero precip (by setting them to NaN).
    # thisyear is one year of data, (an np array) with the time variable in the leftmost dimension

    # thisyear = thisyear.filled(np.nan)  # np.array(thisyear)
    thisyear = thisyear.where(np.isfinite(thisyear))

    dims = thisyear.shape
    nd = dims[0]
    ndwonan = np.sum(~np.isnan(thisyear), axis=0)
    missingfrac = np.sum(np.isnan(thisyear), axis=0) / nd
    ptot = np.nansum(thisyear, axis=0)
    sortandflip = -np.sort(-thisyear, axis=0)
    cum_sum = np.nancumsum(sortandflip, axis=0)
    ptotnp = np.array(ptot)
    ptotnp[np.where(ptotnp == 0)] = np.nan
    pfrac = cum_sum / np.tile(ptotnp[np.newaxis, :, :], [nd, 1, 1])
    ndhy = np.full((dims[1], dims[2]), np.nan)
    prdays = np.full((dims[1], dims[2]), np.nan)
    prdays_gt_1mm = np.full((dims[1], dims[2]), np.nan)
    x = np.linspace(0, nd, num=nd + 1, endpoint=True)
    z = np.array([0.0])
    for ij in range(dims[1]):
        for ik in range(dims[2]):
            p = pfrac[:, ij, ik]
            y = np.concatenate([z, p])
            ndh = np.interp(0.5, y, x)
            ndhy[ij, ik] = ndh
            if np.isnan(ptotnp[ij, ik]):
                prdays[ij, ik] = np.nan
                prdays_gt_1mm[ij, ik] = np.nan
            else:
                # For the case, pfrac does not reach 1 (maybe due to regridding)
                # prdays[ij, ik] = np.where(y >= 1)[0][0]
                prdays[ij, ik] = np.nanargmax(y)
                if np.diff(cum_sum[:, ij, ik])[-1] >= 1:
                    prdays_gt_1mm[ij, ik] = prdays[ij, ik]
                else:
                    prdays_gt_1mm[ij, ik] = np.where(
                        np.diff(np.concatenate([z, cum_sum[:, ij, ik]])) < 1
                    )[0][0]

    # prdyfrac = prdays/ndwonan
    prdyfrac = prdays_gt_1mm / ndwonan
    # sdii = ptot/prdays
    sdii = ptot / prdays_gt_1mm  # Zhang et al. (2011)

    if debug:
        print("missingfrac type:", type(missingfrac))  # xarray.DataArray
        print("missingfrac shape:", missingfrac.shape)  # e.g., (90, 180)
        print("missingfrac dims:", missingfrac.dims)  # ('lat', 'lon')

    ndhy[np.where(missingfrac > missingthresh)] = np.nan
    prdyfrac[np.where(missingfrac > missingthresh)] = np.nan
    sdii[np.where(missingfrac > missingthresh)] = np.nan

    missingfrac2 = np.tile(missingfrac.values[np.newaxis, :, :], (nd, 1, 1))
    pfrac[np.where(missingfrac2 > missingthresh)] = np.nan

    if debug:
        print("pfrac type:", type(pfrac))
        print("pfrac shape:", pfrac.shape)

        print("ndhy type:", type(ndhy))
        print("ndhy shape:", ndhy.shape)

        print("prdyfac type:", type(prdyfrac))
        print("prdyfac shape:", prdyfrac.shape)

        print("sdii type:", type(sdii))
        print("sdii shape:", sdii.shape)

    return pfrac, ndhy, prdyfrac, sdii


# ==================================================================================
def MedDomain(d, months):
    """
    Domain average
    Input
    - d: cdms variable
    - months: month list of input data
    Output
    - ddom: Domain median data (json)
    """
    domains = [
        "Total_50S50N",
        "Ocean_50S50N",
        "Land_50S50N",
        "Total_30N50N",
        "Ocean_30N50N",
        "Land_30N50N",
        "Total_30S30N",
        "Ocean_30S30N",
        "Land_30S30N",
        "Total_50S30S",
        "Ocean_50S30S",
        "Land_50S30S",
    ]

    # Create mask in xarray format: 1.0 for land, 0.0 for ocean
    mask = create_land_sea_mask(d[0])

    # Broadcast the mask to match the data's shape, if necessary
    mask_broadcasted = xr.broadcast(d, mask)[1]

    # Apply land and ocean masks using xarray.where
    d_land = d.where(mask_broadcasted == 1.0)
    d_ocean = d.where(mask_broadcasted == 0.0)

    ddom = {}
    for dom in domains:
        if "Ocean" in dom:
            dmask = d_ocean
        elif "Land" in dom:
            dmask = d_land
        else:
            dmask = d

        # Replace non-finite values (NaNs, Infs) with NaN explicitly
        dmask = dmask.where(np.isfinite(dmask))

        # Latitude slicing based on domain name
        if "50S50N" in dom:
            lat_range = slice(-50, 50)
        elif "30N50N" in dom:
            lat_range = slice(30, 50)
        elif "30S30N" in dom:
            lat_range = slice(-30, 30)
        elif "50S30S" in dom:
            lat_range = slice(-50, -30)
        else:
            lat_range = slice(None)  # no lat restriction

        # Subset and compute median over spatial dims (assumes dims are 'lat' and 'lon')
        lat_key = get_latitude_key(dmask)
        lon_key = get_longitude_key(dmask)
        subset = dmask.sel(**{lat_key: lat_range})
        am = subset.median(dim=[lat_key, lon_key], skipna=True).values.tolist()

        print("subset:", subset)
        print("subset type:", type(subset))
        print("am:", am)

        ddom[dom] = {"CalendarMonths": {}}
        for im, mon in enumerate(months):
            if mon in ["ANN", "MAM", "JJA", "SON", "DJF"]:
                ddom[dom][mon] = am[im]
            else:
                calmon = get_all_months()
                imn = calmon.index(mon) + 1
                ddom[dom]["CalendarMonths"][imn] = am[im]

    print("Completed domain median")
    return ddom


# ==================================================================================
def MedDomain3Clust(d, months):
    """
    Domain average
    Input
    - d: cdms variable
    - months: month list of input data
    Output
    - ddom: Domain median data (json)
    """
    domains = [
        "Total_HR_50S50N",
        "Total_MR_50S50N",
        "Total_LR_50S50N",
        "Total_HR_30N50N",
        "Total_MR_30N50N",
        "Total_LR_30N50N",
        "Total_HR_30S30N",
        "Total_MR_30S30N",
        "Total_LR_30S30N",
        "Total_HR_50S30S",
        "Total_MR_50S30S",
        "Total_LR_50S30S",
        "Ocean_HR_50S50N",
        "Ocean_MR_50S50N",
        "Ocean_LR_50S50N",
        "Ocean_HR_30N50N",
        "Ocean_MR_30N50N",
        "Ocean_LR_30N50N",
        "Ocean_HR_30S30N",
        "Ocean_MR_30S30N",
        "Ocean_LR_30S30N",
        "Ocean_HR_50S30S",
        "Ocean_MR_50S30S",
        "Ocean_LR_50S30S",
        "Land_HR_50S50N",
        "Land_MR_50S50N",
        "Land_LR_50S50N",
        "Land_HR_30N50N",
        "Land_MR_30N50N",
        "Land_LR_30N50N",
        "Land_HR_30S30N",
        "Land_MR_30S30N",
        "Land_LR_30S30N",
        "Land_HR_50S30S",
        "Land_MR_50S30S",
        "Land_LR_50S30S",
    ]

    egg_pth = resources.resource_path()
    file = "cluster3_pdf.amt_regrid.360x180_IMERG_ALL_90S90N.nc"
    cluster = xr.open_dataset(os.path.join(egg_pth, file))["cluster_nb"]

    regs = ["HR", "MR", "LR"]
    mpolygons = []
    regs_name = []
    for irg, reg in enumerate(regs):
        if reg == "HR":
            data = xr.where(cluster == 0, 1, 0)
            regs_name.append("Heavy precipitating region")
        elif reg == "MR":
            data = xr.where(cluster == 1, 1, 0)
            regs_name.append("Moderate precipitating region")
        elif reg == "LR":
            data = xr.where(cluster == 2, 1, 0)
            regs_name.append("Light precipitating region")
        else:
            print("ERROR: data is not defined")
            exit()

        shapes = rasterio.features.shapes(np.int32(data))

        polygons = []
        for shape in shapes:
            for idx, xy in enumerate(shape[0]["coordinates"][0]):
                lst = list(xy)
                lst[0] = lst[0]
                lst[1] = lst[1] - 89.5
                tup = tuple(lst)
                shape[0]["coordinates"][0][idx] = tup
            if shape[1] == 1:
                polygons.append(Polygon(shape[0]["coordinates"][0]))

        mpolygons.append(MultiPolygon(polygons).simplify(3, preserve_topology=False))

    region = regionmask.Regions(
        mpolygons,
        names=regs_name,
        abbrevs=regs,
        name="Heavy/Moderate/Light precipitating regions",
    )
    print(region)

    mask_3D = region.mask_3D(d)
    mask = create_land_sea_mask(d)

    # Ensure mask is broadcast to match mask_3D shape
    mask2 = mask.broadcast_like(mask_3D)

    # Ocean: where mask == 0.0, keep values from mask_3D, else False
    mask_3D_ocn = xr.where(mask2 == 0.0, mask_3D, False)

    # Land: where mask == 1.0, keep values from mask_3D, else False
    mask_3D_lnd = xr.where(mask2 == 1.0, mask_3D, False)

    ddom = {}
    for dom in domains:
        if "Ocean" in dom:
            mask_3D_tmp = mask_3D_ocn
        elif "Land" in dom:
            mask_3D_tmp = mask_3D_lnd
        else:
            mask_3D_tmp = mask_3D

        # Select correct mask slice based on resolution string
        if "HR" in dom:
            selected_mask = mask_3D_tmp.isel(region=0)
        elif "MR" in dom:
            selected_mask = mask_3D_tmp.isel(region=1)
        elif "LR" in dom:
            selected_mask = mask_3D_tmp.isel(region=2)
        else:
            print("ERROR: HR/MR/LR is not defined")
            sys.exit()

        # Broadcast mask to match d's dimensions
        mask3 = selected_mask.broadcast_like(d)

        # Apply mask and filter out non-finite values
        dmask = d.where(mask3)  # Masks where mask3 is False
        dmask = dmask.where(np.isfinite(dmask))  # Masks non-finite values

        print("dom:", dom)
        print("dmask shape:", dmask.shape)
        print("dmask type:", type(dmask))

        # Latitude slicing based on domain name
        if "50S50N" in dom:
            lat_range = slice(-50, 50)
        elif "30N50N" in dom:
            lat_range = slice(30, 50)
        elif "30S30N" in dom:
            lat_range = slice(-30, 30)
        elif "50S30S" in dom:
            lat_range = slice(-50, -30)
        else:
            lat_range = slice(None)  # no lat restriction

        # Subset and compute median over spatial dims (assumes dims are 'lat' and 'lon')
        lat_key = get_latitude_key(dmask)
        lon_key = get_longitude_key(dmask)
        subset = dmask.sel(**{lat_key: lat_range})
        am = subset.median(dim=[lat_key, lon_key], skipna=True).values.tolist()

        print("subset:", subset)
        print("subset type:", type(subset))
        print("am:", am)

        ddom[dom] = {"CalendarMonths": {}}
        for im, mon in enumerate(months):
            if mon in ["ANN", "MAM", "JJA", "SON", "DJF"]:
                ddom[dom][mon] = am[im]
            else:
                calmon = get_all_months()
                imn = calmon.index(mon) + 1
                ddom[dom]["CalendarMonths"][imn] = am[im]

    print("Completed clustering domain median")
    return ddom


# ==================================================================================
def MedDomainAR6(d, months):
    """
    Domain average
    Input
    - d: cdms variable
    - months: month list of input data
    Output
    - ddom: Domain median data (json)
    """
    ar6_all = regionmask.defined_regions.ar6.all
    ar6_land = regionmask.defined_regions.ar6.land
    # ar6_ocean = regionmask.defined_regions.ar6.ocean

    land_names = ar6_land.names
    land_abbrevs = ar6_land.abbrevs

    ocean_names = [
        "Arctic-Ocean",
        "Arabian-Sea",
        "Bay-of-Bengal",
        "Equatorial-Indian-Ocean",
        "S.Indian-Ocean",
        "N.Pacific-Ocean",
        "N.W.Pacific-Ocean",
        "N.E.Pacific-Ocean",
        "Pacific-ITCZ",
        "S.W.Pacific-Ocean",
        "S.E.Pacific-Ocean",
        "N.Atlantic-Ocean",
        "N.E.Atlantic-Ocean",
        "Atlantic-ITCZ",
        "S.Atlantic-Ocean",
        "Southern-Ocean",
    ]
    ocean_abbrevs = [
        "ARO",
        "ARS",
        "BOB",
        "EIO",
        "SIO",
        "NPO",
        "NWPO",
        "NEPO",
        "PITCZ",
        "SWPO",
        "SEPO",
        "NAO",
        "NEAO",
        "AITCZ",
        "SAO",
        "SOO",
    ]

    names = land_names + ocean_names
    abbrevs = land_abbrevs + ocean_abbrevs

    regions = {}
    for reg in abbrevs:
        if (
            reg in land_abbrevs
            or reg == "ARO"
            or reg == "ARS"
            or reg == "BOB"
            or reg == "EIO"
            or reg == "SIO"
        ):
            vertices = ar6_all[reg].polygon
        elif reg == "NPO":
            r1 = [[132, 20], [132, 25], [157, 50], [180, 59.9], [180, 25]]
            r2 = [
                [-180, 25],
                [-180, 65],
                [-168, 65],
                [-168, 52.5],
                [-143, 58],
                [-130, 50],
                [-125.3, 40],
            ]
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == "NWPO":
            vertices = Polygon([[139.5, 0], [132, 5], [132, 20], [180, 25], [180, 0]])
        elif reg == "NEPO":
            vertices = Polygon(
                [[-180, 15], [-180, 25], [-125.3, 40], [-122.5, 33.8], [-104.5, 16]]
            )
        elif reg == "PITCZ":
            vertices = Polygon(
                [[-180, 0], [-180, 15], [-104.5, 16], [-83.4, 2.2], [-83.4, 0]]
            )
        elif reg == "SWPO":
            r1 = Polygon([[155, -30], [155, -10], [139.5, 0], [180, 0], [180, -30]])
            r2 = Polygon([[-180, -30], [-180, 0], [-135, -10], [-135, -30]])
            vertices = MultiPolygon([Polygon(r1), Polygon(r2)])
        elif reg == "SEPO":
            vertices = Polygon(
                [
                    [-135, -30],
                    [-135, -10],
                    [-180, 0],
                    [-83.4, 0],
                    [-83.4, -10],
                    [-74.6, -20],
                    [-78, -41],
                ]
            )
        elif reg == "NAO":
            vertices = Polygon(
                [
                    [-70, 25],
                    [-77, 31],
                    [-50, 50],
                    [-50, 58],
                    [-42, 58],
                    [-38, 62],
                    [-10, 62],
                    [-10, 40],
                ]
            )
        elif reg == "NEAO":
            vertices = Polygon(
                [[-52.5, 10], [-70, 25], [-10, 40], [-10, 30], [-20, 30], [-20, 10]]
            )
        elif reg == "AITCZ":
            vertices = Polygon(
                [[-50, 0], [-50, 7.6], [-52.5, 10], [-20, 10], [-20, 7.6], [8, 0]]
            )
        elif reg == "SAO":
            vertices = Polygon([[-39.5, -25], [-34, -20], [-34, 0], [8, 0], [8, -36]])
        elif reg == "EIO":
            vertices = Polygon([[139.5, 0], [132, 5], [132, 20], [180, 25], [180, 0]])
        elif reg == "SOO":
            vertices = Polygon(
                [
                    [-180, -56],
                    [-180, -70],
                    [-80, -70],
                    [-65, -62],
                    [-56, -62],
                    [-56, -75],
                    [-25, -75],
                    [5, -64],
                    [180, -64],
                    [180, -50],
                    [155, -50],
                    [110, -36],
                    [8, -36],
                    [-39.5, -25],
                    [-56, -40],
                    [-56, -56],
                    [-79, -56],
                    [-79, -47],
                    [-78, -41],
                    [-135, -30],
                    [-180, -30],
                ]
            )
        regions[reg] = vertices

    rdata = []
    for reg in abbrevs:
        rdata.append(regions[reg])
    ar6_all_mod_ocn = regionmask.Regions(
        rdata,
        names=names,
        abbrevs=abbrevs,
        name="AR6 reference regions with modified ocean regions",
    )

    mask_3D = ar6_all_mod_ocn.mask_3D(d)
    lat_key = get_latitude_key(d)
    lon_key = get_longitude_key(d)
    am = d.where(mask_3D).median(dim=(lat_key, lon_key))

    ddom = {}
    for idm, dom in enumerate(abbrevs):
        ddom[dom] = {"CalendarMonths": {}}
        for im, mon in enumerate(months):
            if mon in ["ANN", "MAM", "JJA", "SON", "DJF"]:
                ddom[dom][mon] = am[im, idm].values.tolist()
            else:
                calmon = get_all_months()
                imn = calmon.index(mon) + 1
                ddom[dom]["CalendarMonths"][imn] = am[im, idm].values.tolist()

    print("Completed AR6 domain median")
    return ddom


# ==================================================================================
def numpy_to_xrda(data, dims, coords):
    """
    Convert numpy array to xarray DataArray

    Parameters
    ----------
    data : numpy.ndarray
        numpy array to convert
    dims : list
        list of dimension names
    coords : dict
        dictionary of coordinate names and values

    Return
    ------
    xarray.DataArray
    """
    # Create xarray DataArray
    da = xr.DataArray(data, coords=coords, dims=dims)
    return da


# ==================================================================================
def write_json(data, out_dir, outfilename, cmec=False):
    """Write data to JSON file.

    Parameters
    ----------
    data : dict
        Dictionary containing the data to be written to JSON.
        The structure should be compatible with the expected JSON format.
    out_dir : str
        Directory where the output JSON file will be saved.
    outfilename : str
        Name of the output JSON file.
    cmec : bool, optional
        If True, write the data in CMEC format, in addition. By default, False
    """

    JSON = pcmdi_metrics.io.base.Base(out_dir, outfilename)
    JSON.write(
        data,
        json_structure=["model + realization", "metrics", "domain", "month"],
        sort_keys=True,
        indent=4,
        separators=(", ", ": "),
    )
    if cmec:
        JSON.write_cmec(indent=4, separators=(", ", ": "))
