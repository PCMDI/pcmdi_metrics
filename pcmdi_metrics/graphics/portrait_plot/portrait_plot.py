import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import sys


def portrait_plot(data, 
                  xaxis_labels,
                  yaxis_labels,
                  annotate=False, annotate_data=None, annotate_fontsize=15,
                  figsize=(12,10), vrange=(-3,3),
                  xaxis_fontsize=15, yaxis_fontsize=15,
                  cmap="RdBu_r",
                  cbarlabel=None,
                  cbar_label_fontsize=15,
                  cbar_tick_fontsize=12,
                  invert_yaxis=True,
                  box_as_square=False,
                  debug=False):
    """
    Parameters
    ----------
    - `data`: 2d numpy array, a list of 2d numpy arrays, or a 3d numpy array (i.e. stacked 2d numpy arrays)
    - `xaxis_labels`: list of strings, labels for xaixs
    - `yaxis_labels`: list of strings, labels for yaxis
    - `annotate`: bool, default=False, add annotating text if true, but work only for heatmap style map (i.e., no triangles)
    - `annotate_data`: 2d numpy array, default=None. If None, the image's data is used.  Optional. 
    - `annotate_fontsize`: number (int/float), default=15. Font size for annotation
    - `figsize`: tuple of two numbers, default=(12, 10), figure size
    - `vrange`: tuple of two numbers, default=(-3, 3), range of value for colorbar
    - `xaxis_fontsize`: number, default=15, font size for xaxis tick labels
    - `yaxis_fontsize`: number, default=15, font size for yaxis tick labels
    - `cmap`: string, default="RdBu_r", name of matplotlib colormap
    - `cbarlabel`: string, default=None, label for colorbar
    - `cbar_label_fontsize`: number, default=15, font size for colorbar labels
    - `cbar_tick_fontsize`: number, default=12, font size for colorbar tick labels
    - `invert_yaxis`: bool, default=True, place y=0 at top on the plot
    - `box_as_square`: bool, default=False, make each box as square
    - `debug`: bool, default=False, if true print more message when running that help debugging

    Return
    ------
    - `fig`: matplotlib component for figure
    - `ax`: matplotlib component for axis
    - `cbar`: matplotlib component for colorbar
    
    Author: Jiwoo Lee @ LLNL (2021. 7)
    """

    # ----------------
    # Prepare plotting
    # ----------------
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

    if data.shape[-1] != len(xaxis_labels):
        sys.exit('Error: Number of elements in xaxis_label mismatchs to the data')

    if data.shape[-2] != len(yaxis_labels):
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
    
    if num_divide not in [1, 2, 4]:
        sys.exit('Error: Number of (stacked) array is not 1, 2, or 4.')

    # ----------------
    # Ready to plot!!
    # ----------------
    fig, ax = plt.subplots(figsize=figsize)
    vmin = min(vrange)
    vmax = max(vrange)

    # [1] Heatmap-style portrait plot (no triangles)
    if num_divide == 1:
        ax, cbar, im = heatmap(data, yaxis_labels, xaxis_labels,
                               ax=ax,
                               invert_yaxis=invert_yaxis,
                               cmap=cmap,
                               vmin=vmin, vmax=vmax,
                               edgecolors='k', linewidth=0.5)
        if annotate:
            if annotate_data is not None:
                if (annotate_data.shape != data.shape):
                    sys.exit('Error: annotate_data has different size than data')
            else:
                annotate_data = data
            annotate_heatmap(im, ax=ax,
                             data=data,
                             annotate_data=annotate_data,
                             valfmt="{x:.2f}", threshold=(2, -2),
                             fontsize=annotate_fontsize)

    # [2] Two triangle portrait plot
    elif num_divide == 2:
        upper = data[0]
        lower = data[1]
        ax, cbar = triamatrix_wrap_up(upper, lower, ax, 
                                      xaxis_labels=xaxis_labels, 
                                      yaxis_labels=yaxis_labels,
                                      cmap=cmap,
                                      vmin=vmin, vmax=vmax,
                                      invert_yaxis=invert_yaxis)

    # [4] Four triangle portrait plot
    elif num_divide == 4:
        top = data[0]
        right = data[1]
        bottom = data[2]
        left = data[3]
        ax, cbar = quatromatrix(top, right, bottom, left, ax=ax,
                                tripcolorkw={"cmap": cmap,
                                             "vmin": vmin, "vmax": vmax,
                                             "edgecolors":'k', "linewidth":0.5},
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

    # Label for colorbar
    if cbarlabel is not None:
        cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom",
                           fontsize=cbar_label_fontsize)
        cbar.ax.tick_params(labelsize=cbar_tick_fontsize)

    if box_as_square:
        ax.set_aspect("equal")

    return fig, ax, cbar


