import sys

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.cbook import flatten

from pcmdi_metrics.graphics import add_logo


def parallel_coordinate_plot(
    data,
    metric_names,
    model_names,
    models_to_highlight=list(),
    models_to_highlight_colors=None,
    fig=None,
    ax=None,
    figsize=(15, 5),
    show_boxplot=False,
    show_violin=False,
    violin_colors=("lightgrey", "pink"),
    title=None,
    identify_all_models=True,
    xtick_labelsize=None,
    ytick_labelsize=None,
    colormap="viridis",
    num_color=20,
    legend_off=False,
    logo_rect=None,
    logo_off=False,
    model_names2=None,
    group1_name="group1",
    group2_name="group2",
    comparing_models=None,
    fill_between_lines=False,
    fill_between_lines_colors=("green", "red"),
    median_centered=False,
    median_line=False,
):
    """
    Parameters
    ----------
    - `data`: 2-d numpy array for metrics
    - `metric_names`: list, names of metrics for individual vertical axes (axis=1)
    - `model_names`: list, name of models for markers/lines (axis=0)
    - `models_to_highlight`: list, default=None, List of models to highlight as lines
    - `models_to_highlight_colors`: list, default=None, List of colors for models to highlight as lines
    - `fig`: `matplotlib.figure` instance to which the parallel coordinate plot is plotted.
             If not provided, use current axes or create a new one.  Optional.
    - `ax`: `matplotlib.axes.Axes` instance to which the parallel coordinate plot is plotted.
            If not provided, use current axes or create a new one.  Optional.
    - `figsize`: tuple (two numbers), default=(15,5), image size
    - `show_boxplot`: bool, default=False, show box and wiskers plot
    - `show_violin`: bool, default=False, show violin plot
    - `violin_colors`: tuple or list containing two strings for colors of violin. Default=("lightgrey", "pink")
    - `title`: string, default=None, plot title
    - `identify_all_models`: bool, default=True. Show and identify all models using markers
    - `xtick_labelsize`: number, fontsize for x-axis tick labels (optional)
    - `ytick_labelsize`: number, fontsize for x-axis tick labels (optional)
    - `colormap`: string, default='viridis', matplotlib colormap
    - `num_color`: integer, default=20, how many color to use.
    - `legend_off`: bool, default=False, turn off legend
    - `logo_rect`: sequence of float. The dimensions [left, bottom, width, height] of the new Axes.
                   All quantities are in fractions of figure width and height.  Optional.
    - `logo_off`: bool, default=False, turn off PMP logo
    - `model_names2`: list of string, should be a subset of `model_names`.  If given, violin plot will be split into 2 groups. Optional.
    - `group1_name`: string, needed for violin plot legend if splited to two groups, for the 1st group. Default is 'group1'.
    - `group2_name`: string, needed for violin plot legend if splited to two groups, for the 2nd group. Default is 'group2'.
    - `comparing_models`: tuple or list containing two strings for models to compare with colors filled between the two lines.
    - `fill_between_lines`: bool, default=False, fill color between lines for models in comparing_models
    - `fill_between_lines_colors`: tuple or list containing two strings for colors filled between the two lines. Default=('green', 'red')
    - `median_centered`: bool, default=False, adjust range of vertical axis to set center of vertical axis as median
    - `median_line`: bool, default=False, show median as line

    Return
    ------
    - `fig`: matplotlib component for figure
    - `ax`: matplotlib component for axis

    Author: Jiwoo Lee @ LLNL (2021. 7)
    Update history: 
    2022-09 violin plots added
    2023-03 median centered option added
    Inspired by https://stackoverflow.com/questions/8230638/parallel-coordinates-plot-in-matplotlib
    """
    params = {
        "legend.fontsize": "large",
        "axes.labelsize": "x-large",
        "axes.titlesize": "x-large",
        "xtick.labelsize": "x-large",
        "ytick.labelsize": "x-large",
    }
    pylab.rcParams.update(params)

    # Quick initial QC
    _quick_qc(data, model_names, metric_names, model_names2=model_names2)

    # Transform data for plotting
    zs, zs_meds, N, ymins, ymaxs, df_stacked, df2_stacked = _data_transform(
        data,
        metric_names,
        model_names,
        model_names2=model_names2,
        group1_name=group1_name,
        group2_name=group2_name,
        median_centered=median_centered,
    )

    # Prepare plot
    if N > 20:
        if xtick_labelsize is None:
            xtick_labelsize = "large"
        if ytick_labelsize is None:
            ytick_labelsize = "large"
    else:
        if xtick_labelsize is None:
            xtick_labelsize = "x-large"
        if ytick_labelsize is None:
            ytick_labelsize = "x-large"
    params = {
        "legend.fontsize": "large",
        "axes.labelsize": "x-large",
        "axes.titlesize": "x-large",
        "xtick.labelsize": xtick_labelsize,
        "ytick.labelsize": ytick_labelsize,
    }
    pylab.rcParams.update(params)

    if fig is None and ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    axes = [ax] + [ax.twinx() for i in range(N - 1)]

    for i, ax_y in enumerate(axes):
        ax_y.set_ylim(ymins[i], ymaxs[i])
        ax_y.spines["top"].set_visible(False)
        ax_y.spines["bottom"].set_visible(False)
        if ax_y == ax:
            ax_y.spines["left"].set_position(("data", i))
        if ax_y != ax:
            ax_y.spines["left"].set_visible(False)
            ax_y.yaxis.set_ticks_position("right")
            ax_y.spines["right"].set_position(("data", i))

    # Population distribuion on each vertical axis
    if show_boxplot or show_violin:
        y = [zs[:, i] for i in range(N)]
        y_filtered = [
            y_i[~np.isnan(y_i)] for y_i in y
        ]  # Remove NaN value for box/violin plot

        # Box plot
        if show_boxplot:
            box = ax.boxplot(
                y_filtered, positions=range(N), patch_artist=True, widths=0.15
            )
            for item in ["boxes", "whiskers", "fliers", "medians", "caps"]:
                plt.setp(box[item], color="darkgrey")
            plt.setp(box["boxes"], facecolor="None")
            plt.setp(box["fliers"], markeredgecolor="darkgrey")

        # Violin plot
        if show_violin:
            if model_names2 is None:
                # matplotlib for regular violin plot
                violin = ax.violinplot(
                    y_filtered,
                    positions=range(N),
                    showmeans=False,
                    showmedians=False,
                    showextrema=False,
                )
                for pc in violin["bodies"]:
                    if isinstance(violin_colors, tuple) or isinstance(violin_colors, list):
                        violin_color = violin_colors[0]
                    else:
                        violin_color = violin_colors
                    pc.set_facecolor(violin_color)
                    pc.set_edgecolor("None")
                    pc.set_alpha(0.8)
            else:
                # seaborn for split violin plot
                violin = sns.violinplot(
                    data=df2_stacked,
                    x="Metric",
                    y="value",
                    ax=ax,
                    hue="group",
                    split=True,
                    linewidth=0.1,
                    scale="count",
                    scale_hue=False,
                    palette={
                        group1_name: violin_colors[0],
                        group2_name: violin_colors[1],
                    },
                )

    # Line or marker
    colors = [plt.get_cmap(colormap)(c) for c in np.linspace(0, 1, num_color)]
    marker_types = ["o", "s", "*", "^", "X", "D", "p"]
    markers = list(flatten([[marker] * len(colors) for marker in marker_types]))
    colors *= len(marker_types)
    mh_index = 0
    for j, model in enumerate(model_names):
        # to just draw straight lines between the axes:
        if model in models_to_highlight:
            
            if models_to_highlight_colors is not None:
                color = models_to_highlight_colors[mh_index]
            else:
                color = colors[j]
            ax.plot(range(N), zs[j, :], "-", c=color, label=model, lw=3)
            mh_index += 1
        else:
            if identify_all_models:
                ax.plot(
                    range(N),
                    zs[j, :],
                    markers[j],
                    c=colors[j],
                    label=model,
                    clip_on=False,
                )
    
    if median_line:            
        ax.plot(range(N), zs_meds, "-", c="k", label="median", lw=1)

    # Fill between lines
    if fill_between_lines and (comparing_models is not None):
        if isinstance(comparing_models, tuple) or (
            isinstance(comparing_models, list) and len(comparing_models) == 2
        ):
            x = range(N)
            m1 = model_names.index(comparing_models[0])
            m2 = model_names.index(comparing_models[1])
            y1 = zs[m1, :]
            y2 = zs[m2, :]
            ax.fill_between(
                x,
                y1,
                y2,
                where=y2 >= y1,
                facecolor=fill_between_lines_colors[0],
                interpolate=True,
                alpha=0.5,
            )
            ax.fill_between(
                x,
                y1,
                y2,
                where=y2 <= y1,
                facecolor=fill_between_lines_colors[1],
                interpolate=True,
                alpha=0.5,
            )

    ax.set_xlim(-0.5, N - 0.5)
    ax.set_xticks(range(N))
    ax.set_xticklabels(metric_names, fontsize=xtick_labelsize)
    ax.tick_params(axis="x", which="major", pad=7)
    ax.spines["right"].set_visible(False)
    ax.set_title(title, fontsize=18)

    if not legend_off:
        ax.legend(loc="upper center", ncol=6, bbox_to_anchor=(0.5, -0.14))

    if not logo_off:
        fig, ax = add_logo(fig, ax, logo_rect)

    return fig, ax


