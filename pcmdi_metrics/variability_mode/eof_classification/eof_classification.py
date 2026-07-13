#!/usr/bin/env python3
# © 2026. Triad National Security, LLC. All rights reserved.
# This program was produced under U.S. Government contract 89233218CNA000001
# for Los Alamos National Laboratory (LANL), which is operated by Triad
# National Security, LLC for the U.S. Department of Energy/National Nuclear
# Security Administration. All rights in the program are reserved by Triad
# National Security, LLC, and the U.S. Department of Energy/National Nuclear
# Security Administration. The Government is granted for itself and others
# acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license
# in this material to reproduce, prepare derivative works, distribute copies
# to the public, perform publicly and display publicly, and to permit others
# to do so.
# This program is Open-Source under the BSD-3 License. See LICENSE file.
# LANL O Number: O5081
# Authors: Martin Velez Pardo (LANL, EES-14), Alexandra Jonko (LANL, EES-17)
"""
Combined Arctic and North-Atlantic EOF classification runner (3 methods) with consensus-based summary.

Methods:
  1) Subspace (shift-tolerant): fit EA/SCA controls in span{EOF2, EOF3, EOF4}
  2) Correlations + geographic tests + orthogonalized correlations (scoring)
  3) K-means (area-weighted, anomaly-corr orientation, row-normalized)

Output:
  eof_classification_consensus.tsv   — Per-EOF verdict with per-method confidence
  eof_classification_consensus.txt   — Human-readable version (with explanatory note)

Each method reports, FOR EACH EOF, what pattern it most likely represents
(EA / SCA) and a confidence score in [0, 1].  Scores closer to 1 indicate
stronger resemblance to the assigned pattern.

Consensus label is by simple majority vote across the three methods.
Consensus confidence = (fraction of methods agreeing) × (mean confidence
of agreeing methods).  Quality levels: robust >= 0.7, medium >= 0.5,
weak >= 0.3, very weak < 0.3.

Because model EOFs may span a subspace that mixes the reference patterns
(i.e. a model EOF can be a linear combination of EA and SCA), multiple
EOFs may receive the same label when their projections onto the reference
patterns are not cleanly separable.

K-means uses pre-computed cluster centers saved in a JSON file.  On first
run the centers are trained from the full ensemble and saved; subsequent
runs apply the saved centers per-model.  See the "K-MEANS RETRAINING"
section at the bottom of this script if you need to regenerate centers
for a different reanalysis or model ensemble.

Notes:
  - Model names are clipped at "piControl..." for consistency across methods.
  - lon is wrapped to 0..360 and lat/lon are sorted before region slicing.
"""
import csv
import json
import os
from glob import glob

import numpy as np
import xarray as xr

try:
    from sklearn.cluster import KMeans

    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

# =============================================================================
# CONFIG — User-configurable settings
# =============================================================================
OUTPUT_ROOT = "eof_classification"  # prefix for output filenames
EOF_NUMS = [2, 3, 4]  # which EOF modes to classify

# -- EOF inputs to classify --
# MODEL_EOF_DIR: directory containing model EOF netCDF files (one per model per mode)
MODEL_EOF_DIR = "data/example_eofs"  # Path to directory with EOF files
# EOF_GLOBS: glob patterns to find EOF2, EOF3, EOF4 files; must match 1-to-1 across modes
EOF_GLOBS = {
    n: os.path.join(MODEL_EOF_DIR, f"EOF{n}_psl_JFM_cmip6_*.nc") for n in EOF_NUMS
}
VAR_NAME = "eof"  # variable name inside the netCDF files

# -- Control EOFs (observational ground-truth patterns) --
# Direct paths to the EA and SCA control pattern files.
EA_CTRL_FILE = "data/EA_psl_EOF2_JFM_obs_1969-2012.nc"  # Path to Reanalysis East Atlantic Pattern NetCDF file (20CR-VR recommended)
SCA_CTRL_FILE = "data/SCA_psl_EOF3_JFM_obs_1969-2012.nc"  # Path to Reanalysis Scandinavian Pattern NetCDF file (20CR-VR recommended)
EA_SIGN, SCA_SIGN = +1.0, -1.0  # sign convention applied at load time
# CTRL_REANALYSIS: label identifying which reanalysis the control files come from.
# This is checked against the k-means centers file to warn about mismatches.
CTRL_REANALYSIS = "20CR-V2"

# -- Domain restriction (applied consistently across all methods) --
LAT_RANGE = (20.0, 90.0)  # latitude bounds; None disables
LON_INTERVALS = None  # e.g. [(270,360),(0,60)] or None for all longitudes

# -- Subspace method knobs --
USE_COSLAT_WEIGHTS = True  # area-weight by cos(lat)
SMOOTH_SIGMA_DEG = 4.0  # Gaussian smoothing width in degrees; 0 disables
SHIFT_LON_MAX_DEG = 15.0  # max longitudinal shift tolerance (degrees)
SHIFT_LAT_MAX_DEG = 6.0  # max latitudinal shift tolerance (degrees)
RIDGE = 0.0  # Tikhonov regularisation; 0 = ordinary least squares

# -- K-means method knobs --
N_CLUSTERS = 3  # number of clusters (typically EA + SCA + OTHER)
RANDOM_STATE = 0  # random seed for reproducibility
N_INIT = 50  # number of K-means initialisations
CLUSTER_CORR_THRESHOLD = 0.4  # |corr| with controls below this => OTHER cluster
#
# KMEANS_CENTERS_FILE: path to a pre-computed cluster centers JSON file.
#   - If a file exists at this path, k-means will APPLY those saved centers
#     to classify each model's EOFs individually.  The file records which
#     reanalysis it was trained on; a warning is issued if CTRL_REANALYSIS
#     does not match.  To use a different reanalysis, you must retrain
#     (see "K-MEANS RETRAINING" section at the bottom of this script).
#   - If the file does not exist, k-means will TRAIN from scratch on the
#     first run.  THIS REQUIRES EOF FILES FROM A FULL MULTI-MODEL ENSEMBLE
#     (pointed to by EOF_GLOBS above).  The resulting centers are saved to
#     this path for all subsequent runs.
KMEANS_CENTERS_FILE = "data/kmeans_centers_20CR-V2_CMIP6.json"
CMIP_TAG = "CMIP6"  # label stored in the centers file for provenance