# ======================================================================
# Portrait plot 1: heatmap-style (no triangle)
# (Revised from: https://matplotlib.org/devdocs/gallery/images_contours_and_fields/image_annotated_heatmap.html)
# ----------------------------------------------------------------------
def heatmap(data, row_labels, col_labels, ax=None,
            invert_yaxis=False,
            cbar_kw={}, **kwargs):
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
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if not ax:
        ax = plt.gca()
        
    if invert_yaxis:
        ax.invert_yaxis()

    # Plot the heatmap
    im = ax.pcolormesh(data, **kwargs)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)

    # Show all ticks and label them with the respective list entries.
    ax.set_xticks(np.arange(data.shape[1])+.5, minor=False)
    ax.set_yticks(np.arange(data.shape[0])+.5, minor=False)
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    ax.tick_params(which="minor", bottom=False, left=False)

    return ax, cbar, im


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

    return texts


# ======================================================================
# Portrait plot 2 (two triangles)
# (Revised from: https://stackoverflow.com/questions/44291155/plotting-two-distance-matrices-together-on-same-plot)
# ----------------------------------------------------------------------
def triamatrix_wrap_up(upper, lower, ax, xaxis_labels, yaxis_labels, 
                       cmap="viridis", vmin=-3, vmax=3,
                       invert_yaxis=True):

    # Colorbar range
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)

    # Triangles
    im1 = triamatrix(upper, ax, rot=270, cmap=cmap, norm=norm, edgecolors='k', lw=0.5)
    im2 = triamatrix(lower, ax, rot=90, cmap=cmap, norm=norm, edgecolors='k', lw=0.5)
    ax.set_xlim(-.5, upper.shape[1]-.5)
    ax.set_ylim(-.5, upper.shape[0]-.5)

    if invert_yaxis:
        ax.invert_yaxis()

    ax.set_xticks(np.arange(upper.shape[1]))
    ax.set_yticks(np.arange(upper.shape[0]))

    ax.set_xticklabels(xaxis_labels)
    ax.set_yticklabels(yaxis_labels)

    cbar = ax.figure.colorbar(im1, ax=ax)

    return ax, cbar


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
            segs.append(triatpos((j,i), rot=rot))
    col = collections.PolyCollection(segs, cmap=cmap, **kwargs)
    col.set_array(a.flatten())
    ax.add_collection(col)
    return col


# ======================================================================
# Portrait plot 4 (four triangles)
# (Revised from: https://stackoverflow.com/questions/44666679/something-like-plt-matshow-but-with-triangles)
# ----------------------------------------------------------------------
def quatromatrix(top, right, bottom, left, ax=None, tripcolorkw={}, 
                 xaxis_labels=None, yaxis_labels=None, invert_yaxis=True):
    if not ax: 
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
            A[k*5:(k+1)*5, :] = np.c_[a[:,0]+j, a[:,1]+i]
            Tr[k*4:(k+1)*4, :] = tr + k * 5
            
    if invert_yaxis:
        ax.invert_yaxis()
        C = np.c_[left.flatten(), top.flatten(), 
                  right.flatten(), bottom.flatten()].flatten()        
    else:
        C = np.c_[left.flatten(), bottom.flatten(), 
                  right.flatten(), top.flatten()].flatten()

    tripcolor = ax.tripcolor(A[:,0], A[:,1], Tr, facecolors=C, **tripcolorkw)
    
    ax.margins(0)
    
    if xaxis_labels is not None:
        x_loc = list_between_elements(np.arange(left.shape[1]+1))
        plt.xticks(x_loc, xaxis_labels)
    if yaxis_labels is not None:
        y_loc = list_between_elements(np.arange(left.shape[0]+1))
        plt.yticks(y_loc, yaxis_labels)
    
    cbar = ax.figure.colorbar(tripcolor, ax=ax)
       
    return ax, cbar


def list_between_elements(a):
    a_between = []
    for i in range(len(a)):
        try:
            tmp = (a[i] + a[i+1])/2.
            a_between.append(tmp)
        except:
            pass
    return a_between