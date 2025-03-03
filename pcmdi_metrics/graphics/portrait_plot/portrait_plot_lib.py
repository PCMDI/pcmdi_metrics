import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
import matplotlib.collections as collections
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure

from pcmdi_metrics.graphics import add_logo


def portrait_plot(
    data: Union[np.ndarray, List[np.ndarray]],
    xaxis_labels: List[str],
    yaxis_labels: List[str],
    fig: Optional[Figure] = None,
    ax: Optional[Axes] = None,
    annotate: bool = False,
    annotate_data: Optional[np.ndarray] = None,
    annotate_textcolors: Tuple[str, str] = ("black", "white"),
    annotate_textcolors_threshold: Union[Tuple[float, float], float] = (-2, 2),
    annotate_fontsize: int = 15,
    annotate_format: str = "{x:.2f}",
    figsize: Tuple[int, int] = (12, 10),
    vrange: Optional[Tuple[float, float]] = None,
    xaxis_fontsize: int = 15,
    yaxis_fontsize: int = 15,
    xaxis_tick_labels_top_and_bottom: bool = False,
    xticklabel_rotation: Union[int, float] = 45,
    inner_line_color: str = "k",
    inner_line_width: float = 0.5,
    cmap: str = "RdBu_r",
    cmap_bounds: Optional[List[float]] = None,
    cbar_label: Optional[str] = None,
    cbar_label_fontsize: int = 15,
    cbar_tick_fontsize: int = 12,
    cbar_kw: Dict[str, Any] = {},
    colorbar_off: bool = False,
    missing_color: str = "grey",
    invert_yaxis: bool = True,
    box_as_square: bool = False,
    legend_on: bool = False,
    legend_labels: Optional[List[str]] = None,
    legend_box_xy: Optional[Tuple[float, float]] = None,
    legend_box_size: Optional[float] = None,
    legend_lw: float = 1,
    legend_fontsize: int = 14,
    logo_rect: Optional[List[float]] = None,
    logo_off: bool = False,
    debug: bool = False,
) -> Union[Tuple[Figure, Axes, Colorbar], Tuple[Figure, Axes]]:
    """
    Create a portrait plot for visualizing 2D data arrays.

    .. image:: /_static/images/portrait_plot_4_triangles.png
        :alt: Example portrait plot with four triangles
        :align: center
        :width: 600px

    This function generates a versatile portrait plot that can display data as a heatmap,
    two-triangle, or four-triangle plot. It supports various customization options for
    annotations, axes, colorbar, legend, and more.

    Parameters
    ----------
    data : np.ndarray or List[np.ndarray]
        2D numpy array, list of 2D numpy arrays, or 3D numpy array (stacked 2D arrays).
    xaxis_labels : List[str]
        Labels for x-axis. Must match the x-axis dimension of data, or be empty to turn off labels.
    yaxis_labels : List[str]
        Labels for y-axis. Must match the y-axis dimension of data, or be empty to turn off labels.
    fig : Optional[Figure]
        Figure instance to plot on. If None, creates a new figure.
    ax : Optional[Axes]
        Axes instance to plot on. If None, uses current axes or creates new ones.
    annotate : bool
        If True, adds text annotations to the heatmap (only for non-triangle plots).
    annotate_data : Optional[np.ndarray]
        Data to use for annotations. If None, uses the plot data.
    annotate_textcolors : Tuple[str, str]
        Colors for annotation text.
    annotate_textcolors_threshold : Union[Tuple[float, float], float]
        Threshold values for applying annotation text colors.
    annotate_fontsize : int
        Font size for annotations.
    annotate_format : str
        Format string for annotation values.
    figsize : Tuple[int, int]
        Figure size in inches (width, height).
    vrange : Optional[Tuple[float, float]]
        Range of values for colorbar. If None, uses data min and max.
    xaxis_fontsize : int
        Font size for x-axis tick labels.
    yaxis_fontsize : int
        Font size for y-axis tick labels.
    xaxis_tick_labels_top_and_bottom : bool
        If True, displays x-axis tick labels on both top and bottom.
    xticklabel_rotation : Union[int, float]
        Rotation angle for x-axis tick labels.
    inner_line_color : str
        Color for inner lines in triangle plots.
    inner_line_width : float
        Line width for inner lines in triangle plots.
    cmap : str
        Colormap name.
    cmap_bounds : Optional[List[float]]
        Boundaries for discrete colors. If provided, applies discrete colormap.
    cbar_label : Optional[str]
        Label for colorbar.
    cbar_label_fontsize : int
        Font size for colorbar label.
    cbar_tick_fontsize : int
        Font size for colorbar tick labels.
    cbar_kw : Dict[str, Any]
        Additional keyword arguments for colorbar.
    colorbar_off : bool
        If True, turns off the colorbar.
    missing_color : str
        Color for missing data.
    invert_yaxis : bool
        If True, inverts the y-axis (0 at top).
    box_as_square : bool
        If True, makes each box square-shaped.
    legend_on : bool
        If True, displays a legend (for 2 or 4 triangle plots).
    legend_labels : Optional[List[str]]
        Labels for legend items.
    legend_box_xy : Optional[Tuple[float, float]]
        Position of legend box's upper-left corner in axes coordinates.
    legend_box_size : Optional[float]
        Size of legend box.
    legend_lw : float
        Line width for legend.
    legend_fontsize : int
        Font size for legend text.
    logo_rect : Optional[List[float]]
        Dimensions [left, bottom, width, height] of PMP logo in figure fraction.
    logo_off : bool
        If True, turns off the PMP logo.
    debug : bool
        If True, prints additional debugging information.

    Returns
    -------
    Union[Tuple[Figure, Axes, Colorbar], Tuple[Figure, Axes]]
        The figure, axes, and colorbar components (if colorbar is not turned off).

    Notes
    -----
    - The function supports different plot types based on the input data shape:
      1D array: heatmap, 2D array: two-triangle plot, 3D array: four-triangle plot.
    - Various customization options allow for flexible and detailed plot configurations.

    Author: Jiwoo Lee @ LLNL (2021. 7)

    Last update: 2024. 11.

    Examples
    --------
    Example 1: Create a heatmap-style portrait plot

    >>> from pcmdi_metrics.graphics import portrait_plot
    >>> import numpy as np
    >>> data = np.random.rand(10, 10)
    >>> xaxis_labels = [f'X{i}' for i in range(10)]
    >>> yaxis_labels = [f'Y{i}' for i in range(10)]
    >>> fig, ax, cbar = portrait_plot(data, xaxis_labels, yaxis_labels, cmap='RdBu_r')

    .. image:: /_static/images/portrait_plot_1.png
        :alt: Example portrait plot
        :align: center
        :width: 600px

    Example 2: Create a portrait plot with two triangles

    >>> data1 = np.random.rand(10, 10)
    >>> data2 = np.random.rand(10, 10)
    >>> data = [data1, data2]
    >>> fig, ax, cbar = portrait_plot(data, xaxis_labels, yaxis_labels, cmap='RdBu_r')

    .. image:: /_static/images/portrait_plot_2_triangles.png
        :alt: Example portrait plot with two triangles
        :align: center
        :width: 600px

    Example 3: Create a portrait plot with four triangles

    >>> data1 = np.random.rand(10, 10)
    >>> data2 = np.random.rand(10, 10)
    >>> data3 = np.random.rand(10, 10)
    >>> data4 = np.random.rand(10, 10)
    >>> data = [data1, data2, data3, data4]
    >>> fig, ax, cbar = portrait_plot(data, xaxis_labels, yaxis_labels, cmap='RdBu_r')

    .. image:: /_static/images/portrait_plot_4_triangles.png
        :alt: Example portrait plot with four triangles
        :align: center
        :width: 600px

    Further examples can be found `here <https://github.com/PCMDI/pcmdi_metrics/tree/main/pcmdi_metrics/graphics/portrait_plot#readme>`__.
    """

    # ----------------
    # Prepare plotting
    # ----------------
    data, num_divide = prepare_data(data, xaxis_labels, yaxis_labels, debug=debug)

    if num_divide not in [1, 2, 4]:
        sys.exit("Error: Number of (stacked) array is not 1, 2, or 4.")

    if annotate:
        if annotate_data is None:
            annotate_data = data
            num_divide_annotate = num_divide
        else:
            annotate_data, num_divide_annotate = prepare_data(
                annotate_data, xaxis_labels, yaxis_labels, debug=debug
            )
            if num_divide_annotate != num_divide:
                sys.exit("Error: annotate_data does not have same size as data")

    # ----------------
    # Ready to plot!!
    # ----------------
    if fig is None:
        fig = plt.figure(figsize=figsize)
    if ax is None:
        ax = fig.add_subplot(111)

    ax.set_facecolor(missing_color)

    if vrange is None:
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
    else:
        vmin = min(vrange)
        vmax = max(vrange)

    # Normalize colorbar
    if cmap_bounds is None:
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    else:
        cmap = plt.get_cmap(cmap)
        if "extend" in list(cbar_kw.keys()):
            extend = cbar_kw["extend"]
        else:
            extend = "neither"
        norm = matplotlib.colors.BoundaryNorm(cmap_bounds, cmap.N, extend=extend)

    # [1] Heatmap-style portrait plot (no triangles)
    if num_divide == 1:
        ax, im = heatmap(
            data,
            xaxis_labels,
            yaxis_labels,
            ax=ax,
            invert_yaxis=invert_yaxis,
            cmap=cmap,
            edgecolors="k",
            linewidth=0.5,
            norm=norm,
        )
        if annotate:
            if annotate_data is not None:
                if annotate_data.shape != data.shape:
                    sys.exit("Error: annotate_data has different size than data")
            else:
                annotate_data = data
            ax = annotate_heatmap(
                im,
                ax=ax,
                data=data,
                annotate_data=annotate_data,
                valfmt=annotate_format,
                textcolors=annotate_textcolors,
                threshold=annotate_textcolors_threshold,
                fontsize=annotate_fontsize,
            )

    # [2] Two triangle portrait plot
    elif num_divide == 2:
        # data order is upper, lower
        upper = data[0]
        lower = data[1]
        ax, im = triamatrix_wrap_up(
            upper,
            lower,
            ax,
            xaxis_labels=xaxis_labels,
            yaxis_labels=yaxis_labels,
            cmap=cmap,
            invert_yaxis=invert_yaxis,
            norm=norm,
            inner_line_color=inner_line_color,
            inner_line_width=inner_line_width,
        )

    # [4] Four triangle portrait plot
    elif num_divide == 4:
        # data order is clockwise from top: top, right, bottom, left
        top = data[0]
        right = data[1]
        bottom = data[2]
        left = data[3]
        ax, im = quatromatrix(
            top,
            right,
            bottom,
            left,
            ax=ax,
            tripcolorkw={
                "cmap": cmap,
                "norm": norm,
                "edgecolors": inner_line_color,
                "linewidth": inner_line_width,
            },
            xaxis_labels=xaxis_labels,
            yaxis_labels=yaxis_labels,
            invert_yaxis=invert_yaxis,
        )

    # X-axis tick labels
    if xaxis_tick_labels_top_and_bottom:
        # additional x-axis tick labels
        ax.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=True)
    else:
        # Let the horizontal axes labeling appear on top.
        ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)

    # Rotate and align top ticklabels
    plt.setp(
        [tick.label2 for tick in ax.xaxis.get_major_ticks()],
        rotation=xticklabel_rotation,
        ha="left",
        va="center",
        rotation_mode="anchor",
        fontsize=xaxis_fontsize,
    )

    if xaxis_tick_labels_top_and_bottom:
        # Rotate and align bottom ticklabels
        plt.setp(
            [tick.label1 for tick in ax.xaxis.get_major_ticks()],
            rotation=xticklabel_rotation,
            ha="right",
            va="center",
            rotation_mode="anchor",
            fontsize=xaxis_fontsize,
        )

    # Set font size for yaxis tick labels
    plt.setp(ax.get_yticklabels(), fontsize=yaxis_fontsize)

    # Legend
    if legend_on:
        if legend_labels is None:
            sys.exit("Error: legend_labels was not provided.")
        else:
            add_legend(
                num_divide,
                ax,
                legend_box_xy,
                legend_box_size,
                labels=legend_labels,
                lw=legend_lw,
                fontsize=legend_fontsize,
            )

    if box_as_square:
        ax.set_aspect("equal")

    if not logo_off:
        if logo_rect is None:
            logo_rect = [0.9, 0.15, 0.15, 0.15]
        fig, ax = add_logo(fig, ax, logo_rect)

    if not colorbar_off:
        # Create colorbar
        cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)

        # Label for colorbar
        if cbar_label is not None:
            if "orientation" in list(cbar_kw.keys()):
                if cbar_kw["orientation"] == "horizontal":
                    rotation = 0
                    ha = "center"
                    va = "top"
                    cbar.ax.set_xlabel(
                        cbar_label,
                        rotation=rotation,
                        ha=ha,
                        va=va,
                        fontsize=cbar_label_fontsize,
                    )
                else:
                    rotation = -90
                    ha = "center"
                    va = "bottom"
                    cbar.ax.set_ylabel(
                        cbar_label,
                        rotation=rotation,
                        ha=ha,
                        va=va,
                        fontsize=cbar_label_fontsize,
                    )
            else:
                rotation = -90
                ha = "center"
                va = "bottom"
                cbar.ax.set_ylabel(
                    cbar_label,
                    rotation=rotation,
                    ha=ha,
                    va=va,
                    fontsize=cbar_label_fontsize,
                )
            cbar.ax.tick_params(labelsize=cbar_tick_fontsize)
        return fig, ax, cbar
    else:
        return fig, ax


