# Default Seasons Configuration

This document explains the default season settings for each variability mode in the API.

## Overview

Different climate variability modes have different characteristic timescales. The API defaults reflect these scientific conventions:

- **Atmospheric modes** (NAO, NAM, SAM, PNA, NPO, PSA1, PSA2): Seasonal variability → default to **4 seasons**
- **Oceanic modes** (PDO, NPGO): Slower variability → default to **monthly** analysis
- **Multidecadal modes** (AMO): Longest timescale → default to **yearly** analysis

## Default Seasons by Mode

| Mode | Default Season(s) | Rationale |
|------|------------------|-----------|
| NAO | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| NAM | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| SAM | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| PNA | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| NPO | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| PSA1 | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| PSA2 | `['DJF', 'MAM', 'JJA', 'SON']` | Atmospheric mode, strong seasonal cycle |
| PDO | `['monthly']` | Ocean mode, slow variability, monthly more appropriate |
| NPGO | `['monthly']` | Ocean mode, slow variability, monthly more appropriate |
| AMO | `['yearly']` | Multidecadal mode, very slow variability |

## Scientific Rationale

### Atmospheric Modes (NAO, NAM, SAM, PNA, NPO, PSA1, PSA2)

Atmospheric variability modes are characterized by:
- Fast timescales (days to months)
- Strong seasonal differences in patterns and intensity
- Different teleconnection patterns by season

**Default**: All four standard seasons (`DJF`, `MAM`, `JJA`, `SON`)

**Example**: NAO is strongest in winter (DJF) but has different patterns in other seasons.

### Pacific Decadal Oscillation (PDO) and North Pacific Gyre Oscillation (NPGO)

Ocean variability modes are characterized by:
- Slower timescales (months to years)
- Persistence across seasons
- SST-based rather than atmospheric pressure

**Default**: Monthly analysis (`monthly`)

**Rationale**: 
- PDO/NPGO patterns evolve on decadal timescales
- Monthly analysis captures the full temporal evolution
- Seasonal aggregation may miss important transitions
- Common practice in PDO/NPGO research

### Atlantic Multidecadal Oscillation (AMO)

Multidecadal modes are characterized by:
- Very slow timescales (decades)
- Quasi-periodic behavior on 60-80 year cycles
- Focus on long-term trends

**Default**: Yearly analysis (`yearly`)

**Rationale**:
- AMO operates on multidecadal timescales
- Yearly averaging removes seasonal noise
- Focuses on long-term variability signal
- Standard practice in AMO research

## Usage Examples

### Using Default Seasons

```python
from pcmdi_metrics.variability_mode import NAM, PDO, AMO

# NAM: Automatically analyzes all 4 seasons
results = NAM(model_ds)
print(results['DJF']['diagnostics']['frac'])
print(results['JJA']['diagnostics']['frac'])

# PDO: Automatically uses monthly analysis
results = PDO(model_ds)
print(results['monthly']['diagnostics']['frac'])

# AMO: Automatically uses yearly analysis
results = AMO(model_ds)
print(results['yearly']['diagnostics']['frac'])
```

### Overriding Default Seasons

Users can always override the defaults:

```python
# Compute PDO for specific seasons instead of monthly
results = PDO(model_ds, seasons=['DJF', 'JJA'])
print(results['DJF']['diagnostics']['frac'])

# Compute NAM for only winter
results = NAM(model_ds, seasons=['DJF'])
print(results['DJF']['diagnostics']['frac'])

# Compute AMO with monthly analysis
results = AMO(model_ds, seasons=['monthly'])
print(results['monthly']['diagnostics']['frac'])
```

## Implementation Details

The defaults are set in the function signatures:

```python
# Atmospheric modes
def NAM(
    model_ds,
    seasons: List[str] = ["DJF", "MAM", "JJA", "SON"],  # 4 seasons
    ...
):
    ...

# Ocean modes  
def PDO(
    model_ds,
    seasons: List[str] = ["monthly"],  # Monthly analysis
    ...
):
    ...

# Multidecadal modes
def AMO(
    model_ds,
    seasons: List[str] = ["yearly"],  # Yearly analysis
    ...
):
    ...
```

## Valid Season Options

All modes support:
- Standard seasons: `'DJF'`, `'MAM'`, `'JJA'`, `'SON'`
- Monthly: `'monthly'`
- Yearly: `'yearly'`

Users can specify any combination:
```python
# Multiple seasons
results = NAM(model_ds, seasons=['DJF', 'JJA'])

# Single season
results = NAM(model_ds, seasons=['DJF'])

# Monthly analysis
results = NAM(model_ds, seasons=['monthly'])

# Yearly analysis
results = NAM(model_ds, seasons=['yearly'])
```

## Comparison with Driver Script

The driver script uses the same underlying computation functions but requires explicit season specification in the parameter file:

**Driver parameter file**:
```python
seasons = ['DJF']  # Must explicitly specify
```

**API**:
```python
results = NAM(model_ds)  # Uses sensible defaults automatically
```

## References

### PDO/NPGO Monthly Analysis
- Mantua, N. J., et al. (1997). "A Pacific Interdecadal Climate Oscillation with Impacts on Salmon Production." Bulletin of the American Meteorological Society.
- Di Lorenzo, E., et al. (2008). "North Pacific Gyre Oscillation links ocean climate and ecosystem change." Geophysical Research Letters.

### AMO Yearly Analysis
- Enfield, D. B., et al. (2001). "The Atlantic Multidecadal Oscillation and its relation to rainfall and river flows in the continental U.S." Geophysical Research Letters.
- Knight, J. R., et al. (2005). "A signature of persistent natural thermohaline circulation cycles in observed climate." Geophysical Research Letters.

### Atmospheric Modes Seasonal Analysis
- Hurrell, J. W. (1995). "Decadal Trends in the North Atlantic Oscillation: Regional Temperatures and Precipitation." Science.
- Thompson, D. W. J., and Wallace, J. M. (2000). "Annular Modes in the Extratropical Circulation. Part I: Month-to-Month Variability." Journal of Climate.

## Summary

The API defaults are designed to:
1. ✅ Match scientific conventions for each mode
2. ✅ Provide sensible out-of-the-box behavior
3. ✅ Remain flexible (users can override)
4. ✅ Follow established research practices

Users who need different timescales can easily override the defaults while still benefiting from the convenient API.
