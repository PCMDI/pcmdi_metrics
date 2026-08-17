#!/usr/bin/env python
"""Driver for the effective resolution metric (Klaver et al., 2020).

Usage
-----
::

    python effective_resolution_driver.py -p param/myParam_effective_resolution.py

The driver discovers input files (via ``xsearch`` when available, otherwise a
user-supplied path template), loops over models / experiments / members /
periods, calls
`~pcmdi_metrics.effective_resolution.lib.process_effective_resolution` for
each, and writes a combined ensemble JSON plus the paper's Figure 2 scatter.

Notes
-----
Cost scales as one spherical-harmonic transform per time step per level.  At
6-hourly sampling a single month at HadGEM3-GC31-HM resolution is ~120
transforms per level on a 769x1024 grid -- minutes with ``shtns`` or
``pyspharm``, considerably longer with the numpy fallback.  Start with a
single model and one period.
"""

from __future__ import annotations

import glob
import json
import os
from typing import Any

from pcmdi_metrics.effective_resolution.lib import (
    plot_resolution_scatter,
    process_effective_resolution,
)
from pcmdi_metrics.utils import StringConstructor


def find_input_files(
    mip: str,
    exp: str,
    model: str,
    variable: str,
    frequency: str,
    cmip_table: str,
    member: str | None = None,
    path_template: str | None = None,
) -> dict[str, list[str]]:
    """Locate input files for one variable, keyed by ensemble member.

    Tries ``xsearch`` first (the PMP convention on LLNL/NERSC systems) and
    falls back to globbing ``path_template``.

    Parameters
    ----------
    mip : str
        MIP era in lower case, e.g. ``"cmip6"``.
    exp : str
        Experiment id, e.g. ``"highresSST-present"``.
    model : str
        Source id.
    variable : str
        Variable name, e.g. ``"ua"``.
    frequency : str
        Output frequency, e.g. ``"6hr"``.
    cmip_table : str
        CMIP table, e.g. ``"6hrPlevPt"``.
    member : str or None, optional
        Restrict to one member; ``None`` returns all.
    path_template : str or None, optional
        Fallback template with ``%(mip)``, ``%(exp)``, ``%(model)``,
        ``%(realization)``, ``%(variable)``, ``%(table)`` placeholders.

    Returns
    -------
    dict
        ``{member: [file paths]}``.

    Raises
    ------
    RuntimeError
        If neither ``xsearch`` nor ``path_template`` yields any files.
    """
    try:
        import xsearch as xs

        paths = xs.findPaths(
            exp, variable, frequency, mip_era=mip.upper(), cmipTable=cmip_table
        )
        found = {
            xs.getGroupValues(paths, "realization")[i]: sorted(glob.glob(os.path.join(p, "*.nc")))
            for i, p in enumerate(paths)
            if model in p
        }
        if found:
            return found if member is None else {member: found[member]}
    except ImportError:
        pass

    if path_template is None:
        raise RuntimeError(
            f"No files found for {model}/{exp}/{variable} and no path_template given"
        )

    template = StringConstructor(path_template)
    pattern = template(
        mip=mip,
        exp=exp,
        model=model,
        realization=member or "*",
        variable=variable,
        table=cmip_table,
    )
    files = sorted(glob.glob(pattern))
    if not files:
        raise RuntimeError(f"No files matched {pattern}")
    return {member or "unspecified": files}


