#!/usr/bin/env python3
import argparse
import os
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import regionmask
import shapely
import xarray as xr
import xcdat as xc
from xcdat import spatial

from pcmdi_metrics.drcdm.lib import (
    compute_metrics,
    create_drcdm_parser,
    metadata,
    region_utilities,
    utilities,
)

"""
python spatial_average2.py -p ../param/drcdm_param-era5.py --shp_path /pscratch/sd/j/jsgoodni/shapefiles/regions_conus.shp --attribute region
"""


# lon conventions
def _to_0360(lon):
    lon = np.asarray(lon)
    out = lon.copy()
    out[out < 0] += 360.0
    return out


def _to_m180_180(lon):
    lon = np.asarray(lon)
    out = lon.copy()
    out[out >= 180.0] -= 360.0
    return out


# ---------- helpers: coordinate detection ----------
def get_lat_lon_names(ds: xr.Dataset):
    """Return (lat_name, lon_name) using CF metadata or common fallbacks."""
    # Prefer cf-xarray (bundled with xcdat)
    try:
        lon_name = ds.cf.axes.get("X", [None])[0]
        lat_name = ds.cf.axes.get("Y", [None])[0]
        if lon_name is None:
            lon_name = ds.cf.coordinates.get("longitude", [None])[0]
        if lat_name is None:
            lat_name = ds.cf.coordinates.get("latitude", [None])[0]
    except Exception:
        lon_name = lat_name = None

    # Fallbacks
    if lon_name is None:
        for cand in ("lon", "longitude", "x"):
            if cand in ds.coords:
                lon_name = cand
                break
    if lat_name is None:
        for cand in ("lat", "latitude", "y"):
            if cand in ds.coords:
                lat_name = cand
                break

    if lat_name is None or lon_name is None:
        raise KeyError(
            f"Could not find latitude/longitude coordinates. Found coords: {list(ds.coords)}"
        )
    return lat_name, lon_name


def get_time_name(da_or_ds):
    for cand in ("time", "Time", "t"):
        if cand in getattr(da_or_ds, "coords", {}):
            return cand
    return None


# ---------- shapefile / region mask ----------
def harmonize_polygon_longitudes(gdf, ds_lon_values):
    """Shift polygon longitudes to match dataset convention (0–360 vs −180–180)."""
    ds_uses_0360 = np.nanmax(np.asarray(ds_lon_values)) > 180.0
    from shapely.geometry import mapping, shape

    def map_lon(v):
        if ds_uses_0360:
            return v if v >= 0 else v + 360.0
        else:
            return v if v < 180.0 else v - 360.0

    def shift_geom(geom):
        m = mapping(geom)

        def fix_coords(coords):
            if isinstance(coords[0], (list, tuple)):
                return [fix_coords(c) for c in coords]
            return [map_lon(coords[0]), coords[1]]

        def recurse(obj):
            if isinstance(obj, dict):
                obj = obj.copy()
                if "coordinates" in obj:
                    obj["coordinates"] = fix_coords(obj["coordinates"])
                else:
                    for k in obj:
                        obj[k] = recurse(obj[k])
                return obj
            elif isinstance(obj, (list, tuple)):
                return [recurse(x) for x in obj]
            return obj

        return shape(recurse(m))

    gdf2 = gdf.copy()
    gdf2["geometry"] = gdf2["geometry"].apply(shift_geom)
    return gdf2


