def TaylorDiagram(
        stddev, corrcoef, refstd, fig, colors,
        normalize=True,
        labels=None, markers=None, markersizes=None, zorders=None,
        ref_label=None, smax=None):

    """Plot a Taylor diagram.
    This code was adpated from the ILAMB code by Nathan Collier found here:
    https://github.com/rubisco-sfa/ILAMB/blob/master/src/ILAMB/Post.py#L80,
    which was revised by Jiwoo Lee to enable more customization.

    The original code was written by Yannick Copin that can be found here:
    https://gist.github.com/ycopin/3342888

    Parameters
    ----------
    stddev : numpy.ndarray
        an array of standard deviations
    corrcoeff : numpy.ndarray
        an array of correlation coefficients
    refstd : float
        the reference standard deviation
    fig : matplotlib figure
        the matplotlib figure
    colors : array
        an array of colors for each element of the input arrays
    normalize : bool, optional
        disable to skip normalization of the standard deviation
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

    Return
    ------
    fig : matplotlib figure
        the matplotlib figure
    ax : matplotlib axis
        the matplotlib axis
    """
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
    ax = FA.FloatingSubplot(fig, 111, grid_helper=ghelper)
    fig.add_subplot(ax)

    # adjust axes
    ax.axis["top"].set_axis_direction("bottom")
    ax.axis["top"].toggle(ticklabels=True, label=True)
    ax.axis["top"].major_ticklabels.set_axis_direction("top")
    ax.axis["top"].label.set_axis_direction("top")
    ax.axis["top"].label.set_text("Correlation")
    ax.axis["left"].set_axis_direction("bottom")
    if normalize:
        ax.axis["left"].label.set_text("Normalized standard deviation")
    else:
        ax.axis["left"].label.set_text("Standard deviation")
    ax.axis["right"].set_axis_direction("top")
    ax.axis["right"].toggle(ticklabels=True)
    ax.axis["right"].major_ticklabels.set_axis_direction("left")
    ax.axis["bottom"].set_visible(False)
    ax.grid(True)

    ax = ax.get_aux_axes(tr)
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

    # Add reference point and stddev contour
    l, = ax.plot([0], refstd, 'k*', ms=12, mew=0, label=ref_label)
    t = np.linspace(0, np.pi / 2)
    r = np.zeros_like(t) + refstd
    ax.plot(t, r, 'k--')

    # centralized rms contours
    rs, ts = np.meshgrid(np.linspace(smin, smax),
                         np.linspace(0, np.pi / 2))
    rms = np.sqrt(refstd**2 + rs**2 - 2 * refstd * rs * np.cos(ts))
    contours = ax.contour(ts, rs, rms, 5, colors='k', alpha=0.4)
    ax.clabel(contours, fmt='%1.1f')

    return fig, ax
