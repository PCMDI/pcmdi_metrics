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
    models_to_highlight_by_line=True,
    models_to_highlight_colors=None,
    models_to_highlight_labels=None,
    models_to_highlight_markers=["s", "o", "^", "*"],
    models_to_highlight_markers_size=10,
    fig=None,
    ax=None,
    figsize=(15, 5),
    show_boxplot=False,
    show_violin=False,
    violin_colors=("lightgrey", "pink"),
    violin_label=None,
    title=None,
    identify_all_models=True,
    xtick_labelsize=None,
    ytick_labelsize=None,
    colormap="viridis",
    num_color=20,
    legend_off=False,
    legend_ncol=6,
    legend_bbox_to_anchor=(0.5, -0.14),
    legend_loc="upper center",
    legend_fontsize=10,
    logo_rect=None,
    logo_off=False,
    model_names2=None,
    group1_name="group1",
    group2_name="group2",
    comparing_models=None,
    fill_between_lines=False,
    fill_between_lines_colors=("red", "green"),
    arrow_between_lines=False,
    arrow_between_lines_colors=("red", "green"),
    arrow_alpha=1,
    arrow_width=0.05,
    arrow_linewidth=0,
    arrow_head_width=0.15,
    arrow_head_length=0.15,
    vertical_center=None,
    vertical_center_line=False,
    vertical_center_line_label=None,
    ymax=None,
    ymin=None,
    debug=False,
):
    """
    Create a parallel coordinate plot for visualizing multi-dimensional data.

    .. image:: /_static/images/parallel_coordiate_plot_docstring_example.png
        :alt: Example parallel coordinate plot
        :align: center
        :width: 600px

    Parameters
    ----------
    data : ndarray
        2-d numpy array for metrics.
    metric_names : list
        Names of metrics for individual vertical axes (axis=1).
    model_names : list
        Name of models for markers/lines (axis=0).
    models_to_highlight : list, optional
        List of models to highlight as lines or markers.
    models_to_highlight_by_line : bool, optional
        If True, highlight as lines. If False, highlight as markers. Default is True.
    models_to_highlight_colors : list, optional
        List of colors for models to highlight as lines.
    models_to_highlight_labels : list, optional
        List of string labels for models to highlight as lines.
    models_to_highlight_markers : list, optional
        Matplotlib markers for models to highlight if as marker. Default is ["s", "o", "^", "*"].
    models_to_highlight_markers_size : float, optional
        Size of matplotlib markers for models to highlight if as marker. Default is 10.
    fig : matplotlib.figure.Figure, optional
        Figure instance to which the parallel coordinate plot is plotted.
    ax : matplotlib.axes.Axes, optional
        Axes instance to which the parallel coordinate plot is plotted.
    figsize : tuple, optional
        Figure size (width, height) in inches. Default is (15, 5).
    show_boxplot : bool, optional
        If True, show box and whiskers plot. Default is False.
    show_violin : bool, optional
        If True, show violin plot. Default is False.
    violin_colors : tuple or list, optional
        Two strings for colors of violin. Default is ("lightgrey", "pink").
    violin_label : str, optional
        Label for the violin plot when not split. Default is None.
    title : str, optional
        Plot title.
    identify_all_models : bool, optional
        If True, show and identify all models using markers. Default is True.
    xtick_labelsize : int or str, optional
        Fontsize for x-axis tick labels.
    ytick_labelsize : int or str, optional
        Fontsize for y-axis tick labels.
    colormap : str, optional
        Matplotlib colormap. Default is 'viridis'.
    num_color : int, optional
        Number of colors to use. Default is 20.
    legend_off : bool, optional
        If True, turn off legend. Default is False.
    legend_ncol : int, optional
        Number of columns for legend text. Default is 6.
    legend_bbox_to_anchor : tuple, optional
        Set legend box location. Default is (0.5, -0.14).
    legend_loc : str, optional
        Set legend box location. Default is "upper center".
    legend_fontsize : float, optional
        Legend font size. Default is 10.
    logo_rect : sequence of float, optional
        The dimensions [left, bottom, width, height] of the new Axes for logo.
    logo_off : bool, optional
        If True, turn off PMP logo. Default is False.
    model_names2 : list of str, optional
        Should be a subset of `model_names`. If given, violin plot will be split into 2 groups.
    group1_name : str, optional
        Name for the first group in split violin plot. Default is 'group1'.
    group2_name : str, optional
        Name for the second group in split violin plot. Default is 'group2'.
    comparing_models : tuple or list, optional
        Two strings for models to compare with colors filled between the two lines.
    fill_between_lines : bool, optional
        If True, fill color between lines for models in comparing_models. Default is False.
    fill_between_lines_colors : tuple or list, optional
        Two strings of colors for filled between the two lines. Default is ('red', 'green').
    arrow_between_lines : bool, optional
        If True, place arrows between two lines for models in comparing_models. Default is False.
    arrow_between_lines_colors : tuple or list, optional
        Two strings of colors for arrow between the two lines. Default is ('red', 'green').
    arrow_alpha : float, optional
        Transparency of arrow (fraction between 0 to 1). Default is 1.
    arrow_width : float, optional
        Width of arrow. Default is 0.05.
    arrow_linewidth : float, optional
        Width of arrow edge line. Default is 0.
    arrow_head_width : float, optional
        Width of arrow head. Default is 0.15.
    arrow_head_length : float, optional
        Length of arrow head. Default is 0.15.
    vertical_center : str or float or int, optional
        Adjust range of vertical axis to set center of vertical axis as median, mean, or given number.
    vertical_center_line : bool, optional
        If True, show median as line. Default is False.
    vertical_center_line_label : str, optional
        Label in legend for the horizontal vertical center line. If not given, it will be automatically assigned.
    ymax : int or float or str, optional
        Specify value of vertical axis top. If 'percentile', 95th percentile or extended for top.
    ymin : int or float or str, optional
        Specify value of vertical axis bottom. If 'percentile', 5th percentile or extended for bottom.
    debug : bool, optional
        If True, print debug information. Default is False.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The figure component of the plot.
    ax : matplotlib.axes.Axes
        The axes component of the plot.

    Notes
    -----
    This function creates a parallel coordinate plot for visualizing multi-dimensional data.
    It supports various customization options including highlighting specific models,
    adding violin plots, and comparing models with filled areas or arrows.

    The function uses matplotlib for plotting and can integrate with existing figure and axes objects.

    Author: Jiwoo Lee @ LLNL (2021. 7)

    Update history:

    - 2021-07 Plotting code created. Inspired by https://stackoverflow.com/questions/8230638/parallel-coordinates-plot-in-matplotlib
    - 2022-09 violin plots added
    - 2023-03 median centered option added
    - 2023-04 vertical center option diversified (median, mean, or given number)
    - 2024-03 parameter added for violin plot label
    - 2024-04 parameters added for arrow and option added for ymax/ymin setting
    - 2024-11 docstring cleaned up

    Examples
    --------
    >>> from pcmdi_metrics.graphics import parallel_coordinate_plot
    >>> import numpy as np
    >>> data = np.random.rand(10, 10)
    >>> metric_names = ['Metric' + str(i) for i in range(10)]
    >>> model_names = ['Model' + str(i) for i in range(10)]
    >>> fig, ax = parallel_coordinate_plot(data, metric_names, model_names, models_to_highlight=model_names[0])

    .. image:: /_static/images/parallel_coordiate_plot_docstring_example.png
        :alt: Example parallel coordinate plot
        :align: center
        :width: 600px

    Further examples can be found `here <https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/graphics/parallel_coordinate_plot#readme>`__.
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
    zs, zs_middle, N, ymins, ymaxs, df_stacked, df2_stacked = _data_transform(
        data,
        metric_names,
        model_names,
        model_names2=model_names2,
        group1_name=group1_name,
        group2_name=group2_name,
        vertical_center=vertical_center,
        ymax=ymax,
        ymin=ymin,
    )

    if debug:
        print("ymins:", ymins)
        print("ymaxs:", ymaxs)

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
                    if isinstance(violin_colors, tuple) or isinstance(
                        violin_colors, list
                    ):
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
                    cut=0,
                )

    # Line or marker
    num_color = min(len(model_names), num_color)
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

            if models_to_highlight_labels is not None:
                label = models_to_highlight_labels[mh_index]
            else:
                label = model

            if models_to_highlight_by_line:
                ax.plot(range(N), zs[j, :], "-", c=color, label=label, lw=3)
            else:
                ax.plot(
                    range(N),
                    zs[j, :],
                    models_to_highlight_markers[mh_index],
                    c=color,
                    label=label,
                    markersize=models_to_highlight_markers_size,
                )

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

    if vertical_center_line:
        if vertical_center_line_label is None:
            vertical_center_line_label = str(vertical_center)
        elif vertical_center_line_label == "off":
            vertical_center_line_label = None
        ax.plot(range(N), zs_middle, "-", c="k", label=vertical_center_line_label, lw=1)

    # Compare two models
    if comparing_models is not None:
        if isinstance(comparing_models, tuple) or (
            isinstance(comparing_models, list) and len(comparing_models) == 2
        ):
            x = range(N)
            m1 = model_names.index(comparing_models[0])
            m2 = model_names.index(comparing_models[1])
            y1 = zs[m1, :]
            y2 = zs[m2, :]

            # Fill between lines
            if fill_between_lines:
                ax.fill_between(
                    x,
                    y1,
                    y2,
                    where=(y2 > y1),
                    facecolor=fill_between_lines_colors[0],
                    interpolate=False,
                    alpha=0.5,
                )
                ax.fill_between(
                    x,
                    y1,
                    y2,
                    where=(y2 < y1),
                    facecolor=fill_between_lines_colors[1],
                    interpolate=False,
                    alpha=0.5,
                )

            # Add vertical arrows
            if arrow_between_lines:
                for xi, yi1, yi2 in zip(x, y1, y2):
                    if yi2 > yi1:
                        arrow_color = arrow_between_lines_colors[0]
                    elif yi2 < yi1:
                        arrow_color = arrow_between_lines_colors[1]
                    else:
                        arrow_color = None
                    arrow_length = yi2 - yi1
                    ax.arrow(
                        xi,
                        yi1,
                        0,
                        arrow_length,
                        color=arrow_color,
                        length_includes_head=True,
                        alpha=arrow_alpha,
                        width=arrow_width,
                        linewidth=arrow_linewidth,
                        head_width=arrow_head_width,
                        head_length=arrow_head_length,
                        zorder=999,
                    )

    ax.set_xlim(-0.5, N - 0.5)
    ax.set_xticks(range(N))
    ax.set_xticklabels(metric_names, fontsize=xtick_labelsize)
    ax.tick_params(axis="x", which="major", pad=7)
    ax.spines["right"].set_visible(False)
    ax.set_title(title, fontsize=18)

    if not legend_off:
        if violin_label is not None:
            # Get all lines for legend
            lines = [violin["bodies"][0]] + ax.lines
            # Get labels for legend
            labels = [violin_label] + [line.get_label() for line in ax.lines]
            # Remove unnessasary lines that its name starts with '_' to avoid the burden of warning message
            lines = [aa for aa, bb in zip(lines, labels) if not bb.startswith("_")]
            labels = [bb for bb in labels if not bb.startswith("_")]
            # Add legend
            ax.legend(
                lines,
                labels,
                loc=legend_loc,
                ncol=legend_ncol,
                bbox_to_anchor=legend_bbox_to_anchor,
                fontsize=legend_fontsize,
            )
        else:
            # Add legend
            ax.legend(
                loc=legend_loc,
                ncol=legend_ncol,
                bbox_to_anchor=legend_bbox_to_anchor,
                fontsize=legend_fontsize,
            )

    if not logo_off:
        fig, ax = add_logo(fig, ax, logo_rect)

    return fig, ax


def _quick_qc(data, model_names, metric_names, model_names2=None, debug=False):
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
    if debug:
        print("Passed a quick QC")


def _data_transform(
    data,
    metric_names,
    model_names,
    model_names2=None,
    group1_name="group1",
    group2_name="group2",
    vertical_center=None,
    ymax=None,
    ymin=None,
):
    # Data to plot
    ys = data  # stacked y-axis values
    N = ys.shape[1]  # number of vertical axis (i.e., =len(metric_names))

    if ymax is None:
        ymaxs = np.nanmax(ys, axis=0)  # maximum (ignore nan value)
    else:
        try:
            if isinstance(ymax, str) and ymax == "percentile":
                ymaxs = np.nanpercentile(ys, 95, axis=0)
            else:
                ymaxs = np.repeat(ymax, N)
        except ValueError:
            print(f"Invalid input for ymax: {ymax}")

    if ymin is None:
        ymins = np.nanmin(ys, axis=0)  # minimum (ignore nan value)
    else:
        try:
            if isinstance(ymin, str) and ymin == "percentile":
                ymins = np.nanpercentile(ys, 5, axis=0)
            else:
                ymins = np.repeat(ymin, N)
        except ValueError:
            print(f"Invalid input for ymin: {ymin}")

    ymeds = np.nanmedian(ys, axis=0)  # median
    ymean = np.nanmean(ys, axis=0)  # mean

    # Convert to float type for further calculations
    ymaxs = ymaxs.astype(float)
    ymins = ymins.astype(float)
    ymeds = ymeds.astype(float)
    ymean = ymean.astype(float)

    # Adjust vertical axis range to set center as median/mean/given number
    if vertical_center is not None:
        if vertical_center == "median":
            ymids = ymeds
        elif vertical_center == "mean":
            ymids = ymean
        elif isinstance(vertical_center, float) or isinstance(vertical_center, int):
            ymids = np.repeat(vertical_center, N)
        else:
            raise ValueError(f"vertical center {vertical_center} unknown.")

        for i in range(0, N):
            distance_from_middle = max(
                abs(ymaxs[i] - ymids[i]), abs(ymids[i] - ymins[i])
            )
            ymaxs[i] = ymids[i] + distance_from_middle
            ymins[i] = ymids[i] - distance_from_middle

    dys = ymaxs - ymins
    if ymin is None:
        ymins -= dys * 0.05  # add 5% padding below and above
    if ymax is None:
        ymaxs += dys * 0.05
    dys = ymaxs - ymins

    # Transform all data to be compatible with the main axis
    zs = np.zeros_like(ys)
    zs[:, 0] = ys[:, 0]
    zs[:, 1:] = (ys[:, 1:] - ymins[1:]) / dys[1:] * dys[0] + ymins[0]

    if vertical_center is not None:
        zs_middle = (ymids[:] - ymins[:]) / dys[:] * dys[0] + ymins[0]
    else:
        zs_middle = (ymaxs[:] - ymins[:]) / 2 / dys[:] * dys[0] + ymins[0]

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

    return zs, zs_middle, N, ymins, ymaxs, df_stacked, df2_stacked


def _to_pd_dataframe(
    data: np.ndarray,
    metric_names: list[str],
    model_names: list[str],
    model_names2: list[str] = None,
    group1_name: str = "group1",
    group2_name: str = "group2",
    debug=False,
) -> pd.DataFrame:
    """
    Converts data into a stacked pandas DataFrame for seaborn plotting.

    Parameters
    ----------
    data : np.ndarray
        2D array of data values, where rows correspond to `model_names` and columns to `metric_names`.
    metric_names : list of str
        List of metric names for DataFrame columns.
    model_names : list of str
        List of model names for DataFrame index.
    model_names2 : list of str, optional
        Secondary list of model names for alternate grouping.
    group1_name : str, default="group1"
        Name assigned to the group when `model_names2` is not matched.
    group2_name : str, default="group2"
        Name assigned to the group when `model_names2` is matched.
    debug : bool, default=False
        If True, print debug information.

    Returns
    -------
    pd.DataFrame
        Stacked DataFrame with columns: 'Model', 'Metric', 'value', and 'group'.
    """
    if debug:
        print("data.shape:", data.shape)

    # Check input validity
    if data.shape[1] != len(metric_names):
        raise ValueError(
            "Number of columns in `data` must match length of `metric_names`."
        )
    if data.shape[0] != len(model_names):
        raise ValueError("Number of rows in `data` must match length of `model_names`.")

    # Create DataFrame
    df = pd.DataFrame(data, columns=metric_names, index=model_names)

    # Stack without dropna (using new stack implementation)
    df_stacked = df.stack(future_stack=True).reset_index()
    df_stacked = df_stacked.rename(
        columns={"level_0": "Model", "level_1": "Metric", 0: "value"}
    )
    df_stacked["group"] = group1_name

    # Update group column based on model_names2
    if model_names2 is not None:
        for model2 in model_names2:
            df_stacked["group"] = np.where(
                (df_stacked.Model == model2), group2_name, df_stacked.group
            )
    return df_stacked