# -- Consensus knobs --
CONSENSUS_ROBUST_THRESHOLD = 0.7  # consensus confidence >= this => robust
CONSENSUS_MEDIUM_THRESHOLD = 0.5  # consensus confidence >= this => medium
CONSENSUS_WEAK_THRESHOLD = (
    0.3  # consensus confidence >= this => weak; below => very weak
)


# =============================================================================
# SHARED HELPERS
# =============================================================================
def _clip_model(name):
    idx = name.find("piControl")
    return name[:idx].rstrip("_-") if idx != -1 else name


def _model_label(path):
    base = os.path.basename(path)
    prefix, suffix = "EOF2_psl_JFM_cmip6_", ".nc"
    return (
        base[len(prefix) : -len(suffix)]
        if base.startswith(prefix) and base.endswith(suffix)
        else base
    )


def _rename_latlon(da):
    rmap = {}
    for c in ("latitude", "nav_lat", "y"):
        if c in da.dims and "lat" not in da.dims:
            rmap[c] = "lat"
    for c in ("longitude", "nav_lon", "x"):
        if c in da.dims and "lon" not in da.dims:
            rmap[c] = "lon"
    if rmap:
        da = da.rename(rmap)
    for dim in ("lat", "lon"):
        if dim not in da.coords and dim in da.dims:
            da = da.assign_coords({dim: da[dim]})
    return da


def _wrap_sort(da):
    da = _rename_latlon(da.copy())
    if "lon" in da.coords:
        lon = da["lon"]
        if (lon < 0).any():
            da = da.assign_coords(lon=(lon % 360))
        da = da.sortby("lon")
    if "lat" in da.coords:
        da = da.sortby("lat")
    if {"lat", "lon"}.issubset(da.dims):
        da = da.transpose("lat", "lon")
    return da


def _subset(da, lat_range=LAT_RANGE, lon_intervals=LON_INTERVALS):
    da = _wrap_sort(da)
    if lat_range is not None:
        lat = da["lat"]
        da = da.where((lat >= lat_range[0]) & (lat <= lat_range[1]), drop=True)
    if lon_intervals is not None:
        lon = da["lon"]
        m = xr.zeros_like(lon, dtype=bool)
        for a, b in lon_intervals:
            m = m | ((lon >= a) & (lon <= b))
        da = da.sel(lon=lon.where(m, drop=True))
    return da


def _read_da(path, var=VAR_NAME):
    time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
    with xr.open_dataset(path, decode_times=time_coder) as ds:
        da = ds[var] if var in ds.data_vars else ds[list(ds.data_vars)[0]]
    if "mode" in da.dims:
        da = da.isel(mode=0)
    for d in list(da.dims):
        if da.sizes.get(d, 2) == 1:
            da = da.isel({d: 0})
    da = _wrap_sort(da.squeeze())
    if not {"lat", "lon"}.issubset(da.dims):
        raise ValueError(f"{path}: expected lat/lon dims, got {da.dims}")
    return da


def _coslat_w2d(lat, nlon):
    w = np.clip(np.cos(np.deg2rad(lat.astype(float))), 0, None)
    return w[:, None] * np.ones((1, nlon))


# -- weighted inner products (NaN-safe) --
def _wip(a, b, w):
    m = np.isfinite(a) & np.isfinite(b) & np.isfinite(w)
    return float(np.sum(a[m] * b[m] * w[m])) if m.any() else 0.0


def _wnorm(a, w):
    return float(np.sqrt(_wip(a, a, w)))


def _wcor(a, b, w):
    na, nb = _wnorm(a, w), _wnorm(b, w)
    return _wip(a, b, w) / (na * nb) if na > 0 and nb > 0 else 0.0


def _wmean(a, w):
    m = np.isfinite(a) & np.isfinite(w)
    d = float(np.sum(w[m]))
    return float(np.sum(a[m] * w[m])) / d if d > 0 else 0.0


def _wcor_anom(a, b, w):
    return _wcor(a - _wmean(a, w), b - _wmean(b, w), w)


def _orthogonalize(a, b, w):
    bb = _wip(b, b, w)
    return a - (_wip(a, b, w) / bb) * b if bb > 0 else a.copy()


def _remove_wmean_2d(a, w):
    m = np.isfinite(a)
    if not m.any():
        return a * np.nan
    ww, aa = w[m], a[m]
    d = float(np.sum(ww))
    mu = float(np.sum(ww * aa) / d) if d > 0 else float(np.nanmean(aa))
    return a - mu


# -- Load model EOF triplets --
def _load_model_triplets(eof_globs=None):
    """Return list of (model_name, {2: DataArray, 3: DA, 4: DA})."""
    if eof_globs is None:
        eof_globs = EOF_GLOBS
    file_lists = {n: sorted(glob(eof_globs[n])) for n in EOF_NUMS}
    n_files = len(file_lists[2])
    assert n_files > 0, (
        "No EOF2 model files found. Either set MODEL_EOF_DIR/EOF_GLOBS in the "
        "CONFIG section, or pass eof_globs={2: ..., 3: ..., 4: ...} to "
        "eof_classification()."
    )
    for n in EOF_NUMS:
        assert len(file_lists[n]) == n_files, f"File count mismatch for EOF{n}."
    triplets = []
    for i in range(n_files):
        model = _clip_model(_model_label(file_lists[2][i]))
        eofs = {}
        for n in EOF_NUMS:
            eofs[n] = _subset(_read_da(file_lists[n][i]))
        triplets.append((model, eofs))
    return triplets


