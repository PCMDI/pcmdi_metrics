# CLAUDE.md

## Project Overview

The PCMDI Metrics Package (PMP) is a scientific Python package for evaluating Earth System Models (ESMs). It provides objective comparisons of climate models with observations across multiple metrics including climatology, variability modes (ENSO, MJO), precipitation patterns, cloud feedback, and more.

## Critical Constraints
**MUST NOT alter existing computational logic** - metrics are published/validated. Changing computational logic invalidates scientific results.
**MUST maintain backward compatibility** - driver scripts and parameter files used in operational workflows
**MUST use xCDAT, not CDAT** - CDAT is fully deprecated

## Architecture Overview

### Module Organization
- Metric-specific modules under `pcmdi_metrics/` (e.g., `mean_climate/`, `enso/`, `mjo/`)
- Each metric has `lib/` (core functions), `param/` (examples), optionally `*_driver.py`
- Shared utilities in `io/`, `utils/`, `stats/`, `graphics/`

### Driver scripts (Legacy Interface)
- Existing driver scripts (e.g., `mean_climate_driver.py`) are legacy interfaces used by operational workflows and MUST NOT BREAK.
- Driver scripts read parameter files (`.py` or `.json`) that define paths, variables, and options.
- New metrics should use standard Python API structure: importable functions, not standalone executable scripts.
- Always maintain backward compatibility: add new optional params with defaults, don't remove/change existing behavior.

### API Design (New Development)

#### API Design Principles:
- Accept standard data structures (xarray.Dataset, numpy arrays)
- Return standard data structures (dict, DataFrame, Dataset)
- Use keyword arguments for options with sensible defaults
- Type hints required for main functions, optional for helpers
- Comprehensive docstrings
- Minimal side effects (no global state, file I/O optional)

#### PMP API Code Quality:
- Use NumPy style docstrings with a short one-line description at the top of each function.
- Include citations for any scientific references used.
- Prioritize readability and correctness over premature optimization.
- Use classes minimally.
- Avoid hard coding values, especially if units or order may vary among different datasets.
- Prioritize API flexibility for commonly used climate model and observation datasets. (i.e., functions should handle data inputs with different grids or non-standard units).
- See `pcmdi_metrics.mjo.compute_mjo_ewr_from_dataset` in the docs for a well-designed API example.

### Key Dependencies
- All CDAT functionality has been transitioned to **xCDAT** (imported as `xcdat`).
- Do not introduce any new CDAT dependencies or use CDAT-specific APIs.

### JSON Output Structure
Metrics saved as JSON with nested structure: DIMENSIONS (metadata about structure), RESULTS (nested by model/reference/region/statistic/season), PROVENANCE (tracking). See existing outputs for schema.

## Development Process

### Testing
- Test driver scripts with sample parameter files to ensure backward compatibility.
- For expensive computations, test on a data slice (temporal subset or coarser grid) appropriate to the metric's science.
- Always run pytest before committing changes.
- Always run `pre-commit run --all-files` before committing changes.

## Git Workflow
- Never push changes directly to Main branch
- Reference issue in new branches and pull requests
- Follow this pattern for naming new branches: <issue-number>_<username>_<change-description>
- Always use a clear, descriptive commit message and reference any relevant issue numbers.

## Common Pitfalls (gotchas)
- **Changing existing logic**: If changes are needed, describe the issue, show current vs proposed behavior, and wait for explicit approval before proceeding.

**Avoid**:
- Single-use helper functions
- Over-engineering or premature abstractions