# Plan: Generalize Effective Resolution API for Single Variables

## Current Limitation

The current API `compute_effective_resolution()` is specialized for **wind fields**:
- Requires `ua` and `va` at 250 and 500 hPa
- Computes vorticity and divergence via spherical harmonic transforms
- Calculates kinetic energy spectra for rotational and divergent components
- Uses 2-of-3 confirmation rule across multiple spectra

**Problem**: Cannot compute effective resolution for other variables like temperature, geopotential height, precipitation, or any single 2D field.

## Proposed Enhancement

Add a **generalized API** that computes effective resolution from any single 2D spatial field:
- Input: Single variable (e.g., temperature at 500 hPa, surface pressure, etc.)
- Compute: Power spectrum via spherical harmonic transform
- Detect: Spectral steepening using same methodology
- Output: Effective resolution for that field

## Use Cases

1. **Temperature fields**: Identify resolved temperature scales
2. **Geopotential height**: Understand resolved pressure system scales
3. **Precipitation**: Effective resolution of precipitation patterns
4. **Sea surface temperature**: Resolved SST scales
5. **Any 2D atmospheric/oceanic field**: General applicability

## Technical Approach

### Option A: Separate Function (Recommended)

Create new standalone function: `compute_effective_resolution_scalar()`

**Advantages**:
- Clear separation of concerns
- Explicit about different physical meanings
- No complexity in main API
- Easy to document differences

**Disadvantages**:
- Code duplication for slope fitting/detection
- Two separate APIs to maintain

### Option B: Unified Function with Mode Detection

Extend `compute_effective_resolution()` to auto-detect input type

**Advantages**:
- Single entry point
- Code reuse for common logic

**Disadvantages**:
- More complex function signature
- Risk of confusion about physical interpretation
- Harder to document

**Recommendation**: Start with **Option A** for clarity, can unify later if needed.

## Implementation Details

### 1. Low-Level Spectrum Calculation

Add to `lib/ke_spectra.py`:

```python
def compute_power_spectrum(
    field: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray | None = None,
    ntrunc: int | None = None,
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    rsphere: float = EARTH_RADIUS,
) -> xr.Dataset:
    """Compute power spectrum of a 2D scalar field via spherical harmonics.
    
    Parameters
    ----------
    field : ndarray (nlat, nlon)
        2D scalar field (e.g., temperature, geopotential height)
    lat : ndarray (nlat,)
        Latitude coordinates in degrees
    lon : ndarray (nlon,), optional
        Longitude coordinates in degrees (for metadata only)
    ntrunc : int or None
        Triangular truncation wavenumber (default: nlat - 1)
    gridtype : {"auto", "regular", "gaussian"}
        Grid type for selecting integration weights
    rsphere : float
        Earth radius in meters
        
    Returns
    -------
    ds : xarray.Dataset
        Dataset with:
        - power_spectrum (l,): Power E(l) = Σ_m |C_lm|²
        - wavenumber (l,): Total wavenumber l
        - eddy_scale (l,): Eddy scale ΔS(l) in km
        
    Notes
    -----
    For a scalar field φ with spherical harmonic expansion:
        φ(θ,λ) = Σ_l Σ_m C_lm Y_lm(θ,λ)
    
    The power spectrum is:
        E(l) = Σ_m |C_lm|²
        
    Unlike kinetic energy spectra which require vorticity/divergence
    decomposition, this is a direct measure of variance at each scale.
    
    Physical Interpretation:
    - E(l) represents variance of the field at wavenumber l
    - Steepening indicates loss of variance at small scales
    - "Effective resolution" = scale below which variance is artificially damped
    """
    # 1. Transform field to spherical harmonic coefficients
    coeffs = field_to_spherical_harmonics(field, lat, ntrunc, gridtype)
    
    # 2. Compute power spectrum E(l) = Σ_m |C_lm|²
    ntrunc = coeffs.shape[0] - 1
    ell = np.arange(ntrunc + 1, dtype=float)
    power = np.zeros(ntrunc + 1)
    
    for l in range(ntrunc + 1):
        # Sum over all m for this l
        power[l] = np.sum(np.abs(coeffs[l, :l+1])**2)
    
    # 3. Compute eddy scale
    scale_km = eddy_scale(ell, rsphere, formula='exact')
    
    # 4. Package as xarray Dataset
    ds = xr.Dataset(
        {
            'power_spectrum': (['wavenumber'], power),
            'eddy_scale': (['wavenumber'], scale_km),
        },
        coords={'wavenumber': (['wavenumber'], ell)},
    )
    ds['power_spectrum'].attrs = {
        'long_name': 'Power spectrum',
        'units': '(field units)²',
        'description': 'Variance at each total wavenumber l',
    }
    
    return ds
```