def _regrid_align(eofs_dict, *ctrls):
    """Regrid all DataArrays to EOF2 grid, align inner. Returns numpy dict + lat/lon/w2d."""
    ref = eofs_dict[2]
    das = [ref]
    for n in EOF_NUMS:
        if n != 2:
            das.append(eofs_dict[n].interp_like(ref, method="linear"))
        # (EOF2 already appended as first)
    for c in ctrls:
        das.append(c.interp_like(ref, method="linear"))
    aligned = xr.align(*das, join="inner")
    lat = aligned[0]["lat"].values
    lon = aligned[0]["lon"].values
    w2d = (
        _coslat_w2d(lat, lon.size)
        if USE_COSLAT_WEIGHTS
        else np.ones((lat.size, lon.size))
    )
    # Split back: EOF2 is aligned[0], EOF3=aligned[1], EOF4=aligned[2], then ctrls
    eof_arrs = {
        EOF_NUMS[0]: aligned[0],
        EOF_NUMS[1]: aligned[1],
        EOF_NUMS[2]: aligned[2],
    }
    ctrl_arrs = list(aligned[3:])
    return eof_arrs, ctrl_arrs, lat, lon, w2d


def _check_inversion(eof_da, ctrl_da):
    """Return True if the EOF is sign-inverted relative to the control."""
    eof_sub = _subset(eof_da)
    ctrl_sub = _subset(ctrl_da)
    eof_interp = eof_sub.interp_like(ctrl_sub, method="linear")
    eof_al, ctrl_al = xr.align(eof_interp, ctrl_sub, join="inner")
    lat = eof_al["lat"].values
    w2d = _coslat_w2d(lat, eof_al["lon"].size)
    return _wcor(eof_al.values, ctrl_al.values, w2d) < 0


# =============================================================================
# SUBSPACE HELPERS
# =============================================================================
def _gauss_kernel(sigma_pts):
    if sigma_pts is None or sigma_pts <= 0:
        return np.array([1.0])
    r = int(np.ceil(3.0 * sigma_pts))
    x = np.arange(-r, r + 1, dtype=float)
    k = np.exp(-0.5 * (x / sigma_pts) ** 2)
    k /= k.sum()
    return k


def _conv_rows_periodic(num, den, k):
    if k.size == 1:
        return num, den
    p = k.size // 2
    on = np.empty_like(num)
    od = np.empty_like(den)
    for i in range(num.shape[0]):
        on[i] = np.convolve(np.pad(num[i], p, mode="wrap"), k, "valid")
        od[i] = np.convolve(np.pad(den[i], p, mode="wrap"), k, "valid")
    return on, od


def _conv_cols_reflect(num, den, k):
    if k.size == 1:
        return num, den
    p = k.size // 2
    on = np.empty_like(num)
    od = np.empty_like(den)
    for j in range(num.shape[1]):
        on[:, j] = np.convolve(np.pad(num[:, j], p, mode="reflect"), k, "valid")
        od[:, j] = np.convolve(np.pad(den[:, j], p, mode="reflect"), k, "valid")
    return on, od


def _smooth_gauss(a, lat, lon, sigma_deg):
    if sigma_deg is None or sigma_deg <= 0:
        return a
    latv, lonv = np.asarray(lat, float), np.asarray(lon, float)
    if latv.size < 3 or lonv.size < 3:
        return a
    dlat = float(np.median(np.abs(np.diff(latv))))
    dlon = float(np.median(np.abs(np.diff(lonv))))
    if dlat <= 0 or dlon <= 0:
        return a
    kla = _gauss_kernel(sigma_deg / dlat)
    klo = _gauss_kernel(sigma_deg / dlon)
    m = np.isfinite(a).astype(float)
    af = np.where(m > 0, a, 0.0)
    num, den = _conv_rows_periodic(af * m, m, klo)
    num, den = _conv_cols_reflect(num, den, kla)
    out = np.full_like(a, np.nan)
    g = den > 0
    out[g] = num[g] / den[g]
    return out


def _shift2d(a, dlat, dlon):
    out = np.roll(a, shift=dlon, axis=1)
    if dlat == 0:
        return out
    out2 = np.full_like(out, np.nan)
    if dlat > 0:
        out2[dlat:] = out[:-dlat]
    else:
        out2[:dlat] = out[-dlat:]
    return out2


def _make_shifts(lat, lon, lat_max, lon_max):
    latv, lonv = np.asarray(lat, float), np.asarray(lon, float)
    dlat = float(np.median(np.abs(np.diff(latv)))) if latv.size > 1 else 1.0
    dlon = float(np.median(np.abs(np.diff(lonv)))) if lonv.size > 1 else 1.0
    dlat = max(dlat, 1e-9)
    dlon = max(dlon, 1e-9)
    nl = int(np.floor(lat_max / dlat + 1e-9))
    nlo = int(np.floor(lon_max / dlon + 1e-9))
    return range(-nl, nl + 1), range(-nlo, nlo + 1), dlat, dlon


def _weighted_lstsq(e2, e3, e4, y, w, ridge=0.0):
    X = np.stack([e2, e3, e4], axis=1)
    n = np.array([np.sqrt(np.sum(w * X[:, i] ** 2)) for i in range(3)])
    n = np.where(n > 0, n, 1.0)
    Xn = X / n[None, :]
    sw = np.sqrt(w)
    A, b = sw[:, None] * Xn, sw * y
    if ridge > 0:
        A = np.vstack([A, np.sqrt(ridge) * np.eye(3)])
        b = np.concatenate([b, np.zeros(3)])
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    yhat = Xn @ c
    na = np.sqrt(np.sum(w * yhat**2))
    nb = np.sqrt(np.sum(w * y**2))
    r = float(np.sum(w * yhat * y) / (na * nb)) if na > 0 and nb > 0 else np.nan
    if np.isfinite(r) and r < 0:
        c, yhat, r = -c, -yhat, -r
    cap = float(np.sum(w * yhat**2) / np.sum(w * y**2)) if nb > 0 else np.nan
    return r, cap, c.astype(float)