# ======================================================================
# Prepare data
# ----------------------------------------------------------------------
def prepare_data(data, xaxis_labels, yaxis_labels, debug=False):
    # In case data was given as list of arrays, convert it to numpy (stacked) array
    if isinstance(data, list):
        if debug:
            print("data type is list")
            print("len(data):", len(data))
        if len(data) == 1:  # list has only 1 array as element
            if isinstance(data[0], np.ndarray) and (len(data[0].shape) == 2):
                data = data[0]
                num_divide = 1
            else:
                sys.exit("Error: Element of given list is not in np.ndarray type")
        else:  # list has more than 1 arrays as elements
            data = np.stack(data)
            num_divide = len(data)

    # Now, data is expected to be be a numpy array (whether given or converted from list)
    if debug:
        print("data.shape:", data.shape)

    if data.shape[-1] != len(xaxis_labels) and len(xaxis_labels) > 0:
        sys.exit("Error: Number of elements in xaxis_label mismatchs to the data")

    if data.shape[-2] != len(yaxis_labels) and len(yaxis_labels) > 0:
        sys.exit("Error: Number of elements in yaxis_label mismatchs to the data")

    if isinstance(data, np.ndarray):
        # data = np.squeeze(data)
        if len(data.shape) == 2:
            num_divide = 1
        elif len(data.shape) == 3:
            num_divide = data.shape[0]
        else:
            print("data.shape:", data.shape)
            sys.exit("Error: data.shape is not right")
    else:
        sys.exit("Error: Converted or given data is not in np.ndarray type")

    if debug:
        print("num_divide:", num_divide)

    return data, num_divide