Helper function for spherical harmonic transform:

```python
def field_to_spherical_harmonics(
    field: np.ndarray,
    lat: np.ndarray,
    ntrunc: int | None = None,
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
) -> np.ndarray:
    """Transform 2D field to spherical harmonic coefficients.
    
    Returns
    -------
    coeffs : ndarray (ntrunc+1, ntrunc+1), complex
        Spherical harmonic coefficients C_lm
        coeffs[l, m] = C_lm for m <= l, 0 otherwise
    """
    nlat = len(lat)
    nlon = field.shape[1]
    
    if ntrunc is None:
        ntrunc = nlat - 1
    
    # Get quadrature weights
    if gridtype == "gaussian" or (gridtype == "auto" and not is_regular_lat(lat)):
        weights = gauss_weights(nlat)
    else:
        weights = equal_weights(nlat)
    
    # Forward transform: field → coefficients
    # Similar to vorticity/divergence transform but simpler
    mu = np.sin(np.deg2rad(lat))
    
    # FFT in longitude
    field_f = np.fft.rfft(field, axis=1)
    
    # Legendre transform in latitude
    coeffs = np.zeros((ntrunc + 1, ntrunc + 1), dtype=complex)
    
    for m in range(min(ntrunc + 1, nlon // 2 + 1)):
        # Get Legendre polynomials
        P_m = _legendre(m, ntrunc, mu)[0]  # P_lm(μ)
        
        # Project field_f[:, m] onto Legendre basis
        for l in range(m, ntrunc + 1):
            coeffs[l, m] = np.sum(weights * field_f[:, m] * P_m[l - m]) / nlon
    
    return coeffs
```

### 2. High-Level API Function

Add to `lib/compute_effective_resolution.py`:

