#!/usr/bin/env python
import argparse
import glob
import json
import os

import matplotlib.pyplot as plt
import numpy as np

# ----------------
# Load Metrics
# ----------------
parser = argparse.ArgumentParser(
    prog="sea_ice_figures.py", description="Create figure for sea ice metrics"
)
parser.add_argument(
    "--filelist",
    dest="filelist",
    default="sea_ice_metrics.json",
    type=str,
    help="Filename of sea ice metrics to glob. Permitted to use '*'",
)
parser.add_argument(
    "--output_path",
    dest="output_path",
    default=".",
    type=str,
    help="The directory at which to write figure file",
)
args = parser.parse_args()

filelist = args.filelist
metrics_output_path = args.output_path

model_list = []
print(filelist)
metrics = {"RESULTS": {}}
for metrics_file in glob.glob(filelist):
    with open(metrics_file) as mf:
        results = json.load(mf)
    for item in results["DIMENSIONS"]["model"]:
        model_list.append(item)
    metrics["RESULTS"].update(results["RESULTS"])

model_list.sort()
tmp = model_list[0]
reference_data_set = list(metrics["RESULTS"][tmp]["arctic"]["model_mean"].keys())[0]

# ----------------
# Make figure
# ----------------
sector_list = ["Arctic", "Antarctic"]
sector_short = ["arctic", "antarctic"]
fig7, ax7 = plt.subplots(2, 1, figsize=(5, 4))
mlabels = model_list
ind = np.arange(len(mlabels))  # the x locations for the groups
width = 0.7
n = len(ind)
for inds, sector in enumerate(sector_list):
    # Assemble data
    mse_clim = []
    mse_ext = []
    reg_clim = []
    reg_ext = []
    rgn = sector_short[inds]
    for nmod, model in enumerate(model_list):
        mse_clim.append(
            float(
                metrics["RESULTS"][model][rgn]["model_mean"][reference_data_set][
                    "monthly_clim"
                ]["mse"]
            )
        )
        mse_ext.append(
            float(
                metrics["RESULTS"][model][rgn]["model_mean"][reference_data_set][
                    "total_extent"
                ]["mse"]
            )
        )
        reg_clim.append(
            float(
                metrics["RESULTS"][model][rgn]["model_mean"][reference_data_set][
                    "monthly_clim"
                ]["sector_mse"]
            )
        )
        reg_ext.append(
            float(
                metrics["RESULTS"][model][rgn]["model_mean"][reference_data_set][
                    "total_extent"
                ]["sector_mse"]
            )
        )

    # plot bars
    ax7[inds].bar(
        ind,
        mse_ext,
        width,
        color="r",
        edgecolor="k",
        linewidth=0.1,
        label="Ann. Mean",
        bottom=np.zeros(np.shape(mse_ext)),
    )
    ax7[inds].bar(
        ind,
        mse_clim,
        width,
        color="b",
        edgecolor="k",
        linewidth=0.1,
        label="Ann. Cycle",
        bottom=mse_ext,
    )
    bottom = [mse_ext[x] + mse_clim[x] for x in range(0, len(mse_ext))]
    ax7[inds].bar(
        ind,
        reg_ext,
        width,
        color="y",
        edgecolor="k",
        linewidth=0.1,
        label="Ann. Mean Reg.",
        bottom=bottom,
    )
    bottom = [mse_ext[x] + mse_clim[x] + reg_ext[x] for x in range(0, len(mse_ext))]
    ax7[inds].bar(
        ind,
        reg_clim,
        width,
        color="g",
        edgecolor="k",
        linewidth=0.1,
        label="Ann. Cycle Reg.",
        bottom=bottom,
    )

    # X axis label
    if inds == len(sector_list) - 1:
        ax7[inds].set_xticks(ind, mlabels, rotation=90, size=4, weight="bold")
    else:
        ax7[inds].set_xticks(ind, labels="")
    ax7[inds].set_xlim(-1, len(mse_ext))

    # Y axis
    tmp = [
        mse_ext[x] + mse_clim[x] + reg_ext[x] + reg_clim[x]
        for x in range(0, len(mse_ext))
    ]
    datamax = np.nanmax(np.array(tmp))
    ymax = (datamax) * 1.05
    ax7[inds].set_ylim(0.0, ymax)
    ticks = range(0, round(ymax), 10)
    labels = [str(round(x, 0)) for x in ticks]
    ax7[inds].set_yticks(ticks, labels, fontsize=5)

    # subplot frame styling
    ax7[inds].tick_params(color=[0.3, 0.3, 0.3])
    for spine in ax7[inds].spines.values():
        spine.set_edgecolor([0.3, 0.3, 0.3])
        spine.set_linewidth(0.5)
    # labels etc
    ax7[inds].set_ylabel("10${^1}{^2}$km${^4}$", size=6, weight="bold")
    ax7[inds].grid(True, linestyle=":", linewidth=0.5)
    ax7[inds].annotate(
        sector,
        (0.35, 0.85),
        xycoords="axes fraction",
        size=6,
        weight="bold",
        bbox=dict(facecolor="white", edgecolor="white", pad=1),
    )

# Add legend, save figure
leg = ax7[0].legend(loc="upper right", fontsize=5, edgecolor=[0.3, 0.3, 0.3])
leg.get_frame().set_linewidth(0.5)  # legend styling
t = plt.suptitle(
    "Mean Square Error relative to " + reference_data_set, fontsize=8, y=0.93
)
plt.tight_layout()
figfile = os.path.join(metrics_output_path, "total_MSE_bar_chart.png")
plt.savefig(figfile, dpi=600)
print("Figure written to ", figfile)
print("Done")
