# EOF Classification for EA and SCA Patterns

## Overview

This tool classifies model Empirical Orthogonal Functions (EOFs 2–4 of JFM
sea-level pressure) as **East Atlantic (EA)** or **Scandinavian (SCA)**
patterns.  It addresses the identification problem: given a model's EOF2,
EOF3, and EOF4, which one corresponds to EA and which to SCA?

Model EOFs do not always appear at the expected ordinal position — the EA
pattern is typically EOF2 and SCA is typically EOF3 (of the NAO domain),
but in many CMIP6 models they swap, mix, or shift to EOF4.  This tool
resolves that ambiguity using three independent classification methods
and a consensus layer.

## Methods

### 1. Subspace Projection (shift-tolerant)

Projects the observed EA and SCA control patterns onto the subspace
spanned by {EOF2, EOF3, EOF4} using weighted least squares.  The
projection allows small phase shifts in latitude and longitude to
accommodate differences between model and observed pattern locations.
For each EOF, the relative magnitude of its coefficient in the EA fit
versus the SCA fit determines the classification.

### 2. Correlation + Geographic Tests

Scores each EOF independently on a 100-point scale combining four
diagnostics:

- **Pattern correlation** with EA and SCA controls (0–40 points each)
- **Orthogonalized correlation** with the component unique to each
  pattern (0–40 points each)
- **Geographic tests** based on regional pressure anomalies over
  Greenland, Ireland, and Scandinavia (0–10 points each)

### 3. K-means Clustering

Clusters all EOFs using area-weighted, sign-oriented, row-normalized
features.  Clusters are labeled EA, SCA, or OTHER by their correlation
with the control patterns.  Each EOF receives a soft membership score
indicating its affinity to each cluster type.

