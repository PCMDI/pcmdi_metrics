# PCMDI Metrics Package (PMP) - Claude AI Development Guidelines

## Project Overview

The PCMDI Metrics Package (PMP) is a scientific Python package for evaluating Earth System Models (ESMs). It provides objective comparisons of climate models with observations across multiple metrics including climatology, variability modes (ENSO, MJO), precipitation patterns, cloud feedback, and more.

**Repository**: https://github.com/PCMDI/pcmdi_metrics  
**Lead Institution**: Lawrence Livermore National Laboratory (LLNL)  
**License**: BSD 3-Clause

## Core Development Principles

### 1. Code Modification Policy

**CRITICAL**: Do NOT alter the logic of existing code unless explicitly instructed.

- **Preserve existing algorithms**: The metrics calculations have been validated and published in peer-reviewed literature. Changing computational logic can invalidate scientific results.
- **Ask before refactoring**: If you identify potential improvements to existing algorithms or statistical calculations, describe the issue and ask for permission before making changes.
- **Bug fixes only**: Only modify existing logic when fixing a clear bug, and document the change thoroughly.

### 2. Workflow Compatibility - CRITICAL

**DO NOT break existing workflows, especially driver scripts.**

**Important Context**: Driver scripts (e.g., `mean_climate_driver.py`, `enso_driver.py`, `variability_modes_driver.py`) are **legacy interfaces** that many research groups and operational workflows depend on. While they are not required for new development, existing driver scripts must maintain consistent behavior for backward compatibility.

**Requirements**:
- **Preserve existing command-line interfaces**: Do not change required arguments, remove options, or alter default behavior
- **Maintain driver script functionality**: Any changes to underlying functions must not break how drivers call them
- **Backward compatibility is mandatory**: Existing parameter files and workflows must continue to work
- **Additive changes only**: New features should be added as optional parameters with sensible defaults
- **Test driver scripts**: Always verify that driver scripts run successfully after making changes

**If you need to modify driver behavior**:
1. Add new optional parameters rather than changing existing ones
2. Use feature flags or version parameters for new behavior
3. Maintain the old behavior as the default
4. Document migration paths clearly
5. Get explicit approval before making any driver-level changes

**Example of acceptable change**:
```python
# GOOD: Adding optional parameter with backward-compatible default
def process_data(ds, method='old', new_option=False):
    if new_option:
        # New functionality
        pass
    else:
        # Preserve existing behavior (default)
        pass
```

**Example of unacceptable change**:
```python
# BAD: Changing required parameters or removing options
def process_data(ds, method):  # Removed default value
    # Different implementation that breaks existing calls
    pass
```

### 3. Function and Helper Creation

**Minimize unnecessary abstractions**. Only create helper functions when:
- The same logic is used in 3+ places (DRY principle)
- The function significantly improves code readability
- Explicitly requested by the developer

**Avoid**:
- Single-use helper functions
- Over-engineering or premature abstractions
- Extracting code into helpers "for cleanliness" without functional benefit

### 4. Documentation Standards

**All docstrings MUST use SciPy/NumPy style** for consistency across the codebase.

#### SciPy Docstring Format

```python
def function_name(param1, param2, param3=None):
    """
    Short one-line description.

    Longer description if needed, explaining what the function does,
    its purpose, and any important context.

    Parameters
    ----------
    param1 : type
        Description of param1.
    param2 : str or int
        Description of param2.
    param3 : xr.Dataset, optional
        Description of param3, by default None

    Returns
    -------
    return_type
        Description of return value.

    Raises
    ------
    ExceptionType
        When this exception is raised.

    Notes
    -----
    Additional technical details, assumptions, or caveats.

    Examples
    --------
    >>> result = function_name(arg1, arg2)
    >>> print(result)
    expected output

    References
    ----------
    .. [1] Author, "Title", Journal, Year.
    """
```

**Key sections** (in order):
1. Short summary (one line)
2. Extended summary (optional, if needed)
3. Parameters
4. Returns
5. Raises (if applicable)
6. Warnings (if applicable)
7. See Also (if applicable)
8. Notes (if applicable)
9. Examples (encouraged)
10. References (if applicable)

**Examples of existing good docstrings**:
- `pcmdi_metrics/utils/land_sea_mask.py::create_land_sea_mask()`
- `pcmdi_metrics/mean_climate/lib/compute_metrics.py::compute_metrics()`

## Code Style and Quality

### Formatting

This project uses:
- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- **flake8** for linting (max line length: 119)

Run pre-commit hooks before committing:
```bash
pre-commit run --all-files
```

### Type Hints

