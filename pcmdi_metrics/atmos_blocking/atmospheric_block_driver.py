import argparse
import glob
import importlib.util
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta

import cftime
import numpy as np
import pandas as pd
import xarray as xr
from netCDF4 import Dataset


# Parameters
def _load_params_from_file(path):
    if not path:
        return None
    try:
        spec = importlib.util.spec_from_file_location("height_params", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"WARNING: Failed to import params file '{path}': {e}")
    return None


# Argument parsing to allow the script to be run standalone or imported as a module.
class BlockingParser:

    def __init__(self):
        self._ap = argparse.ArgumentParser(
            description="Run blocking pipeline end-to-end"
        )
        self._ap.add_argument(
            "--params",
            dest="params",
            default=None,
            help="Filesystem path to params .py file (e.g., block_param.py)",
        )
        self._ap.add_argument(
            "--case-id",
            dest="case_id",
            default=None,
            help="Case identifier for output subdir",
        )
        self._ap.add_argument(
            "--file-glob",
            dest="file_glob",
            default=None,
            help="Glob for input height files",
        )
        self._ap.add_argument(
            "--pressure-level",
            dest="pressure_level",
            type=int,
            default=None,
            help="Pressure level (e.g., 500 or 50000 depending on dataset units)",
        )
        self._ap.add_argument(
            "--start-date",
            dest="start_date",
            default=None,
            help="Start date YYYY-MM-DD",
        )
        self._ap.add_argument(
            "--end-date", dest="end_date", default=None, help="End date YYYY-MM-DD"
        )
        self._ap.add_argument(
            "--output-dir",
            dest="output_dir",
            default=None,
            help="Base output directory",
        )
        self._ap.add_argument(
            "--stitched-out-name",
            dest="stitched_out_name",
            default=None,
            help="Output filename for stitched blocks (within temp dir)",
        )
        self._ap.add_argument(
            "--cleanup-temp",
            dest="cleanup_temp",
            action="store_true",
            help="Delete temp dir after processing",
        )

    def get_parameter(self, argparse_vals_only: bool = False):
        args = self._ap.parse_args()
        params_path = args.params or os.environ.get("HEIGHT_PARAMS")
        if not argparse_vals_only and params_path is None:
            default_candidate = os.path.join(
                os.path.dirname(__file__), "block_param.py"
            )
            if os.path.exists(default_candidate):
                params_path = default_candidate

        params_mod = None if argparse_vals_only else _load_params_from_file(params_path)

        def _get(name, default=None):
            return getattr(params_mod, name, default) if params_mod else default

        params = {
            "case_id": args.case_id or _get("CASE_ID", "blocking"),
            "FILE_GLOB": args.file_glob or _get("FILE_GLOB"),
            "PRESSURE_LEVEL": (
                args.pressure_level
                if args.pressure_level is not None
                else _get("PRESSURE_LEVEL")
            ),
            "START_DATE": args.start_date or _get("START_DATE"),
            "END_DATE": args.end_date or _get("END_DATE"),
            "OUTPUT_DIR": args.output_dir or _get("OUTPUT_DIR"),
            "STITCHED_OUT_NAME": args.stitched_out_name
            or _get("STITCHED_OUT_NAME", "stitched_block_id.nc"),
            "CLEANUP_TEMP": args.cleanup_temp or _get("CLEANUP_TEMP", False),
            "params_path": params_path,
        }

        required = [
            "FILE_GLOB",
            "PRESSURE_LEVEL",
            "START_DATE",
            "END_DATE",
            "OUTPUT_DIR",
            "STITCHED_OUT_NAME",
        ]
        missing = [k for k in required if not params.get(k)]
        if missing:
            raise RuntimeError("Missing required parameters: " + ", ".join(missing))

        return argparse.Namespace(**params)


def verify_output_path(base_dir: str, case_id: str) -> str:
    out_dir = os.path.join(base_dir, str(case_id)) if case_id else base_dir
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _parse_e3sm_file_dates(file_path):
    try:
        date_part = os.path.basename(file_path).rsplit("_", 1)[-1].replace(".nc", "")
        start_str, end_str = date_part.split("-")
        return datetime.strptime(start_str, "%Y%m%d"), datetime.strptime(
            end_str, "%Y%m%d"
        )
    except Exception:
        return None, None


def _e3sm_preprocess(ds, pressure_level=None):
    # Standardize E3SM outputs
    rename = {
        k: v
        for k, v in [("lat", "latitude"), ("lon", "longitude")]
        if k in ds.dims or k in ds.coords
    }
    if rename:
        ds = ds.rename(rename)

    for level_name in ["plev", "level", "lev"]:
        if level_name in ds.dims or level_name in ds.coords:
            units = str(ds[level_name].attrs.get("units", "")).lower()
            is_pa = units in ("pa", "pascals", "pascal")
            target = pressure_level * (100 if is_pa else 1)
            ds = ds.sel({level_name: target}, method="nearest")
            try:
                ds = ds.drop_vars(level_name)
            except Exception:
                pass
            break

    # Rename height variable to hgt for consistency
    if "zg" in ds.data_vars:
        ds = ds.rename({"zg": "hgt"})
    if "time" in ds.dims:
        try:
            ds = ds.resample(time="1D").mean()
        except Exception:
            pass
    return ds


def _filter_files_by_date_range(files, start_dt, end_dt):
    valid = [
        (f, s)
        for f in files
        for s, e in [_parse_e3sm_file_dates(f)]
        if s and e and not (e < start_dt or s > end_dt)
    ]
    return [f for f, _ in sorted(valid, key=lambda x: x[1])]