# =============================================================================
# METHOD 1: SUBSPACE — Per-EOF confidence
# =============================================================================
def run_subspace(EA_ctrl, SCA_ctrl, triplets):
    """
    For each model, project EA and SCA controls onto span{EOF2,3,4}.
    Then for each EOF_n, confidence_EA = |c_n(EA_fit)| / sum(|c|),
    confidence_SCA = |c_n(SCA_fit)| / sum(|c|).
    The pattern with higher normalised coefficient wins for that EOF.
    """
    results = {}  # model -> {eof_num: {"label": "EA"/"SCA", "confidence": float}}
    for model, eofs in triplets:
        try:
            eof_das, (EA_a, SC_a), lat, lon, w2d = _regrid_align(
                eofs, EA_ctrl, SCA_ctrl
            )
        except Exception as e:
            print(f"[WARN][subspace] {model}: {e}")
            results[model] = {n: {"label": "NA", "confidence": 0.0} for n in EOF_NUMS}
            continue

        if eof_das[2].sizes["lat"] == 0:
            results[model] = {n: {"label": "NA", "confidence": 0.0} for n in EOF_NUMS}
            continue

        # Convert to numpy, remove mean, smooth
        arrs = {}
        for n in EOF_NUMS:
            arrs[n] = eof_das[n].values.astype(float)
        EA_v, SC_v = EA_a.values.astype(float), SC_a.values.astype(float)

        for key in list(arrs.keys()):
            arrs[key] = _remove_wmean_2d(arrs[key], w2d)
        EA_v = _remove_wmean_2d(EA_v, w2d)
        SC_v = _remove_wmean_2d(SC_v, w2d)

        if SMOOTH_SIGMA_DEG and SMOOTH_SIGMA_DEG > 0:
            for key in arrs:
                arrs[key] = _smooth_gauss(arrs[key], lat, lon, SMOOTH_SIGMA_DEG)
            EA_v = _smooth_gauss(EA_v, lat, lon, SMOOTH_SIGMA_DEG)
            SC_v = _smooth_gauss(SC_v, lat, lon, SMOOTH_SIGMA_DEG)
            for key in arrs:
                arrs[key] = _remove_wmean_2d(arrs[key], w2d)
            EA_v = _remove_wmean_2d(EA_v, w2d)
            SC_v = _remove_wmean_2d(SC_v, w2d)

        # Flatten
        e_flat = {n: arrs[n].ravel() for n in EOF_NUMS}
        wf = w2d.ravel()
        mask = np.isfinite(wf)
        for n in EOF_NUMS:
            mask &= np.isfinite(e_flat[n])

        if not mask.any():
            results[model] = {n: {"label": "NA", "confidence": 0.0} for n in EOF_NUMS}
            continue

        lat_sh, lon_sh, _, _ = _make_shifts(
            lat, lon, SHIFT_LAT_MAX_DEG, SHIFT_LON_MAX_DEG
        )

        def best_fit(ctrl_2d):
            best_r, best_c = -np.inf, None
            for dli in lat_sh:
                for dlj in lon_sh:
                    yS = _shift2d(ctrl_2d, dli, dlj).ravel()
                    m = mask & np.isfinite(yS)
                    if not m.any():
                        continue
                    r, cap, c = _weighted_lstsq(
                        e_flat[2][m], e_flat[3][m], e_flat[4][m], yS[m], wf[m], RIDGE
                    )
                    if np.isfinite(r) and r > best_r:
                        best_r, best_c = r, c
            return best_c, best_r

        c_EA, r_EA = best_fit(EA_v)
        c_SCA, r_SCA = best_fit(SC_v)

        eof_results = {}
        for i, n in enumerate(EOF_NUMS):
            ea_share = (
                abs(c_EA[i]) / max(np.sum(np.abs(c_EA)), 1e-30)
                if c_EA is not None
                else 0.0
            )
            sca_share = (
                abs(c_SCA[i]) / max(np.sum(np.abs(c_SCA)), 1e-30)
                if c_SCA is not None
                else 0.0
            )
            # Weight the share by quality of fit (r) so bad fits contribute less
            ea_conf = ea_share * max(r_EA, 0) if np.isfinite(r_EA) else 0.0
            sca_conf = sca_share * max(r_SCA, 0) if np.isfinite(r_SCA) else 0.0
            total = ea_conf + sca_conf
            if total > 0:
                ea_norm = ea_conf / total
                sca_norm = sca_conf / total
            else:
                ea_norm = sca_norm = 0.0
            if ea_norm > sca_norm:
                eof_results[n] = {"label": "EA", "confidence": round(ea_norm, 3)}
            elif sca_norm > ea_norm:
                eof_results[n] = {"label": "SCA", "confidence": round(sca_norm, 3)}
            else:
                eof_results[n] = {"label": "NA", "confidence": 0.0}
        results[model] = eof_results
    return results


# =============================================================================
# METHOD 2: CORRELATIONS + GEOGRAPHIC TESTS
# =============================================================================
def _areas_for_tests(da):
    GRL = da.sel(lat=slice(55, 65), lon=slice(315, 325)).mean().item()
    IRL = da.sel(lat=slice(50, 60), lon=slice(350, 360)).mean().item()
    SCN = da.sel(lat=slice(60, 70), lon=slice(25, 35)).mean().item()
    return GRL, IRL, SCN


def _test2_favors(da):
    GRL, IRL, SCN = _areas_for_tests(da)
    if (GRL > 0) and (IRL > 0) and (SCN < 1.0):
        return "EA"
    if (GRL < 0) and (IRL < 0) and (SCN > 1.0):
        return "EA"
    if (GRL < 1.0) and (IRL > 0) and (SCN > 0):
        return "SCA"
    if (GRL > 1.0) and (IRL < 0) and (SCN < 0):
        return "SCA"
    return None


def _test3_favors(da):
    _, IRL, SCN = _areas_for_tests(da)
    a, b = abs(IRL), abs(SCN)
    if a > b:
        return "EA"
    if a < b:
        return "SCA"
    return None


def _geo_favors(eof_da, rEA, rSCA):
    """Return (t2_favor, t3_favor) for both EA- and SCA-oriented sign."""
    sEA = 1.0 if rEA >= 0 else -1.0
    sSCA = 1.0 if rSCA >= 0 else -1.0
    t2ea = _test2_favors(eof_da * sEA)
    t2sca = _test2_favors(eof_da * sSCA)
    t2 = (
        "EA"
        if (t2ea == "EA" and t2sca != "SCA")
        else ("SCA" if (t2sca == "SCA" and t2ea != "EA") else None)
    )
    t3ea = _test3_favors(eof_da * sEA)
    t3sca = _test3_favors(eof_da * sSCA)
    t3 = (
        "EA"
        if (t3ea == "EA" and t3sca != "SCA")
        else ("SCA" if (t3sca == "SCA" and t3ea != "EA") else None)
    )
    return t2, t3


