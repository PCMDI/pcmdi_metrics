# PCMDI/pcmdi_metrics — Copilot onboarding instructions

This file tells an automated coding agent how to work efficiently in this repository. Trust these instructions and only run repository-wide searches when the guidance below is incomplete or contradicted by the current repository state.

## High level summary
- What this repo does: The PCMDI Metrics Package (PMP) is an open-source Python package that computes objective summary metrics and diagnostics for Earth System Models (ESMs) and observations. It provides drivers, analysis routines, plotting utilities, and example/demo notebooks focused on climate model metrics (mean climate, ENSO, MJO, monsoons, precipitation statistics, cloud feedbacks, sea ice, extremes, etc.).
- Size & type: A Python library + docs and tests. Primary language: Python (>=3.10, up to <3.14). Small amount of shell scripts for docs and CI.
- Key frameworks/runtime: Python, conda-forge packages (cartopy, xarray/xcdat, netcdf4, rasterio, shapely, xclim), Sphinx for docs, pre-commit hooks for formatting/linting, GitHub Actions for CI.

## Build & validation (always follow these exact steps first)
These are the canonical steps to bootstrap, build, lint, and test changes. The CI workflow (.github/workflows/build_workflow.yml) uses a conda-based environment created from conda-env/ci.yml and runs pre-commit and the build matrix on Python 3.10–3.13.

1) Bootstrap (create the environment)
- Always use conda-forge. Recommended commands:
  - conda env create -f conda-env/ci.yml -n pcmdi_metrics_dev
  - conda activate pcmdi_metrics_dev
- NOTE: conda env files reference many compiled packages (cartopy, rasterio, shapely). Installation can be slow and may require system libraries. Use the provided conda-env/ci.yml to match CI.

2) Install the package
- Preferred (editable): python -m pip install -e .
  - The project uses a pyproject.toml with a custom backend (backend-path = ["_custom_build"]). If editable install fails, try: python -m pip install .
- Verify installation: python -c "import pcmdi_metrics; print(pcmdi_metrics.__version__)" (package exposes metadata)

3) Lint & formatting (pre-commit)
- Pre-commit is enforced in CI. Run locally before pushing:
  - pre-commit install
  - pre-commit run --all-files
- Configured formatters/linters: black, isort, flake8 (see .pre-commit-config.yaml and .flake8.cfg). flake8 max-line-length is 119 (see .flake8.cfg).
- CI runs pre-commit under Python 3.13; use the same or ensure your local pre-commit hooks use the same versions.

4) Run tests
- Two supported ways:
  - Lightweight (pytest): pytest -q
    - Good for incremental work and fast feedback. Use -k to select tests. Many tests rely only on Python packages already in the conda env.
  - Legacy test runner (matches some older test automation): python run_tests.py
    - This uses testsrunner.TestRunnerBase and may perform extra setup (download sample data). Use when requested by maintainers or when reproducing CI behavior.
- Note: Some tests depend on heavy geospatial packages and sample data files; running the full test suite locally can be slow and may require additional system libraries. Prefer running a targeted subset while developing.

5) Docs (optional for changes affecting docs)
- Docs build requires sphinx and dev packages (see conda-env/dev.yml). To build docs locally:
  - conda env create -f conda-env/dev.yml -n pcmdi_metrics_dev_docs
  - conda activate pcmdi_metrics_dev_docs
  - cd docs
  - make clean && make html
- GitHub Actions deploy docs automatically on merges to main.

6) CI (replicate when needed)
- The canonical CI is .github/workflows/build_workflow.yml and uses Miniforge + environment-file conda-env/ci.yml and runs on ubuntu-latest.
- To reproduce locally use act (or run on a VM) configured to match ubuntu-latest and Python matrix or run the same conda env steps and commands in a shell.

Common gotchas & mitigations
- Heavy compiled dependencies: cartopy, rasterio, shapely, etc. Use conda-forge and allow extra time for installation. If install fails on pip wheel build, prefer conda install from conda-forge.
- Custom build backend: pyproject.toml uses a backend wrapper in _custom_build — avoid changing build configuration unless necessary and test install after changes.
- Pre-commit formatting: black may reformat many files — run pre-commit before opening PR to avoid CI failures.
- Tests requiring sample data or external resources: some legacy tests download or expect share/test data. If a test fails due to missing data, check tests or run_tests.py options (UPDATE_TESTS env var) or run targeted pytest selection.

## Project layout & important files
- Top-level files you will use frequently:
  - README.md — project description and usage
  - pyproject.toml — packaging and build config (PEP 621); dynamic versioning; custom backend in _custom_build
  - conda-env/ci.yml — canonical conda environment used by CI (always use this for CI parity)
  - .github/workflows/build_workflow.yml — CI matrix and steps (pre-commit, conda setup, install, test)
  - .pre-commit-config.yaml — formatting and lint rules (black, isort, flake8)
  - .flake8.cfg — flake8 configuration (max-line-length 119)
  - docs/ — Sphinx docs and build scripts; docs/README.md has instructions for local preview
  - tests/ — unit tests (pytest style) and several legacy/deprecated tests
  - run_tests.py — legacy test harness used by some maintainers
  - pcmdi_metrics/ — main Python package (modules, drivers, scripts)

- How to find where to change code:
  - Quick rule: pcmdi_metrics/<area> contains modules by function (diurnal, enso, cloud_feedback, mean_climate, io, utils, graphics, etc.). Search for the function/class name when given a task.
  - Use the package entry points defined in pyproject.toml (project.scripts) to find driver scripts and mapping to modules.

- Tests & static checks run in CI before merge:
  - pre-commit hooks (black, isort, flake8) — fail-fast
  - Conda environment consistency and package install
  - Test matrix across Python 3.10–3.13 (see build_workflow.yml)

Explicit validation checks you can run locally to mirror CI:
- Create the conda env from conda-env/ci.yml and activate it
- pip install -e .
- pre-commit run --all-files
- pytest -q
- Build docs (if relevant): cd docs && make html

## Steps to follow when making a change (agent workflow)
1. Read this file (trust it). Only run repo-wide searches if you cannot find required information here.
2. Create a feature branch. Make minimal changes and include a clear commit message.
3. Run pre-commit hooks locally. Fix formatting/lint issues until pre-commit passes.
4. Run the relevant subset of tests (pytest -k <name>) and make sure they pass locally.
5. Run full test suite or run_tests.py only if maintainers expect it or if the change touches core functionality.
6. Run docs build locally if your change affects documentation or API docs.
7. Open a PR against main. Include short description, testing performed (commands and results), and note any CI caveats (heavy packages, external data requirements).

## Tips for rapid iteration
- Use targeted pytest selection (-k, -m) to run only relevant tests while developing.
- If install from source is slow, consider creating a conda environment once and reusing it across iterations.
- Respect the formatter/linter configuration to avoid churn in PRs.
- If a failing CI job references missing system dependencies, check whether conda installation (conda-forge) fixes it before adding workarounds.

## Final rules for the automated agent
- Always prefer conda-env/ci.yml for environment replication and the CI workflow for validation.
- Always run pre-commit locally (pre-commit run --all-files) before pushing code.
- Do not change packaging/build backend (_custom_build) or top-level CI files unless the change is explicitly related and tests/documentation are updated.
- Add or update tests for behavioral changes. If you cannot run heavy tests locally, add focused unit tests that avoid large compiled deps where possible.
- If any step here contradicts a file in the repository, run a targeted search to resolve the discrepancy and update this file (with a maintainer-reviewed PR).