# ======================================================================
# Portrait plot 1: heatmap-style (no triangle)
# (Inspired from: https://matplotlib.org/devdocs/gallery/images_contours_and_fields/image_annotated_heatmap.html)
# ----------------------------------------------------------------------
def heatmap(data, xaxis_labels, yaxis_labels, ax=None, invert_yaxis=False, **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Parameters
    ----------
    data
        A 2D numpy array of shape (M, N).
    yaxis_labels
        A list or array of length M with the labels for the rows.
    xaxis_labels
        A list or array of length N with the labels for the columns.
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    invert_yaxis
        A bool to decide top-down or bottom-up order on y-axis
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if ax is None:
        ax = plt.gca()

    if invert_yaxis:
        ax.invert_yaxis()

    # Plot the heatmap
    im = ax.pcolormesh(data, **kwargs)

    # Show all ticks and label them with the respective list entries.
    ax.set_xticks(np.arange(data.shape[1]) + 0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[0]) + 0.5, minor=False)
    ax.set_xticklabels(xaxis_labels)
    ax.set_yticklabels(yaxis_labels)
    ax.tick_params(which="minor", bottom=False, left=False)

    return ax, im


def annotate_heatmap(
    im,
    ax,
    data=None,
    annotate_data=None,
    valfmt="{x:.2f}",
    textcolors=("black", "white"),
    threshold=None,
    **textkw,
):
    """
    A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    ax
        Matplotlib axis
    data
        Data used to color in the image.  If None, the image's data is used.  Optional.
    annotate_data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A pair of colors.  The first is used for values below a threshold,
        the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """
    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array().reshape(im._meshHeight, im._meshWidth)

    if annotate_data is None:
        annotate_data = data

    if threshold is None:
        threshold = (data.max()) / 2.0

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center", verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if type(threshold) is tuple:
                kw.update(
                    color=textcolors[
                        int(
                            (data[i, j] > max(threshold))
                            or (data[i, j] < min(threshold))
                        )
                    ]
                )
            else:
                kw.update(color=textcolors[int(data[i, j] > threshold)])
            text = ax.text(j + 0.5, i + 0.5, valfmt(annotate_data[i, j], None), **kw)
            texts.append(text)

    return ax