def run_correlations(EA_ctrl, SCA_ctrl, triplets):
    """
    For each EOF: score_EA and score_SCA out of 100 (40 corr + 40 ortho + 10+10 geo).
    Confidence = winner_score / 100.  Label = pattern with higher score.
    """
    results = {}
    for model, eofs in triplets:
        try:
            eof_das, (EA_a, SC_a), lat, lon, w2d = _regrid_align(
                eofs, EA_ctrl, SCA_ctrl
            )
        except Exception as e:
            print(f"[WARN][corr] {model}: {e}")
            results[model] = {n: {"label": "NA", "confidence": 0.0} for n in EOF_NUMS}
            continue

        if eof_das[2].sizes["lat"] == 0:
            results[model] = {n: {"label": "NA", "confidence": 0.0} for n in EOF_NUMS}
            continue

        EA_perp = _orthogonalize(EA_a.values, SC_a.values, w2d)
        SCA_perp = _orthogonalize(SC_a.values, EA_a.values, w2d)

        eof_results = {}
        for n in EOF_NUMS:
            da_n = eof_das[n]
            rEA = float(_wcor(da_n.values, EA_a.values, w2d))
            rSCA = float(_wcor(da_n.values, SC_a.values, w2d))

            # Geographic tests
            t2, t3 = _geo_favors(da_n, rEA, rSCA)

            # Orient for orthogonal test
            target = "EA" if abs(rEA) >= abs(rSCA) else "SCA"
            sgn = 1.0
            if target == "EA" and rEA < 0:
                sgn = -1.0
            if target == "SCA" and rSCA < 0:
                sgn = -1.0
            oriented = (da_n * sgn).values
            rEAp = float(_wcor(oriented, EA_perp, w2d))
            rSCAp = float(_wcor(oriented, SCA_perp, w2d))

            # Scoring (max 100 each)
            sEA = 40.0 * abs(rEA) + 40.0 * abs(rEAp)
            sSCA = 40.0 * abs(rSCA) + 40.0 * abs(rSCAp)
            if t2 == "EA":
                sEA += 10
            elif t2 == "SCA":
                sSCA += 10
            if t3 == "EA":
                sEA += 10
            elif t3 == "SCA":
                sSCA += 10

            if sEA > sSCA:
                eof_results[n] = {"label": "EA", "confidence": round(sEA / 100.0, 3)}
            elif sSCA > sEA:
                eof_results[n] = {"label": "SCA", "confidence": round(sSCA / 100.0, 3)}
            else:
                eof_results[n] = {"label": "NA", "confidence": 0.0}
        results[model] = eof_results
    return results


# =============================================================================
# METHOD 3: K-MEANS (two-phase: train from ensemble OR apply saved centers)
# =============================================================================
def _row_normalize(X):
    norms = np.linalg.norm(X, axis=1)
    norms = np.where(norms > 0, norms, 1.0)
    return X / norms[:, None]


def _soft_membership(distances):
    assigned = distances[np.arange(len(distances)), np.argmin(distances, axis=1)]
    sigma = max(float(np.median(assigned)), 1e-30)
    sim = np.exp(-(distances**2) / (2 * sigma**2))
    return sim / sim.sum(axis=1, keepdims=True)


def _label_clusters(centers, w_sqrt, mask_flat, EA_v, SCA_v, w2d):
    """Assign EA/SCA/OTHER to each cluster center by correlation with controls."""
    inv_w = np.where(w_sqrt > 0, 1.0 / w_sqrt, 0.0)
    cluster_types = []
    for k in range(centers.shape[0]):
        flat = np.full(EA_v.size, np.nan)
        flat[mask_flat] = centers[k] * inv_w
        c2d = flat.reshape(EA_v.shape)
        rE = _wcor_anom(c2d, EA_v, w2d)
        rS = _wcor_anom(c2d, SCA_v, w2d)
        if max(abs(rE), abs(rS)) < CLUSTER_CORR_THRESHOLD:
            cluster_types.append("OTHER")
        elif abs(rE) >= abs(rS):
            cluster_types.append("EA")
        else:
            cluster_types.append("SCA")
    return cluster_types


def _scores_from_membership(p, cluster_types):
    """Return (ea_like, sca_like) for a single sample's soft membership row."""
    ea_idx = [k for k, t in enumerate(cluster_types) if t == "EA"]
    sca_idx = [k for k, t in enumerate(cluster_types) if t == "SCA"]
    ea_like = float(np.sum(p[ea_idx])) if ea_idx else 0.0
    sca_like = float(np.sum(p[sca_idx])) if sca_idx else 0.0
    return ea_like, sca_like


def _prepare_kmeans_grid(EA_ctrl, SCA_ctrl):
    """Subset and align controls, return (EA_sub, SCA_sub, lat, lon, w2d)."""
    EA_sub = _subset(EA_ctrl)
    SCA_sub = _subset(SCA_ctrl)
    EA_sub, SCA_sub = xr.align(EA_sub, SCA_sub, join="inner")
    lat, lon = EA_sub["lat"].values, EA_sub["lon"].values
    w2d = _coslat_w2d(lat, lon.size)
    return EA_sub, SCA_sub, lat, lon, w2d


def _prepare_eof_sample(eof_da, EA_sub, SCA_sub, w2d, mask_flat, w_sqrt):
    """Regrid, orient, area-weight, mask, and row-normalise a single EOF."""
    da = _subset(eof_da).interp_like(EA_sub, method="linear")
    da, EA_al, SCA_al = xr.align(da, EA_sub, SCA_sub, join="inner")
    arr = da.values.astype(float)
    rEA = _wcor_anom(arr, EA_al.values.astype(float), w2d)
    rSCA = _wcor_anom(arr, SCA_al.values.astype(float), w2d)
    sgn = (
        (1.0 if rEA >= 0 else -1.0)
        if abs(rEA) >= abs(rSCA)
        else (1.0 if rSCA >= 0 else -1.0)
    )
    arr = arr * sgn
    v = arr.ravel()[mask_flat] * w_sqrt
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


