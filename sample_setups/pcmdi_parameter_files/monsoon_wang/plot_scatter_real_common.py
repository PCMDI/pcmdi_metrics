import json
import os

import matplotlib.pyplot as plt
import numpy as np
from common_model import get_common_model


def read_stats_old(json_file, region_name, stats_name):
    with open(json_file, "r") as f:
        data = json.load(f)

    cor_values = []

    for model, regions in data.items():
        for region, stats in regions.items():
            # if region == "EASM" and "rmsn" in stats:
            #    cor_values.append(float(stats["rmsn"]))
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
            # if 'EASM' in regions and 'rmsn' in regions['EASM']:
            #    model_rmsn.append(float(regions['EASM']['rmsn']))
            if region_name in regions and stats_name in regions[region_name]:
                model_rmsn.append(float(regions[region_name][stats_name]))

        rmsn_values.append(model_rmsn)
        model_keys.append(model)

    return rmsn_values, model_keys


region = "EASM"


stat = "rmsn"
# stat = 'cor'
# stat = 'threat_score'

model_list = []
model_list_common = []

directory = "CMIP_results/"

json_file = os.path.join(
    "CMIP_results", "combined_results_" + "CMIP5" + "_" + region + ".json"
)

cmip5, model_keys = read_stats(json_file, region, stat)

model_list.extend(model_keys)
keys_5 = model_keys

json_file = os.path.join(
    "CMIP_results", "combined_results_" + "CMIP6" + "_" + region + ".json"
)

cmip6, model_keys = read_stats(json_file, region, stat)
keys_6 = model_keys

model_list.extend(model_keys)

cmip56 = cmip5 + cmip6

keys_5_common, keys_6_common = get_common_model(keys_5, keys_6)

cmip5_common_index = [keys_5.index(item) for item in keys_5_common]
cmip6_common_index = [keys_6.index(item) for item in keys_6_common]

cmip5_common = [cmip5[index] for index in cmip5_common_index]
cmip6_common = [cmip6[index] for index in cmip6_common_index]

model_list_common.extend(keys_5_common)
model_list_common.extend(keys_6_common)

cmip56_common = cmip5_common + cmip6_common

# -------------------------------------------
cmip5 = cmip5_common
cmip6 = cmip6_common
cmip56 = cmip56_common
model_list = model_list_common
# -------------------------------------------


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
