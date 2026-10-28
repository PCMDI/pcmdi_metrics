# Repository Guidelines

## Project Structure & Module Organization

`pcmdi_metrics/` contains the Python package, organized by climate metric (e.g., `mean_climate/`, `enso/`, `effective_resolution/`). Subpackages typically include drivers, `lib/` calculations, and parameter examples. Shared functionality lives in `io/`, `utils/`, and `graphics/`; `cmec/` provides integration wrappers.

Unit tests live in `tests/`, with additional metric-specific tests inside subpackages. `docs/` contains Sphinx sources; `doc/jupyter/Demo/` contains notebook demonstrations. `sample_setups/` holds configuration examples, and `share/` supplies reference data, region definitions, and graphics assets.

## Build, Test, and Development Commands

Run from the repository root:

```bash
conda env create -f conda-env/dev.yml -n pcmdi_metrics_dev
conda activate pcmdi_metrics_dev
python -m pip install --no-build-isolation --no-deps -e .
```

These commands install scientific dependencies from conda-forge and install PMP in editable mode. Use `conda-env/ci.yml` for CI parity.

- `pre-commit install`: enable commit hooks.
- `pre-commit run --all-files`: run formatting and lint checks before committing.
- `pytest`: run the full discovered suite, including subpackage tests.
- `pytest tests/test_qc.py`: run a focused test module during development.
- `make -C docs html`: build documentation in `docs/_build/html/`.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions/modules, and `PascalCase` classes. Black and isort use 88-character lines; Flake8 configuration lives in `.flake8.cfg`. Add type hints to main API functions, NumPy-style docstrings, and citations for scientific algorithms. Prefer importable functions accepting standard xarray/NumPy structures and keyword options with defaults.

## Testing Guidelines

Use pytest and pytest-cov. Name files `test_*.py` and functions `test_*`. Cover changed behavior, edge cases, and driver compatibility with sample parameters; use scientifically appropriate small datasets for expensive calculations. Pytest excludes `tests/deprecated/` and generates terminal, HTML, and XML coverage reports under `tests_coverage_reports/`. No numerical coverage threshold is configured. Run relevant tests before committing.

## Commit & Pull Request Guidelines

History uses descriptive subjects such as “Add …”, “Fix …”, and “Reorganize …”; no uniform Conventional Commits scheme is enforced. Reference relevant issues. Use branches named `<issue-number>_<username>_<change-description>` and submit PRs to `main`. Describe behavior changes and validation, link issues, include tests, and update documentation for new functionality. Require passing CI and review; squash and rebase before merging.

## Scientific & Compatibility Constraints

Follow `docs/contributing.rst`: obtain explicit approval before changing validated computational logic or adding dependencies. Preserve driver/parameter compatibility and CMEC output formats. Use xCDAT for new code and CF-compliant input data. Contributions use the BSD-3-Clause license.