# -- Save / load centers --
def _save_centers(
    centers, cluster_types, lat, lon, mask_flat, w_sqrt, centers_file=None
):
    """Save cluster centers and metadata to JSON."""
    if centers_file is None:
        centers_file = KMEANS_CENTERS_FILE
    data = {
        "reanalysis": CTRL_REANALYSIS,
        "cmip_tag": CMIP_TAG,
        "n_clusters": int(centers.shape[0]),
        "cluster_types": cluster_types,
        "centers": centers.tolist(),
        "lat": lat.tolist(),
        "lon": lon.tolist(),
        "mask_flat": mask_flat.tolist(),
        "w_sqrt": w_sqrt.tolist(),
    }
    with open(centers_file, "w") as f:
        json.dump(data, f)
    print(f"[kmeans] saved centers: {centers_file}")
    return centers_file


def _load_centers(filepath):
    """Load saved centers; warn if reanalysis doesn't match current config."""
    with open(filepath) as f:
        data = json.load(f)
    if data["reanalysis"] != CTRL_REANALYSIS:
        print(
            f"[WARN][kmeans] Centers were trained on {data['reanalysis']} "
            f"but current CTRL_REANALYSIS is {CTRL_REANALYSIS}."
        )
    if data.get("cmip_tag", "") != CMIP_TAG:
        print(
            f"[WARN][kmeans] Centers were trained on {data.get('cmip_tag', '?')} "
            f"but current CMIP_TAG is {CMIP_TAG}."
        )
    centers = np.array(data["centers"])
    cluster_types = data["cluster_types"]
    lat = np.array(data["lat"])
    lon = np.array(data["lon"])
    mask_flat = np.array(data["mask_flat"], dtype=bool)
    w_sqrt = np.array(data["w_sqrt"])
    print(
        f"[kmeans] loaded centers from {filepath} "
        f"(reanalysis={data['reanalysis']}, cmip={data.get('cmip_tag', '?')})"
    )
    return centers, cluster_types, lat, lon, mask_flat, w_sqrt


# -- Train (full ensemble) or Apply (pre-computed) --
def _train_kmeans(EA_ctrl, SCA_ctrl, triplets, centers_file=None):
    """
    Train k-means on the full ensemble.  Requires EOF files from ALL models.
    Saves cluster centers to a JSON file for future reuse.
    Returns per-model results dict.

    Requires scikit-learn to be installed.
    """
    if not _HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for k-means retraining but is not installed. "
            "Install it with: pip install scikit-learn (or conda install scikit-learn). "
            "If you only need to apply pre-computed centers, ensure a valid centers "
            "file exists at KMEANS_CENTERS_FILE."
        )

    EA_sub, SCA_sub, lat, lon, w2d = _prepare_kmeans_grid(EA_ctrl, SCA_ctrl)
    EA_v, SCA_v = EA_sub.values, SCA_sub.values

    # Build feature matrix from all models
    pattern_arrays, meta = [], []
    for model, eofs in triplets:
        for n in EOF_NUMS:
            da = _subset(eofs[n]).interp_like(EA_sub, method="linear")
            da, EA_al, SCA_al = xr.align(da, EA_sub, SCA_sub, join="inner")
            arr = da.values.astype(float)
            rEA = _wcor_anom(arr, EA_al.values.astype(float), w2d)
            rSCA = _wcor_anom(arr, SCA_al.values.astype(float), w2d)
            sgn = (
                (1.0 if rEA >= 0 else -1.0)
                if abs(rEA) >= abs(rSCA)
                else (1.0 if rSCA >= 0 else -1.0)
            )
            pattern_arrays.append(arr * sgn)
            meta.append({"model": model, "eof": n})

    # Common finite mask across all patterns + controls
    mask2d = np.isfinite(EA_v) & np.isfinite(SCA_v)
    for arr in pattern_arrays:
        mask2d &= np.isfinite(arr)
    mf = mask2d.ravel()
    w_sqrt = np.sqrt(np.clip(w2d.ravel()[mf], 0, None))

    X = np.zeros((len(pattern_arrays), int(mf.sum())))
    for i, arr in enumerate(pattern_arrays):
        X[i] = arr.ravel()[mf] * w_sqrt
    X = _row_normalize(X)

    # Fit
    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=N_INIT)
    km.fit(X)
    distances = km.transform(X)
    p = _soft_membership(distances)

    # Label clusters and save
    cluster_types = _label_clusters(km.cluster_centers_, w_sqrt, mf, EA_v, SCA_v, w2d)
    _save_centers(
        km.cluster_centers_,
        cluster_types,
        lat,
        lon,
        mf,
        w_sqrt,
        centers_file=centers_file,
    )

    # Score each EOF
    results = {}
    for i, m in enumerate(meta):
        ea_like, sca_like = _scores_from_membership(p[i], cluster_types)
        if ea_like > sca_like:
            label, conf = "EA", ea_like
        elif sca_like > ea_like:
            label, conf = "SCA", sca_like
        else:
            label, conf = "NA", 0.0
        results.setdefault(m["model"], {})[m["eof"]] = {
            "label": label,
            "confidence": round(conf, 3),
        }
    return results