# Unified calendar date handling
_CALENDAR_MAP = {
    "365_day": cftime.DatetimeNoLeap,
    "no_leap": cftime.DatetimeNoLeap,
    "noleap": cftime.DatetimeNoLeap,
    "gregorian": cftime.DatetimeGregorian,
    "standard": cftime.DatetimeGregorian,
    "proleptic_gregorian": cftime.DatetimeGregorian,
    "360_day": cftime.Datetime360Day,
    "360day": cftime.Datetime360Day,
    "julian": cftime.DatetimeJulian,
}


def _cfdate_like(time_coord, dt):
    try:
        v0 = time_coord.values[0]
    except Exception:
        return dt
    if isinstance(v0, (np.datetime64, datetime)):
        return np.datetime64(pd.Timestamp(dt).normalize())
    try:
        return type(v0)(dt.year, dt.month, dt.day)
    except Exception:
        cal = str(getattr(time_coord, "attrs", {}).get("calendar", "standard")).lower()
        return _CALENDAR_MAP.get(cal, lambda y, m, d: dt)(dt.year, dt.month, dt.day)


def _get_lon_indices_within_range(lon_array, center_lon, half_width_deg):
    # Longitude handling for wrap-around issues
    lon_norm = np.asarray(lon_array) % 360
    delta = ((lon_norm - (center_lon % 360) + 540) % 360) - 180
    within = np.abs(delta) <= half_width_deg
    return np.where(within & (delta < 0))[0], np.where(within & (delta > 0))[0]


def _as_ndarray(a, fill=np.nan):
    if np.ma.isMaskedArray(a):
        return np.ma.filled(a, fill)
    return np.asarray(getattr(a, "values", a))


def _compute_grid_area_km2(lat, lon):
    # Compute grid cell areas using spherical geometry for later size filtering
    R = 6371.0
    lat_rad, lon_rad = np.radians(lat), np.radians(lon)
    dlat, dlon = np.abs(np.gradient(lat_rad)), np.abs(np.gradient(lon_rad))
    return (
        (dlat[:, np.newaxis] * dlon[np.newaxis, :])
        * np.cos(lat_rad[:, np.newaxis])
        * R**2
    )


# -----------------------------
# BLOCKING DETECTION ALGORITHM
# -----------------------------


def run_ibto_and_write_combined(
    file_pattern, start_date, end_date, output_base_dir, pressure_level
):
    lat0_range = np.arange(35, 90.5, 0.5)
    # Note: Adjustments above 70°N prevent running off the pole
    latS_range = np.where(
        lat0_range > 70, lat0_range - (90 - lat0_range), lat0_range - 20
    )
    latN_range = np.where(
        lat0_range > 70, lat0_range + (90 - lat0_range), lat0_range + 20
    )
    # Additional metric used to prevent false positives caused by tropical disturbances
    lat15S_range = np.where(
        lat0_range > 70, lat0_range - (90 - lat0_range) * 0.75, lat0_range - 15
    )
    lat30S_range = np.where(
        lat0_range > 70, lat0_range - (90 - lat0_range) * 1.5, lat0_range - 30
    )

    all_files = glob.glob(file_pattern)
    start_dt_loc = pd.Timestamp(start_date).to_pydatetime()
    end_dt_loc = pd.Timestamp(end_date).to_pydatetime()
    filtered_files = _filter_files_by_date_range(all_files, start_dt_loc, end_dt_loc)

    # Use temp directory to store intermediate files (memory management)
    output_temp_dir = tempfile.mkdtemp(prefix="block_processing_", dir=output_base_dir)
    print(f"Created temporary directory: {output_temp_dir}")
    print()
    output_temp_files = []

    for file_path in filtered_files:
        print(f"Processing {file_path}")
        ds = xr.open_dataset(file_path, engine="netcdf4")
        ds_daily = _e3sm_preprocess(ds, pressure_level=pressure_level)

        Z500_lat0 = ds_daily["hgt"].sel(latitude=lat0_range, method="nearest")
        Z500_latS = ds_daily["hgt"].sel(latitude=latS_range, method="nearest")
        Z500_latN = ds_daily["hgt"].sel(latitude=latN_range, method="nearest")
        Z500_lat15S = ds_daily["hgt"].sel(latitude=lat15S_range, method="nearest")
        Z500_lat30S = ds_daily["hgt"].sel(latitude=lat30S_range, method="nearest")

        lat0_vals = Z500_lat0.coords["latitude"].values
        latS_vals = Z500_latS.coords["latitude"].values
        latN_vals = Z500_latN.coords["latitude"].values

        delta_S_deg = np.abs(lat0_vals - latS_vals)
        delta_N_deg = np.abs(latN_vals - lat0_vals)
        delta_S_deg = np.where(delta_S_deg == 0, 20.0, delta_S_deg)
        delta_N_deg = np.where(delta_N_deg == 0, 20.0, delta_N_deg)

        # Compute meridional gradients for blocking criteria
        GHGS = (Z500_lat0.values - Z500_latS.values) / delta_S_deg[
            np.newaxis, :, np.newaxis
        ]
        GHGN = (Z500_latN.values - Z500_lat0.values) / delta_N_deg[
            np.newaxis, :, np.newaxis
        ]
        gradient_S = Z500_lat15S.values - Z500_lat30S.values

        # Block tag: all three conditions must be met simultaneously
        valid_mask = ((GHGS > 0) & (GHGN < -10) & (gradient_S < 0)).astype(int)
        valid_mask = xr.DataArray(
            valid_mask, coords=Z500_lat0.coords, dims=Z500_lat0.dims
        )
        GHGS_da = xr.DataArray(GHGS, coords=Z500_lat0.coords, dims=Z500_lat0.dims)
        GHGN_da = xr.DataArray(GHGN, coords=Z500_lat0.coords, dims=Z500_lat0.dims)

        ds_out = xr.Dataset({"block_tag": valid_mask, "GHGS": GHGS_da, "GHGN": GHGN_da})
        f_start, _ = _parse_e3sm_file_dates(file_path)
        date_tag = f_start.strftime("%Y%m%d") if f_start else "unknown"
        temp_path = os.path.join(output_temp_dir, f"block_tag.{date_tag}.nc")
        ds_out.to_netcdf(temp_path, format="NETCDF4_CLASSIC")
        output_temp_files.append(temp_path)
        ds.close()

    # Combine all temp files into single dataset for stitching
    print()
    print(
        f"Combining {len(output_temp_files)} temporary files into one dataset (mfdataset)."
    )
    print()
    combined = xr.open_mfdataset(output_temp_files, combine="by_coords")
    final_dataset = xr.Dataset(
        {
            "block_tag": combined["block_tag"],
            "GHGS": combined["GHGS"],
            "GHGN": combined["GHGN"],
        }
    )
    try:
        final_dataset["block_tag"] = (
            final_dataset["block_tag"].fillna(0).astype("uint8")
        )
    except Exception:
        final_dataset["block_tag"] = final_dataset["block_tag"].fillna(0)

    encoding = {
        "block_tag": {"dtype": "uint8", "zlib": True, "complevel": 1},
        "GHGS": {"dtype": "float64", "zlib": True, "complevel": 1},
        "GHGN": {"dtype": "float64", "zlib": True, "complevel": 1},
        "time": {
            "dtype": "int32",
            "zlib": True,
            "complevel": 1,
            "calendar": "gregorian",
            "units": "days since 1900-01-01",
        },
        "latitude": {"dtype": "float64", "zlib": True, "complevel": 1},
        "longitude": {"dtype": "float64", "zlib": True, "complevel": 1},
    }
    final_dataset = final_dataset.chunk({"time": 365})
    combined_path = os.path.join(output_temp_dir, "block_tag_1d.nc")
    print(f"Writing combined dataset to {combined_path}")
    print()
    final_dataset.to_netcdf(
        combined_path,
        format="NETCDF4_CLASSIC",
        engine="netcdf4",
        encoding=encoding,
        compute=True,
    )

    # Clean up intermediate files to save disk space
    for temp_file in output_temp_files:
        try:
            os.remove(temp_file)
        except Exception:
            pass
    print(f"Cleaned up {len(output_temp_files)} temporary files")
    print()
    return combined_path, output_temp_dir


