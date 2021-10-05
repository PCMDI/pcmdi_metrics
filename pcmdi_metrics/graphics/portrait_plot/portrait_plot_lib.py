from pcmdi_metrics.graphics import add_logo
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import sys


def portrait_plot(data,
                  xaxis_labels,
                  yaxis_labels,
                  fig=None, ax=None,
                  annotate=False, annotate_data=None, annotate_fontsize=15,
                  annotate_format="{x:.2f}",
                  figsize=(12, 10), vrange=None,
                  xaxis_fontsize=15, yaxis_fontsize=15,
                  cmap="RdBu_r",
                  cmap_bounds=None,
                  cbar_label=None,
                  cbar_label_fontsize=15,
                  cbar_tick_fontsize=12,
                  cbar_kw={},
                  colorbar_off=False,
                  missing_color='grey',
                  invert_yaxis=True,
                  box_as_square=False,
                  legend_on=False,
                  legend_labels=None,
                  legend_box_xy=None,
                  legend_box_size=None,
                  legend_lw=1,
                  legend_fontsize=14,
                  logo_rect=None,
                  logo_off=False,
                  debug=False):
    """
    Parameters
    ----------
    - `data`: 2d numpy array, a list of 2d numpy arrays, or a 3d numpy array (i.e. stacked 2d numpy arrays)
    - `xaxis_labels`: list of strings, labels for xaixs. Number of list element must consistent to x-axis,
                      or 0 (empty list) to turn off xaxis tick labels
    - `yaxis_labels`: list of strings, labels for yaxis. Number of list element must consistent to y-axis,
                      or 0 (empty list) to turn off yaxis tick labels
    - `fig`: `matplotlib.figure` instance to which the portrait plot is plotted.
             If not provided, use current axes or create a new one.  Optional.
    - `ax`: `matplotlib.axes.Axes` instance to which the portrait plot is plotted.
            If not provided, use current axes or create a new one.  Optional.
    - `annotate`: bool, default=False, add annotating text if true,
                  but work only for heatmap style map (i.e., no triangles)
    - `annotate_data`: 2d numpy array, default=None. If None, the image's data is used.  Optional.
    - `annotate_fontsize`: number (int/float), default=15. Font size for annotation
    - `annotate_format`: format for annotate value, default="{x:.2f}"
    - `figsize`: tuple of two numbers (width, height), default=(12, 10), figure size in inches
    - `vrange`: tuple of two numbers, range of value for colorbar.  Optional.
    - `xaxis_fontsize`: number, default=15, font size for xaxis tick labels
    - `yaxis_fontsize`: number, default=15, font size for yaxis tick labels
    - `cmap`: string, default="RdBu_r", name of matplotlib colormap
    - `cmap_bounds`: list of numbers.  If given, discrete colors are applied.  Optional.
    - `cbar_label`: string, default=None, label for colorbar
    - `cbar_label_fontsize`: number, default=15, font size for colorbar labels
    - `cbar_tick_fontsize`: number, default=12, font size for colorbar tick labels
    - `cbar_kw`: A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    - `colorbar_off`: Trun off colorbar if True.  Optional.
    - `missing_color`: color, default="grey", `matplotlib.axes.Axes.set_facecolor` parameter
    - `invert_yaxis`: bool, default=True, place y=0 at top on the plot
    - `box_as_square`: bool, default=False, make each box as square
    - `legend_on`: bool, default=False, show legend (only for 2 or 4 triangles portrait plot)
    - `legend_labels`: list of strings, legend labels for triangls
    - `legend_box_xy`: tuple of numbers, position of legend box's upper-left corner
                       (lower-left if `invert_yaxis=False`), in `axes` coordinate
    - `legend_box_size`: number, size of legend box
    - `legend_lw`: number, line width of legend, default=1
    - `legend_fontsize`: number, font size for legend, default=14
    - `logo_rect`: sequence of float. The dimensions [left, bottom, width, height] of the the PMP logo.
                   All quantities are in fractions of figure width and height.  Optional
    - `logo_off`: bool, default=False, turn off PMP logo
    - `debug`: bool, default=False, if true print more message when running that help debugging

    Return
    ------
    - `fig`: matplotlib component for figure
    - `ax`: matplotlib component for axis
    - `cbar`: matplotlib component for colorbar (not returned if colorbar_off=True)

    Author: Jiwoo Lee @ LLNL (2021. 7)
    """

    # ----------------
    # Prepare plotting
    # ----------------
    data, num_divide = prepare_data(data, xaxis_labels, yaxis_labels, debug)

    if num_divide not in [1, 2, 4]:
        sys.exit('Error: Number of (stacked) array is not 1, 2, or 4.')

    if annotate:
        if annotate_data is None:
            annotate_data = data
            num_divide_annotate = num_divide
        else:
            annotate_data, num_divide_annotate = prepare_data(annotate_data, xaxis_labels, yaxis_labels, debug)
            if num_divide_annotate != num_divide:
                sys.exit('Error: annotate_data does not have same size as data')

    # ----------------
    # Ready to plot!!
    # ----------------
    if fig is None and ax is None:
        fig, ax = plt.subplots(figsize=figsize)

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
        norm = matplotlib.colors.BoundaryNorm(cmap_bounds, cmap.N, **cbar_kw)

    # [1] Heatmap-style portrait plot (no triangles)
    if num_divide == 1:
        ax, im = heatmap(data, yaxis_labels, xaxis_labels,
                         ax=ax,
                         invert_yaxis=invert_yaxis,
                         cmap=cmap,
                         edgecolors='k', linewidth=0.5,
                         norm=norm)
        if annotate:
            if annotate_data is not None:
                if (annotate_data.shape != data.shape):
                    sys.exit('Error: annotate_data has different size than data')
            else:
                annotate_data = data
            annotate_heatmap(im, ax=ax,
                             data=data,
                             annotate_data=annotate_data,
                             valfmt=annotate_format, threshold=(2, -2),
                             fontsize=annotate_fontsize)

    # [2] Two triangle portrait plot
    elif num_divide == 2:
        # data order is upper, lower
        upper = data[0]
        lower = data[1]
        ax, im = triamatrix_wrap_up(upper, lower, ax,
                                    xaxis_labels=xaxis_labels,
                                    yaxis_labels=yaxis_labels,
                                    cmap=cmap,
                                    invert_yaxis=invert_yaxis,
                                    norm=norm)

    # [4] Four triangle portrait plot
    elif num_divide == 4:
        # data order is clockwise from top: top, right, bottom, left
        top = data[0]
        right = data[1]
        bottom = data[2]
        left = data[3]
        ax, im = quatromatrix(top, right, bottom, left,
                              ax=ax,
                              tripcolorkw={"cmap": cmap, "norm": norm,
                                           "edgecolors": 'k', "linewidth": 0.5},
                              xaxis_labels=xaxis_labels,
                              yaxis_labels=yaxis_labels,
                              invert_yaxis=invert_yaxis)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False,
                   labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(),
             fontsize=xaxis_fontsize,
             rotation=-30, ha="right", rotation_mode="anchor")

    # Set font size for yaxis tick labels
    plt.setp(ax.get_yticklabels(), fontsize=yaxis_fontsize)

    # Legend
    if legend_on:
        if legend_labels is None:
            sys.exit("Error: legend_labels was not provided.")
        else:
            add_legend(num_divide, ax, legend_box_xy, legend_box_size,
                       labels=legend_labels, lw=legend_lw, fontsize=legend_fontsize)

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
            cbar.ax.set_ylabel(cbar_label, rotation=-90, va="bottom",
                               fontsize=cbar_label_fontsize)
            cbar.ax.tick_params(labelsize=cbar_tick_fontsize)

        return fig, ax, cbar
    else:
        return fig, ax