# ======================================================================
# Portrait plot 2 (two triangles)
# (Inspired from: https://stackoverflow.com/questions/44291155/plotting-two-distance-matrices-together-on-same-plot)
# ----------------------------------------------------------------------
def triamatrix_wrap_up(
    upper,
    lower,
    ax,
    xaxis_labels,
    yaxis_labels,
    cmap="viridis",
    vmin=-3,
    vmax=3,
    norm=None,
    invert_yaxis=True,
    inner_line_color="k",
    inner_line_width=0.5,
):
    # Colorbar range
    if norm is None:
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)

    # Triangles
    im = triamatrix(
        upper,
        ax,
        rot=270,
        cmap=cmap,
        norm=norm,
        edgecolors=inner_line_color,
        lw=inner_line_width,
    )
    im = triamatrix(
        lower,
        ax,
        rot=90,
        cmap=cmap,
        norm=norm,
        edgecolors=inner_line_color,
        lw=inner_line_width,
    )
    ax.set_xlim(-0.5, upper.shape[1] - 0.5)
    ax.set_ylim(-0.5, upper.shape[0] - 0.5)

    if invert_yaxis:
        ax.invert_yaxis()

    ax.set_xticks(np.arange(upper.shape[1]))
    ax.set_yticks(np.arange(upper.shape[0]))

    ax.set_xticklabels(xaxis_labels)
    ax.set_yticklabels(yaxis_labels)

    return ax, im


