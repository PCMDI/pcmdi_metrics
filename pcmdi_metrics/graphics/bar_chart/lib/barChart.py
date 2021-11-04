import matplotlib.pyplot as plt
import numpy as np


class BarChart(object):
    def __init__(self, mods, data, stat, unit=None, unit_adjust=1, fig=None, rect=111):

        # Canvas setup
        if fig is None:
            fig = plt.figure
        ax = fig.add_subplot(rect)

        # Enable to control ax options outside of this file
        self._ax = ax

        # Axis setup
        ymax = max(data)
        ymin = min(data)

        # Array setup
        num_mods = len(mods)
        x = np.linspace(0, num_mods - 1, num_mods)
        y = np.array(data) * unit_adjust
        labels = mods

        # Plotting
        ax.bar(x, y, bottom=0, align="center")
        ax.axhline(0, color="black")

        # Title and axis
        ax.set_title("Subtitle needed here")
        ax.set_xlabel("Models")
        ylabel = stat
        if unit is not None:
            ylabel = stat + ", (" + unit + ")"
        ax.set_ylabel(ylabel)
        ax.set_xlim([-1.0, len(y) - 0.5])
        ax.set_ylim([y.min() * 1.1, y.max() * 1.1])

        # Axis labels
        plt.xticks(x, labels, rotation="vertical")  # Label x-axis as model names

        # Multi model mean / std. dev. / min / max
        yave = np.mean(y)
        ystd = np.std(y)
        ymin = np.amin(y)
        ymax = np.amax(y)

        ax.plot(-0.7, yave, "x", c="red", markersize=12)  # ave
        ax.plot(-0.7, ymin, "+", c="red", markersize=12)  # min
        ax.plot(-0.7, ymax, "+", c="red", markersize=12)  # max
        ax.errorbar(
            -0.7, yave, yerr=ystd, ls="solid", color="red", linewidth=1
        )  # inter-model std. dev.