# ======================================================================
# Prepare data
# ----------------------------------------------------------------------
def prepare_data(data, xaxis_labels, yaxis_labels, debug):
    # In case data was given as list of arrays, convert it to numpy (stacked) array
    if (type(data) == list):
        if debug:
            print('data type is list')
            print('len(data):', len(data))
        if (len(data) == 1):  # list has only 1 array as element
            if ((type(data[0]) == np.ndarray) and (len(data[0].shape) == 2)):
                data = data[0]
                num_divide = 1
            else:
                sys.exit('Error: Element of given list is not in np.ndarray type')
        else:  # list has more than 1 arrays as elements
            data = np.stack(data)
            num_divide = len(data)

    # Now, data is expected to be be a numpy array (whether given or converted from list)
    if debug:
        print('data.shape:', data.shape)

    if data.shape[-1] != len(xaxis_labels) and len(xaxis_labels) > 0:
        sys.exit('Error: Number of elements in xaxis_label mismatchs to the data')

    if data.shape[-2] != len(yaxis_labels) and len(yaxis_labels) > 0:
        sys.exit('Error: Number of elements in yaxis_label mismatchs to the data')

    if (type(data) == np.ndarray):
        data = np.squeeze(data)
        if len(data.shape) == 2:
            num_divide = 1
        elif len(data.shape) == 3:
            num_divide = data.shape[0]
        else:
            print('data.shape:', data.shape)
            sys.exit('Error: data.shape is not right')
    else:
        sys.exit('Error: Converted or given data is not in np.ndarray type')

    if debug:
        print('num_divide:', num_divide)

    # Mask out nan data
    data = np.ma.masked_invalid(data)

    return data, num_divide