Use type hints for function signatures:
```python
from typing import Optional, Union, Dict, Any
import xarray as xr

def process_data(
    ds: xr.Dataset,
    var_name: str,
    threshold: Optional[float] = None
) -> Dict[str, Any]:
    """Function with proper type hints."""
    pass
```

### Import Organization

Follow this order (enforced by isort):
1. Standard library imports
2. Third-party imports (numpy, xarray, xcdat, etc.)
3. Local package imports

```python
import os
import sys
from typing import Optional

import numpy as np
import xarray as xr
import xcdat as xc

from pcmdi_metrics import stats
from pcmdi_metrics.io import xcdat_dataset_io
```

## Key Technologies and Libraries

### Core Dependencies
- **xarray**: Primary data structure for N-dimensional arrays
- **xcdat (xCDAT)**: Extension of xarray for climate data analysis (successor to CDAT)
- **numpy**: Numerical computations

**Important**: CDAT is a legacy dependency and is **no longer used**. All CDAT functionality has been transitioned to **xCDAT**. Do not introduce any new CDAT dependencies or use CDAT-specific APIs.

### Common Patterns

#### Working with xarray Datasets
```python
# Always check if input is Dataset or DataArray
def process_data(data: Union[xr.Dataset, xr.DataArray], var: str = "variable"):
    if isinstance(data, xr.DataArray):
        ds = data.to_dataset(name=var)
    else:
        ds = data.copy(deep=True)
    
    # Add missing bounds
    ds = ds.bounds.add_missing_bounds()
    
    # Process...
    return ds
```

#### Spatial/Temporal Operations with xCDAT
```python
# Use xcdat methods for climate-specific operations
import xcdat as xc

# Temporal operations
dm_am = dm.temporal.average(var)
dm_seasonal = dm.temporal.group_average(var, freq="season")

# Spatial operations
dm_spatial = dm.spatial.average(var, axis=["X", "Y"])

# Get spatial weights
weights = ds.spatial.get_weights(axis=["X", "Y"])

# Regridding with xCDAT
target_grid = xc.create_uniform_grid(-90, 90, 4.0, 0, 360, 5.0)
ds_regridded = ds.regridder.horizontal(var, target_grid)
```

#### Standard Python API Design (Recommended for New Metrics)
```python
# Design functions to be importable and reusable
from typing import Dict, Any, Optional
import xarray as xr

def compute_my_metric(
    model_data: xr.Dataset,
    obs_data: xr.Dataset,
    variable: str,
    reference_period: Optional[tuple] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Compute my metric following modern API design.
    
    Parameters
    ----------
    model_data : xr.Dataset
        Model dataset
    obs_data : xr.Dataset
        Observational dataset
    variable : str
        Variable name to analyze
    reference_period : tuple, optional
        Start and end years for reference period
    **kwargs
        Additional options
    
    Returns
    -------
    Dict[str, Any]
        Dictionary containing computed metrics
    """
    # Implementation using xarray/xCDAT
    pass
```

## Project Structure

```
pcmdi_metrics/
├── mean_climate/       # Mean climate metrics
├── variability_mode/   # Modes of variability (ENSO, MJO, etc.)
├── monsoon_wang/       # Monsoon metrics (Wang method)
├── monsoon_sperber/    # Monsoon metrics (Sperber method)
├── enso/              # ENSO-specific metrics
├── mjo/               # Madden-Julian Oscillation metrics
├── precip_distribution/ # Precipitation distribution metrics
├── precip_variability/ # Precipitation variability across timescales
├── extremes/          # Climate extremes metrics
├── sea_ice/           # Sea ice metrics
├── cloud_feedback/    # Cloud feedback metrics
├── diurnal/           # Diurnal cycle metrics
├── drcdm/             # Decision-Relevant metrics
├── io/                # Input/output utilities
├── stats/             # Statistical functions
├── utils/             # Utility functions
├── graphics/          # Plotting and visualization
└── viewer/            # Web-based results viewer
```

## Testing

- Tests are in the `tests/` directory
- Run tests with: `pytest tests/`
- Add tests for new functionality
- Ensure existing tests pass before committing
- **Critical**: Test driver scripts to ensure workflows are not broken
- Run driver scripts with sample data to verify end-to-end functionality
- Check that parameter/configuration files used by drivers still work

## Git Workflow

### Commit Messages

Use clear, descriptive commit messages:
```
component: Brief description

Longer explanation if needed. Reference issue numbers.

Fixes #123
```

Examples from recent commits:
- `clean up`
- `pre-commit fix`
- `add identifier`

### Branches

- `main`: Production-ready code
- Feature branches: Create descriptive branch names

## Common Tasks

### Adding a New Metric

