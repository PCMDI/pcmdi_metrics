# Effective Resolution Metric

This module estimates the **effective resolution** of an atmospheric model — the smallest spatial scale it plausibly represents — from the kinetic energy spectra of the rotational and divergent parts of the horizontal wind, following Klaver et al. (2020).

A model's *nominal* resolution is just its mesh size. Its *effective* resolution is coarser, because parameterisation, numerical diffusion, interpolation and anti-aliasing filters drain energy from the smallest resolved scales. The diagnostic finds where that drain begins, and reports it both as a length `L_eff` and as the grid-independent ratio `L_eff / L̃_box`, which Klaver et al. find to lie between 2.7 and 4.8 across models spanning regular latitude–longitude, Gaussian, reduced Gaussian and octahedral grids.

`L_eff` is interpretive context for every other PMP metric: a metric evaluated at scales below `L_eff` is measuring numerics rather than climate. No observational reference dataset is required — the criterion is internal to the model's own spectrum.

## Method

Three spectra are examined per model configuration:

| Spectrum | Role |
|---|---|
| divergent KE, 250 hPa | Steepens earliest and most sharply — the most sensitive indicator |
| rotational KE, 250 hPa | Near-tropopause rotational component |
| rotational KE, 500 hPa | Confirms the signal is not confined to the tropopause |

The divergent spectrum at 500 hPa is computed but **deliberately excluded**: Klaver et al. find it steepens at all scales and carries no usable signal.

1. **Spectra.** From spherical-harmonic coefficients of vorticity and divergence, `E_l = a²/(2l(l+1)) Σ_m (|ζ_lm|² + |d_lm|²)` (Eqs. 1–2), averaged over time. Eddy scale `ΔS = π√(a²/(l(l+1))) ≈ 20000/l` km (Eq. 3).
2. **Slope.** Fit `E = C·l^(−n)` in a sliding 20-wavenumber window to get the local exponent `n(l)`.
3. **Steepening.** The smallest `l ≥ 32` where `n` grows by ≥25% over a doubling of `l` and stays above that reference line throughout.
4. **Effective resolution.** The wavenumber at which ≥2 of the 3 spectra steepen, equivalently the median of the three.
5. **Ratio.** `L_eff / L̃_box`, where `L̃_box` is the area-weighted mean grid box diagonal (Appendix S1).

The spherical-harmonic transform is done in NumPy, forming vorticity and divergence *exactly* in spectral space from the coefficients of `u cosφ` and `v cosφ` (Bourke, 1972). No optional Fortran spectral library is required. Forming them by finite differences on the grid would damp precisely the high wavenumbers this diagnostic inspects, and manufacture the steepening it is meant to detect.

## Metrics reported

| Metric | Symbol | Description |
|---|---|---|
| `effective_wavenumber` | `l_eff` | Total wavenumber where ≥2 of 3 spectra steepen |
| `effective_resolution_km` | `L_eff` | Eddy scale (half wavelength) of `l_eff`, Eq. 3 |
| `grid_box_distance_km` | `L̃_box` | Area-weighted mean grid box diagonal (nominal resolution) |
| `resolution_ratio` | `L_eff / L̃_box` | **Headline metric**, grid-independent; 2.7–4.8 in the paper |
| `resolution_ratio_dx_convention` | `L_eff / Δx` | Same, in the Skamarock (2004) / Abdalla et al. (2013) convention |
| `steepening_wavenumber` | — | Per-spectrum detections (`div_250`, `rot_250`, `rot_500`) |
| `steepening_wavenumber_range` | — | Min/max over the three spectra — the error bar of the paper's Figure 2 |
| `is_upper_limit` | — | `True` when steepening is already present at `min_wavenumber`, so the value bounds rather than resolves `l_eff` |

## Public API

```python
from pcmdi_metrics.effective_resolution import (
    compute_effective_resolution,   # pure computation, xarray in / dicts out
    process_effective_resolution,   # file paths in, NetCDF + JSON + PNG out
)
```

### `compute_effective_resolution()`

Pure computation API accepting an already-opened xarray Dataset. Performs no file I/O and produces no plots. Suitable for notebooks, pipelines and unit tests.

```python
metrics, diagnostics = compute_effective_resolution(
    ds,                      # (time, plev, lat, lon) on the model's NATIVE grid
    uvar="ua",
    vvar="va",
    levels=(250.0, 500.0),   # hPa, whatever units the plev axis uses
    steepening_factor=0.25,  # the paper's ad hoc threshold
    min_wavenumber=32,
    model="HadGEM3-GC31-HM",
    member="r1i1p1f1",
)

metrics["HadGEM3-GC31-HM"]["r1i1p1f1"]["resolution_ratio"]   # -> L_eff / L̃_box
diagnostics["dataset"].to_netcdf("spectra.nc")
```