# ======================================================================
# Portrait plot 1: heatmap-style (no triangle)
# (Inspired from: https://matplotlib.org/devdocs/gallery/images_contours_and_fields/image_annotated_heatmap.html)
# ----------------------------------------------------------------------
def heatmap(data, row_labels, col_labels, ax=None,
            invert_yaxis=False,
            **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Parameters
    ----------
    data
        A 2D numpy array of shape (M, N).
    row_labels
        A list or array of length M with the labels for the rows.
    col_labels
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
    ax.set_xticks(np.arange(data.shape[1])+.5, minor=False)
    ax.set_yticks(np.arange(data.shape[0])+.5, minor=False)
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    ax.tick_params(which="minor", bottom=False, left=False)

    return ax, im


def annotate_heatmap(im, ax,
                     data=None,
                     annotate_data=None,
                     valfmt="{x:.2f}",
                     textcolors=("black", "white"),
                     threshold=None, **textkw):
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
        threshold = (data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
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
                kw.update(color=textcolors[int((data[i, j] > max(threshold)) or (data[i, j] < min(threshold)))])
            else:
                kw.update(color=textcolors[int(data[i, j] > threshold)])
            text = ax.text(j+.5, i+.5, valfmt(annotate_data[i, j], None), **kw)
            texts.append(text)


# ======================================================================
# Portrait plot 2 (two triangles)
# (Inspired from: https://stackoverflow.com/questions/44291155/plotting-two-distance-matrices-together-on-same-plot)
# ----------------------------------------------------------------------
def triamatrix_wrap_up(upper, lower, ax, xaxis_labels, yaxis_labels,
                       cmap="viridis", vmin=-3, vmax=3, norm=None,
                       invert_yaxis=True):

    # Colorbar range
    if norm is None:
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)

    # Triangles
    im = triamatrix(upper, ax, rot=270, cmap=cmap, norm=norm, edgecolors='k', lw=0.5)
    im = triamatrix(lower, ax, rot=90, cmap=cmap, norm=norm, edgecolors='k', lw=0.5)
    ax.set_xlim(-.5, upper.shape[1]-.5)
    ax.set_ylim(-.5, upper.shape[0]-.5)

    if invert_yaxis:
        ax.invert_yaxis()

    ax.set_xticks(np.arange(upper.shape[1]))
    ax.set_yticks(np.arange(upper.shape[0]))

    ax.set_xticklabels(xaxis_labels)
    ax.set_yticklabels(yaxis_labels)

    return ax, im


def triatpos(pos=(0, 0), rot=0):
    r = np.array([[-1, -1], [1, -1], [1, 1], [-1, -1]]) * .5
    rm = [[np.cos(np.deg2rad(rot)), -np.sin(np.deg2rad(rot))],
          [np.sin(np.deg2rad(rot)), np.cos(np.deg2rad(rot))]]
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
def quatromatrix(top, right, bottom, left, ax=None, tripcolorkw={},
                 xaxis_labels=None, yaxis_labels=None, invert_yaxis=True):
    if ax is None:
        ax = plt.gca()

    n = left.shape[0]
    m = left.shape[1]

    a = np.array([[0, 0], [0, 1], [.5, .5], [1, 0], [1, 1]])
    tr = np.array([[0, 1, 2], [0, 2, 3], [2, 3, 4], [1, 2, 4]])

    A = np.zeros((n*m*5, 2))
    Tr = np.zeros((n*m*4, 3))

    for i in range(n):
        for j in range(m):
            k = i * m + j
            A[k*5:(k+1)*5, :] = np.c_[a[:, 0]+j, a[:, 1]+i]
            Tr[k*4:(k+1)*4, :] = tr + k * 5

    if invert_yaxis:
        ax.invert_yaxis()
        C = np.c_[left.flatten(), top.flatten(),
                  right.flatten(), bottom.flatten()].flatten()
    else:
        C = np.c_[left.flatten(), bottom.flatten(),
                  right.flatten(), top.flatten()].flatten()

    # Prevent coloring missing data
    C = np.ma.array(C, mask=np.isnan(C))

    tripcolor = ax.tripcolor(A[:, 0], A[:, 1], Tr, facecolors=C, **tripcolorkw)

    ax.margins(0)

    if xaxis_labels is not None:
        x_loc = list_between_elements(np.arange(left.shape[1]+1))
        ax.set_xticks(x_loc)
        ax.set_xticklabels(xaxis_labels)
    if yaxis_labels is not None:
        y_loc = list_between_elements(np.arange(left.shape[0]+1))
        ax.set_yticks(y_loc)
        ax.set_yticklabels(yaxis_labels)

    return ax, tripcolor


def list_between_elements(a):
    a_between = []
    for i in range(len(a)):
        try:
            tmp = (a[i] + a[i+1])/2.
            a_between.append(tmp)
        except Exception:
            pass
    return a_between


# ======================================================================
# Portrait plot legend (four/two triangles)
# ======================================================================
def add_legend(num_divide, ax, box_xy=None, box_size=None, labels=None, lw=1, fontsize=14):
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
            labels = ['TOP', 'RIGHT', 'BOTTOM', 'LEFT']
        ax.add_patch(plt.Polygon([[box_x, box_y],
                                 [box_x + box_size/2., box_y + box_size/2],
                                 [box_x + box_size, box_y]],
                                 color="k", fill=False, clip_on=False, lw=lw))
        ax.add_patch(plt.Polygon([[box_x + box_size, box_y],
                                 [box_x + box_size/2., box_y + box_size/2],
                                 [box_x + box_size, box_y + box_size]],
                                 color="k", fill=False, clip_on=False, lw=lw))
        ax.add_patch(plt.Polygon([[box_x + box_size, box_y + box_size],
                                 [box_x + box_size/2., box_y + box_size/2],
                                 [box_x, box_y + box_size]],
                                 color="k", fill=False, clip_on=False, lw=lw))
        ax.add_patch(plt.Polygon([[box_x, box_y],
                                 [box_x + box_size/2., box_y + box_size/2],
                                 [box_x, box_y + box_size]],
                                 color="k", fill=False, clip_on=False, lw=lw))
        ax.text(box_x + box_size * 0.5, box_y + box_size * 0.2, labels[0],
                ha='center', va='center', fontsize=fontsize)
        ax.text(box_x + box_size * 0.8, box_y + box_size * 0.5, labels[1],
                ha='center', va='center', fontsize=fontsize)
        ax.text(box_x + box_size * 0.5, box_y + box_size * 0.8, labels[2],
                ha='center', va='center', fontsize=fontsize)
        ax.text(box_x + box_size * 0.2, box_y + box_size * 0.5, labels[3],
                ha='center', va='center', fontsize=fontsize)
    elif num_divide == 2:
        if labels is None:
            labels = ['UPPER', 'LOWER']
        ax.add_patch(plt.Polygon([[box_x, box_y],
                                 [box_x, box_y + box_size],
                                 [box_x + box_size, box_y]],
                                 color="k", fill=False, clip_on=False, lw=lw))
        ax.add_patch(plt.Polygon([[box_x + box_size, box_y + box_size],
                                 [box_x, box_y + box_size],
                                 [box_x + box_size, box_y]],
                                 color="k", fill=False, clip_on=False, lw=lw))
        ax.text(box_x + box_size * 0.05, box_y + box_size * 0.2, labels[0],
                ha='left', va='center', fontsize=fontsize)
        ax.text(box_x + box_size * 0.95, box_y + box_size * 0.8, labels[1],
                ha='right', va='center', fontsize=fontsize)