def build_regionmask_from_shapefile(shapefile, name_col, ds_lon_vals, ds_lat_vals):
    import geopandas as gpd
    import numpy as np
    import regionmask

    gdf = gpd.read_file(shapefile)
    if name_col not in gdf.columns:
        raise ValueError(
            f"Column '{name_col}' not in shapefile. Columns: {list(gdf.columns)}"
        )

    # shift polygon longitudes to match dataset convention (0–360 vs −180–180)
    gdf = harmonize_polygon_longitudes(gdf, ds_lon_vals)

    # ensure one polygon per region name (merge multipart regions)
    gdf = gdf[[name_col, "geometry"]].dissolve(
        by=name_col, as_index=False, aggfunc="first"
    )

    # make a stable, explicit integer-id column for region numbers
    gdf = gdf.reset_index(drop=True).copy()
    gdf["rid"] = np.arange(len(gdf), dtype=int)

    region_names = gdf[name_col].astype(str).tolist()

    # IMPORTANT: pass column names to 'names' and 'numbers'
    rmask = regionmask.from_geopandas(
        gdf,
        names=name_col,  # column name, not list
        numbers="rid",  # column name, not list
    )

    return rmask, region_names, gdf["rid"].tolist()


def mask_for_region_2d(rmask, ridx, ds, lat_name, lon_name):
    """
    Return a boolean mask for a single region aligned to ds grid.
    Uses a 3D mask to handle overlapping polygons safely.
    """
    lon = ds[lon_name]
    lat = ds[lat_name]

    # 3D mask has dims: (lat_name, lon_name, region)
    # method="rasterize" is fast & robust; omit it to use point-in-polygon.
    mask3d = rmask.mask_3D(lon, lat)  # , method="shapely")

    # Select the one region plane -> dims: (lat_name, lon_name)
    regmask = mask3d.sel(region=ridx)

    # Ensure boolean dtype (some versions can yield float if NA sneaks in)
    regmask = regmask.astype(bool)

    return regmask


def _manual_spatial_average(
    da: xr.DataArray, mask_2d: xr.DataArray, lat_name: str, lon_name: str
):
    """
    Area-weighted mean over (lat, lon) using cos(lat) weights and a boolean polygon mask.
    Works for any extra dims (e.g., time) since weights broadcast.
    """
    # Build 2-D weights on (lat, lon): cos(lat) broadcast along lon
    lat_rad = np.deg2rad(da[lat_name])
    wlat = xr.DataArray(
        np.cos(lat_rad), coords={lat_name: da[lat_name]}, dims=(lat_name,)
    )
    w2d = wlat * xr.ones_like(da[lon_name])  # broadcasts to (lat, lon)

    # Apply polygon mask (False -> weight 0)
    wmasked = w2d.where(mask_2d).fillna(0)

    # Weighted mean over spatial dims
    return da.weighted(wmasked).mean(dim=(lat_name, lon_name))


def spatial_mean(da: xr.DataArray, mask_2d: xr.DataArray, lat_name: str, lon_name: str):
    """
    Try xcdat.spatial.average; if unavailable, use manual weighted mean.
    """
    try:
        # Some installs expose the function as xcdat.spatial.average
        from xcdat import spatial as _xcdat_spatial

        if hasattr(_xcdat_spatial, "average"):
            return _xcdat_spatial.average(
                da, axes=["X", "Y"], weights="coslat", mask=mask_2d
            )
    except Exception:
        pass

    # Fallback (xcDAT not available or older version)
    return _manual_spatial_average(da, mask_2d, lat_name, lon_name)


# ---------- concat helper ----------
def concat_region_series(series_list, region_names, region_dim_name="region"):
    out = xr.concat(series_list, dim=region_dim_name)
    out = out.assign_coords(
        {region_dim_name: xr.IndexVariable(region_dim_name, region_names)}
    )
    out = out.set_index({region_dim_name: region_dim_name})

    return out


