#!/usr/bin/env python
"""Figures for the effective-resolution diagnostic.

`plot_spectra_and_slope` reproduces Figure 1 of Klaver et al. (2020): an
:math:`l^{-3}`-compensated KE spectrum panel above a spectral-slope panel,
with reference power laws, detection wavenumbers and the "skewed" steepening
reference lines.  `plot_resolution_scatter` reproduces their Figure 2:
:math:`L_{eff}` against :math:`\\tilde{L}_{box}` for a model ensemble, with
the ratio shaded behind and the per-spectrum detection range as error bars.

The compensation matters: KE amplitude falls by several orders of magnitude
over the plotted range, so an uncompensated spectrum hides exactly the
curvature the diagnostic is about.  On log-log axes a power law is a straight
line, so any curvature visible in a compensated panel is real.

References
----------
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .ke_spectra import EARTH_RADIUS, eddy_scale, wavenumber_from_eddy_scale
from .spectral_slope import reference_steepening_line

__all__ = ["plot_resolution_scatter", "plot_spectra_and_slope"]

#: Consistent colours and labels for the three diagnosed spectra.
SPECTRUM_STYLE = {
    "div_250": ("tab:blue", "divergent, 250 hPa"),
    "rot_250": ("tab:red", "rotational, 250 hPa"),
    "rot_500": ("tab:green", "rotational, 500 hPa"),
}


def plot_spectra_and_slope(
    diagnostics: dict[str, Any],
    metrics: dict[str, Any] | None = None,
    compensate: float = 3.0,
    title: str = "",
    output_file: str | None = None,
    figsize: tuple[float, float] = (7.0, 8.0),
    slope_ylim: tuple[float, float] = (0.0, 8.0),
    rsphere: float = EARTH_RADIUS,
    xlim: tuple[float, float] | None = None,
    spec_ylim: tuple[float, float] | None = None,
    xticks: Sequence[float] | None = None,
):
    """Two-panel compensated spectrum and slope figure (paper Figure 1).

    Parameters
    ----------
    diagnostics : dict
        Second return value of
        `~pcmdi_metrics.effective_resolution.compute_effective_resolution`,
        holding ``spectra``, ``slopes`` and ``detections``.
    metrics : dict or None, optional
        Inner metrics dict for the model/member, used to draw the final
        :math:`l_{eff}` line.  If ``None``, only per-spectrum detections are
        drawn.
    compensate : float, optional
        Exponent :math:`p` in the compensation :math:`l^{p} E_l`.  Default
        ``3.0``, so a :math:`k^{-3}` spectrum plots flat.
    title : str, optional
        Figure title.
    output_file : str or None, optional
        If given, save to this path, close the figure and return ``None``.
    figsize : tuple of float, optional
        Figure size in inches.
    slope_ylim : tuple of float, optional
        y-limits of the slope panel.
    rsphere : float, optional
        Sphere radius in metres, used for the eddy-scale top axis.
    xlim : tuple of float or None, optional
        x-limits for both panels (wavenumber range). If ``None`` (default),
        automatically determined from data. To match Klaver et al. (2020)
        Figure 1, use ``(13, 240)`` or similar depending on model resolution.
    spec_ylim : tuple of float or None, optional
        y-limits for the compensated spectrum panel. If ``None`` (default),
        automatically determined from data. To match Klaver et al. (2020)
        Figure 1, use ``(1e0, 1e2)`` or adjust based on model output.
    xticks : sequence of float or None, optional
        Custom x-axis (wavenumber) tick positions for both panels. If ``None``
        (default), matplotlib automatically selects tick positions. To match
        Klaver et al. (2020) Figure 1, use values like ``[13, 20, 32, 40, 60,
        80, 100, 120, 160, 200, 240]`` or adjust based on the xlim range.

    Returns
    -------
    matplotlib.figure.Figure or None

    Examples
    --------
    >>> fig = plot_spectra_and_slope(diags, metrics["M"]["r1i1p1f1"])  # doctest: +SKIP
    >>> # Match paper Figure 1 axis ranges and ticks:
    >>> fig = plot_spectra_and_slope(  # doctest: +SKIP
    ...     diags, metrics["M"]["r1i1p1f1"],
    ...     xlim=(13, 240), spec_ylim=(1e0, 1e2), slope_ylim=(1, 5),
    ...     xticks=[13, 20, 32, 40, 60, 80, 100, 120, 160, 200, 240]
    ... )
    """
    import matplotlib.pyplot as plt

    spectra = diagnostics["spectra"]
    slopes = diagnostics["slopes"]
    detections = diagnostics["detections"]

    fig, (ax_spec, ax_slope) = plt.subplots(
        2, 1, figsize=figsize, sharex=True, gridspec_kw={"height_ratios": [2, 1]}
    )

    for key, slope in slopes.items():
        component, level = key.split("_")
        spec = spectra[float(level)][f"ke_{component}"]
        ell = np.asarray(spec["wavenumber"].values, dtype=float)
        color, label = SPECTRUM_STYLE.get(key, ("0.4", key))

        ax_spec.loglog(
            ell, ell**compensate * np.asarray(spec.values), color=color, label=label
        )
        ax_slope.semilogx(ell, np.asarray(slope.values), color=color)

        detected = detections.get(key, {}).get("wavenumber")
        if detected is None:
            continue
        for axis in (ax_spec, ax_slope):
            axis.axvline(detected, color=color, alpha=0.35, lw=1.0)

        # The "skewed" reference line: +25% exponent per doubling of l.
        criterion = detections[key]["criterion"]
        line_l = np.linspace(detected / 2.0, detected * 2.0, 50)
        ax_slope.plot(
            line_l,
            reference_steepening_line(
                line_l,
                detected,
                detections[key]["slope_at_detection"],
                criterion["steepening_factor"],
                criterion["wavenumber_ratio"],
            ),
            color=color,
            ls=":",
            lw=1.0,
        )

    if slopes:
        _add_reference_laws(ax_spec, ax_slope, spectra, list(slopes), compensate)

    if metrics is not None and metrics.get("effective_wavenumber") is not None:
        for axis in (ax_spec, ax_slope):
            axis.axvline(metrics["effective_wavenumber"], color="k", lw=1.6, ls="--")
        ax_spec.text(
            metrics["effective_wavenumber"],
            ax_spec.get_ylim()[1],
            f"  $l_{{eff}}$={metrics['effective_wavenumber']:.0f}"
            f"\n  $L_{{eff}}$={metrics['effective_resolution_km']:.0f} km",
            va="top",
            ha="left",
            fontsize=8,
        )

    ax_spec.set_ylabel(rf"$l^{{{compensate:g}}} E_l$")
    ax_spec.legend(fontsize=8, frameon=False)
    ax_spec.grid(alpha=0.2, which="both")

    # Apply axis limits if provided
    if xlim is not None:
        ax_spec.set_xlim(*xlim)
    if spec_ylim is not None:
        ax_spec.set_ylim(*spec_ylim)

    # Apply custom x-axis ticks if provided
    if xticks is not None:
        from matplotlib.ticker import FixedLocator, NullFormatter
        ax_spec.xaxis.set_major_locator(FixedLocator(xticks))
        ax_spec.xaxis.set_minor_locator(FixedLocator([]))
        ax_spec.xaxis.set_minor_formatter(NullFormatter())

    ax_slope.set_ylim(*slope_ylim)
    ax_slope.set_ylabel(r"slope exponent $n$")
    ax_slope.set_xlabel("total wavenumber $l$")
    ax_slope.grid(alpha=0.2, which="both")

    # Apply custom x-axis ticks to slope panel as well
    if xticks is not None:
        from matplotlib.ticker import FixedLocator, NullFormatter
        ax_slope.xaxis.set_major_locator(FixedLocator(xticks))
        ax_slope.xaxis.set_minor_locator(FixedLocator([]))
        ax_slope.xaxis.set_minor_formatter(NullFormatter())

    # Secondary axis in eddy scale (km), as in the paper's top axis.
    ax_top = ax_spec.secondary_xaxis(
        "top",
        functions=(
            lambda x: eddy_scale(np.maximum(x, 1e-9), rsphere),
            lambda s: np.vectorize(wavenumber_from_eddy_scale)(
                np.maximum(s, 1e-9), rsphere
            ),
        ),
    )
    ax_top.set_xlabel(r"eddy scale $\Delta S$ (km)")

    if title:
        fig.suptitle(title, fontsize=11)
    fig.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return None
    return fig


def _add_reference_laws(ax_spec, ax_slope, spectra, keys, compensate):
    """Draw the k^-5/3 and k^-3 reference laws, anchored to the plotted spectra.

    Anchoring to the data rather than to a fixed amplitude keeps the lines
    inside the panel for any model and any units; anchoring to the *largest*
    of the plotted spectra keeps them alongside the dominant curve rather than
    floating below it.
    """

    def get_anchor_value(key):
        component, level = key.split("_")
        spec = spectra[float(level)][f"ke_{component}"]
        wn = np.asarray(spec["wavenumber"].values, dtype=float)
        compensated = wn**compensate * np.asarray(spec.values)
        l_val = float(np.clip(30.0, wn.min(), wn.max()))
        return l_val, float(np.interp(l_val, wn, compensated)), wn

    anchors = [get_anchor_value(k) for k in keys]
    anchor_l, anchor_y, ell = max(anchors, key=lambda x: x[1])

    ell_ref = np.array([ell.min(), ell.max()])

    for exponent, color, label in (
        (5.0 / 3.0, "lightblue", r"$k^{-5/3}$"),
        (3.0, "orange", r"$k^{-3}$"),
    ):
        for factor, style, width in ((1.0, "-", 1.2), (1.1, "-.", 1.0)):
            ax_spec.loglog(
                ell_ref,
                anchor_y * (ell_ref / anchor_l) ** (compensate - factor * exponent),
                color=color,
                lw=width,
                ls=style,
                label=label if factor == 1.0 else None,
                zorder=0,
            )
        ax_slope.axhline(exponent, color=color, lw=1.0, zorder=0)


def plot_resolution_scatter(
    results: Sequence[dict[str, Any]],
    labels: Sequence[str] | None = None,
    title: str = "",
    output_file: str | None = None,
    figsize: tuple[float, float] = (6.5, 5.5),
    ratio_levels: Sequence[float] = (2.0, 3.0, 4.0, 5.0, 6.0),
    rsphere: float = EARTH_RADIUS,
):
    """Ensemble scatter of :math:`L_{eff}` against :math:`\\tilde{L}_{box}` (Figure 2).

    Parameters
    ----------
    results : sequence of dict
        One inner metrics dict per model configuration, as returned by
        `~pcmdi_metrics.effective_resolution.compute_effective_resolution`.
    labels : sequence of str or None, optional
        Point labels.  Default uses each result's ``"model"`` key if present,
        else the index.
    title : str, optional
        Figure title.
    output_file : str or None, optional
        If given, save, close and return ``None``.
    figsize : tuple of float, optional
        Figure size in inches.
    ratio_levels : sequence of float, optional
        Contour levels for the background :math:`L_{eff}/\\tilde{L}_{box}`
        shading.  Klaver et al. find all their models fall in 2.7-4.8.
    rsphere : float, optional
        Sphere radius in metres, used to convert the detection wavenumber
        range into the plotted error bars.

    Returns
    -------
    matplotlib.figure.Figure or None

    Examples
    --------
    >>> plot_resolution_scatter(  # doctest: +SKIP
    ...     [m["HadGEM3-GC31-HM"]["r1i1p1f1"], m["ECMWF-IFS-HR"]["r1i1p1f1"]],
    ...     labels=["HadGEM3-GC31-HM", "ECMWF-IFS-HR"],
    ... )
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)

    lbox = np.array([r["grid_box_distance_km"] for r in results], dtype=float)
    leff = np.array(
        [
            (
                np.nan
                if r["effective_resolution_km"] is None
                else r["effective_resolution_km"]
            )
            for r in results
        ],
        dtype=float,
    )

    x_max, y_max = np.nanmax(lbox) * 1.25, np.nanmax(leff) * 1.25
    xx, yy = np.meshgrid(np.linspace(1.0, x_max, 200), np.linspace(1.0, y_max, 200))
    contour = ax.contourf(
        xx, yy, yy / xx, levels=ratio_levels, cmap="YlGnBu", alpha=0.55
    )
    fig.colorbar(contour, ax=ax, label=r"$L_{eff}/\tilde{L}_{box}$")

    for i, result in enumerate(results):
        span = result.get("steepening_wavenumber_range")
        yerr = None
        if span is not None and result["effective_resolution_km"] is not None:
            # Smallest wavenumber maps to the largest scale.
            high = float(eddy_scale(span[0], rsphere))
            low = float(eddy_scale(span[1], rsphere))
            centre = result["effective_resolution_km"]
            yerr = np.array([[max(centre - low, 0.0)], [max(high - centre, 0.0)]])

        ax.errorbar(
            lbox[i],
            leff[i],
            yerr=yerr,
            fmt="v" if result.get("is_upper_limit") else "o",
            capsize=3,
            ms=7,
            label=labels[i] if labels is not None else result.get("model", str(i)),
        )

    ax.set_xlabel(r"representative grid box distance $\tilde{L}_{box}$ (km)")
    ax.set_ylabel(r"effective resolution $L_{eff}$ (km)")
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.legend(fontsize=8, frameon=False, ncol=2)
    if title:
        ax.set_title(title, fontsize=11)
    fig.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return None
    return fig
