# Classification Algorithm for Empirical Orthogonal Functions of Arctic Atmospheric Variability in Python

LANL O number: O5081

Classifies model Empirical Orthogonal Functions (EOFs 2–4 of JFM sea-level
pressure) as **East Atlantic (EA)** or **Scandinavian (SCA)** patterns using
three independent methods and a consensus score.

Developed as a contribution to [PMP](https://pcmdi.github.io/pcmdi_metrics/),
the PCMDI Metrics Package (Lawrence Livermore National Laboratory).

## Authors

- Martin Velez Pardo (Los Alamos National Laboratory, EES-14)
- Alexandra Jonko (Los Alamos National Laboratory, EES-17)

---

## Overview

The script compares each model's EOF2, EOF3, and EOF4 against observational
ground-truth control patterns (EA and SCA) derived from reanalysis data.
Three methods independently classify each EOF, and a consensus layer
aggregates their results.

### Methods

**1. Subspace projection (shift-tolerant)**
Projects the EA and SCA control patterns onto the model's EOF subspace
(span{EOF2, EOF3, EOF4}) via weighted least squares, allowing for small
phase shifts in latitude and longitude.  For each EOF, the relative
coefficient dominance across both fits determines whether it more closely
represents EA or SCA.

**2. Correlation + geographic tests**
Scores each EOF on a 100-point scale combining four diagnostics: weighted
pattern correlation with each control (0–40 points), correlation with the
orthogonalised component unique to each pattern (0–40 points), and two
geographic tests based on regional pressure anomalies over Greenland,
Ireland, and Scandinavia (0–10 points each).

**3. K-means clustering**
Clusters all EOFs across models into three groups using area-weighted,
sign-oriented, row-normalised features.  Clusters are labelled EA, SCA, or
OTHER by correlation with the controls.  Each EOF receives a soft membership
score indicating its affinity to each cluster type.  Pre-computed cluster
centers are saved to a JSON file so that subsequent runs classify new models
without needing the full ensemble.

### Consensus

For each EOF, the three methods each produce a label (EA or SCA) and a
confidence score in [0, 1].  The consensus layer combines these into a
single classification:

- **Label**: simple majority vote (2/3 or 3/3 agree).  If no majority
  exists, the label is UNCLASSIFIED.
- **Confidence**: (fraction of methods agreeing) × (mean confidence of
  agreeing methods).
- **Quality**: derived from the consensus confidence:

  | Quality   | Confidence range | Warning? |
  |-----------|-----------------|----------|
  | robust    | ≥ 0.7           | no       |
  | medium    | 0.5 – 0.7       | no       |
  | weak      | 0.3 – 0.5       | WARNING  |
  | very weak | < 0.3           | WARNING  |

Because model EOFs may span a subspace that mixes the reference patterns,
multiple EOFs can receive the same label when their projections are not
cleanly separable.

---

## Requirements

Python 3.8+ with:

- **NumPy**
- **Xarray**
- **scikit-learn**

All other imports (`glob`, `os`, `csv`, `json`, `collections`) are Python
standard library.

---

## Inputs

The script requires three types of input files, all in netCDF format:

1. **Model EOF files** — one file per EOF mode (2, 3, 4) per model,
   containing a 2-D (lat × lon) spatial pattern.  File paths are discovered
   via glob patterns set in `EOF_GLOBS`.

2. **Control patterns** — EA and SCA reference patterns from a reanalysis
   (e.g., 20CR-V2).  Paths set in `EA_CTRL_FILE` and `SCA_CTRL_FILE`.

3. **K-means centers file** (JSON, optional on first run) — pre-computed
   cluster centers.  If the file does not exist on first run, the script
   trains from the full ensemble and saves the centers for future use.

---

## Quick Start

1. Edit the `CONFIG` section at the top of `eof_classification.py`:
   - Set `MODEL_EOF_DIR` and `EOF_GLOBS` to point to your model EOF files.
   - Set `EA_CTRL_FILE` and `SCA_CTRL_FILE` to your control pattern paths.
   - Set `CTRL_REANALYSIS` to the label for your reanalysis (e.g., `"20CR-V2"`).

2. Run the script:
   ```
   python eof_classification.py
   ```

3. On first run, unless a .json file exists, the script trains k-means from
   the full ensemble and saves `data/kmeans_centers_20CR-V2_CMIP6.json`. This
   requires EOF files from all models.

4. On subsequent runs, the saved centers are loaded and applied per-model.
   You can classify a single new model without needing the rest of the
   ensemble.

---

## Output

Two files are produced:

- **`eof_classification_consensus.tsv`** — tab-separated, machine-readable.
- **`eof_classification_consensus.txt`** — fixed-width, human-readable.

Each row represents one EOF of one model and contains:

| Column            | Description                                       |
|-------------------|---------------------------------------------------|
| Model             | Model name                                        |
| EOF               | EOF mode (EOF2, EOF3, or EOF4)                    |
| Subspace_label    | Subspace method classification (EA / SCA / NA)    |
| Subspace_conf     | Subspace confidence [0, 1]                        |
| Correlation_label | Correlation method classification                 |
| Correlation_conf  | Correlation confidence [0, 1]                     |
| Kmeans_label      | K-means classification                            |
| Kmeans_conf       | K-means confidence [0, 1]                         |
| Consensus_label   | Majority-vote label (EA / SCA / UNCLASSIFIED)     |
| Consensus_conf    | Consensus confidence [0, 1]                       |
| Quality           | robust / medium / weak / very weak                |
| Warning           | WARNING flag if quality is weak or very weak      |

---

## Configuration Reference

All configurable parameters are in the `CONFIG` section at the top of the
script.  Key settings:

| Parameter           | Default    | Description                                        |
|---------------------|------------|----------------------------------------------------|
| `EA_CTRL_FILE`      | (path)     | Path to the EA control pattern netCDF               |
| `SCA_CTRL_FILE`     | (path)     | Path to the SCA control pattern netCDF              |
| `EA_SIGN`/`SCA_SIGN`| +1.0/−1.0 | Sign convention applied to controls at load time   |
| `CTRL_REANALYSIS`   | "20CR-V2"  | Label for provenance checking vs. k-means centers  |
| `LAT_RANGE`         | (20, 90)   | Latitude bounds for domain restriction             |
| `SMOOTH_SIGMA_DEG`  | 4.0        | Gaussian smoothing (degrees); 0 disables           |
| `SHIFT_LON_MAX_DEG` | 15.0       | Longitudinal shift tolerance (degrees)             |
| `SHIFT_LAT_MAX_DEG` | 6.0        | Latitudinal shift tolerance (degrees)              |
| `RIDGE`             | 0.0        | Tikhonov regularisation; 0 = ordinary least squares|
| `KMEANS_CENTERS_FILE`| (path)    | Path to pre-computed k-means centers JSON          |

---

## K-Means Retraining

The pre-computed k-means centers are tied to a specific reanalysis and model
ensemble.  If you need to retrain for a different reanalysis or a new
generation of models (e.g., CMIP7):

1. Set `EA_CTRL_FILE` and `SCA_CTRL_FILE` to the new control patterns.
2. Set `CTRL_REANALYSIS` and `CMIP_TAG` to match.
3. Set `EOF_GLOBS` to point to EOF files from the full multi-model ensemble
   (training requires ~20+ models for meaningful clusters).
4. Delete or rename the existing `KMEANS_CENTERS_FILE`.
5. Run the script — a new JSON file is saved automatically.

If the current control files do not match the reanalysis recorded in the
centers file, a warning is printed.  The subspace and correlation methods
are unaffected by this mismatch; only the k-means results may be unreliable.

---

## PMP Integration

The code is structured for integration into PMP as a callable function.
The natural API is:

```python
results = classify_eofs(eof2, eof3, eof4, ea_ctrl, sca_ctrl,
                        kmeans_centers_file="data/kmeans_centers_20CR-V2_CMIP6.json")
```

All three EOFs are required together because the subspace method fits
controls as a linear combination of the full {EOF2, EOF3, EOF4} basis.
The internal methods (`run_subspace`, `run_correlations`, `run_kmeans`)
already accept their inputs as function arguments; wrapping them into a
single entry-point function requires passing CONFIG values as parameters
instead of reading module-level globals.

---

## Release

LANL O Number: **O5081**

This software has been approved for open-source release by the National
Nuclear Security Administration (NNSA).

## License

© 2026. Triad National Security, LLC. All rights reserved.

This program was produced under U.S. Government contract 89233218CNA000001
for Los Alamos National Laboratory (LANL), which is operated by Triad
National Security, LLC for the U.S. Department of Energy/National Nuclear
Security Administration.

Distributed under the BSD-3-Clause License. See [LICENSE](LICENSE) for full
terms.