def _apply_kmeans(EA_ctrl, SCA_ctrl, triplets, centers_file):
    """
    Apply pre-computed cluster centers to classify each model individually.
    Does not require the full ensemble — works model-by-model.
    """
    centers, cluster_types, saved_lat, saved_lon, mask_flat, w_sqrt = _load_centers(
        centers_file
    )

    EA_sub, SCA_sub, lat, lon, w2d = _prepare_kmeans_grid(EA_ctrl, SCA_ctrl)

    results = {}
    for model, eofs in triplets:
        eof_results = {}
        for n in EOF_NUMS:
            try:
                sample = _prepare_eof_sample(
                    eofs[n], EA_sub, SCA_sub, w2d, mask_flat, w_sqrt
                )
                # Compute distances to saved centers
                distances = np.array([np.linalg.norm(sample - c) for c in centers])
                p = _soft_membership(distances.reshape(1, -1))[0]
                ea_like, sca_like = _scores_from_membership(p, cluster_types)
                if ea_like > sca_like:
                    label, conf = "EA", ea_like
                elif sca_like > ea_like:
                    label, conf = "SCA", sca_like
                else:
                    label, conf = "NA", 0.0
                eof_results[n] = {"label": label, "confidence": round(conf, 3)}
            except Exception as e:
                print(f"[WARN][kmeans-apply] {model} EOF{n}: {e}")
                eof_results[n] = {"label": "NA", "confidence": 0.0}
        results[model] = eof_results
    return results


def run_kmeans(EA_ctrl, SCA_ctrl, triplets, kmeans_centers_file=None):
    """
    Apply pre-computed centers if available; otherwise train on first run.
    On first run, the centers file is created from the full ensemble.
    On subsequent runs, the saved centers are loaded and applied per-model.
    """
    if kmeans_centers_file is None:
        kmeans_centers_file = KMEANS_CENTERS_FILE
    if os.path.isfile(kmeans_centers_file):
        return _apply_kmeans(EA_ctrl, SCA_ctrl, triplets, kmeans_centers_file)
    else:
        print(f"[kmeans] No centers file found at {kmeans_centers_file}.")
        print("[kmeans] Training from the full ensemble and saving for future runs.")
        print("[kmeans] This requires EOF files from ALL models in EOF_GLOBS.")
        return _train_kmeans(
            EA_ctrl, SCA_ctrl, triplets, centers_file=kmeans_centers_file
        )


# =============================================================================
# CONSENSUS + OUTPUT
# =============================================================================
def _consensus(method_results):
    """
    Determine consensus label and quality from three method results.

    method_results: list of 3 dicts, each {"label": str, "confidence": float}

    Label:       simple majority vote (2/3 or 3/3); no majority => UNCLASSIFIED.
    Confidence:  (fraction of methods agreeing) × (mean confidence of agreeing).
    Quality:     robust >= 0.7, medium >= 0.5, weak >= 0.3, very weak < 0.3.
    """
    from collections import Counter

    labels = [r["label"] for r in method_results]
    confs = [r["confidence"] for r in method_results]
    valid = [(ll, c) for ll, c in zip(labels, confs) if ll not in ("NA", None)]

    if not valid:
        return "UNCLASSIFIED", "very weak", 0.0

    # Label by simple majority
    counts = Counter(ll for ll, _ in valid)
    top_label, top_count = counts.most_common(1)[0]
    n_methods = len(labels)

    if top_count < 2:
        return "UNCLASSIFIED", "very weak", 0.0

    # Confidence = (fraction agreeing) × (mean confidence of agreeing)
    agreeing = [c for ll, c in zip(labels, confs) if ll == top_label]
    frac = len(agreeing) / n_methods
    mean_conf = sum(agreeing) / len(agreeing)
    cons_conf = round(frac * mean_conf, 3)

    if cons_conf >= CONSENSUS_ROBUST_THRESHOLD:
        return top_label, "robust", cons_conf
    if cons_conf >= CONSENSUS_MEDIUM_THRESHOLD:
        return top_label, "medium", cons_conf
    if cons_conf >= CONSENSUS_WEAK_THRESHOLD:
        return top_label, "weak", cons_conf
    return top_label, "very weak", cons_conf


def write_outputs(res_sub, res_corr, res_km, output_root=None, consensus_results=None):
    if output_root is None:
        output_root = OUTPUT_ROOT
    out_tsv = f"{output_root}_consensus.tsv"
    out_txt = f"{output_root}_consensus.txt"

    models = sorted(set(res_sub) | set(res_corr) | set(res_km))

    NOTE = (
        "NOTE: Confidence scores range from 0 to 1; values closer to 1 indicate "
        "stronger resemblance to the assigned pattern. The consensus label is by "
        "simple majority vote. The consensus confidence = (fraction of methods "
        "agreeing) x (mean confidence of agreeing methods). Quality levels: "
        "robust >= 0.7, medium >= 0.5, weak >= 0.3, very weak < 0.3. "
        "Because model EOFs may span a subspace that mixes the reference "
        "patterns, multiple EOFs can receive the same label when their "
        "projections are not cleanly separable. "
        "Notes: 'sign-inverted' means the EOF has opposite sign convention "
        "to the reference pattern. 'check sign' means the classification "
        "confidence is below 0.5 and the sign should be verified manually."
    )

    # -- Consensus table --
    header = [
        "Model",
        "EOF",
        "Subspace_label",
        "Subspace_conf",
        "Correlation_label",
        "Correlation_conf",
        "Kmeans_label",
        "Kmeans_conf",
        "Consensus_label",
        "Consensus_conf",
        "Quality",
        "Warning",
        "Notes",
    ]
    rows = []
    for m in models:
        for n in EOF_NUMS:
            s = res_sub.get(m, {}).get(n, {"label": "NA", "confidence": 0.0})
            c = res_corr.get(m, {}).get(n, {"label": "NA", "confidence": 0.0})
            k = res_km.get(m, {}).get(n, {"label": "NA", "confidence": 0.0})
            cons, quality, cons_conf = _consensus([s, c, k])
            warn = "WARNING" if quality in ("weak", "very weak") else ""
            if consensus_results is not None:
                inv = consensus_results.get(m, {}).get(n, {}).get("inverted", False)
                if cons_conf >= 0.5:
                    note = "sign-inverted" if inv else ""
                else:
                    note = "check sign"
            else:
                note = ""
            rows.append(
                [
                    m,
                    f"EOF{n}",
                    s["label"],
                    f"{s['confidence']:.2f}",
                    c["label"],
                    f"{c['confidence']:.2f}",
                    k["label"],
                    f"{k['confidence']:.2f}",
                    cons,
                    f"{cons_conf:.2f}",
                    quality,
                    warn,
                    note,
                ]
            )

    # TSV (note as comment header)
    with open(out_tsv, "w", newline="") as f:
        f.write(f"# {NOTE}\n")
        w = csv.writer(f, delimiter="\t")
        w.writerow(header)
        w.writerows(rows)

    # Pretty TXT
    all_rows = [header] + rows
    widths = [max(len(str(r[i])) for r in all_rows) for i in range(len(header))]
    with open(out_txt, "w") as g:
        g.write(NOTE + "\n\n")
        g.write(
            "  ".join(str(header[i]).ljust(widths[i]) for i in range(len(header)))
            + "\n"
        )
        g.write("  ".join("-" * widths[i] for i in range(len(header))) + "\n")
        for r in rows:
            g.write(
                "  ".join(str(r[i]).ljust(widths[i]) for i in range(len(header))) + "\n"
            )

    print(f"[output] wrote: {out_tsv}")
    print(f"[output] wrote: {out_txt}")