# ---------- open & align ----------
def open_and_align(file, chunks=None):
    ds = None

    if file:
        ds = xc.open_dataset(str(file), chunks=chunks)

    # lat_m, lon_m = get_lat_lon_names(ds_monthly)
    # monthly_lon_vals = ds_monthly[lon_m].values
    # use_0360 = np.nanmax(monthly_lon_vals) > 180.0

    # def maybe_shift(ds, target_0360):
    #     lat, lon = get_lat_lon_names(ds)
    #     lon_vals = ds[lon].values
    #     if target_0360 and np.nanmax(lon_vals) <= 180.0:
    #         new_lon = _to_0360(lon_vals)
    #         return ds.assign_coords({lon: (lon, new_lon)}).sortby(lon)
    #     if (not target_0360) and np.nanmax(lon_vals) > 180.0:
    #         new_lon = _to_m180_180(lon_vals)
    #         return ds.assign_coords({lon: (lon, new_lon)}).sortby(lon)
    #     return ds

    # ds_monthly = maybe_shift(ds_monthly, use_0360)
    # ds_annual  = maybe_shift(ds_annual,  use_0360)

    return ds


# ---------- computations ----------
def compute_monthly_regional(
    ds_monthly,
    varname,
    rmask,
    region_names,
    region_numbers,
    lat_name,
    lon_name,
    anom=False,
    reference_start_year=1980,
    reference_end_year=2010,
):  # TODO: user-input anomaly start/end
    if anom:
        ds_reference = ds_monthly.isel(
            time=ds_monthly.time.dt.year.isin(
                range(reference_start_year, reference_end_year)
            )
        )
        monthly_mean = ds_reference.groupby("time.month").mean()
        ds_monthly = ds_monthly.groupby("time.month") - monthly_mean

    series = []
    for ridx, _ in zip(region_numbers, region_names):
        mask2d = mask_for_region_2d(rmask, ridx, ds_monthly, lat_name, lon_name)
        reg_mean = spatial_mean(ds_monthly[varname], mask2d, lat_name, lon_name)
        series.append(reg_mean.rename("regional_mean"))
    return concat_region_series(series, region_names, "region")  # (time, region)


