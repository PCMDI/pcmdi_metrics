def TaylorDiagram(
        stddev, corrcoef, refstd,
        fig=None,
        colors=None,
        cmap=None,
        normalize=False,
        labels=None, markers=None, markersizes=None, zorders=None,
        ref_label=None, smax=None,
        compare_models=None,
        arrowprops_dict=None,
        annotate_text=None,
        radial_axis_title=None,
        angular_axis_title=None):

    """Plot a Taylor diagram

    This code was adpated from the ILAMB code that was written by Nathan Collier (ORNL)
    (https://github.com/rubisco-sfa/ILAMB/blob/master/src/ILAMB/Post.py#L80)
    and revised by Jiwoo Lee (LLNL) to implement into PMP and to enable more customizations.

    The original code was written by Yannick Copin:
    https://gist.github.com/ycopin/3342888

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
    rlocs = np.concatenate((np.arange(10) / 10., [0.95, 0.99]))
    tlocs = np.arccos(rlocs)
    gl1 = GF.FixedLocator(tlocs)
    tf1 = GF.DictFormatter(dict(zip(tlocs, map(str, rlocs))))

    # standard deviation axis extent
    if normalize:
        stddev = stddev / refstd
        refstd = 1.
    smin = 0
    if smax is None:
        smax = max(2.0, 1.1 * stddev.max())

    # add the curvilinear grid
    ghelper = FA.GridHelperCurveLinear(tr,
                                       extremes=(0, np.pi / 2, smin, smax),
                                       grid_locator1=gl1,
                                       tick_formatter1=tf1)

    if fig is None:
        fig = plt.figure(figsize=(8, 8))

    ax = FA.FloatingSubplot(fig, 111, grid_helper=ghelper)
    fig.add_subplot(ax)

    if colors is None:
        if cmap is None:
            cmap = 'viridis'
        cm = plt.get_cmap(cmap)
        colors = cm(np.linspace(0.1, 0.9, len(stddev)))

    # adjust axes
    ax.axis["top"].set_axis_direction("bottom")
    ax.axis["top"].toggle(ticklabels=True, label=True)
    ax.axis["top"].major_ticklabels.set_axis_direction("top")
    ax.axis["top"].label.set_axis_direction("top")
    if angular_axis_title is None:
        ax.axis["top"].label.set_text("Correlation")
    else:
        ax.axis["top"].label.set_text(angular_axis_title)

    ax.axis["left"].set_axis_direction("bottom")
    if radial_axis_title is None:
        if normalize:
            ax.axis["left"].label.set_text("Normalized standard deviation")
        else:
            ax.axis["left"].label.set_text("Standard deviation")
    else:
        ax.axis["left"].label.set_text(radial_axis_title)

    ax.axis["right"].set_axis_direction("top")
    ax.axis["right"].toggle(ticklabels=True)
    ax.axis["right"].major_ticklabels.set_axis_direction("left")

    ax.axis["bottom"].set_visible(False)
    ax.grid(True)

    ax = ax.get_aux_axes(tr)

    # Add reference point and stddev contour
    ax.plot([0], refstd, 'k*', ms=12, mew=0, label=ref_label)
    t = np.linspace(0, np.pi / 2)
    r = np.zeros_like(t) + refstd
    ax.plot(t, r, 'k--')

    # centralized rms contours
    rs, ts = np.meshgrid(np.linspace(smin, smax),
                         np.linspace(0, np.pi / 2))
    rms = np.sqrt(refstd**2 + rs**2 - 2 * refstd * rs * np.cos(ts))
    contours = ax.contour(ts, rs, rms, 5, colors='k', alpha=0.4)
    ax.clabel(contours, fmt='%1.1f')

    # Plot data
    corrcoef = corrcoef.clip(-1, 1)
    for i in range(len(corrcoef)):
        # customize label
        if labels is not None:
            label = labels[i]
        else:
            label = None
        # customize marker
        if markers is not None:
            marker = markers[i]
        else:
            marker = 'o'
        # customize marker size
        if markersizes is not None:
            ms = markersizes[i]
        else:
            ms = 8
        # customize marker order
        if zorders is not None:
            zorder = zorders[i]
        else:
            zorder = None
        # customize end
        ax.plot(np.arccos(corrcoef[i]), stddev[i], marker, color=colors[i], mew=0, ms=ms, label=label, zorder=zorder)

    # Add arrow
    if arrowprops_dict is None:
        arrowprops_dict = dict(facecolor='black',
                               lw=0.5,
                               width=0.5,
                               shrink=0.05)  # shrink arrow length little bit to make it look good...
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
                xycoords='data',
                textcoords='data',
                arrowprops=arrowprops_dict,
                horizontalalignment='center',
                verticalalignment='center')

    return fig, ax