# =============================================================================
# MAIN
# =============================================================================
def eof_classification(
    ea_ctrl_file=None,
    sca_ctrl_file=None,
    eof_globs=None,
    kmeans_centers_file=None,
    output_root=None,
):
    """
    Classify model EOFs as East Atlantic (EA) or Scandinavian (SCA) patterns.

    All parameters are optional.  When None, they fall back to the CONFIG
    defaults at the top of this module.  This allows the function to be
    called with no arguments (standalone use) or with explicit paths
    (programmatic use from PMP or other frameworks).

    Parameters
    ----------
    ea_ctrl_file : str or None
        Path to the EA control pattern netCDF file.
    sca_ctrl_file : str or None
        Path to the SCA control pattern netCDF file.
    eof_globs : dict or None
        Dictionary mapping EOF number to glob pattern, e.g.
        {2: "/path/to/EOF2_*.nc", 3: "/path/to/EOF3_*.nc", 4: "/path/to/EOF4_*.nc"}.
    kmeans_centers_file : str or None
        Path to pre-computed k-means cluster centers JSON file.
        If the file exists, saved centers are applied.
        If it does not exist, k-means trains from the full ensemble and
        saves centers to this path (requires scikit-learn).
    output_root : str or None
        Prefix for output filenames (produces {output_root}_consensus.tsv
        and {output_root}_consensus.txt).

    Returns
    -------
    dict
        Consensus results keyed by model name, with per-EOF classification
        labels, confidences, and quality flags.
    """
    if ea_ctrl_file is None:
        ea_ctrl_file = EA_CTRL_FILE
    if sca_ctrl_file is None:
        sca_ctrl_file = SCA_CTRL_FILE
    if kmeans_centers_file is None:
        kmeans_centers_file = KMEANS_CENTERS_FILE
    if output_root is None:
        output_root = OUTPUT_ROOT

    for f, name in [(ea_ctrl_file, "EA"), (sca_ctrl_file, "SCA")]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"{name} control not found: {f}")

    print("=" * 60)
    print(f"Controls : {CTRL_REANALYSIS}")
    print(f"EA  : {ea_ctrl_file}  (×{EA_SIGN:+.0f})")
    print(f"SCA : {sca_ctrl_file} (×{SCA_SIGN:+.0f})")
    print(
        f"Domain: lat={LAT_RANGE}, lon={'ALL' if LON_INTERVALS is None else LON_INTERVALS}"
    )
    kmeans_mode = (
        "apply saved" if os.path.isfile(kmeans_centers_file) else "train from ensemble"
    )
    print(f"K-means: {kmeans_centers_file} ({kmeans_mode})")
    print("=" * 60 + "\n")

    if eof_globs is None and MODEL_EOF_DIR == "data/example_eofs":
        print("!" * 60)
        print("WARNING: Running with EXAMPLE data (single CMIP6 model).")
        print("Results are for demonstration only, not your own models.")
        print("To use your own data, set MODEL_EOF_DIR or pass eof_globs=...")
        print("!" * 60 + "\n")

    EA_ctrl = EA_SIGN * _read_da(ea_ctrl_file)
    SCA_ctrl = SCA_SIGN * _read_da(sca_ctrl_file)
    triplets = _load_model_triplets(eof_globs=eof_globs)

    res_sub = run_subspace(EA_ctrl, SCA_ctrl, triplets)
    res_corr = run_correlations(EA_ctrl, SCA_ctrl, triplets)
    res_km = run_kmeans(
        EA_ctrl, SCA_ctrl, triplets, kmeans_centers_file=kmeans_centers_file
    )

    # Build and return consensus results dict
    triplet_dict = {name: eofs for name, eofs in triplets}

    models = sorted(set(res_sub) | set(res_corr) | set(res_km))
    consensus_results = {}
    for m in models:
        consensus_results[m] = {}
        for n in EOF_NUMS:
            s = res_sub.get(m, {}).get(n, {"label": "NA", "confidence": 0.0})
            c = res_corr.get(m, {}).get(n, {"label": "NA", "confidence": 0.0})
            k = res_km.get(m, {}).get(n, {"label": "NA", "confidence": 0.0})
            cons_label, quality, cons_conf = _consensus([s, c, k])

            inverted = False
            if m in triplet_dict:
                if cons_label == "EA":
                    inverted = _check_inversion(triplet_dict[m][n], EA_ctrl)
                elif cons_label == "SCA":
                    inverted = _check_inversion(triplet_dict[m][n], SCA_ctrl)

            consensus_results[m][n] = {
                "label": cons_label,
                "confidence": cons_conf,
                "quality": quality,
                "inverted": inverted,
                "methods": {
                    "subspace": s,
                    "correlation": c,
                    "kmeans": k,
                },
            }

    write_outputs(
        res_sub,
        res_corr,
        res_km,
        output_root=output_root,
        consensus_results=consensus_results,
    )

    return consensus_results


if __name__ == "__main__":
    eof_classification()


# =============================================================================
# K-MEANS RETRAINING (not called during normal classification)
# =============================================================================
# For k-means retraining instructions, see EOF_CLASSIFICATION_GUIDE.md