**Modern Approach (Recommended for New Development)**:
1. Create a new subdirectory under `pcmdi_metrics/` if it's a new metric category
2. Implement as a **standard Python API** (importable functions/classes)
3. Use xarray/xCDAT for data structures and operations
4. Place core computation functions in a `lib/` subdirectory
5. Add comprehensive tests in `tests/`
6. Update documentation in `doc/` or `docs/`
7. Provide usage examples in Jupyter notebooks

**Legacy Approach (Only for Consistency with Existing Metrics)**:
- Include a driver script (e.g., `*_driver.py`) only if it matches the pattern of existing metrics
- Add script entry point in `pyproject.toml` if creating a driver

**New Development Philosophy**:
- **Prefer standard Python API over driver scripts** for new metrics
- Make functions importable and usable in Python scripts/notebooks
- Driver scripts are legacy interfaces - new metrics should be accessible via `import pcmdi_metrics.your_metric`
- Design for programmatic use first, command-line use second

### Modifying Existing Metrics

1. **ALWAYS** verify the change won't affect published results
2. **Test driver scripts**: Ensure driver scripts still work with the modified code
3. Add versioning or a flag to maintain backward compatibility if needed
4. Update tests to cover the new behavior while ensuring old behavior still passes
5. Document changes in docstrings and comments
6. Consider whether results need recomputation
7. Verify that parameter files used by drivers remain compatible

### Adding Utility Functions

1. Place in appropriate module under `pcmdi_metrics/utils/`
2. Add to `__init__.py` for public API exposure
3. Include comprehensive docstring with examples
4. Add unit tests in `tests/`

## Data Handling

### File Paths and Data Access

- Use `pcmdi_metrics.resources` for package data access
- Expect CF-compliant NetCDF files as input
- Handle missing data appropriately with xarray's built-in methods

### Provenance Tracking

Many functions include provenance tracking via `generateProvenance()`. Maintain this pattern when adding new metrics.

## Performance Considerations

- Use vectorized numpy/xarray operations instead of loops when possible
- Be mindful of memory usage with large climate datasets
- Consider chunking for dask-enabled parallel processing
- Profile before optimizing

## Development Best Practices

### For New Metrics
1. **Design as a Python module** with importable functions, not a standalone script
2. **Use xarray and xCDAT** for all data operations
3. **No CDAT dependencies** - it's fully deprecated
4. **Provide Jupyter notebook examples** showing usage
5. **Write comprehensive unit tests**
6. **Document with SciPy-style docstrings**

### For Modifying Existing Code
1. **Maintain backward compatibility** for driver scripts
2. **Preserve existing computational logic** unless fixing bugs
3. **Test both programmatic API and driver scripts** (if applicable)
4. **Update but don't break existing workflows**

## Questions and Clarifications

When uncertain about:
- **Algorithm changes**: Always ask before modifying computational logic
- **Helper function necessity**: Describe the use case and ask if abstraction is warranted
- **Breaking changes**: Discuss impact on existing users and results
- **Scientific validity**: Defer to domain experts on climate science questions
- **API design for new metrics**: Prefer Python module/function approach over driver scripts

## Resources

- **Documentation**: http://pcmdi.github.io/pcmdi_metrics/
- **Issues**: https://github.com/PCMDI/pcmdi_metrics/issues
- **PCMDI Website**: https://pcmdi.llnl.gov/
- **Contact**: pcmdi-metrics@llnl.gov

## Important Notes

1. **Scientific Integrity**: This package produces results used in published research and CMIP assessments. Code changes must maintain scientific validity.

2. **Workflow Stability**: Research groups have operational workflows and scripts that depend on driver interfaces remaining stable. Any change that breaks existing workflows is unacceptable without explicit approval and migration plan.

3. **Backward Compatibility**: Many users rely on consistent metric calculations across CMIP phases. Breaking changes require careful consideration and communication.

4. **Driver Scripts Are Legacy Interfaces**: Existing driver scripts are production interfaces used by the community and must remain stable. However, **new development should use standard Python API patterns** rather than creating new driver scripts.

5. **Use xCDAT, Not CDAT**: CDAT is deprecated. All functionality has been migrated to xCDAT. Never introduce CDAT dependencies in new code.

6. **Modern Python API Design**: New metrics should be designed as importable functions/classes that can be used programmatically in Python scripts and notebooks, not as standalone executables.

7. **CF Compliance**: Input data is expected to follow CF conventions. Include appropriate checks and error messages for non-compliant data.

8. **Citation**: When using this package, cite:
   - Lee et al. (2024), GMD, https://doi.org/10.5194/gmd-17-3919-2024

---

*Last updated: 2026-07-21*