```python
def compute_effective_resolution_scalar(
    field: xr.DataArray,
    field_name: str | None = None,
    ntrunc: int | None = None,
    gridtype: Literal["auto", "regular", "gaussian"] = "auto",
    fit_window: int = 20,
    fit_anchor: Literal["center", "right", "left"] = "right",
    steepening_factor: float = 0.25,
    wavenumber_ratio: float = 2.0,
    min_wavenumber: int = 32,
    rsphere: float = EARTH_RADIUS,
    grid_box_distance_km: float | None = None,
    model: str = "model",
    member: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute effective resolution from a single 2D scalar field.
    
    Parameters
    ----------
    field : xarray.DataArray
        2D spatial field with dimensions (lat, lon) or (time, lat, lon).
        If time dimension present, will average over time before computing spectrum.
        Examples: temperature, geopotential height, precipitation, SST, etc.
    field_name : str, optional
        Name of the field for labeling (default: field.name or 'field')
    ntrunc, gridtype, fit_window, fit_anchor, steepening_factor, wavenumber_ratio, 
    min_wavenumber, rsphere, grid_box_distance_km : 
        Same as compute_effective_resolution()
    model, member : str
        Model and member identifiers for output structure
        
    Returns
    -------
    metrics : dict
        Nested {model: {member: {...}}} containing:
        - effective_wavenumber: Detected steepening wavenumber (or None)
        - effective_resolution_km: Effective resolution length scale
        - grid_box_distance_km: Nominal grid spacing
        - resolution_ratio: L_eff / L_box
        - steepening_wavenumber: Single detection (not 2-of-3)
        - field_name: Name of analyzed field
        - analysis_type: 'scalar_field'
    diagnostics : dict
        Contains:
        - spectrum: Power spectrum dataset
        - slope: Fitted spectral slope
        - detection: Steepening detection info
        
    Notes
    -----
    Physical Interpretation:
    - For wind fields: KE spectrum → resolved kinetic energy scales
    - For scalar fields: Power spectrum → resolved variance scales
    - "Effective resolution" = scale below which variance is artificially damped
      by numerical diffusion, filters, or parameterizations
      
    Differences from wind-based analysis:
    - Single spectrum instead of rotational/divergent decomposition
    - No 2-of-3 confirmation rule (only one spectrum available)
    - Physical meaning depends on the field being analyzed
    
    Use Cases:
    - Temperature: Identify resolved temperature gradient scales
    - Geopotential: Understand resolved pressure system scales  
    - Precipitation: Effective resolution of precipitation patterns
    - Any 2D field: General spectral analysis
    
    Examples
    --------
    >>> # Temperature at 500 hPa
    >>> field = ds['ta'].sel(plev=50000)
    >>> metrics, diags = compute_effective_resolution_scalar(
    ...     field, field_name='temperature_500hPa', model='HadGEM3-GC31-HM'
    ... )
    
    >>> # Sea surface temperature
    >>> sst = ds['tos']  # (time, lat, lon)
    >>> metrics, diags = compute_effective_resolution_scalar(
    ...     sst, field_name='SST', model='CESM2'
    ... )
    """
    # Extract coordinates
    lat = field.lat.values
    lon = field.lon.values if 'lon' in field.coords else None
    
    # Time average if present
    if 'time' in field.dims:
        field_2d = field.mean(dim='time').values
    else:
        field_2d = field.values
    
    # Determine field name
    if field_name is None:
        field_name = field.name if field.name else 'field'
    
    # Compute power spectrum
    spectrum_ds = compute_power_spectrum(
        field_2d, lat, lon, ntrunc=ntrunc, gridtype=gridtype, rsphere=rsphere
    )
    
    # Fit spectral slope
    slope = fit_spectral_slope(
        spectrum_ds['power_spectrum'],
        window=fit_window,
        anchor=fit_anchor,
    )
    
    # Detect steepening
    detection = detect_steepening(
        slope,
        steepening_factor=steepening_factor,
        wavenumber_ratio=wavenumber_ratio,
        min_wavenumber=min_wavenumber,
    )
    
    # Extract effective wavenumber
    l_eff = detection['wavenumber']
    
    # Compute metrics
    if l_eff is not None:
        l_eff_km = float(eddy_scale(l_eff, rsphere))
    else:
        l_eff_km = None
    
    # Grid box distance
    if grid_box_distance_km is None:
        grid_box_distance_km = representative_grid_box_distance(lat, lon, rsphere)
    
    # Resolution ratio
    ratio = None if l_eff_km is None else float(l_eff_km / grid_box_distance_km)
    
    # Package metrics
    inner = {
        'effective_wavenumber': l_eff,
        'effective_resolution_km': l_eff_km,
        'grid_box_distance_km': float(grid_box_distance_km),
        'resolution_ratio': ratio,
        'resolution_ratio_dx_convention': (
            None if ratio is None else float(ratio_to_dx_convention(ratio))
        ),
        'is_upper_limit': bool(detection['is_upper_limit']),
        'steepening_wavenumber': {field_name: l_eff},
        'steepening_eddy_scale_km': {
            field_name: None if l_eff is None else float(eddy_scale(l_eff, rsphere))
        },
        'field_name': field_name,
        'analysis_type': 'scalar_field',
        'criterion': {
            'fit_window': fit_window,
            'fit_anchor': fit_anchor,
            'steepening_factor': steepening_factor,
            'wavenumber_ratio': wavenumber_ratio,
            'min_wavenumber': min_wavenumber,
        },
        'reference': REFERENCE,
    }
    
    # Package diagnostics
    diagnostics = {
        'spectrum': spectrum_ds,
        'slope': slope,
        'detection': detection,
    }
    
    # Return in standard structure
    metrics = {model: {member if member else 'unspecified': inner}}
    
    return metrics, diagnostics
```

### 3. Visualization Support

Add to `lib/plot.py`:

```python
def plot_scalar_spectrum_and_slope(
    diagnostics: dict,
    metrics: dict,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (8, 6),
) -> Figure:
    """Plot power spectrum and slope for scalar field analysis.
    
    Similar to plot_spectra_and_slope() but for single field.
    Two panels:
    - Top: Compensated power spectrum (l³ E_l)
    - Bottom: Spectral slope n(l) with steepening detection
    """
    # Similar structure to existing plot function
    # but adapted for single spectrum
    pass
```

### 4. Update Main API (Optional Enhancement)

Could extend `compute_effective_resolution()` to accept either format:

```python
def compute_effective_resolution(
    data: xr.Dataset | xr.DataArray,
    # ... existing parameters ...
    analysis_mode: Literal["auto", "wind", "scalar"] = "auto",
):
    """Compute effective resolution from winds or scalar field.
    
    Parameters
    ----------
    data : xarray.Dataset or xarray.DataArray
        - Dataset with ua/va → wind-based analysis (original)
        - DataArray → scalar field analysis (new)
    analysis_mode : {"auto", "wind", "scalar"}
        - "auto": Detect based on data type
        - "wind": Force wind analysis (requires Dataset with ua/va)
        - "scalar": Force scalar analysis (requires DataArray)
    """
    if isinstance(data, xr.DataArray) or analysis_mode == "scalar":
        # Route to scalar analysis
        return compute_effective_resolution_scalar(data, ...)
    else:
        # Original wind analysis
        # ... existing code ...
```

