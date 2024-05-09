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
sector_list = [
    "Central Arctic Sector",
    "North Atlantic Sector",
    "North Pacific Sector",
    "Indian Ocean Sector",
    "South Atlantic Sector",
    "South Pacific Sector",
]
sector_short = ["ca", "na", "np", "io", "sa", "sp"]
fig7, ax7 = plt.subplots(6, 1, figsize=(5, 9))
mlabels = model_list
ind = np.arange(len(mlabels))  # the x locations for the groups
width = 0.3
n = len(ind)
for inds, sector in enumerate(sector_list):
    # Assemble data
    mse_clim = []
    mse_ext = []
    clim_range = []
    ext_range = []
    clim_err_x = []
    clim_err_y = []
    ext_err_y = []
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
        # Get spread, only if there are multiple realizations
        if len(metrics["RESULTS"][model][rgn].keys()) > 2:
            for r in metrics["RESULTS"][model][rgn]:
                if r != "model_mean":
                    clim_err_x.append(ind[nmod])
                    clim_err_y.append(
                        float(
                            metrics["RESULTS"][model][rgn][r][reference_data_set][
                                "monthly_clim"
                            ]["mse"]
                        )
                    )
                    ext_err_y.append(
                        float(
                            metrics["RESULTS"][model][rgn][r][reference_data_set][
                                "total_extent"
                            ]["mse"]
                        )
                    )

    # plot data
    if len(model_list) < 4:
        mark_size = 9
    elif len(model_list) < 12:
        mark_size = 3
    else:
        mark_size = 1
    ax7[inds].bar(ind - width / 2.0, mse_clim, width, color="b", label="Ann. Cycle")
    ax7[inds].bar(ind, mse_ext, width, color="r", label="Ann. Mean")

    # X axis label
    if inds == len(sector_list) - 1:
        ax7[inds].set_xticks(ind + width / 2.0, mlabels, rotation=90, size=7)
    else:
        ax7[inds].set_xticks(ind + width / 2.0, labels="")

    # Y axis
    datamax = np.nanmax(np.concatenate((np.array(mse_clim), np.array(mse_ext))))
    ymax = (datamax) * 1.3
    ax7[inds].set_ylim(0.0, ymax)
    print(ymax)
    if ymax < 0.1:
        ticks = np.linspace(0, 0.1, 6)
        labels = [str(round(x, 3)) for x in ticks]
    elif ymax < 1:
        ticks = np.linspace(0, 1, 5)
        labels = [str(round(x, 1)) for x in ticks]
    elif ymax < 4:
        ticks = np.linspace(0, round(ymax), num=round(ymax / 2) * 2 + 1)
        labels = [str(round(x, 1)) for x in ticks]
    elif ymax > 10:
        ticks = range(0, round(ymax), 5)
        labels = [str(round(x, 0)) for x in ticks]
    else:
        ticks = range(0, round(ymax))
        labels = [str(round(x, 0)) for x in ticks]
    ax7[inds].set_yticks(ticks, labels, fontsize=8)

    # labels etc
    ax7[inds].set_ylabel("10${^1}{^2}$km${^4}$", size=8)
    ax7[inds].grid(True, linestyle=":")
    ax7[inds].annotate(
        sector,
        (0.35, 0.8),
        xycoords="axes fraction",
        size=9,
    )
    aw = 0.07

# Add legend, save figure
ax7[0].legend(loc="upper right", fontsize=6)
plt.suptitle("Mean Square Error relative to " + reference_data_set, y=0.91)
figfile = os.path.join(metrics_output_path, "MSE_bar_chart.png")
plt.savefig(figfile)
print("Figure written to ", figfile)
print("Done")
