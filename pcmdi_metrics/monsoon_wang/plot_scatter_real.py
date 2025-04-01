import json
import os

import matplotlib.pyplot as plt
import numpy as np


def read_stats_old(json_file, region_name, stats_name):
    with open(json_file, "r") as f:
        data = json.load(f)

    cor_values = []

    for model, regions in data.items():
        for region, stats in regions.items():
            if region == region_name and stats_name in stats:
                cor_values.append(float(stats[stats_name]))

    return cor_values


def read_stats(json_file, region_name, stats_name):
    with open(json_file, "r") as f:
        data = json.load(f)

    rmsn_values = []
    model_keys = []

    for model, realizations in data.items():
        model_rmsn = []

        for realization, regions in realizations.items():
            if region_name in regions and stats_name in regions[region_name]:
                model_rmsn.append(float(regions[region_name][stats_name]))

        rmsn_values.append(model_rmsn)
        model_keys.append(model)

    return rmsn_values, model_keys


region = "SAFM"


stat = "rmsn"
# stat = 'cor'
# stat = 'threat_score'

model_list = []

directory = "CMIP_results/"

json_file = os.path.join(
    "CMIP_results", "combined_results_" + "CMIP5" + "_" + region + ".json"
)

cmip5, model_keys = read_stats(json_file, region, stat)

model_list.extend(model_keys)

json_file = os.path.join(
    "CMIP_results", "combined_results_" + "CMIP6" + "_" + region + ".json"
)

cmip6, model_keys = read_stats(json_file, region, stat)

model_list.extend(model_keys)

cmip56 = cmip5 + cmip6


medians = [np.median(row) for row in cmip56]

medians_cmip5 = [np.median(row) for row in cmip5]
medians_cmip6 = [np.median(row) for row in cmip6]

median_cmip5 = np.median(medians_cmip5)
median_cmip6 = np.median(medians_cmip6)

##################################################
fig, ax = plt.subplots(figsize=(10, 6))


x1 = np.arange(len(medians_cmip5))
x2 = np.arange(len(medians_cmip6)) + len(medians_cmip5)

bars1 = ax.bar(x1, medians_cmip5, width=0.7, label="CMIP5", color="skyblue")
bars2 = ax.bar(x2, medians_cmip6, width=0.7, label="CMIP6", color="lightgreen")

for i, (row, model_key) in enumerate(zip(cmip56, model_list)):
    ax.scatter([i] * len(row), row, color="LightCoral", zorder=2, s=3)


ax.axhline(
    median_cmip5,
    color="skyblue",
    linestyle="--",
    label=f"Median CMIP5: {median_cmip5:.2f}",
)
ax.axhline(
    median_cmip6,
    color="lightgreen",
    linestyle="--",
    label=f"Median CMIP6: {median_cmip6:.2f}",
)


ax.set_xticks(range(len(cmip56)))
ax.set_xticklabels(model_list, rotation=45, ha="right", fontsize=5)

ax.set_ylabel(f"{stat}", fontsize=15)
ax.set_title(
    f"Realization Median of {stat} of Monsoon Precipitation Intensity, "
    + region
    + ", ref=GPCP",
    fontsize=12,
)

ax.legend(labelspacing=0.2, borderpad=0.3, markerscale=0.5, fontsize=10, frameon=False)

plt.tight_layout()
plt.show()
