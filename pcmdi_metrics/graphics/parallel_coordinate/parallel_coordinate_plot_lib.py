from matplotlib.cbook import flatten
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import numpy as np



def parallel_plot(data, metric_names, model_names, model_highlights=list(),
                  show_boxplot=True, show_violin=True, title=None, identify_all_models=True,
                  filename='test', figsize=(15, 5),
                  xtick_labels=None, colormap='viridis'):
    """
    Input
    -----
    - data: 2-d numpy array for metrics
    - metric_names: list, names of metrics for individual vertical axes (axis=1)
    - model_names: list, name of models for markers/lines (axis=0)
    - model_highlights: list, default=None, List of models to highlight as lines
    - show_boxplot: bool, default=True, show box and wiskers plot
    - show_violin: bool, default=True, show violin plot
    - title: string, default=None, plot title
    - identify_all_models: bool, default=True. Show and identify all models using markers
    - filename: string, default='test', file name for saving the plot
    - figsize: tuple (two numbers), default=(15,5), image size
    - xtick_labels: list, default=None, list of strings that to use as metric names (optional)
    - colormap: string, default='viridis', matplotlib colormap
    """
    params = {'legend.fontsize': 'large',
              'axes.labelsize': 'x-large',
              'axes.titlesize':'x-large',
              'xtick.labelsize':'x-large',
              'ytick.labelsize':'x-large'}
    pylab.rcParams.update(params)

    # Quick initial QC
    if data.shape[0] != len(model_names):
        sys.exit('Error: data.shape[0], ' + str(data.shape[0])
                 + ', mismatch to len(model_names), ' + str(len(model_names)))
    if data.shape[1] != len(metric_names):
        sys.exit('Error: data.shape[1], ' + str(data.shape[1])
                 +', mismatch to len(metric_names), ' + str(len(metric_names)))
    if xtick_labels != None:
        if len(xtick_labels) != len(metric_names):
            sys.exit('Error: xtick_labels has different number than metric_names')

    # Data to plot
    ys = data  # stacked y-axis values
    N = ys.shape[1]  # number of vertical axis (i.e., =len(metric_names))
    ymins = np.nanmin(ys, axis=0)
    ymaxs = np.nanmax(ys, axis=0)
    dys = ymaxs - ymins
    ymins -= dys * 0.05  # add 5% padding below and above
    ymaxs += dys * 0.05
    dys = ymaxs - ymins

    # Transform all data to be compatible with the main axis
    zs = np.zeros_like(ys)
    zs[:, 0] = ys[:, 0]
    zs[:, 1:] = (ys[:, 1:] - ymins[1:]) / dys[1:] * dys[0] + ymins[0]

    # Prepare plot
    if N > 20:
        if xtick_labels is not None:
            xtick_labelsize = 'medium'
        else:
            xtick_labelsize = 'large'
        ytick_labelsize = 'large'
    else:
        xtick_labelsize = 'x-large'
        ytick_labelsize = 'x-large'
    params = {'legend.fontsize': 'large',
              'axes.labelsize': 'x-large',
              'axes.titlesize': 'x-large',
              'xtick.labelsize': xtick_labelsize,
              'ytick.labelsize': ytick_labelsize}
    pylab.rcParams.update(params)

    fig, host = plt.subplots(figsize=figsize)

    axes = [host] + [host.twinx() for i in range(N - 1)]

    for i, ax in enumerate(axes):
        ax.set_ylim(ymins[i], ymaxs[i])
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        if ax == host:
            ax.spines["left"].set_position(("data", i))
        if ax != host:
            ax.spines['left'].set_visible(False)
            ax.yaxis.set_ticks_position('right')
            ax.spines["right"].set_position(("data", i))

    # Population distribuion on each vertical axis
    if show_boxplot or show_violin:
        y = [zs[:, i] for i in range(N)]
        y_filtered = [y_i[~np.isnan(y_i)] for y_i in y]  # Remove NaN value for box/violin plot

        # Box plot
        if show_boxplot:
            box = host.boxplot(y_filtered, positions=range(N), 
                               patch_artist=True, widths=0.15)
            for item in ['boxes', 'whiskers', 'fliers', 'medians', 'caps']:
                plt.setp(box[item], color='darkgrey')
            plt.setp(box["boxes"], facecolor='None')
            plt.setp(box["fliers"], markeredgecolor='darkgrey')

        # Violin plot
        if show_violin:
            violin = host.violinplot(y_filtered, positions=range(N),
                                     showmeans=False, showmedians=False, showextrema=False)
            for pc in violin['bodies']:
                pc.set_facecolor('lightgrey')
                pc.set_edgecolor('None')
                pc.set_alpha(0.8)
    
    # Line or marker
    num_color = 10
    colors = [plt.get_cmap(colormap)(c) for c in np.linspace(0, 1, num_color)]
    marker_types = ['o', 's', '*', '^', 'X', 'D']
    markers = list(flatten([[marker] * len(colors) for marker in marker_types]))
    colors *= len(marker_types)
    for j, model in enumerate(model_names):
        # to just draw straight lines between the axes:
        if model in model_highlights:
            host.plot(range(N), zs[j,:], '-',
                      c=colors[j],
                      label=model, lw=3)
        else:
            if identify_all_models:
                host.plot(range(N), zs[j,:], markers[j],
                          c=colors[j],
                          label=model,
                          clip_on=False)        

    host.set_xlim(-0.5, N - 0.5)
    host.set_xticks(range(N))
    if xtick_labels is not None:
        host.set_xticklabels(xtick_labels, fontsize=xtick_labelsize)
    else:
        host.set_xticklabels(metric_names, fontsize=xtick_labelsize)
    host.tick_params(axis='x', which='major', pad=7)
    host.spines['right'].set_visible(False)
    host.set_title(title, fontsize=18)
    host.legend(loc='upper center', ncol=6, bbox_to_anchor=(0.5, -0.14))

    if 'png' != filename.split('.')[-1]:
        filename += '.png'

    plt.savefig(filename, bbox_inches="tight")
