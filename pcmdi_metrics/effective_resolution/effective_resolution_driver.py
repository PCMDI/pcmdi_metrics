#!/usr/bin/env python
"""Driver for the effective resolution metric (Klaver et al., 2020).

Usage
-----
::

    python effective_resolution_driver.py -p param/myParam_effective_resolution.py

The driver discovers input files (via ``xsearch`` when available, otherwise a
user-supplied path template), loops over models, experiments, members and
periods, calls
`~pcmdi_metrics.effective_resolution.process_effective_resolution` for each,
and writes a combined ensemble JSON plus the paper's Figure 2 scatter.

Notes
-----
Cost scales as one spherical-harmonic transform per time step per level.  One
month of 6-hourly data is ~120 transforms per level; on a 769x1024 grid that
is of order an hour.  Start with a single model and one period.
"""

from __future__ import annotations

import glob
import os
from typing import Any

from pcmdi_metrics.effective_resolution.lib import (
    plot_resolution_scatter,
    process_effective_resolution,
)
from pcmdi_metrics.io.base import Base
from pcmdi_metrics.utils import PMPMetricsParser, StringConstructor

REFERENCE = "Klaver et al. (2020), doi:10.1002/asl.952"


def find_input_files(
    mip: str,
    exp: str,
    model: str,
    variable: str,
    frequency: str,
    cmip_table: str,
    path_template: str | None = None,
) -> dict[str, list[str]]:
    """Locate input files for one variable, keyed by ensemble member.

    Tries ``xsearch`` first (the PMP convention on LLNL and NERSC systems) and
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
    path_template : str or None, optional
        Fallback template with ``%(mip)``, ``%(exp)``, ``%(model)``,
        ``%(realization)``, ``%(variable)`` and ``%(table)`` placeholders.

    Returns
    -------
    dict
        ``{member: [file paths]}``.  Empty if nothing was found.
    """
    try:
        import xsearch as xs

        paths = xs.findPaths(
            exp, variable, frequency, mip_era=mip.upper(), cmipTable=cmip_table
        )
        found = {}
        for path in paths:
            if model not in path:
                continue
            members = xs.getGroupValues([path], "realization")
            if not members:
                continue
            files = sorted(glob.glob(os.path.join(path, "*.nc")))
            if files:
                found[members[0]] = files
        if found:
            return found
    except ImportError:
        pass

    if path_template is None:
        return {}

    pattern = StringConstructor(path_template)(
        mip=mip,
        exp=exp,
        model=model,
        realization="*",
        variable=variable,
        table=cmip_table,
    )
    files = sorted(glob.glob(pattern))
    return {"unspecified": files} if files else {}


def build_params(
    config: dict[str, Any],
    model: str,
    exp: str,
    member: str,
    u_files: list[str],
    v_files: list[str],
    start: str,
    end: str,
) -> dict[str, Any]:
    """Assemble the ``params`` dict for one model, member and period.

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
        `~pcmdi_metrics.effective_resolution.process_effective_resolution`.
    """
    lbox = config.get("grid_box_distance_km") or {}
    keys = (
        "uvar",
        "vvar",
        "levels",
        "ntrunc",
        "gridtype",
        "fit_window",
        "fit_anchor",
        "steepening_factor",
        "wavenumber_ratio",
        "min_wavenumber",
        "n_confirm",
        "save_netcdf",
        "save_json",
        "plot",
        "debug",
    )
    params = {key: config[key] for key in keys if key in config}
    params.update(
        model=model,
        exp=exp,
        member=member,
        input_file=u_files,
        input_file_v=v_files,
        start=start,
        end=end,
        grid_box_distance_km=lbox.get(model),
        output_dir=config.get("result_dir", "output"),
    )
    return params


def main() -> None:
    """Run the effective resolution metric over the configured ensemble."""
    parser = PMPMetricsParser()
    parser.add_argument("--models", nargs="+", help="Model list override")
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
            search = dict(
                mip=config.get("mip", "cmip6"),
                exp=exp,
                model=model,
                frequency=config.get("freq", "6hr"),
                cmip_table=config.get("cmipTable", "6hrPlevPt"),
                path_template=config.get("path_template"),
            )
            u_by_member = find_input_files(variable=config.get("uvar", "ua"), **search)
            v_by_member = find_input_files(variable=config.get("vvar", "va"), **search)

            members = sorted(set(u_by_member) & set(v_by_member))
            if not members:
                print(f"[skip] {model} / {exp}: no matching ua/va files")
                continue
            if config.get("first_member_only", True):
                members = members[:1]

            for member in members:
                for start, end in periods:
                    print(f"[run] {model} {exp} {member} {start}..{end}")
                    try:
                        metrics = process_effective_resolution(
                            build_params(
                                config,
                                model,
                                exp,
                                member,
                                u_by_member[member],
                                v_by_member[member],
                                start,
                                end,
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

    json_structure = ["model", "realization", "period", "metric"]
    Base(output_dir, "effective_resolution_ensemble.json").write(
        {
            "DIMENSIONS": {"json_structure": json_structure},
            "RESULTS": ensemble,
            "REFERENCE": REFERENCE,
        },
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )

    if config.get("plot", False) and scatter_rows:
        plot_resolution_scatter(
            scatter_rows,
            labels=scatter_labels,
            title="Effective resolution vs. representative grid box distance",
            output_file=os.path.join(output_dir, "effective_resolution_scatter.png"),
        )


if __name__ == "__main__":
    main()