def triatpos(pos=(0, 0), rot=0):
    r = np.array([[-1, -1], [1, -1], [1, 1], [-1, -1]]) * 0.5
    rm = [
        [np.cos(np.deg2rad(rot)), -np.sin(np.deg2rad(rot))],
        [np.sin(np.deg2rad(rot)), np.cos(np.deg2rad(rot))],
    ]
    r = np.dot(rm, r.T).T
    r[:, 0] += pos[0]
    r[:, 1] += pos[1]
    return r


def triamatrix(a, ax, rot=0, cmap="viridis", **kwargs):
    segs = []
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            segs.append(triatpos((j, i), rot=rot))
    col = collections.PolyCollection(segs, cmap=cmap, **kwargs)
    col.set_array(a.flatten())
    ax.add_collection(col)
    return col


# ======================================================================
# Portrait plot 4 (four triangles)
# (Inspired from: https://stackoverflow.com/questions/44666679/something-like-plt-matshow-but-with-triangles)
# ----------------------------------------------------------------------
def quatromatrix(
    top,
    right,
    bottom,
    left,
    ax=None,
    tripcolorkw={},
    xaxis_labels=None,
    yaxis_labels=None,
    invert_yaxis=True,
):
    if ax is None:
        ax = plt.gca()

    n = left.shape[0]
    m = left.shape[1]

    a = np.array([[0, 0], [0, 1], [0.5, 0.5], [1, 0], [1, 1]])
    tr = np.array([[0, 1, 2], [0, 2, 3], [2, 3, 4], [1, 2, 4]])

    A = np.zeros((n * m * 5, 2))
    Tr = np.zeros((n * m * 4, 3))

    for i in range(n):
        for j in range(m):
            k = i * m + j
            A[k * 5 : (k + 1) * 5, :] = np.c_[a[:, 0] + j, a[:, 1] + i]
            Tr[k * 4 : (k + 1) * 4, :] = tr + k * 5

    if invert_yaxis:
        ax.invert_yaxis()
        C = np.c_[
            left.flatten(), top.flatten(), right.flatten(), bottom.flatten()
        ].flatten()
    else:
        C = np.c_[
            left.flatten(), bottom.flatten(), right.flatten(), top.flatten()
        ].flatten()

    # Prevent coloring missing data
    C = np.ma.array(C, mask=np.isnan(C))

    tripcolor = ax.tripcolor(A[:, 0], A[:, 1], Tr, facecolors=C, **tripcolorkw)

    ax.margins(0)

    if xaxis_labels is not None:
        x_loc = list_between_elements(np.arange(left.shape[1] + 1))
        ax.set_xticks(x_loc)
        ax.set_xticklabels(xaxis_labels)
    if yaxis_labels is not None:
        y_loc = list_between_elements(np.arange(left.shape[0] + 1))
        ax.set_yticks(y_loc)
        ax.set_yticklabels(yaxis_labels)

    return ax, tripcolor


