import math


def TaylorDiagram(
    stddev,
    corrcoef,
    refstd,
    fig=None,
    rect=111,
    title=None,
    titleprops_dict=dict(),
    colors=None,
    cmap=None,
    normalize=False,
    labels=None,
    markers=None,
    markersizes=None,
    closed_marker=True,
    markercloses=None,
    zorders=None,
    ref_label=None,
    smax=None,
    compare_models=None,
    arrowprops_dict=None,
    annotate_text=None,
    radial_axis_title=None,
    angular_axis_title="Correlation",
    grid=True,
    debug=False,
):

    """Plot a Taylor diagram

    Jiwoo Lee (PCMDI LLNL) - last update: 2022. 10

    This code was adpated from the ILAMB code that was written by Nathan Collier (ORNL)
    (https://github.com/rubisco-sfa/ILAMB/blob/master/src/ILAMB/Post.py#L80)
    and revised by Jiwoo Lee (LLNL) to add capabilities and enable more customizations
    for implementation into PCMDI Metrics Package (PMP).
    The original code was written by Yannick Copin (https://gist.github.com/ycopin/3342888)

    Reference for Taylor Diagram:
    Taylor, K. E. (2001), Summarizing multiple aspects of model performance in a single diagram,
    J. Geophys. Res., 106(D7), 7183–7192, http://dx.doi.org/10.1029/2000JD900719


    Parameters
    ----------
    stddev : numpy.ndarray
        an array of standard deviations
    corrcoef : numpy.ndarray
        an array of correlation coefficients
    refstd : float
        the reference standard deviation
    fig : matplotlib figure, optional
        the matplotlib figure
    rect : a 3-digit integer, optional
        ax subplot rect, , default is 111, which indicate the figure has 1 row, 1 column, and this plot is the first plot.
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot.html
        https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.add_subplot
    title : string, optional
        title for the plot
    titleprops_dict : dict, optional
        title property dict (e.g., fontsize)
    cmap : string, optional
        a name of matplotlib colormap
        https://matplotlib.org/stable/gallery/color/colormap_reference.html
    colors : array, optional
        an array or list of colors for each element of the input arrays
        if colors is given, it will override cmap
    normalize : bool, optional
        disable to skip normalization of the standard deviation
        default is False
    labels : list, optional
        list of text for labels
    markers : list, optional
        list of marker type
    markersizes : list, optional
        list of integer for marker size
    closed_marker : bool, optional
        closed marker or opened marker
        default - True
    markercloses : list of bool,  optional
        When closed_marker is False but you still want to have a few closed markers among opened markers, provide list of True (close) or False (open)
        default - None
    zorders : list, optional
        list of integer for zorder
    ref_label : str, optional
        label for reference data
    smax : int or float, optional
        maximum of axis range for (normalized) standard deviation
    compare_models : list of tuples, optional
        list of pair of two models to compare by showing arrows
    arrowprops_dict: dict, optional
        dict for matplotlib annotation arrowprops for compare_models arrow
        See https://matplotlib.org/stable/tutorials/text/annotations.html for details
    annotate_text : string, optional
        text to place at the begining of the comparing arrow
    radial_axis_title : string, optional
        axis title for radial axis
        default - Standard deviation (when normalize=False) or Normalized standard deviation (when normalize=True)
    angular_axis_title : string, optional
        axis title for angular axis
        default - Correlation
    grid : bool, optional
        grid line in plot
        default - True
    debug : bool, optional
        default - False
        if true print some interim results for debugging purpose

    Return
    ------
    fig : matplotlib figure
        the matplotlib figure
    ax : matplotlib axis
        the matplotlib axis
    """
    import matplotlib.pyplot as plt
    import mpl_toolkits.axisartist.floating_axes as FA
    import mpl_toolkits.axisartist.grid_finder as GF
    import numpy as np
    from matplotlib.projections import PolarAxes

    # define transform
    tr = PolarAxes.PolarTransform()

    # correlation labels
    rlocs = np.concatenate((np.arange(10) / 10.0, [0.95, 0.99]))
    tlocs = np.arccos(rlocs)
    gl1 = GF.FixedLocator(tlocs)
    tf1 = GF.DictFormatter(dict(zip(tlocs, map(str, rlocs))))

    # standard deviation axis extent
    if normalize:
        stddev = stddev / refstd
        refstd = 1.0

    # Radial axis range
    smin = 0
    if smax is None:
        smax = max(2.0, 1.1 * stddev.max())

    # add the curvilinear grid
    ghelper = FA.GridHelperCurveLinear(
        tr, extremes=(0, np.pi / 2, smin, smax), grid_locator1=gl1, tick_formatter1=tf1
    )

    if fig is None:
        fig = plt.figure(figsize=(8, 8))

    ax = fig.add_subplot(rect, axes_class=FA.FloatingAxes, grid_helper=ghelper)

    if title is not None:
        ax.set_title(title, **titleprops_dict)

    if colors is None:
        if cmap is None:
            cmap = "viridis"
        cm = plt.get_cmap(cmap)
        colors = cm(np.linspace(0.1, 0.9, len(stddev)))

    if radial_axis_title is None:
        if normalize:
            radial_axis_title = "Normalized standard deviation"
        else:
            radial_axis_title = "Standard deviation"

    # adjust axes
    ax.axis["top"].set_axis_direction("bottom")
    ax.axis["top"].toggle(ticklabels=True, label=True)
    ax.axis["top"].major_ticklabels.set_axis_direction("top")
    ax.axis["top"].label.set_axis_direction("top")
    ax.axis["top"].label.set_text(angular_axis_title)
    ax.axis["left"].set_axis_direction("bottom")
    ax.axis["left"].label.set_text(radial_axis_title)
    ax.axis["right"].set_axis_direction("top")
    ax.axis["right"].toggle(ticklabels=True)
    ax.axis["right"].major_ticklabels.set_axis_direction("left")
    ax.axis["bottom"].set_visible(False)
    ax.grid(grid)

    ax = ax.get_aux_axes(tr)

    # Add reference point and stddev contour
    ax.plot([0], refstd, "k*", ms=12, mew=0, label=ref_label)
    t = np.linspace(0, np.pi / 2)
    r = np.zeros_like(t) + refstd
    ax.plot(t, r, "k--")

    # centralized rms contours
    rs, ts = np.meshgrid(np.linspace(smin, smax), np.linspace(0, np.pi / 2))
    rms = np.sqrt(refstd**2 + rs**2 - 2 * refstd * rs * np.cos(ts))
    contours = ax.contour(ts, rs, rms, 5, colors="k", alpha=0.4)
    ax.clabel(contours, fmt="%1.1f")

    # Plot data
    corrcoef = corrcoef.clip(-1, 1)
    for i in range(len(corrcoef)):
        # --- customize start ---
        # customize label
        if labels is None:
            label = None
        else:
            label = labels[i]
        # customize marker
        if markers is None:
            marker = "o"
        else:
            marker = markers[i]
        # customize marker size
        if markersizes is None:
            ms = 8
        else:
            ms = markersizes[i]
        # customize marker order
        if zorders is None:
            zorder = None
        else:
            zorder = zorders[i]
        # customize marker closed/opened
        if closed_marker:
            markerclose = True
        else:
            if markercloses is None:
                markerclose = False
            else:
                markerclose = markercloses[i]

        if markerclose:
            if closed_marker:
                marker_dict = dict(
                    color=colors[i],
                    mew=0,
                )
            else:
                marker_dict = dict(mfc=colors[i], mec="k", mew=1)
        else:
            marker_dict = dict(
                mec=colors[i],
                mfc="none",
                mew=1,
            )
        # --- customize end ---

        # -------------------------
        # place marker on the graph
        # -------------------------
        ax.plot(
            np.arccos(corrcoef[i]),
            stddev[i],
            marker,
            ms=ms,
            label=label,
            zorder=zorder,
            **marker_dict,
        )

        # debugging
        if debug:
            crmsd = math.sqrt(
                stddev[i] ** 2 + refstd**2 - 2 * stddev[i] * refstd * corrcoef[i]
            )  # centered rms difference
            print(
                "i, label, corrcoef[i], np.arccos(corrcoef[i]), stddev[i], crmsd:",
                i,
                label,
                corrcoef[i],
                np.arccos(corrcoef[i]),
                stddev[i],
                crmsd,
            )

    # Add arrow(s)
    if arrowprops_dict is None:
        arrowprops_dict = dict(
            facecolor="black", lw=0.5, width=0.5, shrink=0.05
        )  # shrink arrow length little bit to make it look good...
    if compare_models is not None:
        for compare_models_pair in compare_models:
            index_model1 = labels.index(compare_models_pair[0])
            index_model2 = labels.index(compare_models_pair[1])
            theta1 = np.arccos(corrcoef[index_model1])
            theta2 = np.arccos(corrcoef[index_model2])
            r1 = stddev[index_model1]
            r2 = stddev[index_model2]

            ax.annotate(
                annotate_text,
                xy=(theta2, r2),  # theta, radius of arrival
                xytext=(theta1, r1),  # theta, radius of departure
                xycoords="data",
                textcoords="data",
                arrowprops=arrowprops_dict,
                horizontalalignment="center",
                verticalalignment="center",
            )

    return fig, ax