def _quick_qc(data, model_names, metric_names, model_names2=None):
    # Quick initial QC
    if data.shape[0] != len(model_names):
        sys.exit(
            "Error: data.shape[0], "
            + str(data.shape[0])
            + ", mismatch to len(model_names), "
            + str(len(model_names))
        )
    if data.shape[1] != len(metric_names):
        sys.exit(
            "Error: data.shape[1], "
            + str(data.shape[1])
            + ", mismatch to len(metric_names), "
            + str(len(metric_names))
        )
    if model_names2 is not None:
        # Check: model_names2 should be a subset of model_names
        for model in model_names2:
            if model not in model_names:
                sys.exit(
                    "Error: model_names2 should be a subset of model_names, but "
                    + model
                    + " is not in model_names"
                )
    print("Passed a quick QC")


def _data_transform(
    data,
    metric_names,
    model_names,
    model_names2=None,
    group1_name="group1",
    group2_name="group2",
    median_centered=False,
):
    # Data to plot
    ys = data  # stacked y-axis values
    N = ys.shape[1]  # number of vertical axis (i.e., =len(metric_names))
    ymins = np.nanmin(ys, axis=0)  # minimum (ignore nan value)
    ymaxs = np.nanmax(ys, axis=0)  # maximum (ignore nan value)
    ymeds = np.nanmedian(ys, axis=0)  # median
    if median_centered:
        for i in range(0, N):
            max_distance_from_median = max(abs(ymaxs[i] - ymeds[i]), abs(ymeds[i] - ymins[i]))
            ymaxs[i] = ymeds[i] + max_distance_from_median
            ymins[i] = ymeds[i] - max_distance_from_median
    dys = ymaxs - ymins
    ymins -= dys * 0.05  # add 5% padding below and above
    ymaxs += dys * 0.05
    dys = ymaxs - ymins

    # Transform all data to be compatible with the main axis
    zs = np.zeros_like(ys)
    zs[:, 0] = ys[:, 0]
    zs[:, 1:] = (ys[:, 1:] - ymins[1:]) / dys[1:] * dys[0] + ymins[0]
    
    zs_meds = (ymeds[:] - ymins[:]) / dys[:] * dys[0] + ymins[0]

    if model_names2 is not None:
        print("Models in the second group:", model_names2)

    # Pandas dataframe for seaborn plotting
    df_stacked = _to_pd_dataframe(
        data,
        metric_names,
        model_names,
        model_names2=model_names2,
        group1_name=group1_name,
        group2_name=group2_name,
    )
    df2_stacked = _to_pd_dataframe(
        zs,
        metric_names,
        model_names,
        model_names2=model_names2,
        group1_name=group1_name,
        group2_name=group2_name,
    )

    return zs, zs_meds, N, ymins, ymaxs, df_stacked, df2_stacked


def _to_pd_dataframe(
    data,
    metric_names,
    model_names,
    model_names2=None,
    group1_name="group1",
    group2_name="group2",
):
    print("data.shape:", data.shape)
    # Pandas dataframe for seaborn plotting
    df = pd.DataFrame(data, columns=metric_names, index=model_names)
    # Stack
    df_stacked = df.stack(dropna=False).reset_index()
    df_stacked = df_stacked.rename(
        columns={"level_0": "Model", "level_1": "Metric", 0: "value"}
    )
    df_stacked = df_stacked.assign(group=group1_name)
    if model_names2 is not None:
        for model2 in model_names2:
            df_stacked["group"] = np.where(
                (df_stacked.Model == model2), group2_name, df_stacked.group
            )
    return df_stacked