# ------------------------------------
# BLOB STITCHING VIA TEMPEST EXTREMES
# ------------------------------------


def call_stitchblobs(combined_path, temp_dir, stitched_out_name, stitched_path=None):
    if stitched_path is None:
        stitched_path = os.path.join(temp_dir, stitched_out_name)
    stitch_bin = shutil.which("StitchBlobs")
    if stitch_bin is None:
        print("WARNING: StitchBlobs binary not found on PATH. Skipping stitching step.")
        print(
            "If you want stitching, install or put StitchBlobs on PATH and re-run this script."
        )
        return None
    cmd = [
        stitch_bin,
        "--in",
        combined_path,
        "--out",
        stitched_path,
        "--var",
        "block_tag",
        "--outvar",
        "block_id",
        "--latname",
        "latitude",
        "--lonname",
        "longitude",
        "--mintime",
        "4d",  # Blocks must persist at more than 4 days
        "--min_overlap_prev",
        "20",  # Require 20% spatial overlap for tracking
        "--verbose",
    ]
    print(f"Running StitchBlobs (mintime=4d): {' '.join(cmd)}")
    print()
    try:
        proc = subprocess.run(
            cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    except Exception as e:
        print(f"ERROR: Failed to execute StitchBlobs: {e}")
        return None
    if proc.returncode != 0:
        print(
            f"ERROR: StitchBlobs failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
        )
        return None
    if os.path.exists(stitched_path):
        print(f"Stitching complete, output at: {stitched_path}")
        print()
        return stitched_path
    print(
        f"WARNING: StitchBlobs reported success but output file not found: {stitched_path}"
    )
    return None


# ---------------------
# BLOCK SIZE FILTERING
# ---------------------
# Filter blocks by spatial extent to remove noise (too small) and merged
# events (too large). Valid blocking events have maximum areas
# between 2-7.5 million km².


def realign_block_ids(input_file, final_file):
    ds = xr.open_dataset(input_file)
    obj_id = ds["block_id"]
    lat, lon = ds["latitude"].values, ds["longitude"].values
    area_km2 = _compute_grid_area_km2(lat, lon)
    filtered_obj_id = obj_id.values.copy()

    # Track maximum area for each block across all timesteps of lifetime for accurate filtering
    block_areas = {}
    for t in range(obj_id.sizes["time"]):
        ids = obj_id[t].values
        for bid in np.unique(ids[ids != 0]):
            area = np.sum(area_km2[ids == bid])
            block_areas[bid] = max(block_areas.get(bid, 0), area)

    valid_ids = {bid for bid, area in block_areas.items() if 2.0e6 <= area <= 7.5e6}
    mask = np.isin(filtered_obj_id, list(valid_ids), invert=True)
    filtered_obj_id[mask] = 0

    def _infer_nc_dtype(var):
        if enc := var.encoding.get("dtype"):
            return enc
        dt = var.dtype
        return (
            "f8"
            if np.issubdtype(dt, np.floating)
            else (
                "i4"
                if np.issubdtype(dt, np.integer)
                else "i1" if np.issubdtype(dt, np.byte) else "f8"
            )
        )

    def _copy_attrs(src, dst, skip=()):
        for attr, val in src.attrs.items():
            if attr not in skip:
                dst.setncattr(attr, val)

    with Dataset(final_file, "w", format="NETCDF4") as dst_nc:
        for dim_name, dim_len in ds.sizes.items():
            dst_nc.createDimension(dim_name, dim_len)

        for var_name, varin in ds.variables.items():
            if var_name == "block_id":
                continue
            fill_val = varin.attrs.get("_FillValue")
            is_time = var_name == "time"
            var_out = dst_nc.createVariable(
                var_name,
                "i4" if is_time else _infer_nc_dtype(varin),
                varin.dims,
                fill_value=fill_val,
            )

            if is_time:
                var_out.setncattr("units", "days since 1900-01-01")
                var_out.setncattr("calendar", "gregorian")
                _copy_attrs(varin, var_out, skip=("_FillValue", "units", "calendar"))
                time_dt = xr.decode_cf(ds)["time"].values
                if hasattr(time_dt[0], "strftime"):
                    time_dt = np.array(
                        [
                            np.datetime64(t.strftime("%Y-%m-%dT%H:%M:%S"))
                            for t in time_dt
                        ]
                    )
                var_out[:] = (
                    (time_dt - np.datetime64("1900-01-01")) / np.timedelta64(1, "D")
                ).astype("i4")
            else:
                _copy_attrs(varin, var_out, skip=("_FillValue",))
                var_out[:] = varin[:]

        obj_varin = ds["block_id"]
        obj_var_out = dst_nc.createVariable(
            "block_id",
            obj_varin.dtype,
            obj_varin.dims,
            fill_value=obj_varin.attrs.get("_FillValue"),
        )
        _copy_attrs(obj_varin, obj_var_out, skip=("_FillValue",))
        obj_var_out[:] = filtered_obj_id

    print(
        f"Reassigned sequential block IDs written to '{os.path.basename(final_file)}'."
    )
    print()


# --------------------------------------
# LOCAL WAVE ACTIVITY (LWA) COMPUTATION
# --------------------------------------


def compute_lwa_for_date(
    date, file_pattern, pressure_level, lat_range=None, lon_range=None
):
    a = 6.371e6
    date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
    all_files = sorted(glob.glob(file_pattern))
    target_dt = pd.Timestamp(date).to_pydatetime()
    hgt_files = _filter_files_by_date_range(all_files, target_dt, target_dt)
    if not hgt_files:
        print(f"WARNING: No files found for date {date_str}")
        return None, None, None, None, None

    def _pp(ds):
        return _e3sm_preprocess(ds, pressure_level=pressure_level)

    ds = xr.open_mfdataset(
        hgt_files, combine="by_coords", preprocess=_pp, parallel=False, engine="netcdf4"
    )
    ds = xr.decode_cf(ds)
    ds = ds.sortby("time")
    ds_daily = ds.resample(time="1D").mean()

    try:
        cf_date = _cfdate_like(ds_daily["time"], pd.Timestamp(date).to_pydatetime())
        z500 = ds_daily["hgt"].sel(time=cf_date, method="nearest")
    except KeyError:
        print(f"WARNING: Date {date_str} not found in dataset")
        ds.close()
        return None, None, None, None, None

    if lat_range is not None:
        z500 = z500.sel(latitude=slice(lat_range[0], lat_range[1]))
    if lon_range is not None:
        z500 = z500.sel(longitude=slice(lon_range[0], lon_range[1]))
    z500 = z500.load()

    lat = z500.latitude.values
    lon = z500.longitude.values
    phi = np.deg2rad(lat)
    cosphi = np.cos(phi)
    dphi = np.abs(np.gradient(phi))

    valid_lat_idx = np.where(lat >= 35)[0]
    z_zonal_mean = z500.mean(dim="longitude")
    z_prime = z500 - z_zonal_mean

    shape = (len(lat), len(lon))
    lwa_arr, lwa_anti_arr, lwa_cyclo_arr = [
        np.full(shape, np.nan, dtype=np.float32) for _ in range(3)
    ]

    # LWA computed via equivalent-latitude method
    # Sort by geopotential height to find equivalent latitudes
    for li in range(len(lon)):
        z_col = _as_ndarray(z_prime.isel(longitude=li).values, fill=np.nan)
        z_full = _as_ndarray(z500.isel(longitude=li).values, fill=np.nan)
        sort_idx = np.argsort(z_full)
        phi_sorted = phi[sort_idx]
        z_prime_sorted = z_col[sort_idx]
        order = np.argsort(phi_sorted)
        x = phi_sorted[order]
        y = z_prime_sorted[order]
        x_unique, inv = np.unique(x, return_inverse=True)
        if len(x_unique) != len(x):
            y_accum = np.zeros_like(x_unique, dtype=float)
            counts = np.zeros_like(x_unique, dtype=np.int64)
            finite = np.isfinite(y)
            np.add.at(y_accum, inv[finite], y[finite])
            np.add.at(counts, inv[finite], 1)
            y = np.where(counts > 0, y_accum / counts, np.nan)
            x = x_unique
        else:
            x = x_unique

        z_regrid = np.interp(phi, x, y, left=0.0, right=0.0)
        z_regrid_weighted = z_regrid * cosphi * dphi

        for lat_idx in valid_lat_idx:
            phi_ei = phi[lat_idx]
            cosphi_ei = np.maximum(np.cos(phi_ei), 1e-1)
            factor = a / cosphi_ei

            # Anticyclonic: positive anomalies equatorward of reference
            anti_mask = (phi <= phi_ei) & (z_regrid >= 0)
            # Cyclonic: negative anomalies poleward of reference
            cyclo_mask = (phi >= phi_ei) & (z_regrid <= 0)

            lwa_anti_arr[lat_idx, li] = factor * np.sum(z_regrid_weighted[anti_mask])
            lwa_cyclo_arr[lat_idx, li] = -factor * np.sum(z_regrid_weighted[cyclo_mask])
            lwa_arr[lat_idx, li] = (
                lwa_anti_arr[lat_idx, li] + lwa_cyclo_arr[lat_idx, li]
            )

    ds.close()
    return lwa_arr, lwa_anti_arr, lwa_cyclo_arr, lat, lon


# --------------------------
# BLOCK ANALYSIS AND OUTPUT
# --------------------------


def analyze_blocks_and_write(
    block_file_path,
    nc_out_path,
    csv_path,
    file_pattern,
    start_date,
    end_date,
    pressure_level,
):
    nc_block = Dataset(block_file_path, "r")
    hgt_files_all = sorted(glob.glob(file_pattern))
    start_dt_loc = pd.Timestamp(start_date).to_pydatetime()
    end_dt_loc = pd.Timestamp(end_date).to_pydatetime()
    hgt_files = _filter_files_by_date_range(hgt_files_all, start_dt_loc, end_dt_loc)

    def _pp2(ds):
        return _e3sm_preprocess(ds, pressure_level=pressure_level)

    ds_hgt = xr.open_mfdataset(
        hgt_files,
        combine="by_coords",
        preprocess=_pp2,
        parallel=False,
        join="override",
        engine="netcdf4",
    )
    ds_hgt = ds_hgt.sortby("time")
    hgt = ds_hgt["hgt"]
    hgt_lat = ds_hgt["latitude"].values
    R = 6371  # Earth radius in km (redefined from earlier usage in meters)

    block_lat = _as_ndarray(nc_block.variables["latitude"][:], fill=np.nan)
    block_lon = _as_ndarray(nc_block.variables["longitude"][:], fill=np.nan)
    time_var = nc_block.variables["time"]
    time_origin = datetime(1900, 1, 1)
    times_all = np.array([time_origin + timedelta(days=float(t)) for t in time_var[:]])

    start_dt_loc = pd.Timestamp(start_date).to_pydatetime()
    end_dt_loc = pd.Timestamp(end_date).to_pydatetime()
    time_mask = (times_all >= start_dt_loc) & (times_all <= end_dt_loc)
    valid_time_indices = np.where(time_mask)[0]
    times = times_all
    time_resolution_days = (times[1] - times[0]).total_seconds() / (24 * 3600)

    lat_step = np.diff(block_lat)
    lat_step = lat_step[0] if len(lat_step) > 0 else 1.0
    lat_edges = np.empty(len(block_lat) + 1)
    lat_edges[1:-1] = 0.5 * (block_lat[:-1] + block_lat[1:])
    lat_edges[0] = block_lat[0] - lat_step / 2.0
    lat_edges[-1] = block_lat[-1] + lat_step / 2.0

    lon_vals = block_lon % 360
    lon_step = np.diff(lon_vals)
    median_step = np.median(np.where(lon_step > 0, lon_step, np.nan))
    if np.isnan(median_step):
        median_step = 360.0 / max(len(block_lon), 1)
    lon_edges = np.empty(len(block_lon) + 1)
    lon_edges[1:-1] = 0.5 * (lon_vals[:-1] + lon_vals[1:])
    lon_edges[0] = (lon_vals[0] - median_step / 2.0) % 360
    lon_edges[-1] = (lon_vals[-1] + median_step / 2.0) % 360

    # Area weights account for spherical geometry
    phi_edges = np.radians(lat_edges)
    lam_edges = np.radians(lon_edges)
    dsin_phi = np.abs(np.sin(phi_edges[1:]) - np.sin(phi_edges[:-1]))
    dlam = np.abs(lam_edges[1:] - lam_edges[:-1])
    area_weights_block = dsin_phi[:, None] * dlam[None, :]

    # Map between block grid and height grid (may differ in resolution)
    hgt_lat_map = {lat: np.abs(hgt_lat - lat).argmin() for lat in block_lat}

    block_id = nc_block.variables["block_id"]

    # First pass: collect all grid points belonging to each block
    print("First pass: collecting block locations...")
    block_points = defaultdict(lambda: {"times": [], "y": [], "x": []})
    block_times = {}
    block_area = defaultdict(list)

    for t in valid_time_indices:
        if t % 100 == 0:
            print(f"Processing timestep {t}/{len(times_all)}")
        tag_slice = _as_ndarray(block_id[t, :, :], fill=0)
        valid_mask = ~np.isnan(tag_slice) & (tag_slice != 0)
        unique_blocks = np.unique(tag_slice[valid_mask])

        for block in unique_blocks:
            block = int(block)
            y_idx, x_idx = np.where(tag_slice == block)
            block_points[block]["times"].extend([t] * len(y_idx))
            block_points[block]["y"].extend(y_idx.tolist())
            block_points[block]["x"].extend(x_idx.tolist())

            if block not in block_times:
                block_times[block] = [times[t], times[t]]
            else:
                block_times[block][1] = times[t]

            area_km2 = np.sum(area_weights_block[y_idx, x_idx]) * R**2
            block_area[block].append((area_km2, times[t]))

    print()
    print("Converting block point lists to arrays...")
    print()
    for block in block_points:
        block_points[block]["times"] = np.array(
            block_points[block]["times"], dtype=np.int32
        )
        block_points[block]["y"] = np.array(block_points[block]["y"], dtype=np.int32)
        block_points[block]["x"] = np.array(block_points[block]["x"], dtype=np.int32)

    # Second pass: compute statistics for each block
    print("Second pass: analyzing blocks...")
    block_data = {}
    BI_values = {}
    LWA_data = {}
    lwa_cache = {}  # Cache LWA to avoid recomputing for same date
    t_MZ_dict = {}
    lat_MZ_dict = {}
    lon_MZ_dict = {}

    print(f"Analyzing blocks ({len(block_points)} blocks)...")
    for block in block_points.keys():
        times_arr = block_points[block]["times"]
        y_arr = block_points[block]["y"]
        x_arr = block_points[block]["x"]

        # Find maximum Z500 point to identify the date of maximum intensity (MZ = Max Z)
        hgt_lat_idx_arr = np.array(
            [hgt_lat_map[block_lat[y]] for y in y_arr], dtype=np.int32
        )
        hgt_vals = _as_ndarray(
            hgt.isel(
                time=xr.DataArray(times_arr),
                latitude=xr.DataArray(hgt_lat_idx_arr),
                longitude=xr.DataArray(x_arr),
            ).values,
            fill=np.nan,
        )

        if not np.isfinite(hgt_vals).any():
            print(f"DEBUG: Skipping block {block} due to all-NaN hgt values")
            continue

        max_index = np.nanargmax(hgt_vals)
        t_MZ = times_arr[max_index]
        y_MZ = y_arr[max_index]
        x_MZ = x_arr[max_index]
        lat_MZ = block_lat[y_MZ]
        lon_MZ = block_lon[x_MZ] % 360

        t_MZ_dict[block] = int(t_MZ)
        lat_MZ_dict[block] = float(lat_MZ)
        lon_MZ_dict[block] = float(lon_MZ)

        # Compute Blocking Index (measure of block intensity)
        # Horizontal gradient between maximum height and upstream/downstream minima within 90°
        west_lons, east_lons = _get_lon_indices_within_range(block_lon, lon_MZ, 90)
        lat_MZ_idx = hgt_lat_map[lat_MZ]
        MZ = hgt.isel(
            time=int(t_MZ), latitude=lat_MZ_idx, longitude=int(x_MZ)
        ).values.item()

        lat_spacing = np.median(np.diff(block_lat)) if len(block_lat) > 1 else 0.0
        at_south_edge = (lat_MZ - block_lat.min()) <= (lat_spacing / 2.0)

        # Handle edge case where block is at southern boundary to avoid index errors
        if at_south_edge:
            lat_below_idx = lat_MZ_idx - 1 if lat_MZ_idx > 0 else None
            if lat_below_idx is not None:
                hgt_slice = _as_ndarray(
                    hgt.isel(time=int(t_MZ), latitude=lat_below_idx).values, fill=np.nan
                )
            else:
                BI_values[block] = np.nan
                lat_below_idx = None
        else:
            hgt_slice = _as_ndarray(
                hgt.isel(time=int(t_MZ), latitude=lat_MZ_idx).values, fill=np.nan
            )
            lat_below_idx = lat_MZ_idx

        if lat_below_idx is not None:
            # Zu/Zd are upstream/downstream minimum heights
            Zu_vals = hgt_slice[west_lons]
            Zd_vals = hgt_slice[east_lons]
            if Zu_vals.size == 0 or Zd_vals.size == 0:
                BI_values[block] = np.nan
            else:
                Zu = np.nanmin(Zu_vals)
                Zd = np.nanmin(Zd_vals)
                RC = (((Zu + MZ) / 2) + ((Zd + MZ) / 2)) / 2
                BI_values[block] = 100 * ((MZ / RC) - 1)

        # Collect size statistics
        area_times = block_area[block]
        min_area_km2, min_time = min(area_times, key=lambda x: x[0])
        max_area_km2, max_time = max(area_times, key=lambda x: x[0])

        # Initial center position (at first detection)
        first_t = times_arr[0]
        first_mask = times_arr == first_t
        first_ys = y_arr[first_mask]
        first_xs = x_arr[first_mask]
        center_latitude = np.mean(block_lat[first_ys])

        # Circular mean for longitude to handle wrap-around
        lons = block_lon[first_xs] % 360
        lons_rad = np.deg2rad(lons)
        mean_angle = np.arctan2(np.mean(np.sin(lons_rad)), np.mean(np.cos(lons_rad)))
        center_longitude = np.rad2deg(mean_angle) % 360

        unique_times = np.unique(times_arr)
        block_data[block] = {
            "start_time": block_times[block][0],
            "end_time": block_times[block][1],
            "duration_steps": len(unique_times),
            "duration_days": len(unique_times) * time_resolution_days,
            "min_spatial_area_km2": min_area_km2,
            "min_size_time": min_time,
            "max_spatial_area_km2": max_area_km2,
            "max_size_time": max_time,
            "center_latitude": center_latitude,
            "center_longitude": center_longitude,
        }

        # Compute LWA at the time of maximum height
        mask_t_MZ = times_arr == t_MZ
        y_MZ_arr = y_arr[mask_t_MZ]
        x_MZ_arr = x_arr[mask_t_MZ]
        t_dt_MZ = times[t_MZ]
        date_key = pd.Timestamp(t_dt_MZ).strftime("%Y-%m-%d")

        if date_key not in lwa_cache:
            lwa_arr, lwa_anti_arr, lwa_cyclo_arr, lwa_lat, lwa_lon = (
                compute_lwa_for_date(t_dt_MZ, file_pattern, pressure_level)
            )
            lwa_cache[date_key] = (
                lwa_arr,
                lwa_anti_arr,
                lwa_cyclo_arr,
                lwa_lat,
                lwa_lon,
            )
        lwa_arr, lwa_anti_arr, lwa_cyclo_arr, lwa_lat, lwa_lon = lwa_cache[date_key]

        if lwa_arr is None:
            avg_lwa = avg_anti = avg_cyclo = np.nan
        else:
            lat_vals = block_lat[y_MZ_arr]
            lon_vals = block_lon[x_MZ_arr] % 360
            lat_idx = np.array(
                [np.abs(lwa_lat - lv).argmin() for lv in lat_vals], dtype=np.int32
            )
            lon_idx = np.array(
                [np.abs((lwa_lon % 360) - lv).argmin() for lv in lon_vals],
                dtype=np.int32,
            )

            if len(lat_idx) > 0:
                avg_lwa = np.nanmean(lwa_arr[lat_idx, lon_idx])
                avg_anti = np.nanmean(lwa_anti_arr[lat_idx, lon_idx])
                avg_cyclo = np.nanmean(lwa_cyclo_arr[lat_idx, lon_idx])
            else:
                avg_lwa = avg_anti = avg_cyclo = np.nan

        # Classify block type based on LWA ratio
        def _classify(anti, cyclo):
            if anti > 10 * cyclo:
                return "ridge block"
            if 10 * cyclo > anti > 0.5 * cyclo:
                return "dipole block"
            if anti < 0.5 * cyclo:
                return "cutoff low"
            return "unclassified"

        LWA_data[block] = {
            "max_lwa": avg_lwa,
            "time_of_max_lwa": t_dt_MZ,
            "avg_LWA_anticyclonic": avg_anti,
            "avg_LWA_cyclonic": avg_cyclo,
            "classification": _classify(avg_anti, avg_cyclo),
        }

    print()
    print("Block classifications:")
    cutoff_low_ids = set()
    for block, data in LWA_data.items():
        print(f"Block {block}: {data['classification']}")
        if data["classification"] == "cutoff low":
            cutoff_low_ids.add(block)

    excluded_ids = cutoff_low_ids
    print(f"Excluded {len(cutoff_low_ids)} cutoff lows (total {len(excluded_ids)}).")
    print()

    nc_block.close()
    ds_hgt.close()

    # Write filtered NetCDF with sequential IDs
    print("Writing filtered NetCDF with vectorized remapping...")
    print()
    with Dataset(block_file_path, "r") as src:
        time_dim = src.dimensions["time"].size
        chunk_size = 100
        unique_ids = set()
        total_chunks = (time_dim + chunk_size - 1) // chunk_size

        # Build ID remap to create sequential IDs
        print(f"Scanning IDs across {total_chunks} chunks...")
        for t_start in range(0, time_dim, chunk_size):
            t_end = min(t_start + chunk_size, time_dim)
            block_id_chunk = _as_ndarray(
                src.variables["block_id"][t_start:t_end, :, :], fill=0
            )
            mask = np.isin(block_id_chunk, list(excluded_ids))
            filtered_chunk = np.where(mask, 0, block_id_chunk)
            unique_ids.update(np.unique(filtered_chunk[filtered_chunk != 0]).tolist())
        print("Done scanning IDs.")

        id_map = {
            int(old_id): new_id
            for new_id, old_id in enumerate(sorted(unique_ids), start=1)
        }
        print("Mapping of original to sequential IDs (excluding 0):")
        for old_id in sorted(id_map.keys()):
            print(f"{old_id} -> {id_map[old_id]}")

        max_id = max(id_map.keys()) if id_map else 0
        remap_array = np.zeros(max_id + 1, dtype=np.int32)
        for old_id, new_id in id_map.items():
            remap_array[old_id] = new_id

        with Dataset(nc_out_path, "w") as dst:
            for name, dim in src.dimensions.items():
                dst.createDimension(name, len(dim) if not dim.isunlimited() else None)
            for name, var in src.variables.items():
                if name == "block_id":
                    continue
                out_var = dst.createVariable(name, var.datatype, var.dimensions)
                out_var.setncatts({k: var.getncattr(k) for k in var.ncattrs()})
                out_var[:] = var[:]
            out_var = dst.createVariable(
                "block_id", "i4", ("time", "latitude", "longitude")
            )
            out_var.setncatts(
                {
                    k: src.variables["block_id"].getncattr(k)
                    for k in src.variables["block_id"].ncattrs()
                }
            )
            excluded_ids_arr = np.array(list(excluded_ids))

            print()
            print(f"Remapping block IDs across {total_chunks} chunks...")
            for t_start in range(0, time_dim, chunk_size):
                t_end = min(t_start + chunk_size, time_dim)
                block_id_chunk = _as_ndarray(
                    src.variables["block_id"][t_start:t_end, :, :], fill=0
                )
                mask = np.isin(block_id_chunk, excluded_ids_arr)
                filtered_chunk = np.where(mask, 0, block_id_chunk).astype(np.int32)
                valid_mask = (filtered_chunk > 0) & (filtered_chunk < len(remap_array))
                remapped_chunk = np.zeros_like(filtered_chunk)
                remapped_chunk[valid_mask] = remap_array[filtered_chunk[valid_mask]]
                out_var[t_start:t_end, :, :] = remapped_chunk
            print("Done remapping block IDs.")

    def _date_mz_for_block(bid):
        t_idx = t_MZ_dict.get(bid, None)
        if t_idx is None:
            return pd.NaT
        try:
            return (
                times[t_idx].date() if hasattr(times[t_idx], "date") else times[t_idx]
            )
        except Exception:
            return pd.NaT

    # Assemble CSV summary (excluding cutoff lows and spatial exclusions)
    print()
    print("Assembling CSV summary...")
    print()
    valid_block_ids = sorted(set(block_data.keys()) - excluded_ids)
    filtered_block_data = {bid: block_data[bid] for bid in valid_block_ids}
    df = pd.DataFrame.from_dict(filtered_block_data, orient="index")
    df.index.name = "block_id"
    df = df.reset_index()
    df["block_id_original"] = df["block_id"]

    bid_col = df["block_id_original"]
    df["lat_MaxZ"] = bid_col.map(lambda b: lat_MZ_dict.get(b, np.nan))
    df["date_MaxZ"] = bid_col.map(_date_mz_for_block)
    df["lon_MaxZ"] = bid_col.map(lambda b: lon_MZ_dict.get(b, np.nan))
    df["blocking_index"] = bid_col.map(lambda b: BI_values.get(b, np.nan))
    for col in [
        "max_lwa",
        "time_of_max_lwa",
        "avg_LWA_anticyclonic",
        "avg_LWA_cyclonic",
        "classification",
    ]:
        default = (
            pd.NaT
            if "time" in col
            else (np.nan if col != "classification" else "unclassified")
        )
        df[col] = bid_col.map(lambda b, c=col, d=default: LWA_data.get(b, {}).get(c, d))

    # Remap to sequential IDs and clean up
    try:
        df["block_id"] = (
            df["block_id"].map(lambda b: id_map.get(int(b), np.nan)).astype("Int64")
        )
    except Exception:
        print("WARNING: ID remap unavailable; keeping original block IDs in CSV.")
    df = df.drop(columns=["block_id_original"], errors="ignore")
    df.to_csv(csv_path, index=False)
    print(f"Block summary written to {csv_path}")
    print()


# -----------------------
# PIPELINE ORCHESTRATION
# -----------------------
# Orchestrates the full detection-to-analysis workflow.


def run_full_combined_pipeline(
    file_glob: str,
    pressure_level: int,
    start_date: str,
    end_date: str,
    output_dir: str,
    stitched_out_name: str,
    cleanup_temp: bool,
):
    # BLOCKING DETECTION ALGORITHM
    combined_path, temp_dir = run_ibto_and_write_combined(
        file_pattern=file_glob,
        start_date=start_date,
        end_date=end_date,
        output_base_dir=output_dir,
        pressure_level=pressure_level,
    )

    # BLOB STITCHING VIA TEMPEST EXTREMES
    stitched_path = call_stitchblobs(
        combined_path,
        temp_dir,
        stitched_out_name,
        stitched_path=os.path.join(temp_dir, stitched_out_name),
    )
    if stitched_path is None:
        raise RuntimeError("Stitching failed or was skipped; cannot proceed.")

    # BLOCK SIZE FILTERING
    start_year = pd.Timestamp(start_date).year
    end_year = pd.Timestamp(end_date).year
    final_block_nc = os.path.join(
        output_dir, f"block_id_base.{start_year}{end_year}.nc"
    )
    realign_block_ids(stitched_path, final_block_nc)
    print("Starting analysis on stitched blocks..")
    print()

    # LOCAL WAVE ACTIVITY (LWA) COMPUTATION / BLOCK ANALYSIS AND OUTPUT
    lwa_out_nc = os.path.join(output_dir, f"block_id.{start_year}{end_year}.nc")
    csv_path = os.path.join(output_dir, "block_summary.csv")
    analyze_blocks_and_write(
        block_file_path=final_block_nc,
        nc_out_path=lwa_out_nc,
        csv_path=csv_path,
        file_pattern=file_glob,
        start_date=start_date,
        end_date=end_date,
        pressure_level=pressure_level,
    )

    # Remove intermediate base file now that analysis is complete
    try:
        os.remove(final_block_nc)
        print(f"Deleted intermediate file: {final_block_nc}")
        print()
    except Exception as e:
        print(f"WARNING: Could not delete intermediate file {final_block_nc}: {e}")

    outputs = {
        "combined_path": combined_path,
        "stitched_path": stitched_path,
        "lwa_out_nc": lwa_out_nc,
        "csv_path": csv_path,
        "temp_dir": temp_dir,
        "output_dir": output_dir,
    }

    # Clean up temp directory if requested to save space
    try:
        if cleanup_temp and os.path.abspath(output_dir) != os.path.abspath(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Deleted temporary directory: {temp_dir}")
            print()
    except Exception as e:
        print(f"WARNING: Could not delete temporary directory {temp_dir}: {e}")

    return outputs


# -------------------
# DRIVER ENTRY POINT
# -------------------


def run_blocking_driver(parameter=None):
    # Parse from CLI/config if no parameter object provided
    if parameter is None:
        parameter = BlockingParser().get_parameter(argparse_vals_only=False)

    print(f"Using params from: {getattr(parameter, 'params_path', None) or 'CLI only'}")
    print()
    output_dir = verify_output_path(parameter.OUTPUT_DIR, parameter.case_id)
    print(f"Output directory: {output_dir}")
    print()

    res = run_full_combined_pipeline(
        file_glob=parameter.FILE_GLOB,
        pressure_level=parameter.PRESSURE_LEVEL,
        start_date=parameter.START_DATE,
        end_date=parameter.END_DATE,
        output_dir=output_dir,
        stitched_out_name=parameter.STITCHED_OUT_NAME,
        cleanup_temp=parameter.CLEANUP_TEMP,
    )

    print(f"Processing complete. Outputs: {res['lwa_out_nc']}, {res['csv_path']}")
    return res


def main():
    return run_blocking_driver()


if __name__ == "__main__":
    run_blocking_driver()
