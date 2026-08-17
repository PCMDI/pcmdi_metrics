#!/usr/bin/env python
"""Figures for the effective-resolution diagnostic.

Two plots, mirroring Klaver et al. (2020):

`plot_spectra_and_slope`
    Their Figure 1: an :math:`l^{-3}`-compensated KE spectrum panel above a
    spectral-slope panel, with reference power laws, detection wavenumbers,
    and the "skewed" steepening reference lines.
`plot_resolution_scatter`
    Their Figure 2: :math:`L_{eff}` against :math:`\\tilde{L}_{box}` for a
    model ensemble, with the ratio shaded in the background and the
    per-spectrum detection range as error bars.

The compensation matters: KE amplitude falls by several orders of magnitude
over the plotted range, so an uncompensated spectrum hides exactly the
curvature the diagnostic is about.  On log-log axes a power law is a straight
line, so any curvature visible in a compensated panel is real curvature of
the spectrum.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .ke_spectra import eddy_scale
from .spectral_slope import reference_steepening_line

__all__ = ["plot_spectra_and_slope", "plot_resolution_scatter"]

#: Consistent colours for the three diagnosed spectra, following the paper.
SPECTRUM_COLORS = {
    "div_250": "tab:blue",
    "rot_250": "tab:red",
    "rot_500": "tab:green",
}
SPECTRUM_LABELS = {
    "div_250": "divergent, 250 hPa",
    "rot_250": "rotational, 250 hPa",
    "rot_500": "rotational, 500 hPa",
}


def plot_spectra_and_slope(
    diagnostics: dict[str, Any],
    metrics: dict[str, Any] | None = None,
    compensate: float = 3.0,
    title: str = "",
    output_file: str | None = None,
    figsize: tuple[float, float] = (7.0, 8.0),
    slope_ylim: tuple[float, float] = (0.0, 8.0),
    show_reference_laws: bool = True,
):
    """Two-panel compensated spectrum and slope figure (paper Figure 1).

    Parameters
    ----------
    diagnostics : dict
        Second return value of
        `~pcmdi_metrics.effective_resolution.lib.compute_effective_resolution.compute_effective_resolution`,
        containing ``spectra``, ``slopes`` and ``detections``.
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
        If given, save to this path and close the figure.
    figsize : tuple of float, optional
        Figure size in inches.
    slope_ylim : tuple of float, optional
        y-limits of the slope panel.
    show_reference_laws : bool, optional
        Draw the :math:`k^{-5/3}` and :math:`k^{-3}` reference laws and their
        10%-steeper dash-dot counterparts.  Default ``True``.

    Returns
    -------
    matplotlib.figure.Figure
        The figure, or ``None`` if ``output_file`` was given.

    Examples
    --------
    >>> fig = plot_spectra_and_slope(diags, metrics["M"]["r1i1p1f1"])  # doctest: +SKIP
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
        color = SPECTRUM_COLORS.get(key, "0.4")

        ax_spec.loglog(
            ell,
            ell**compensate * np.asarray(spec.values),
            color=color,
            label=SPECTRUM_LABELS.get(key, key),
        )
        ax_slope.semilogx(ell, np.asarray(slope.values), color=color)

        detected = detections.get(key, {}).get("wavenumber")
        if detected is None:
            continue
        ax_slope.axvline(detected, color=color, alpha=0.35, lw=1.0)
        ax_spec.axvline(detected, color=color, alpha=0.35, lw=1.0)

        # The "skewed" reference line: +25% exponent per doubling of l.
        n0 = detections[key]["slope_at_detection"]
        crit = detections[key]["criterion"]
        line_l = np.linspace(detected / 2.0, detected * 2.0, 50)
        ax_slope.plot(
            line_l,
            reference_steepening_line(
                line_l,
                detected,
                n0,
                crit["steepening_factor"],
                crit["wavenumber_ratio"],
            ),
            color=color,
            ls=":",
            lw=1.0,
        )

    if show_reference_laws and slopes:
        # Anchor the reference laws to the spectra themselves, so they sit in
        # the panel rather than at an arbitrary amplitude. The anchor is the
        # compensated amplitude of the first spectrum at l = anchor_l.
        first = next(iter(slopes))
        component, level = first.split("_")
        anchor_spec = spectra[float(level)][f"ke_{component}"]
        anchor_ell = np.asarray(anchor_spec["wavenumber"].values, dtype=float)
        anchor_l = float(np.clip(30.0, anchor_ell.min(), anchor_ell.max()))
        anchor_y = float(
            np.interp(anchor_l, anchor_ell, anchor_ell**compensate * np.asarray(anchor_spec.values))
        )
        ell_ref = np.array([anchor_ell.min(), anchor_ell.max()])

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

    if metrics is not None and metrics.get("effective_wavenumber") is not None:
        for axis in (ax_spec, ax_slope):
            axis.axvline(
                metrics["effective_wavenumber"], color="k", lw=1.6, ls="--"
            )
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

    ax_slope.set_ylim(*slope_ylim)
    ax_slope.set_ylabel(r"slope exponent $n$")
    ax_slope.set_xlabel("total wavenumber $l$")
    ax_slope.grid(alpha=0.2, which="both")

    # Secondary axis in eddy scale (km), as in the paper's top axis.
    ax_top = ax_spec.secondary_xaxis(
        "top",
        functions=(
            lambda x: np.where(x > 0, eddy_scale(np.maximum(x, 1e-9)), np.inf),
            lambda s: np.pi * 6371.0 / np.maximum(s, 1e-9),
        ),
    )
    ax_top.set_xlabel("eddy scale $\\Delta S$ (km)")

    if title:
        fig.suptitle(title, fontsize=11)
    fig.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches="tight")
        import matplotlib.pyplot as plt_close

        plt_close.close(fig)
        return None
    return fig