By default, this method applies **pre-computed cluster centers** shipped
with the tool (trained on the CMIP6 ensemble with 20CR-V2 controls).
This means classification works on a single model without needing access
to the full ensemble.  See [K-means Retraining](#k-means-retraining)
below if you need to regenerate centers.

### Consensus

For each EOF, the three methods each produce a label (EA or SCA) and a
confidence score in [0, 1].  The consensus layer combines them:

- **Label**: simple majority vote (2/3 or 3/3 agree); no majority →
  UNCLASSIFIED
- **Confidence**: (fraction of methods agreeing) × (mean confidence of
  agreeing methods)
- **Quality levels**:

| Quality   | Confidence range | Warning flag |
|-----------|-----------------|--------------|
| robust    | ≥ 0.7           | no           |
| medium    | 0.5 – 0.7       | no           |
| weak      | 0.3 – 0.5       | WARNING      |
| very weak | < 0.3           | WARNING      |

Because model EOFs may span a subspace that mixes the reference patterns,
multiple EOFs can receive the same label when their projections are not
cleanly separable.  This is reported transparently rather than forced
into a one-to-one assignment.

## Requirements

- Python 3.8+
- NumPy
- Xarray
- scikit-learn (only required for [k-means retraining](#k-means-retraining);
  not needed when applying pre-computed centers)

## Inputs

The tool requires three types of input, all in netCDF format:

1. **Model EOF files** — one file per EOF mode (2, 3, 4) per model,
   each containing a 2-D (lat × lon) spatial pattern.  Files are
   discovered via glob patterns.

   **Filename convention**: By default, model EOF files are expected to follow the
   pattern `EOF{n}_psl_JFM_cmip6_<model_name>.nc` (where `{n}` is 2, 3, or 4). The
   model name is extracted from the portion between the prefix and the `.nc`
   extension. If your files use a different naming scheme, either rename them or
   update `EOF_GLOBS` in the CONFIG section to match your convention.

   **Note**: By default,'eof_classification()" runs on a single CMIP6 model
   included in 'data/example_eofs' so you can try the tool out of the box. This
   example data is for **demonstration only**. To classify your own data, change
   'MODEL_EOF_DIR' in the CONFIG section or pass 'eofs_globs' to
   'eof_classification()' to point at your own files.

2. **Control patterns** — observed EA and SCA reference patterns from
   reanalysis.  The default controls are from 20CR-V2, which among the
   reanalyses tested shows the clearest eigenvalue separation between
   the EA and SCA modes (per the North et al. 1982 test).  These are
   included in the `data/` directory.

3. **K-means centers file** (JSON) — pre-computed cluster centers.
   Included in the `data/` directory.  See
   [K-means Retraining](#k-means-retraining) if you need to regenerate.

**Note**: By default, 'eof_classification()" runs on a single CMIP6 model
included in 'data/example_eofs' so you can try the tool out of the box. This
example data is for **demonstration only**. To classify your own data,
change 'MODEL_EOF_DIR' in the CONFIG section or pass 'eofs_globs'
to 'eof_classification()' to point at your own files.

## Usage

### Standalone (command line)

Edit the CONFIG section at the top of `eof_classification.py` to set
paths, then run:

```bash
python eof_classification.py
```

### Programmatic (from Python / PMP)

```python
from eof_classification import eof_classification

results = eof_classification(
    ea_ctrl_file="data/EA_psl_EOF2_JFM_obs_1969-2012.nc",
    sca_ctrl_file="data/SCA_psl_EOF2_JFM_obs_1969-2012.nc",
    eof_globs={
        2: "/path/to/EOF2_psl_JFM_cmip6_*.nc",
        3: "/path/to/EOF3_psl_JFM_cmip6_*.nc",
        4: "/path/to/EOF4_psl_JFM_cmip6_*.nc",
    },
    kmeans_centers_file="data/kmeans_centers_20CR-V2_CMIP6.json",
    output_root="eof_classification",
)
```

All parameters are optional — when omitted, they fall back to the
CONFIG defaults at the top of the module.

### Return Value

`eof_classification()` returns a dictionary:

```python
{
    "ModelName": {
        2: {
            "label": "EA",          # EA, SCA, or UNCLASSIFIED
            "confidence": 0.72,     # consensus confidence [0, 1]
            "quality": "robust",    # robust, medium, weak, or very weak
            "methods": {
                "subspace":    {"label": "EA",  "confidence": 0.85},
                "correlation": {"label": "EA",  "confidence": 0.76},
                "kmeans":      {"label": "EA",  "confidence": 0.91},
            },
        },
        3: { ... },
        4: { ... },
    },
    ...
}
```

## Output Files

Two files are written to the working directory (or the path specified
by `output_root`):

- **`eof_classification_consensus.tsv`** — tab-separated, machine-readable
- **`eof_classification_consensus.txt`** — fixed-width, human-readable

Each row represents one EOF of one model:

| Column            | Description                                    |
|-------------------|------------------------------------------------|
| Model             | Model name                                     |
| EOF               | EOF mode (EOF2, EOF3, or EOF4)                 |
| Subspace_label    | Subspace method classification                 |
| Subspace_conf     | Subspace confidence [0, 1]                     |
| Correlation_label | Correlation method classification              |
| Correlation_conf  | Correlation confidence [0, 1]                  |
| Kmeans_label      | K-means classification                         |
| Kmeans_conf       | K-means confidence [0, 1]                      |
| Consensus_label   | Majority-vote label                            |
| Consensus_conf    | Consensus confidence [0, 1]                    |
| Quality           | robust / medium / weak / very weak             |
| Warning           | WARNING flag if quality is weak or very weak    |

## Configuration Reference

Key parameters in the CONFIG section:

| Parameter          | Default      | Description                              |
|--------------------|-------------|------------------------------------------|
| `EA_CTRL_FILE`     | (path)      | Path to EA control pattern netCDF        |
| `SCA_CTRL_FILE`    | (path)      | Path to SCA control pattern netCDF       |
| `EA_SIGN`/`SCA_SIGN` | +1.0/−1.0 | Sign convention applied at load time    |
| `CTRL_REANALYSIS`  | "20CR-V2"   | Label for provenance checking            |
| `LAT_RANGE`        | (20, 90)    | Latitude bounds for domain restriction   |
| `SMOOTH_SIGMA_DEG` | 4.0         | Gaussian smoothing width (degrees)       |
| `SHIFT_LON_MAX_DEG`| 15.0        | Longitudinal shift tolerance (degrees)   |
| `SHIFT_LAT_MAX_DEG`| 6.0         | Latitudinal shift tolerance (degrees)    |
| `RIDGE`            | 0.0         | Tikhonov regularisation (0 = OLS)        |
| `KMEANS_CENTERS_FILE` | (path)   | Path to pre-computed k-means centers     |

## K-means Retraining

The pre-computed k-means centers shipped with this tool were trained on
the CMIP6 multi-model ensemble using 20CR-V2 control patterns.  **For
normal classification, retraining is not necessary** — the saved centers
are applied automatically.

Retraining is only needed if you want to use:
- A different reanalysis for the control patterns, or
- A different model ensemble (e.g., CMIP7)

### Requirements for Retraining

- **scikit-learn** must be installed (`pip install scikit-learn` or
  `conda install scikit-learn`)
- EOF files from a **full multi-model ensemble** (~20+ models) must be
  available and pointed to by the `eof_globs` parameter or `EOF_GLOBS`
  config variable

### How to Retrain

1. Set `EA_CTRL_FILE` and `SCA_CTRL_FILE` to the new control patterns.
2. Set `CTRL_REANALYSIS` and `CMIP_TAG` to match.
3. Set `EOF_GLOBS` to point to EOF files from the full ensemble.
4. Delete or rename the existing centers file at `KMEANS_CENTERS_FILE`.
5. Run the script — a new JSON file is saved automatically.

Alternatively, call `_train_kmeans` directly from Python:

```python
from eof_classification import (
    _read_da, _load_model_triplets, _train_kmeans,
    EA_SIGN, SCA_SIGN
)

EA_ctrl  = EA_SIGN  * _read_da("path/to/new_EA_ctrl.nc")
SCA_ctrl = SCA_SIGN * _read_da("path/to/new_SCA_ctrl.nc")
triplets = _load_model_triplets(eof_globs={
    2: "/path/to/EOF2_*.nc",
    3: "/path/to/EOF3_*.nc",
    4: "/path/to/EOF4_*.nc",
})
results = _train_kmeans(EA_ctrl, SCA_ctrl, triplets,
                        centers_file="new_centers.json")
```

If the current control files do not match the reanalysis recorded in the
centers file, a warning is printed.  The subspace and correlation methods
are unaffected by this mismatch; only the k-means results may be
unreliable.

## References

- North, G. R., T. L. Bell, R. F. Cahalan, and F. J. Moeng, 1982:
  Sampling errors in the estimation of empirical orthogonal functions.
  *Mon. Wea. Rev.*, 110, 699–706.
- Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019:
  Quantifying the Agreement Between Observed and Simulated Extratropical
  Modes of Interannual Variability. *Climate Dynamics*, 52, 4057–4089.

## License

© 2026. Triad National Security, LLC. All rights reserved.
BSD-3-Clause License. See LICENSE file. LANL O Number: O5081.