## Implementation Steps

### Phase 1: Core Functionality (Priority 1)
1. ✅ Create this plan document
2. ⬜ Implement `field_to_spherical_harmonics()` in `lib/ke_spectra.py`
3. ⬜ Implement `compute_power_spectrum()` in `lib/ke_spectra.py`
4. ⬜ Add unit tests for spherical harmonic transform and power spectrum
5. ⬜ Implement `compute_effective_resolution_scalar()` in `lib/compute_effective_resolution.py`
6. ⬜ Add unit tests for full scalar resolution computation

### Phase 2: Integration and Testing (Priority 1)
7. ⬜ Create test with synthetic scalar field (2D Gaussian, known spectrum)
8. ⬜ Test with real temperature data
9. ⬜ Test with real geopotential height data
10. ⬜ Verify results make physical sense

### Phase 3: Visualization (Priority 2)
11. ⬜ Implement `plot_scalar_spectrum_and_slope()` in `lib/plot.py`
12. ⬜ Test plotting with sample data

### Phase 4: Documentation (Priority 2)
13. ⬜ Add section to demo notebook showing scalar field analysis
14. ⬜ Update README with scalar field examples
15. ⬜ Document physical interpretation differences
16. ⬜ Add example use cases

### Phase 5: Optional Enhancements (Priority 3)
17. ⬜ Unified API with mode detection
18. ⬜ Support for multiple fields (compute multiple spectra at once)
19. ⬜ Time-varying resolution analysis (don't average over time)

## Design Decisions to Confirm

### 1. Function Naming
- `compute_effective_resolution_scalar()` ✓ (clear)
- vs `compute_effective_resolution_field()`
- vs `compute_effective_resolution_2d()`

### 2. Physical Interpretation
How should we interpret "effective resolution" for non-wind fields?
- For winds: Resolved kinetic energy scales
- For temperature: Resolved temperature variance scales
- For precipitation: Resolved precipitation pattern scales

**Recommendation**: Generalize as "resolved variance scales" and document that physical meaning depends on the field.

### 3. Steepening Criterion
Should we use same 25% threshold for all fields?
- **Option A**: Same threshold (consistent with paper, easier to compare)
- **Option B**: Field-dependent thresholds (more physically motivated but arbitrary)

**Recommendation**: Start with Option A, allow user override.

### 4. Multiple Fields
Should we support analyzing multiple fields at once?
- Single field: Simpler API, clear interpretation
- Multiple fields: Could do multi-field confirmation like 2-of-3 rule

**Recommendation**: Start with single field, add multi-field later if needed.

## Testing Strategy

### Synthetic Test Cases
1. **2D Gaussian with known roll-off**: Verify detection accuracy
2. **Power law spectrum**: Verify slope fitting
3. **White noise**: Should find no clear effective resolution

### Real Data Test Cases
1. **Temperature at 500 hPa** from CMIP6 model
2. **Geopotential height at 500 hPa** from reanalysis
3. **Sea surface temperature** from observations
4. **Precipitation** from model output

### Validation Criteria
- Detected resolution should be physically reasonable (2-10× grid spacing)
- Results should be reproducible
- Different fields from same model should show similar resolution ratios

## Documentation Requirements

### API Documentation
- Complete docstrings with examples
- Physical interpretation section
- Comparison with wind-based analysis
- When to use which approach

### User Guide
- Tutorial section in demo notebook
- Example use cases
- Interpretation guidelines
- Limitations and caveats

### Scientific Documentation
- Mathematical formulation
- Relationship to Klaver et al. (2020) method
- Differences in interpretation
- References for power spectrum analysis

## Open Questions

1. **Should we normalize the power spectrum?**
   - By total variance?
   - By l(l+1) factor?
   - Leave raw?

2. **How to handle missing values?**
   - Reject if any missing?
   - Interpolate?
   - Masked spherical harmonics?

3. **Should we support 3D fields?**
   - Analyze each level separately?
   - Compute 3D spectrum?
   - Keep as 2D only?

4. **Integration with existing process_effective_resolution()?**
   - Create `process_effective_resolution_scalar()` for file I/O?
   - Extend existing function?
   - Keep separate?

## Success Criteria

✅ **Minimum Viable Product**:
- Can compute power spectrum from any 2D field
- Detects effective resolution using same methodology
- Returns metrics in consistent format
- Has basic tests and documentation

✅ **Full Feature Set**:
- Comprehensive test suite (synthetic + real data)
- Visualization support
- Complete documentation with examples
- Integration with existing API

✅ **Production Ready**:
- Edge case handling
- Performance optimization
- Full docstrings and type hints
- User guide and tutorials