def plot_resolution_scatter(
    results: Sequence[dict[str, Any]],
    labels: Sequence[str] | None = None,
    title: str = "",
    output_file: str | None = None,
    figsize: tuple[float, float] = (6.5, 5.5),
    ratio_levels: Sequence[float] = (2.0, 3.0, 4.0, 5.0, 6.0),
):
    """Ensemble scatter of :math:`L_{eff}` against :math:`\\tilde{L}_{box}` (paper Figure 2).

    Parameters
    ----------
    results : sequence of dict
        One inner metrics dict per model configuration, each as returned by
        `~pcmdi_metrics.effective_resolution.lib.compute_effective_resolution.compute_effective_resolution`.
    labels : sequence of str or None, optional
        Point labels.  Default uses ``result["model"]`` if present, else the
        index.
    title : str, optional
        Figure title.
    output_file : str or None, optional
        If given, save and close.
    figsize : tuple of float, optional
        Figure size in inches.
    ratio_levels : sequence of float, optional
        Contour levels for the background :math:`L_{eff}/\\tilde{L}_{box}`
        shading.  Klaver et al. find all their models fall in 2.7-4.8.

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
        [np.nan if r["effective_resolution_km"] is None else r["effective_resolution_km"]
         for r in results],
        dtype=float,
    )

    x_max = np.nanmax(lbox) * 1.25
    y_max = np.nanmax(leff) * 1.25
    xx, yy = np.meshgrid(
        np.linspace(1.0, x_max, 200), np.linspace(1.0, y_max, 200)
    )
    ratio = yy / xx
    contour = ax.contourf(xx, yy, ratio, levels=ratio_levels, cmap="YlGnBu", alpha=0.55)
    fig.colorbar(contour, ax=ax, label=r"$L_{eff}/\tilde{L}_{box}$")

    for i, result in enumerate(results):
        label = (
            labels[i]
            if labels is not None
            else result.get("model", str(i))
        )
        span = result.get("steepening_wavenumber_range")
        yerr = None
        if span is not None and result["effective_resolution_km"] is not None:
            hi = float(eddy_scale(span[0]))  # smallest l -> largest scale
            lo = float(eddy_scale(span[1]))
            centre = result["effective_resolution_km"]
            yerr = np.array([[max(centre - lo, 0.0)], [max(hi - centre, 0.0)]])

        marker = "v" if result.get("is_upper_limit") else "o"
        ax.errorbar(
            lbox[i],
            leff[i],
            yerr=yerr,
            fmt=marker,
            capsize=3,
            ms=7,
            label=label,
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