def list_between_elements(a):
    a_between = []
    for i in range(len(a)):
        try:
            tmp = (a[i] + a[i + 1]) / 2.0
            a_between.append(tmp)
        except Exception:
            pass
    return a_between


# ======================================================================
# Portrait plot legend (four/two triangles)
# ======================================================================
def add_legend(
    num_divide, ax, box_xy=None, box_size=None, labels=None, lw=1, fontsize=14
):
    if box_xy is None:
        box_x = ax.get_xlim()[1] * 1.25
        box_y = ax.get_ylim()[1]
    else:
        # Convert axes coordinate to data coordinate
        # Ref: https://matplotlib.org/stable/tutorials/advanced/transforms_tutorial.html
        box_x, box_y = ax.transLimits.inverted().transform(box_xy)

    if box_size is None:
        box_size = 1.5

    if num_divide == 4:
        if labels is None:
            labels = ["TOP", "RIGHT", "BOTTOM", "LEFT"]
        ax.add_patch(
            plt.Polygon(
                [
                    [box_x, box_y],
                    [box_x + box_size / 2.0, box_y + box_size / 2],
                    [box_x + box_size, box_y],
                ],
                color="k",
                fill=False,
                clip_on=False,
                lw=lw,
            )
        )
        ax.add_patch(
            plt.Polygon(
                [
                    [box_x + box_size, box_y],
                    [box_x + box_size / 2.0, box_y + box_size / 2],
                    [box_x + box_size, box_y + box_size],
                ],
                color="k",
                fill=False,
                clip_on=False,
                lw=lw,
            )
        )
        ax.add_patch(
            plt.Polygon(
                [
                    [box_x + box_size, box_y + box_size],
                    [box_x + box_size / 2.0, box_y + box_size / 2],
                    [box_x, box_y + box_size],
                ],
                color="k",
                fill=False,
                clip_on=False,
                lw=lw,
            )
        )
        ax.add_patch(
            plt.Polygon(
                [
                    [box_x, box_y],
                    [box_x + box_size / 2.0, box_y + box_size / 2],
                    [box_x, box_y + box_size],
                ],
                color="k",
                fill=False,
                clip_on=False,
                lw=lw,
            )
        )
        ax.text(
            box_x + box_size * 0.5,
            box_y + box_size * 0.2,
            labels[0],
            ha="center",
            va="center",
            fontsize=fontsize,
        )
        ax.text(
            box_x + box_size * 0.8,
            box_y + box_size * 0.5,
            labels[1],
            ha="center",
            va="center",
            fontsize=fontsize,
        )
        ax.text(
            box_x + box_size * 0.5,
            box_y + box_size * 0.8,
            labels[2],
            ha="center",
            va="center",
            fontsize=fontsize,
        )
        ax.text(
            box_x + box_size * 0.2,
            box_y + box_size * 0.5,
            labels[3],
            ha="center",
            va="center",
            fontsize=fontsize,
        )
    elif num_divide == 2:
        if labels is None:
            labels = ["UPPER", "LOWER"]
        ax.add_patch(
            plt.Polygon(
                [[box_x, box_y], [box_x, box_y + box_size], [box_x + box_size, box_y]],
                color="k",
                fill=False,
                clip_on=False,
                lw=lw,
            )
        )
        ax.add_patch(
            plt.Polygon(
                [
                    [box_x + box_size, box_y + box_size],
                    [box_x, box_y + box_size],
                    [box_x + box_size, box_y],
                ],
                color="k",
                fill=False,
                clip_on=False,
                lw=lw,
            )
        )
        ax.text(
            box_x + box_size * 0.05,
            box_y + box_size * 0.2,
            labels[0],
            ha="left",
            va="center",
            fontsize=fontsize,
        )
        ax.text(
            box_x + box_size * 0.95,
            box_y + box_size * 0.8,
            labels[1],
            ha="right",
            va="center",
            fontsize=fontsize,
        )
