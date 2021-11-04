import numpy as np
import matplotlib.pyplot as PLT
import sys
import pdb


class BarChart(object):
    def __init__(self, mods, data, uni, fig=None, rect=111, **kwargs):

        print("IN FCN..... ")

        # Canvas setup
        if fig is None:
            fig = PLT.figure
        ax = fig.add_subplot(rect)

        # Enable to control ax options outside of this file
        self._ax = ax

        # Axis setup
        unit_adjust = 1.0
        if "yaxis_label" in kwargs:
            unit = kwargs["label"]
        else:
            unit = uni  # 'Unit needed here ...'
        print("data above max ")
        ymax = max(data)
        ymin = min(data)
        #   yint = float((ymax-ymin)/3.)  # REPLACE INT WITH FLOAT
        yint = 0.004

        # Array setup
        num_mods = len(mods)
        x = np.linspace(0, num_mods - 1, num_mods)
        y = np.array(data) * unit_adjust
        labels = mods

        # Plotting
        ax.bar(x, y, bottom=0, align="center", color="b")
        # JS: add the bars for each simulation
        if "highlights" in kwargs:
            highlights = kwargs["highlights"]
            # -- Dealing with the colors
            if "colors" in kwargs:
                colors = str.split(kwargs["colors"], ",")
                if len(colors) != len(highlights):
                    if len(colors) == 1:
                        # -- if we provide only one color, we will use it for every highlighted simulation
                        colors = colors * len(highlights)
                    else:
                        # -- if we didn't provide enough colors (for the number of simulations),
                        #    we will use green as a default
                        tmpcolors = ["g"] * len(highlights)
                        for i in range(len(colors)):
                            tmpcolors[i] = colors[i]
                        colors = tmpcolors
            else:
                colors = ["g"] * len(highlights)
            print("highlights = ", highlights)
            for highlight in highlights:
                y_highlight = [0] * len(y)

                y_highlight[mods.index(highlight)] = y[mods.index(highlight)]
                ax.bar(
                    x,
                    y_highlight,
                    bottom=0,
                    align="center",
                    color=colors[highlights.index(highlight)],
                )
        ax.axhline(0, color="black")

        # Title and axis
        ax.set_title("Subtitle needed here..")
        ax.set_xlabel("Models")
        ax.set_ylabel(unit)
        ax.set_xlim([-1.0, len(y) - 0.5])
        ax.set_ylim([y.min() * 1.1, y.max() * 1.1])
        ax.grid(True)

        # Axis labels
        # Label x-axis as model names
        PLT.xticks(x, labels, rotation="vertical")
        ax.yaxis.set_ticks(np.arange(int(ymin - yint), int(ymax + yint), yint))

        # Multi model mean / std. dev. / min / max
        yave = np.mean(y)
        ystd = np.std(y)
        ymin = np.amin(y)
        ymax = np.amax(y)

        ax.plot(-0.7, yave, "x", c="red", markersize=12)  # ave
        ax.plot(-0.7, ymin, "+", c="red", markersize=12)  # min
        ax.plot(-0.7, ymax, "+", c="red", markersize=12)  # max
        # inter-model std. dev.
        ax.errorbar(-0.7, yave, yerr=ystd, ls="solid", color="red", linewidth=1)