def build_params(config: dict[str, Any], model: str, exp: str, member: str,
                 u_files: list[str], v_files: list[str],
                 start: str, end: str) -> dict[str, Any]:
    """Assemble the ``params`` dict for one model/member/period.

    Parameters
    ----------
    config : dict
        Contents of the parameter file, as a plain dict.
    model, exp, member : str
        Identifiers for this run.
    u_files, v_files : list of str
        Input file lists for the zonal and meridional wind.
    start, end : str
        Period bounds, ``"YYYY-MM-DD"``.

    Returns
    -------
    dict
        Ready to pass to
        `~pcmdi_metrics.effective_resolution.lib.process_effective_resolution`.
    """
    lbox = config.get("grid_box_distance_km") or {}
    return {
        "model": model,
        "exp": exp,
        "member": member,
        "input_file": u_files,
        "input_file_v": v_files,
        "uvar": config.get("uvar", "ua"),
        "vvar": config.get("vvar", "va"),
        "levels": config.get("levels", (250.0, 500.0)),
        "start": start,
        "end": end,
        "backend": config.get("backend", "auto"),
        "gridtype": config.get("gridtype", "auto"),
        "ntrunc": config.get("ntrunc"),
        "fit_window": config.get("fit_window", 20),
        "fit_anchor": config.get("fit_anchor", "center"),
        "steepening_factor": config.get("steepening_factor", 0.25),
        "wavenumber_ratio": config.get("wavenumber_ratio", 2.0),
        "min_wavenumber": config.get("min_wavenumber", 32),
        "n_confirm": config.get("n_confirm", 2),
        "grid_box_distance_km": lbox.get(model),
        "output_dir": config.get("result_dir", "output"),
        "save_netcdf": config.get("save_netcdf", True),
        "save_json": config.get("save_json", True),
        "plot": config.get("plot", False),
        "debug": config.get("debug", False),
    }


def main() -> None:
    """Run the effective resolution metric over the configured ensemble."""
    from pcmdi_metrics.mean_climate.lib import pmp_parser

    parser = pmp_parser.PMPMetricsParser()
    parser.add_argument("--models", nargs="+", help="Model list override")
    parser.add_argument("--backend", help="Spherical harmonic backend override")
    args = parser.get_parameter(argparse_vals_only=False)
    config = {k: v for k, v in vars(args).items() if not k.startswith("_")}

    models = config.get("models") or []
    exps = config.get("exps", ["highresSST-present"])
    periods = config.get("periods", [("2014-03-01", "2014-03-31")])
    output_dir = config.get("result_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    ensemble: dict[str, Any] = {}
    scatter_rows: list[dict[str, Any]] = []
    scatter_labels: list[str] = []

    for exp in exps:
        for model in models:
            try:
                u_by_member = find_input_files(
                    config.get("mip", "cmip6"), exp, model,
                    config.get("uvar", "ua"), config.get("freq", "6hr"),
                    config.get("cmipTable", "6hrPlevPt"),
                    path_template=config.get("path_template"),
                )
                v_by_member = find_input_files(
                    config.get("mip", "cmip6"), exp, model,
                    config.get("vvar", "va"), config.get("freq", "6hr"),
                    config.get("cmipTable", "6hrPlevPt"),
                    path_template=config.get("path_template"),
                )
            except RuntimeError as err:
                print(f"[skip] {model} / {exp}: {err}")
                continue

            members = sorted(set(u_by_member) & set(v_by_member))
            if config.get("first_member_only", True):
                members = members[:1]

            for member in members:
                for start, end in periods:
                    print(f"[run] {model} {exp} {member} {start}..{end}")
                    try:
                        metrics = process_effective_resolution(
                            build_params(
                                config, model, exp, member,
                                u_by_member[member], v_by_member[member],
                                start, end,
                            )
                        )
                    except Exception as err:  # noqa: BLE001 - keep the loop alive
                        print(f"[fail] {model} {exp} {member}: {err}")
                        continue

                    ensemble.setdefault(model, {}).setdefault(member, {})[
                        f"{start}_{end}"
                    ] = metrics[model][member]
                    scatter_rows.append(metrics[model][member])
                    scatter_labels.append(f"{model} ({start[:7]})")

    combined = os.path.join(output_dir, "effective_resolution_ensemble.json")
    with open(combined, "w") as handle:
        json.dump(
            {
                "DIMENSIONS": {
                    "json_structure": ["model", "realization", "period", "metric"]
                },
                "RESULTS": ensemble,
                "REFERENCE": "Klaver et al. (2020), doi:10.1002/asl.952",
            },
            handle,
            indent=2,
            sort_keys=True,
        )
    print(f"[done] wrote {combined}")

    if config.get("plot", False) and scatter_rows:
        plot_resolution_scatter(
            scatter_rows,
            labels=scatter_labels,
            title="Effective resolution vs. representative grid box distance",
            output_file=os.path.join(output_dir, "effective_resolution_scatter.png"),
        )


if __name__ == "__main__":
    main()
