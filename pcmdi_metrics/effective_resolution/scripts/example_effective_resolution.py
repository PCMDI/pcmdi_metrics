#!/usr/bin/env python
"""Minimal, runnable example of the effective resolution diagnostic.

Runs on synthetic data, so it needs no input files and no optional spectral
library.  Its purpose is to exercise the whole chain -- spectra, slope fit,
steepening detection, grid distance, ratio -- and to show what the returned
dictionaries look like.

Run::

    python example_effective_resolution.py

For real data, see ``../README.md`` and
``../param/myParam_effective_resolution.py``.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

from pcmdi_metrics.effective_resolution.lib import (
    compute_effective_resolution,
    detect_steepening,
    eddy_scale,
    fit_spectral_slope,
    normalized_legendre,
    parseval_check,
    plot_spectra_and_slope,
    representative_grid_box_distance,
    scalar_sh_analysis,
)


def synthetic_spectrum(
    n_max: int = 400, roll_off: int = 90, decay: float = 60.0
) -> xr.DataArray:
    """A k**-3 spectrum with an exponential roll-off past ``roll_off``.

    Stands in for a model spectrum whose small scales are damped by
    diffusion and filtering.

    Parameters
    ----------
    n_max : int, optional
        Largest wavenumber.
    roll_off : int, optional
        Wavenumber at which damping begins.
    decay : float, optional
        e-folding wavenumber scale of the damping.

    Returns
    -------
    xarray.DataArray
        Synthetic KE spectrum on a ``wavenumber`` dimension.
    """
    ell = np.arange(1, n_max + 1, dtype=float)
    power = ell**-3.0 * np.exp(-np.maximum(ell - roll_off, 0.0) / decay)
    return xr.DataArray(
        power,
        coords={"wavenumber": ell, "eddy_scale": ("wavenumber", np.asarray(eddy_scale(ell)))},
        dims="wavenumber",
        name="ke_rot",
    )


def demo_detection() -> None:
    """Slope fit and steepening detection on a single synthetic spectrum."""
    spectrum = synthetic_spectrum()
    slope = fit_spectral_slope(spectrum, window=20, anchor="center")
    result = detect_steepening(slope, steepening_factor=0.25, min_wavenumber=32)

    print("--- single spectrum ---")
    print(f"  detected at l = {result['wavenumber']}")
    print(f"  eddy scale   = {eddy_scale(result['wavenumber']):.0f} km")
    print(f"  slope there  = {result['slope_at_detection']:.2f}")

    print("  sensitivity to the ad hoc 25% threshold:")
    for factor in (0.15, 0.20, 0.25, 0.30, 0.40):
        alt = detect_steepening(slope, steepening_factor=factor, min_wavenumber=32)
        print(f"    factor={factor:.2f} -> l={alt['wavenumber']}")


def demo_grid_distance() -> None:
    """Representative grid box distance for a few CMIP6 HighResMIP grids."""
    print("--- representative grid box distance ---")
    cases = {
        "HadGEM3-GC31-LM (145x192)": (145, 192, 217.0),
        "HadGEM3-GC31-MM (325x432)": (325, 432, 96.7),
        "HadGEM3-GC31-HM (769x1024)": (769, 1024, 40.8),
        "CMCC-CM2-VHR4 (768x1152)": (768, 1152, 38.2),
    }
    for label, (nlat, nlon, published) in cases.items():
        lat = np.linspace(-90.0, 90.0, nlat)
        lon = np.arange(0.0, 360.0, 360.0 / nlon)
        computed = representative_grid_box_distance(lat, lon)
        print(f"  {label:30s} computed {computed:6.1f} km | Table 1 {published:6.1f} km")


def demo_transform_accuracy() -> None:
    """Verify the numpy backend's Legendre recursion and normalisation.

    Two independent checks that any SH backend must pass before its spectra
    mean anything:

    1. The normalised associated Legendre functions are orthonormal,
       :math:`\\tfrac{1}{2}\\int \\bar{P}_{l,m}^2 d\\mu = 1`.
    2. Parseval's identity closes -- grid-space variance equals summed
       spectral power.

    Run the same Parseval check after switching backend or after a
    ``pyspharm``/``shtns`` version bump; SH normalisation conventions differ
    between packages and releases.
    """
    print("--- transform accuracy ---")
    mu, weights = np.polynomial.legendre.leggauss(200)
    for order in (0, 1, 3, 7):
        legendre = normalized_legendre(order, 12, mu)
        norms = 0.5 * (legendre**2 * weights).sum(axis=1)
        print(f"  m={order}: max |1 - norm| = {np.abs(1.0 - norms).max():.2e}")

    rng = np.random.default_rng(1)
    nlat, nlon = 180, 360
    lat = np.linspace(-89.5, 89.5, nlat)
    field = _band_limited(rng, nlat, nlon, kc=15.0)
    grid_var, spectral_power = parseval_check(
        field, lat, scalar_sh_analysis(field, lat, 120)
    )
    print(
        f"  Parseval: grid={grid_var:.4e} spectral={spectral_power:.4e} "
        f"rel. diff={abs(grid_var - spectral_power) / grid_var:.2%}"
    )


def _band_limited(
    rng: np.random.Generator,
    nlat: int,
    nlon: int,
    slope: float = 1.5,
    kc: float = 25.0,
    amplitude: float = 12.0,
) -> np.ndarray:
    """A random field with a power-law spectrum damped past ``kc``.

    Crude stand-in for a model wind field: enough spectral structure that the
    steepening criterion has something to find, without pretending to be an
    atmosphere.
    """
    noise = np.fft.fft2(rng.normal(0.0, 1.0, (nlat, nlon)))
    ky = np.fft.fftfreq(nlat, 1.0 / nlat)[:, None]
    kx = np.fft.fftfreq(nlon, 1.0 / nlon)[None, :]
    k = np.sqrt(ky**2 + kx**2)
    k[0, 0] = 1.0
    shaped = np.real(np.fft.ifft2(noise * k**-slope * np.exp(-((k / kc) ** 2))))
    return shaped / shaped.std() * amplitude


def demo_full_pipeline() -> None:
    """End-to-end run on a synthetic wind field.

    The wind is a random, spectrally shaped field -- not an atmosphere -- so
    the numbers below carry no physical meaning.  What the demo shows is that
    the chain runs, that all three spectra register a detection, and what the
    returned dictionaries look like.  ``min_wavenumber`` is lowered to 16
    because the synthetic damping scale sits well below the paper's ``l = 32``
    cutoff; do not lower it for real data.
    """
    rng = np.random.default_rng(0)
    nlat, nlon, ntime = 96, 192, 2
    lat = np.linspace(-88.0, 88.0, nlat)
    lon = np.arange(0.0, 360.0, 360.0 / nlon)
    plev = np.array([25000.0, 50000.0])

    def stack() -> np.ndarray:
        return np.stack(
            [np.stack([_band_limited(rng, nlat, nlon) for _ in plev]) for _ in range(ntime)]
        )

    ds = xr.Dataset(
        {
            "ua": (("time", "plev", "lat", "lon"), stack()),
            "va": (("time", "plev", "lat", "lon"), stack()),
        },
        coords={"time": np.arange(ntime), "plev": plev, "lat": lat, "lon": lon},
    )

    metrics, diagnostics = compute_effective_resolution(
        ds,
        uvar="ua",
        vvar="va",
        levels=(250.0, 500.0),
        backend="numpy",
        min_wavenumber=16,
        model="SYNTHETIC",
        member="r1i1p1f1",
    )

    print("--- full pipeline (synthetic; numbers are not physically meaningful) ---")
    inner = metrics["SYNTHETIC"]["r1i1p1f1"]
    for key in (
        "effective_wavenumber",
        "effective_resolution_km",
        "grid_box_distance_km",
        "resolution_ratio",
        "n_spectra_steepening",
    ):
        print(f"  {key:28s} {inner[key]}")
    print(f"  per-spectrum detections     {inner['steepening_wavenumber']}")
    print(f"  detection range (l)         {inner['steepening_wavenumber_range']}")
    print(f"  diagnostics dataset vars    {list(diagnostics['dataset'].data_vars)}")

    try:
        plot_spectra_and_slope(
            diagnostics,
            inner,
            title="SYNTHETIC (demo)",
            output_file="example_effective_resolution.png",
        )
        print("  wrote example_effective_resolution.png")
    except ImportError:
        print("  (matplotlib unavailable; skipped the figure)")


if __name__ == "__main__":
    demo_detection()
    print()
    demo_grid_distance()
    print()
    demo_transform_accuracy()
    print()
    demo_full_pipeline()