### `process_effective_resolution()`

File-path API for driver scripts. Writes the spectra to NetCDF, the metrics to JSON with the standard PMP provenance block, and optionally the Figure 1 diagnostic plot.

```python
params = {
    "model": "HadGEM3-GC31-HM",
    "exp": "highresSST-present",
    "member": "r1i1p1f1",
    "input_file": "/path/to/ua_6hrPlevPt_*.nc",
    "input_file_v": "/path/to/va_6hrPlevPt_*.nc",
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

## Supporting utilities

```python
from pcmdi_metrics.effective_resolution.lib import (
    compute_ke_spectra,               # Eqs. 1-3 for one 2-D wind field
    compute_ke_spectra_timeseries,    # ... looped over time at one level
    vrtdiv_spectral_coefficients,     # exact spherical-harmonic transform
    fit_spectral_slope,               # sliding-window exponent n(l)
    detect_steepening,                # the 25%-per-doubling criterion
    representative_grid_box_distance, # L̃_box, incl. reduced/octahedral grids
    plot_spectra_and_slope,           # paper Figure 1
    plot_resolution_scatter,          # paper Figure 2
)
```

## Data requirements

- **Frequency:** 6-hourly instantaneous or finer (`6hrPlevPt` in CMIP6). Daily means smooth away the transient small scales the diagnostic lives on.
- **Variables:** `ua`, `va` on pressure levels, at 250 and 500 hPa. The vertical coordinate may be in Pa or hPa; requesting a level that is not present raises rather than silently snapping to the nearest one.
- **Grid:** the model's **native** horizontal grid. Regridding overwrites the very scales being measured, and `L̃_box` derived from a regridded file describes the target grid, not the model. For reduced Gaussian and octahedral grids (e.g. ECMWF-IFS `TCO`), the file's rectilinear coordinates misrepresent the mesh — pass `grid_box_distance_km` explicitly.
- **Period:** Klaver et al. use March, June, September and December of 2014. Spectral slopes barely differ between months, so one month suffices once time-invariance is confirmed for a new model.

Cost is one spherical-harmonic transform per time step per level.

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

The paper uses pre-publication HighResMIP labels; the ESGF `source_id` values differ (`EC-Earth3` → `EC-Earth3P`, `CNRM-CM6-0` → `CNRM-CM6-1`, `MPIESM-1-2-HR` → `MPI-ESM1-2-HR`). `representative_grid_box_distance` and `eddy_scale` reproduce the `L̃_box` and `L_eff` columns of this table to within rounding; both comparisons are covered by `tests/test_effective_resolution.py`.

## Caveats

- The **25% threshold** is described by the authors as "ad hoc and somewhat arbitrary". They argue the two-of-three confirmation rule limits sensitivity to it, an argument made for their 13 configurations; a sweep of `steepening_factor` over 0.15–0.40 is worth running for any new model.
- The **slope-fit anchoring** is ambiguous in the paper. `fit_anchor="center"` is the default and the conventional choice; `"right"` is the literal reading of "steepening at the largest wavenumber in the range". The two shift the diagnosed wavenumber by roughly `fit_window / 2` — material at `l ≈ 35`, minor at `l ≈ 110`.
- The spectrum is **global and time-mean**, which the authors note may obscure a phenomenon-dependent effective resolution (midlatitude storms versus equatorial updraughts).
- The diagnostic says nothing about the fidelity of scales *larger* than `L_eff`. A model can have a good effective resolution and a poor spectrum in the resolved range.

## Examples

- `demo_effective_resolution.ipynb` — runnable notebook demonstration on synthetic data, no input files needed
- `param/myParam_effective_resolution.py` — example parameter file for the driver

## References

- Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective resolution in high resolution global atmospheric models for climate studies. *Atmos. Sci. Lett.*, 21, e952. https://doi.org/10.1002/asl.952
- Bourke, W. (1972). An efficient, one-level, primitive-equation spectral model. *Mon. Weather Rev.*, 100, 683–689.
- Skamarock, W. C. (2004). Evaluating mesoscale NWP models using kinetic energy spectra. *Mon. Weather Rev.*, 132, 3019–3032.
- Abdalla, S., Isaksen, L., Janssen, P., & Wedi, N. (2013). Effective spectral resolution of ECMWF atmospheric forecast models. *ECMWF Newsletter*, 137, 19–22.
- Callies, J., Ferrari, R., & Bühler, O. (2014). Transition from geostrophic turbulence to inertia–gravity waves in the atmospheric energy spectrum. *PNAS*, 111, 17033–17038.
