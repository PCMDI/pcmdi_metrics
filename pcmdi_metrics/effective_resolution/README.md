# Effective Resolution Metric

Draft PMP module implementing the effective-resolution diagnostic of **Klaver, Haarsma, Vidale & Hazeleger (2020)**, *Effective resolution in high resolution global atmospheric models for climate studies*, Atmos. Sci. Lett. 21, e952, [doi:10.1002/asl.952](https://doi.org/10.1002/asl.952).

**Status: draft API for review.** The structure, signatures and criteria are complete and the code runs end to end on synthetic data. Two components are already validated against the published Table 1; the spectra and the detection step are not. See [What is and isn't validated](#what-is-and-isnt-validated) and [Open questions](#open-questions-before-merging) before merging.

## Why this belongs in PMP

PMP characterises models by nominal resolution, which is just mesh size. This diagnostic measures the *dynamical* resolution — the smallest scale a model plausibly represents — and it is a property PMP can report once per model configuration, independent of any reference dataset.

Three properties make it a good fit:

- **No observational reference needed.** The criterion is internal to the spectrum (progressive steepening relative to its own resolved-range slope), so there is no obs4MIPs dependency and no uncertainty inherited from an analysis product.
- **Grid-agnostic and comparable.** Global spherical-harmonic spectra plus the `L_eff / L_box` ratio make regular, Gaussian, reduced-Gaussian and octahedral grids directly comparable — the paper spans all four.
- **Interpretive value for every other PMP metric.** `L_eff` tells a user which scales in a model are safe to interpret. A metric computed at scales below `L_eff` is measuring numerics, not climate.

## Proposed metrics

| Metric | Symbol | Description |
|---|---|---|
| `effective_wavenumber` | `l_eff` | Total wavenumber where ≥2 of 3 spectra steepen (equivalently, the median of the three) |
| `effective_resolution_km` | `L_eff` | Eddy scale (half wavelength) of `l_eff`, Eq. 3 |
| `grid_box_distance_km` | `L̃_box` | Area-weighted mean grid box diagonal (nominal resolution) |
| `resolution_ratio` | `L_eff / L̃_box` | **Headline metric.** 2.7–4.8 across the paper's 13 configurations; grid-independent |
| `resolution_ratio_dx_convention` | `L_eff / Δx` | Same, in the Skamarock (2004) / Abdalla et al. (2013) convention for comparison with the NWP literature |
| `steepening_wavenumber` | — | Per-spectrum detections (`div_250`, `rot_250`, `rot_500`) |
| `steepening_wavenumber_range` | — | Min/max over the three spectra — the error bar of the paper's Figure 2 |
| `is_upper_limit` | — | `True` when steepening is already present at `min_wavenumber`, so the value bounds rather than resolves `l_eff` |

## Proposed diagnostics

| Diagnostic | Function |
|---|---|
| Rotational / divergent / total KE spectra `E_l` | `compute_ke_spectra`, `compute_ke_spectra_timeseries` |
| Sliding-window spectral slope exponent `n(l)` | `fit_spectral_slope` |
| Steepening detection with reference lines | `detect_steepening`, `reference_steepening_line` |
| Representative grid box distance | `representative_grid_box_distance` |
| Figure 1 (compensated spectra + slope panels) | `plot_spectra_and_slope` |
| Figure 2 (ensemble `L_eff` vs `L̃_box` scatter) | `plot_resolution_scatter` |

## Public API

Following the `pcmdi_metrics.qbo` two-tier convention:

```python
from pcmdi_metrics.effective_resolution import (
    compute_effective_resolution,   # pure computation, xarray in / dicts out
    process_effective_resolution,   # file paths in, NetCDF + JSON + PNG out
)
```

### `compute_effective_resolution()`

Pure computation. No file I/O, no plots. Suitable for notebooks, pipelines and unit tests.

```python
metrics, diagnostics = compute_effective_resolution(
    ds,                      # (time, plev, lat, lon), NATIVE grid
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),
    backend="auto",          # windspharm -> shtns -> numpy
    steepening_factor=0.25,  # the paper's ad hoc threshold
    min_wavenumber=32,
    model="HadGEM3-GC31-HM",
    member="r1i1p1f1",
)

metrics["HadGEM3-GC31-HM"]["r1i1p1f1"]["effective_wavenumber"]   # -> l_eff
metrics["HadGEM3-GC31-HM"]["r1i1p1f1"]["resolution_ratio"]       # -> L_eff / L_box
diagnostics["dataset"].to_netcdf("spectra.nc")
```

### `process_effective_resolution()`

File-path API for driver scripts.

```python
params = {
    "model": "HadGEM3-GC31-HM",
    "exp": "highresSST-present",
    "member": "r1i1p1f1",
    "input_file": "/path/to/ua_6hrPlevPt_*.nc",
    "input_file_v": "/path/to/va_6hrPlevPt_*.nc",
    "levels": (250.0, 500.0),
    "start": "2014-03-01",
    "end": "2014-03-31",
    "grid_box_distance_km": 40.8,   # native value; see note on reduced grids
    "output_dir": "./output",
    "plot": True,
}
metrics = process_effective_resolution(params)
```

### Driver

```bash
python effective_resolution_driver.py -p param/myParam_effective_resolution.py
```

## Method

Three spectra are examined per configuration:

| Spectrum | Role |
|---|---|
| divergent KE, 250 hPa | Steepens earliest and most sharply — the most sensitive indicator |
| rotational KE, 250 hPa | Near-tropopause rotational component |
| rotational KE, 500 hPa | Confirms the signal is not confined to the tropopause |

The divergent spectrum at 500 hPa is computed but **deliberately excluded**: Klaver et al. find it steepens at all scales and carries no usable signal.

Chain of steps:

1. **Spectra.** From spherical-harmonic coefficients of vorticity and divergence, `E_l = a²/(2l(l+1)) Σ_m (|ζ_lm|² + |d_lm|²)` (Eqs. 1–2), averaged over time. Eddy scale `ΔS = π√(a²/(l(l+1))) ≈ 20000/l` km (Eq. 3).
2. **Slope.** Fit `y = C·l^(−n)` in a sliding 20-wavenumber window → exponent `n(l)`.
3. **Steepening.** Smallest `l ≥ 32` where `n` grows ≥25% over a doubling of `l`.
4. **Effective resolution.** The wavenumber where ≥2 of 3 spectra steepen.
5. **Ratio.** `L_eff / L̃_box`.

## Dependencies

Core: `numpy`, `xarray`, `xcdat`, `matplotlib` — all already in the PMP environment.

Optional spherical-harmonic backends, selected by `backend=`:

| Backend | Package | Notes |
|---|---|---|
| `"windspharm"` | `pyspharm` (`spharm`) | Default when present. Fortran SPHEREPACK; widely available in the climate stack |
| `"shtns"` | `shtns` | What Klaver et al. used (Schaeffer 2013). Fastest; less commonly installed |
| `"numpy"` | none | **Testing only.** Finite-difference vorticity/divergence damps exactly the high wavenumbers the diagnostic examines |
| `"auto"` | — | windspharm → shtns → numpy, warning on the fallback |

Adding no new hard dependency to PMP's environment is deliberate; a user who never calls this module never needs a spectral library.

## Data requirements

- **Frequency:** 6-hourly instantaneous or finer (`6hrPlevPt` in CMIP6). Daily means smooth away the transient small scales the diagnostic lives on.
- **Variables:** `ua`, `va` on pressure levels, at 250 and 500 hPa.
- **Grid:** the model's **native** horizontal grid. Regridding overwrites the very scales being measured. `process_effective_resolution` does no regridding, by design.
- **Period:** Klaver et al. use March, June, September and December of 2014. Spectral slopes barely differ between months, so one month suffices once time-invariance is confirmed for a new model.

Cost is one SH transform per time step per level. One month of 6-hourly data at 769×1024 is ~120 transforms per level — minutes with `shtns` or `pyspharm`.

## What is and isn't validated

Run `python scripts/example_effective_resolution.py` to reproduce all of this — it needs no input files and no optional spectral library.

**Validated against the paper:**

- **`representative_grid_box_distance`** reproduces the `L̃_box` column of Table 1 exactly for every grid-point configuration tested: 145×192 → 217.5 (published 217), 325×432 → 96.7 (96.7), 769×1024 → 40.8 (40.8), 192×288 → 153.2 (153), 768×1152 → 38.2 (38.2).
- **`eddy_scale`** reproduces the `L_eff` column: `l=108` → 184 km (published 185), `l=55` → 361 km (364), `l=84` → 237 km (238). The ~1% offset is because Table 1 was computed from the `20000/l` shorthand; `formula="approx"` matches exactly.

**Validated internally, not against the paper:**

- The numpy backend's normalised Legendre recursion is orthonormal to ~1e-13, and Parseval's identity closes to 0.01% on a band-limited field. This checks the transform's *self-consistency*, not the SPHEREPACK unpacking factor in `_unpack_triangular` — see open question 2.
- `fit_spectral_slope` recovers the exact exponent of a pure power law.
- `detect_steepening` fires at `l=53` on a `k⁻³` spectrum rolling off past `l=60`. The ~7-wavenumber lead is inherent to a centred 20-wavenumber window and applies equally to the published values.
- The full pipeline runs end to end on a synthetic wind field with all three spectra registering a detection.

**Not validated:** the KE spectra themselves against any model output, and the diagnosed `l_eff` against any Table 1 entry. That requires real 6-hourly HighResMIP data and is the acceptance test proposed in open question 5.

## Open questions before merging

These are places where the paper is ambiguous or where the implementation makes a choice that should be reviewed:

1. **Slope-fit anchoring.** The paper says steepening in a 20-wavenumber window is "indicative of steepening at the largest wavenumber in the range", but plots `n(l)` as a curve without stating the anchoring. `fit_anchor="center"` is the default; `"right"` is the literal reading. The two differ by ~10 wavenumbers — material at `l ≈ 35`, minor at `l ≈ 110`. **Suggest contacting the authors or testing both against Table 1.**

2. **SPHEREPACK normalisation.** `_unpack_triangular` applies a `1/√2` factor to convert SPHEREPACK's convention to the 4π normalisation used here. SH normalisation conventions differ between packages and releases. `parseval_check()` is provided to verify this; **it must be run against a known field before any published number.**

3. **Reduced and octahedral grids.** ECMWF-IFS `TCO` grids and reduced Gaussian grids are not rectilinear, so a Dataset's lat/lon coordinates misrepresent the native mesh. `representative_grid_box_distance` accepts `nlon_per_lat` for this, but the driver currently expects `L̃_box` to be supplied from Table 1 rather than derived. Deriving it automatically needs grid metadata PMP does not currently carry.

4. **The 25% threshold.** The authors call it "ad hoc and somewhat arbitrary" and argue the two-of-three rule limits sensitivity to it. That argument was made for their 13 configurations. A sensitivity sweep (`steepening_factor` 0.15–0.40) should be part of the acceptance test for any new model.

5. **Validation targets.** Table 1 of the paper gives `l_eff`, `L_eff` and `L_eff/L̃_box` for 13 configurations. Reproducing even two or three of these — say HadGEM3-GC31-HM (`l_eff = 108`) and MPI-ESM1-2-XR (`l_eff = 78`) — would be the natural acceptance test. Note the paper's model names are the pre-publication HighResMIP labels; the ESGF `source_id` values differ (`EC-Earth3` → `EC-Earth3P`, `CNRM-CM6-0` → `CNRM-CM6-1`, `MPIESM-1-2-HR` → `MPI-ESM1-2-HR`).

6. **Physical scope.** The authors caution that a global, time-mean spectrum may obscure a phenomenon-dependent effective resolution — midlatitude storms versus equatorial updraughts. A regional variant (spectra over latitude bands) would be a natural PMP extension but is *not* what the paper validated.

## Reference values (Klaver et al. 2020, Table 1)

| Model configuration | L̃_box (km) | l_eff | L_eff (km) | L_eff/L̃_box |
|---|---|---|---|---|
| HadGEM3-GC31-LM | 217 | ≤32 | ≥625 | ≥2.9 |
| HadGEM3-GC31-MM | 96.7 | 55 | 364 | 3.8 |
| HadGEM3-GC31-HM | 40.8 | 108 | 185 | 4.5 |
| CMCC-CM2-HR4 | 153 | 35 | 571 | 3.7 |
| CMCC-CM2-VHR4 | 38.2 | 110 | 182 | 4.8 |
| ECMWF-IFS-LR | 79.6 | 79 | 253 | 3.2 |
| ECMWF-IFS-HR | 40.4 | 108 | 185 | 4.6 |
| EC-Earth3 | 107 | 57 | 351 | 3.3 |
| EC-Earth3-HR | 54.2 | 84 | 238 | 4.4 |
| MPIESM-1-2-HR | 134 | 55 | 364 | 2.7 |
| MPIESM-1-2-XR | 66.9 | 78 | 256 | 3.8 |
| CNRM-CM6-0 | 207 | ≤32 | ≥625 | ≥3.0 |
| CNRM-CM6-0-HR | 75.3 | 64 | 313 | 4.2 |

The highest effective resolution reached by any CMIP6-generation model in this study is roughly 200 km — the newest high-resolution models are only beginning to resolve synoptic scales.

## Module layout

```
effective_resolution/
├── README.md
├── __init__.py
├── effective_resolution_driver.py
├── lib/
│   ├── __init__.py
│   ├── spherical_harmonics.py           # pluggable SH backends + Parseval check
│   ├── ke_spectra.py                    # Eqs. 1-3
│   ├── spectral_slope.py                # sliding fit + steepening criterion
│   ├── grid_distance.py                 # L̃_box for regular/Gaussian/reduced grids
│   ├── compute_effective_resolution.py  # compute_* / process_* public API
│   └── plot.py                          # Figures 1 and 2
├── param/
│   └── myParam_effective_resolution.py
└── scripts/
    └── example_effective_resolution.py  # runnable, synthetic, no input files
```

## References

- Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective resolution in high resolution global atmospheric models for climate studies. *Atmos. Sci. Lett.*, 21, e952. https://doi.org/10.1002/asl.952
- Skamarock, W. C. (2004). Evaluating mesoscale NWP models using kinetic energy spectra. *Mon. Weather Rev.*, 132, 3019–3032.
- Abdalla, S., Isaksen, L., Janssen, P., & Wedi, N. (2013). Effective spectral resolution of ECMWF atmospheric forecast models. *ECMWF Newsletter*, 137, 19–22.
- Callies, J., Ferrari, R., & Bühler, O. (2014). Transition from geostrophic turbulence to inertia–gravity waves in the atmospheric energy spectrum. *PNAS*, 111, 17033–17038.
- Lambert, S. J. (1984). A global available potential energy-kinetic energy budget in terms of the two-dimensional wavenumber for the FGGE year. *Atmos.-Ocean*, 22, 265–282.
- Schaeffer, N. (2013). Efficient spherical harmonic transforms aimed at pseudospectral numerical simulations. *G-cubed*, 14, 751–758.