def compute_annual_seasonal_regional(
    ds_annual: xr.Dataset,
    rmask,
    region_names,
    region_numbers,
    lat_name: str,
    lon_name: str,
    var_in_annual: str | None = None,
    periods_all=("ANN", "DJF", "MAM", "JJA", "SON", "ANN5"),
    anom=False,
    reference_start_year=1980,
    reference_end_year=2010,
):
    """
    Returns DataArray with dims: (time?, period, region).
    Handles two layouts:
      A) one variable with a 'season' dimension      -> period comes from the 'season' coord
      B) separate variables ANN/DJF/MAM/JJA/SON      -> period comes from those var names
    """
    # ---- Case A: single variable with 'season' dim ----
    da = None
    season_dim = None

    if var_in_annual is not None and var_in_annual in ds_annual.data_vars:
        da_candidate = ds_annual[var_in_annual]
        for cand in ("season", "Season", "SEASON"):
            if cand in da_candidate.dims or cand in da_candidate.coords:
                da = da_candidate
                season_dim = cand if cand in da_candidate.dims else "season"
                # if 'season' is only a coord (not a dim), try to get its dim name
                if season_dim not in da.dims and "season" in da.dims:
                    season_dim = "season"
                break
    else:
        # Auto-detect single-var + season
        dvs = list(ds_annual.data_vars)
        if len(dvs) == 1:
            da_candidate = ds_annual[dvs[0]]
            for cand in ("season", "Season", "SEASON"):
                if cand in da_candidate.dims or cand in da_candidate.coords:
                    da = da_candidate
                    season_dim = cand if cand in da_candidate.dims else "season"
                    if season_dim not in da.dims and "season" in da.dims:
                        season_dim = "season"
                    break

    if da is not None and season_dim is not None:
        # Standardize order: put 'time' first if present, then 'season', then space dims
        order = []
        if "time" in da.dims:
            order.append("time")
        order.append(season_dim)
        for d in da.dims:
            if d not in order:
                order.append(d)
        da = da.transpose(*order)

        seasons = [str(v) for v in da[season_dim].values]
        per_arrays = []
        for ridx, _ in zip(region_numbers, region_names):
            mask2d = mask_for_region_2d(rmask, ridx, ds_annual, lat_name, lon_name)
            reg_mean = spatial_mean(
                da, mask2d, lat_name, lon_name
            )  # dims: time?, season
            # Ensure 'time' exists (some seasonal files may omit)
            if "time" not in reg_mean.dims:
                reg_mean = reg_mean.expand_dims(time=[np.datetime64("1900-01-01")])
            # Rename season -> period
            reg_mean = reg_mean.rename({season_dim: "period"}).assign_coords(
                period=seasons
            )
            per_arrays.append(reg_mean.expand_dims(region=[ridx]))

        out = xr.concat(per_arrays, dim="region")  # dims: time, period, region
        # Replace numeric region ids with names
        out = out.assign_coords(region=("region", region_names))
        return out.rename("regional_mean")

    # ---- Case B: separate variables ANN/DJF/MAM/JJA/SON ----
    periods = [p for p in periods_all if p in ds_annual.data_vars]
    if not periods:
        raise KeyError(
            f"No seasonal/annual variables found. Either provide --var_in_annual for a 'season' layout "
            f"or include any of: {periods_all} as variables."
        )

    per_arrays = []
    for p in periods:
        series = []
        if anom:
            time_slice = slice(
                *(f"{reference_start_year}-01-01", f"{reference_end_year}-12-31")
            )
            ds_annual_climo = ds_annual[p].sel(time=time_slice).mean(dim="time")
            # print(ds_annual_climo)
            ds_annual[p] = ds_annual[p] - ds_annual_climo

        for ridx, _ in zip(region_numbers, region_names):
            mask2d = mask_for_region_2d(rmask, ridx, ds_annual, lat_name, lon_name)
            reg_mean = spatial_mean(
                ds_annual[p], mask2d, lat_name, lon_name
            )  # -> time? or scalar
            if "time" not in reg_mean.dims:
                reg_mean = reg_mean.expand_dims(time=[np.datetime64("1900-01-01")])
            series.append(reg_mean.rename("regional_mean"))
        reg_by_region = (
            xr.concat(series, dim="region")
            .assign_coords(region=region_names)
            .expand_dims(period=[p])
        )
        per_arrays.append(reg_by_region)

    return xr.concat(per_arrays, dim="period")  # dims: time, period, region


# ---------- CLI ----------
def main():
    # ap = argparse.ArgumentParser()
    # # Preferred: explicit files
    # ap.add_argument("--monthly_file", type=str, help="Path to monthly NetCDF (timeseries of monthly means).")
    # ap.add_argument("--annual_file",  type=str, help="Path to annual/seasonal NetCDF. Either has one var with a 'season' dim, or separate ANN/DJF/MAM/JJA/SON vars.")
    # ap.add_argument("--var_in_monthly", type=str, help="Variable name in the monthly file (e.g., tasmax). If omitted and the file has one var, auto-detect.")
    # ap.add_argument("--var_in_annual",  type=str, help="Variable name in the annual file if it has a single var with a 'season' dimension (e.g., tasmax). If omitted and the file has one var, auto-detect.")
    # # Back-compat layout
    # ap.add_argument("--base_path", type=str)
    # ap.add_argument("--variable", type=str)
    # ap.add_argument("--file_name", type=str)
    # ap.add_argument("--annual_file_name", type=str)
    # ap.add_argument("--monthly_subdir", default="monthly")
    # ap.add_argument("--annual_subdir",  default="annual")
    # # Regions
    # ap.add_argument("--shapefile", required=True)
    # ap.add_argument("--region_name_col", required=True)
    # # Output
    # ap.add_argument("--outdir", default=".")
    # ap.add_argument("--out_monthly_nc", default="monthly_by_region.nc")
    # ap.add_argument("--out_annual_nc",  default="annual_seasonal_by_region.nc")
    # ap.add_argument("--engine", default="netcdf4")
    # ap.add_argument("--chunks_time", type=int, default=None)

    parser = create_drcdm_parser.create_extremes_parser()
    parameter = parser.get_parameter(argparse_vals_only=False)

    # Parameters
    # I/O settings
    case_id = parameter.case_id
    model_list = parameter.test_data_set
    realizations = parameter.realization
    compute_tas = parameter.compute_tasmean
    mode = parameter.mode
    thresholds = parameter.custom_thresholds

    # Mapping metric name to keys in custom_thresholds
    threshold_key_mapping = {
        "annual_tasmin_le": "tasmin_le",
        "annual_tasmin_ge": "tasmin_ge",
        "annual_tasmax_le": "tasmax_le",
        "annual_tasmax_ge": "tasmax_ge",
        "first_date_below": "growing_season",
        "last_date_below": "growing_season",
        "growing_season": "growing_season",
        "tmax_days_above_q": "tmax_days_above_q",
        "tmax_days_below_q": "tmax_days_below_q",
        "tmin_days_above_q": "tmin_days_above_q",
        "tmin_days_below_q": "tmin_days_below_q",
        "pr_days_above_q": "pr_ge_quant",
        "pr_sum_above_q": "pr_ge_quant",
        "pr_days_above_non_zero_q": "pr_ge_quant",
        "annual_pr_ge": "pr_ge",
    }

    if mode != "timeseries":
        raise ValueError(
            "DRCDP must be run in 'timeseries' mode to compute spatially-averaged timeseries"
        )

    ## MUST BE PROVIDED MANUALLY

    shapefile = parameter.shp_path
    col = parameter.attribute
    anom = parameter.anom
    osyear = parameter.osyear
    oeyear = parameter.oeyear
    no_mask = False

    if (shapefile is None) or (col is None):
        no_mask = True
        print(f"No shapefile provided. Reverting to full-domain averaging")
        # raise FileNotFoundError("Provide shapefile and associated column name")

    # Expected variables - pr, tasmax, tasmin, tas
    variable_list = parameter.vars
    # Ordering -> expected order is ['tasmax', 'tasmin', 'tas', 'pr']
    expected_order = ["tasmax", "tasmin", "pr", "tas"]

    ## Creating the variable list
    # Ordering -> expected order is ['tasmax', 'tasmin', 'tas', 'pr']
    ordered_vars = [
        variable for variable in expected_order if variable in variable_list
    ]
    remaining_vars = [
        variable for variable in variable_list if variable not in expected_order
    ]
    variable_list = ordered_vars + remaining_vars

    if ("tasmax" in variable_list) and ("tasmin" in variable_list):
        if compute_tas:
            variable_list.append("tas")

    metrics_output_path = parameter.metrics_output_path
    include_metrics = parameter.include_metrics
    var_metric_dict = parameter.var_metric_map

    # base_metrics = list(var_metric_dict.pop("other"))
    for var in remaining_vars:  ## Appending variable name to the metric names
        var_metric_dict[var] = var_metric_dict.copy()["other"].copy()
    del var_metric_dict["other"]

    arr = []

    if set(include_metrics) == set(
        item for sublist in var_metric_dict.values() for item in sublist
    ):  # include_metrics == [item for sublist in var_metric_dict.values() for item in sublist]:
        # Include metrics wasn't given
        for variable in ordered_vars:
            arr.extend(var_metric_dict[variable])
        for variable in remaining_vars:
            arr.extend([f"{metric}_{variable}" for metric in var_metric_dict[variable]])
            var_metric_dict[variable] = [
                f"{metric}_{variable}" for metric in var_metric_dict[variable]
            ]
        include_metrics = arr
    else:
        pass

    # print(include_metrics)
    # Initialize Output Path for NetCDF Files
    outdir_dict = {variable: None for variable in variable_list}

    for p in ["postproc"]:
        postproc_dir = os.path.join(metrics_output_path, p)
        nc_subdir = os.path.join(postproc_dir, "netcdf")

        os.makedirs(nc_subdir, exist_ok=True)

        for v in variable_list:
            var_nc_outdir = os.path.join(nc_subdir, v)
            os.makedirs(var_nc_outdir, exist_ok=True)
            outdir_dict[v] = var_nc_outdir

    skipped_metrics = []

    # Build file name paths
    for model in model_list:
        for realization in realizations:
            for metric in include_metrics:
                print(metric)
                if metric.startswith("ref"):
                    print(f"Skipping {metric}")
                    continue  # We don't care about reference variable metrics

                values = [""]
                if metric in threshold_key_mapping.keys():
                    unit = thresholds[threshold_key_mapping[metric]]["units"]
                    if unit == "inches":
                        unit = "in"

                    prefix = "_"
                    if "deg" in unit:
                        unit = unit.removeprefix("deg")
                    elif unit == "%":
                        unit = ""
                        prefix = ""
                    values = [
                        f"{prefix}{value}{unit}"
                        for value in thresholds[threshold_key_mapping[metric]]["values"]
                    ]

                elif metric == "annual_max_nday_pr":
                    values = [5, 10, 20, 30]

                print(values)
                for value in values:
                    if metric == "annual_max_nday_pr":
                        new_metric_name = metric.replace("nday", f"{value}day")
                    else:
                        new_metric_name = metric + f"{value}"

                    # Determine if metric is monthly, annual, seasonal, or annual-seasonal

                    print(
                        f"Creating Spatially-Averaged Timeseries for {model}, {realization}, {new_metric_name}"
                    )

                    # Initialize annual/monthly paths
                    path = False
                    input_dir = os.path.join(metrics_output_path, "netcdf")

                    nc_base = os.path.join(input_dir, "$freq")
                    nc_base = os.path.join(nc_base, "$varname")
                    nc_base = os.path.join(
                        nc_base, "_".join([model, realization, "$metric.nc"])
                    )

                    freq = "annual"
                    monthly = False

                    if "monthly" in new_metric_name:
                        monthly = "True"
                        freq = "monthly"
                    elif "JJA" in new_metric_name:
                        freq = "seasonal"
                    elif "q" in new_metric_name:
                        freq = "quantile"

                    if ("q" in new_metric_name or "median" in new_metric_name) and (
                        "above" not in new_metric_name
                        and "below" not in new_metric_name
                    ):
                        print("Skipping quantile metric (no yearly data)")
                        continue

                    variable = [
                        variable
                        for variable, metric_list in var_metric_dict.items()
                        if metric in metric_list
                    ][0]
                    path = compute_metrics.create_nc_outpath(
                        nc_base, freq, variable, new_metric_name
                    )
                    print(path)
                    if not os.path.exists(path):
                        print(
                            f"Timeseries File not found for {new_metric_name}. Skipping\n"
                        )
                        skipped_metrics.append(new_metric_name)
                        continue

                    chunks = {"time": -1}

                    # Open & align longitude conventions
                    ds = open_and_align(path, chunks=chunks)
                    lat_name, lon_name = get_lat_lon_names(ds)

                    # ----------------------------
                    # Build regionmask on monthly grid (works for both files)
                    # ----------------------------
                    if not no_mask:
                        (
                            rmask,
                            region_names,
                            region_numbers,
                        ) = build_regionmask_from_shapefile(
                            shapefile, col, ds[lon_name].values, ds[lat_name].values
                        )
                    else:
                        # Get the shape of your spatial grid
                        lon = ds[lon_name].values
                        lat = ds[lat_name].values
                        lon_min, lon_max = lon.min(), lon.max()
                        lat_min, lat_max = lat.min(), lat.max()

                        # Create a rectangular polygon covering the whole domain
                        polygon = shapely.geometry.box(
                            lon_min, lat_min, lon_max, lat_max
                        )

                        # Build a GeoDataFrame
                        gdf = gpd.GeoDataFrame(
                            {
                                "name": ["default_region"],
                                "geometry": [polygon],
                                "number": [1],
                            }
                        )

                        # Create regionmask from GeoDataFrame
                        rmask = regionmask.from_geopandas(
                            gdf, names="name", numbers="number"
                        )
                        region_names = ["default_region"]
                        region_numbers = [1]

                    # Compute monthly timeseies (time, region)
                    if monthly:
                        da_monthly = compute_monthly_regional(
                            ds,
                            variable,
                            rmask,
                            region_names,
                            region_numbers,
                            lat_name,
                            lon_name,
                            anom,
                            reference_start_year=osyear,
                            reference_end_year=oeyear,
                        )
                        ds_out = da_monthly.to_dataset(name=new_metric_name)
                        ds_out["region"] = ds_out["region"].astype(str)

                        # carry units/attrs
                        if "units" in ds[variable].attrs:
                            ds_out[new_metric_name].attrs["units"] = ds[variable].attrs[
                                "units"
                            ]
                        printed_name = (
                            Path(shapefile).name
                            if shapefile is not None
                            else "given_dataset"
                        )
                        ds_out[new_metric_name].attrs[
                            "description"
                        ] = f"Area-weighted (coslat) spatial average over polygon; mask from {printed_name}"
                        ds_out["region"].attrs[
                            "long_name"
                        ] = "Region name from shapefile"

                    # ----------------------------
                    # Compute annual/seasonal (time, period, region)
                    # Handles:
                    #   - one var with 'season' dim (var_a not None)
                    #   - separate ANN/DJF/MAM/JJA/SON variables (var_a None)
                    # ----------------------------

                    else:  # Annual or Seasonal
                        da_annual = compute_annual_seasonal_regional(
                            ds,
                            rmask,
                            region_names,
                            region_numbers,
                            lat_name,
                            lon_name,
                            var_in_annual=variable,
                            anom=True,
                            reference_start_year=osyear,
                            reference_end_year=oeyear,
                        )
                        ds_out = da_annual.to_dataset(name=new_metric_name)
                        ds_out["region"] = ds_out["region"].astype(str)
                        ds_out["period"] = ds_out["period"].astype(str)

                        # carry units from annual variable(s)
                        # if "units" in ds[variable].attrs:
                        #     ds_out["regional_mean"].attrs["units"] = ds[variable].attrs["units"]
                        # else:
                        for p in ("ANN", "DJF", "MAM", "JJA", "SON"):
                            if p in ds and "units" in ds[p].attrs:
                                ds_out[new_metric_name].attrs["units"] = ds[p].attrs[
                                    "units"
                                ]
                                break
                        printed_name = (
                            Path(shapefile).name
                            if shapefile is not None
                            else "given dataset"
                        )
                        ds_out[new_metric_name].attrs[
                            "description"
                        ] = f"Area-weighted (coslat) spatial average over polygon; mask from {printed_name}"
                        ds_out["region"].attrs[
                            "long_name"
                        ] = "Region name from shapefile"
                        ds_out["period"].attrs[
                            "long_name"
                        ] = "Climatological period (ANN,DJF,MAM,JJA,SON subset)"

                    # Write NetCDF
                    outdir = Path(outdir_dict[variable])
                    outdir.mkdir(parents=True, exist_ok=True)
                    anom_add = "_anom" if anom else ""

                    outf = outdir / Path(path).name.replace(
                        ".nc", f"{anom_add}_timeseries.nc"
                    )
                    ds_out.to_netcdf(outf)
                    print(f"Wrote {outf}")
                    print("\n")
    if len(skipped_metrics) > 0:
        print("The following metrics were skipped:")
        for name in skipped_metrics:
            print(f"- {name}")


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
